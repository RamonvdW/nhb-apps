# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.shortcuts import render
from django.views.generic import TemplateView
from Account.operations.aanmaken import AccountCreateError, account_create
from Account.operations.email import account_vraag_email_bevestiging
from Functie.models import Functie
from Logboek.models import schrijf_in_logboek
from Mailer.operations import mailer_email_is_valide, mailer_obfuscate_email
from Overig.helpers import get_safe_from_ip
from Plein.menu import menu_dynamics
from Sporter.forms import RegistreerForm
from Sporter.models import Sporter, SporterGeenEmail, SporterInactief
from Vereniging.models import Secretaris
import logging


TEMPLATE_REGISTREER = 'registreer/registreer-nhb-account.dtl'
TEMPLATE_REGISTREER_GEEN_EMAIL = 'registreer/registreer-geen-email.dtl'
TEMPLATE_REGISTREER_AANGEMAAKT = 'registreer/registreer-aangemaakt.dtl'

my_logger = logging.getLogger('NHBApps.Registreer')


def sporter_create_account_nhb(lid_nr_str, email, nieuw_wachtwoord):
    """ Maak een nieuw account aan voor een NHB lid
        raises AccountCreateError als:
            - het lidnummer niet valide is
            - het lidnummer niet bekend is in het CRM
            - het ingevoerde emailadres niet overeen komt
            - er al een account bestaat
        raises SporterGeenEmail als:
            - voor de sporter geen e-mail bekend is
        raises SporterInactief als:
            - de sporter niet lid is bij een vereniging
        geeft de url terug die in de email verstuurd moet worden
    """
    # zoek het e-mailadres van dit NHB lid erbij
    try:
        # deze conversie beschermd ook tegen gevaarlijke invoer
        lid_nr = int(lid_nr_str)
    except ValueError:
        raise AccountCreateError('Onbekend bondsnummer')

    try:
        sporter = Sporter.objects.get(lid_nr=lid_nr)
    except Sporter.DoesNotExist:
        raise AccountCreateError('Onbekend bondsnummer')

    if not mailer_email_is_valide(sporter.email):
        raise SporterGeenEmail(sporter)

    # vergelijk e-mailadres hoofdletter ongevoelig
    if email.lower() != sporter.email.lower():
        raise AccountCreateError('De combinatie van bondsnummer en e-mailadres worden niet herkend. Probeer het nog eens.')

    if not sporter.is_actief_lid or not sporter.bij_vereniging:
        raise SporterInactief()

    # maak het account aan
    account = account_create(lid_nr_str, sporter.voornaam, sporter.achternaam, nieuw_wachtwoord, sporter.email, False)

    # koppelen sporter en account
    sporter.account = account
    sporter.save()

    # bij de volgende CRM import wordt dit account gekoppeld aan de SEC functie en wordt een e-mail gestuurd met instructies

    account_vraag_email_bevestiging(account, nhb_nummer=lid_nr_str, email=email)


class RegistreerNhbLidView(TemplateView):
    """
        Deze view wordt gebruikt om het bondsnummer in te voeren voor een nieuw account.
    """

    @staticmethod
    def post(request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Registreer knop.
        """
        form = RegistreerForm(request.POST)

        # still here --> re-render with error message
        context = {
            'form': form,
            'sec_email': '',
            'sec_naam': '',
            'email_bb': settings.EMAIL_BONDSBUREAU,
            'verberg_login_knop': True,
            'kruimels': (
                (None, 'Account aanmaken'),
            ),
        }
        menu_dynamics(request, context)

        if form.is_valid():
            # compleetheid en wachtwoord sterkte worden gecontroleerd door het formulier
            nhb_nummer = form.cleaned_data.get('nhb_nummer')
            email = form.cleaned_data.get('email')
            nieuw_wachtwoord = form.cleaned_data.get('nieuw_wachtwoord')
            from_ip = get_safe_from_ip(request)

            try:
                sporter_create_account_nhb(nhb_nummer, email, nieuw_wachtwoord)

            except SporterGeenEmail as exc:
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Registreer met bondsnummer",
                                   activiteit='NHB lid %s heeft geen email adres.' % nhb_nummer)
                my_logger.info('%s REGISTREER Geblokkeerd voor bondsnummer %s (geen email)' % (from_ip, repr(nhb_nummer)))

                # redirect naar een pagina met een uitgebreider duidelijk bericht
                ver = exc.sporter.bij_vereniging
                if ver:
                    try:
                        sec = Secretaris.objects.get(vereniging=ver)
                    except Secretaris.DoesNotExist:
                        pass
                    else:
                        if sec.sporters.count() > 0:                # pragma: no branch
                            sporter = sec.sporters.all()[0]
                            context['sec_naam'] = sporter.volledige_naam()

                    functie = Functie.objects.get(rol='SEC', nhb_ver=ver)
                    context['sec_email'] = functie.bevestigde_email

                menu_dynamics(request, context)
                return render(request, TEMPLATE_REGISTREER_GEEN_EMAIL, context)

            except AccountCreateError as exc:
                form.add_error(None, str(exc))

                # schrijf in het logboek
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Registreer met bondsnummer",
                                   activiteit="Mislukt voor bondsnummer %s vanaf IP %s: %s" % (repr(nhb_nummer), from_ip, str(exc)))
                my_logger.info('%s REGISTREER Mislukt voor bondsnummer %s met email %s (reden: %s)' % (from_ip, repr(nhb_nummer), repr(email), str(exc)))

            except SporterInactief:
                # lid is mag niet gebruik maken van de diensten van de NHB, inclusief deze website
                form.add_error(None, 'Gebruik van NHB diensten is geblokkeerd. Neem contact op met de secretaris van je vereniging.')

                # schrijf in het logboek
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Registreer met bondsnummer",
                                   activiteit='NHB lid %s is inactief (geblokkeerd van gebruik NHB diensten).' % nhb_nummer)
                my_logger.info('%s REGISTREER Geblokkeerd voor bondsnummer %s (inactief)' % (from_ip, repr(nhb_nummer)))

                # FUTURE: redirect naar een pagina met een uitgebreider duidelijk bericht

            else:
                # schrijf in het logboek
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Registreer met bondsnummer",
                                   activiteit="Account aangemaakt voor bondsnummer %s vanaf IP %s" % (repr(nhb_nummer), from_ip))
                my_logger.info('%s REGISTREER account aangemaakt voor bondsnummer %s' % (from_ip, repr(nhb_nummer)))

                context['login_naam'] = nhb_nummer
                context['partial_email'] = mailer_obfuscate_email(email)
                return render(request, TEMPLATE_REGISTREER_AANGEMAAKT, context)

        # opnieuw
        context['toon_tip'] = True
        return render(request, TEMPLATE_REGISTREER, context)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        # GET operation --> create empty form
        form = RegistreerForm()

        context = dict()
        context['form'] = form

        context['kruimels'] = (
            (None, 'Account aanmaken'),
        )

        menu_dynamics(request, context)
        return render(request, TEMPLATE_REGISTREER, context)


# end of file
