# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView
from Plein.menu import menu_dynamics
from Mailer.models import mailer_obfuscate_email
from Logboek.models import schrijf_in_logboek
from Overig.helpers import get_safe_from_ip
from Mailer.models import mailer_email_is_valide
from Account.models import AccountCreateError, account_create
from Account.views import account_vraag_email_bevestiging
from Functie.models import Functie
from NhbStructuur.models import NhbLid
from .models import SchutterNhbLidGeenEmail, SchutterNhbLidInactief
from .forms import RegistreerForm
import logging


TEMPLATE_REGISTREER = 'schutter/registreer-nhb-account.dtl'
TEMPLATE_REGISTREER_GEEN_EMAIL = 'schutter/registreer-geen-email.dtl'

my_logger = logging.getLogger('NHBApps.Schutter')


def schutter_create_account_nhb(nhb_nummer, email, nieuw_wachtwoord):
    """ Maak een nieuw account aan voor een NHB lid
        raises AccountError als:
            - er al een account bestaat
            - het nhb nummer niet valide is
            - het email adres niet bekend is bij de nhb
            - het email adres niet overeen komt
        geeft de url terug die in de email verstuurd moet worden
    """
    # zoek het email adres van dit NHB lid erbij
    try:
        # deze conversie beschermd ook tegen gevaarlijke invoer
        nhb_nr = int(nhb_nummer)
    except ValueError:
        raise AccountCreateError('Onbekend NHB nummer')

    try:
        nhblid = NhbLid.objects.get(nhb_nr=nhb_nr)
    except NhbLid.DoesNotExist:
        raise AccountCreateError('Onbekend NHB nummer')

    if not mailer_email_is_valide(nhblid.email):
        raise SchutterNhbLidGeenEmail(nhblid)

    # vergelijk e-mailadres hoofdletter ongevoelig
    if email.lower() != nhblid.email.lower():
        raise AccountCreateError('De combinatie van NHB nummer en email worden niet herkend. Probeer het nog eens.')

    if not nhblid.is_actief_lid or not nhblid.bij_vereniging:
        raise SchutterNhbLidInactief()

    # maak het account aan
    account, accountmail = account_create(nhb_nummer, nhblid.voornaam, nhblid.achternaam, nieuw_wachtwoord, nhblid.email, False)

    # koppelen nhblid en account
    nhblid.account = account
    nhblid.save()

    # indien dit een secretaris is, ook meteen koppelen aan SEC functie van zijn vereniging
    if nhblid.bij_vereniging.secretaris_lid == nhblid:
        functie = Functie.objects.get(rol='SEC', nhb_ver=nhblid.bij_vereniging)
        functie.accounts.add(account)

    account_vraag_email_bevestiging(accountmail, nhb_nummer=nhb_nummer, email=email)


class RegistreerNhbNummerView(TemplateView):
    """
        Deze view wordt gebruikt om het NHB nummer in te voeren voor een nieuw account.
    """

    @staticmethod
    def post(request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Registreer knop.
        """
        form = RegistreerForm(request.POST)
        if form.is_valid():
            nhb_nummer = form.cleaned_data.get('nhb_nummer')
            email = form.cleaned_data.get('email')
            nieuw_wachtwoord = form.cleaned_data.get('nieuw_wachtwoord')
            from_ip = get_safe_from_ip(request)
            try:
                schutter_create_account_nhb(nhb_nummer, email, nieuw_wachtwoord)
            except SchutterNhbLidGeenEmail as exc:
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Registreer met NHB nummer",
                                   activiteit='NHB lid %s heeft geen email adres.' % nhb_nummer)
                my_logger.info('%s REGISTREER Geblokkeerd voor NHB nummer %s (geen email)' % (from_ip, repr(nhb_nummer)))

                # redirect naar een pagina met een uitgebreider duidelijk bericht
                context = {'sec_email': '',
                           'sec_naam': '',
                           'email_bb': settings.EMAIL_BONDSBURO}
                ver = exc.nhblid.bij_vereniging
                if ver:
                    sec_lid = ver.secretaris_lid
                    if sec_lid:
                        context['sec_naam'] = sec_lid.volledige_naam()

                    functie = Functie.objects.get(rol='SEC', nhb_ver=ver)
                    context['sec_email'] = functie.bevestigde_email

                menu_dynamics(request, context)
                return render(request, TEMPLATE_REGISTREER_GEEN_EMAIL, context)

            except AccountCreateError as exc:
                form.add_error(None, str(exc))

                # schrijf in het logboek
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Registreer met NHB nummer",
                                   activiteit="Mislukt voor nhb nummer %s vanaf IP %s: %s" % (repr(nhb_nummer), from_ip, str(exc)))
                my_logger.info('%s REGISTREER Mislukt voor NHB nummer %s met email %s (reden: %s)' % (from_ip, repr(nhb_nummer), repr(email), str(exc)))
            except SchutterNhbLidInactief:
                # NHB lid is mag niet gebruik maken van de diensten van de NHB, inclusief deze website
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Registreer met NHB nummer",
                                   activiteit='NHB lid %s is inactief (geblokkeerd van gebruik NHB diensten).' % nhb_nummer)
                form.add_error(None, 'Gebruik van NHB diensten is geblokkeerd. Neem contact op met de secretaris van je vereniging.')
                my_logger.info('%s REGISTREER Geblokkeerd voor NHB nummer %s (inactief)' % (from_ip, repr(nhb_nummer)))
                # FUTURE: redirect naar een pagina met een uitgebreider duidelijk bericht
            else:
                # schrijf in het logboek
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Registreer met NHB nummer",
                                   activiteit="Account aangemaakt voor NHB nummer %s vanaf IP %s" % (repr(nhb_nummer), from_ip))
                my_logger.info('%s REGISTREER account aangemaakt voor NHB nummer %s' % (from_ip, repr(nhb_nummer)))

                request.session['login_naam'] = nhb_nummer
                request.session['partial_email'] = mailer_obfuscate_email(email)
                return HttpResponseRedirect(reverse('Account:aangemaakt'))

        # still here --> re-render with error message
        context = {'form': form}
        menu_dynamics(request, context)
        return render(request, TEMPLATE_REGISTREER, context)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        # GET operation --> create empty form
        form = RegistreerForm()
        context = {'form': form}
        menu_dynamics(request, context)
        return render(request, TEMPLATE_REGISTREER, context)


# end of file
