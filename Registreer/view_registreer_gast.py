# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import transaction
from django.conf import settings
from django.utils import timezone
from django.shortcuts import render, reverse
from django.views.generic import TemplateView
from Account.operations.aanmaken import AccountCreateError, account_create
from Account.operations.email import account_vraag_email_bevestiging
from Logboek.models import schrijf_in_logboek
from Mailer.operations import mailer_email_is_valide, mailer_queue_email
from Overig.helpers import get_safe_from_ip
from Plein.menu import menu_dynamics
from Registreer.definities import REGISTRATIE_FASE_EMAIL
from Registreer.forms import RegistreerGastForm
from Registreer.models import GastLidNummer, GastRegistratie, GastRegistratieRateTracker, GAST_LID_NUMMER_FIXED_PK
from Sporter.models import Sporter, SporterGeenEmail, SporterInactief
from TijdelijkeCodes.operations import maak_tijdelijke_code_registreer_gast_email
import datetime
import logging


TEMPLATE_REGISTREER_GAST = 'registreer/registreer-gast.dtl'
TEMPLATE_REGISTREER_GAST_BEVESTIG_EMAIL = 'registreer/registreer-gast-bevestig-email.dtl'

my_logger = logging.getLogger('NHBApps.Registreer')


def registratie_gast_volgende_lid_nr():
    """ Neem het volgende lid_nr voor gast accounts uit """
    with transaction.atomic():
        tracker = (GastLidNummer
                   .objects
                   .select_for_update()                 # lock tegen concurrency
                   .get(pk=GAST_LID_NUMMER_FIXED_PK))

        # het volgende nummer is het nieuwe unieke nummer
        tracker.volgende_lid_nr += 1
        tracker.save()

        nummer = tracker.volgende_lid_nr

    return nummer


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


def registreer_gast_vraag_email_bevestiging(gast, **kwargs):
    """ Stuur een mail naar het adres om te vragen om een bevestiging.
        Gebruik een tijdelijke URL die, na het volgen, weer in deze module uit komt.
    """

    # maak de url aan om het e-mailadres te bevestigen
    url = maak_tijdelijke_code_registreer_gast_email(gast, **kwargs)

    text_body = ("Hallo!\n\n"
                 + "Je hebt een gast-account aangemaakt op " + settings.NAAM_SITE + ".\n"
                 + "Klik op onderstaande link om dit te bevestigen.\n\n"
                 + url + "\n\n"
                 + "Als jij dit niet was, neem dan contact met ons op via " + settings.EMAIL_BONDSBUREAU + "\n\n"
                 + "Veel plezier met de site!\n"
                 + "Het bondsbureau\n")

    mailer_queue_email(gast.email,
                       'Aanmaken gast-account voltooien',
                       text_body,
                       enforce_whitelist=False)     # deze mails altijd doorlaten


def registreer_gast_email_bevestiging_ontvangen(gast):
    """ Deze functie wordt vanuit de tijdelijke url receiver functie (zie view)
        aanroepen met gast = GastRegistratie object waar dit op van toepassing is
    """
    gast.email_is_bevestigd = True
    gast.save(update_fields=['email_is_bevestigd'])


class RegistreerGastView(TemplateView):
    """
        Deze view wordt gebruikt om het bondsnummer en e-mailadres van een NHB lid en daarmee een account aan te maken.
    """

    @staticmethod
    def _check_rate_limit(from_ip) -> bool:
        """
            Blokkeer meerdere verzoeken binnen 1 minuut.

            Returns 'mag door':
                True:  Mag door
                False: Verzoek blokkeren
        """
        now = timezone.now()
        recent_limiet = now - datetime.timedelta(seconds=60)

        # ga er vanuit dat er meerdere threads zijn die tegelijkertijd bezig willen!
        if GastRegistratieRateTracker.objects.filter(from_ip=from_ip, vorige_gebruik__gt=recent_limiet).count() == 0:
            # voeg een nieuw record toe
            GastRegistratieRateTracker(from_ip=from_ip, vorige_gebruik=now).save()
            mag_door = True
        else:
            mag_door = False

        return mag_door

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        # begin met een leeg formulier
        form = RegistreerGastForm()

        context = {
            'form': form,
            'url_aanmaken': reverse('Registreer:gast'),
            'kruimels': (
                (reverse('Registreer:begin'), 'Account aanmaken'),
                (None, 'Gast')),
        }

        menu_dynamics(request, context)
        return render(request, TEMPLATE_REGISTREER_GAST, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Registreer knop.
        """
        form = RegistreerGastForm(request.POST)

        # still here --> re-render with error message
        context = {
            'form': form,
            'email_bb': settings.EMAIL_BONDSBUREAU,
            'verberg_login_knop': True,
            'url_aanmaken': reverse('Registreer:gast'),
            'kruimels': (
                (reverse('Registreer:begin'), 'Account aanmaken'),
                (None, 'Gast')),
        }

        menu_dynamics(request, context)

        if form.is_valid():
            # compleetheid wordt gecontroleerd door het formulier
            voornaam = form.cleaned_data.get('voornaam')
            tussenvoegsel = form.cleaned_data.get('tussenvoegsel')
            achternaam = form.cleaned_data.get('achternaam')
            email = form.cleaned_data.get('email')

            # begin een nieuwe gast-account registratie
            now = timezone.now()
            stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
            from_ip = get_safe_from_ip(request)

            mag_door = self._check_rate_limit(from_ip)
            if not mag_door:
                # verzoek moet geblokkeerd worden
                form.add_error(None, 'Te snel. Wacht 1 minuut.')
                return render(request, TEMPLATE_REGISTREER_GAST, context)

            # laat het e-mailadres bevestigen (ook al accepteren we deze straks niet)
            gast = GastRegistratie(
                        fase=REGISTRATIE_FASE_EMAIL,
                        voornaam=voornaam,
                        tussenvoegsel=tussenvoegsel,
                        achternaam=achternaam,
                        email=email,
                        logboek='[%s] IP=%s: aangemaakt met naam en e-mail\n' % (stamp_str, from_ip))
            gast.save()

            my_logger.info('%s REGISTREER gast-account aanmaken; stuur e-mail' % from_ip)

            # stuur een e-mail
            registreer_gast_vraag_email_bevestiging(gast,
                                                    naam=voornaam + tussenvoegsel + achternaam,
                                                    stamp=stamp_str,
                                                    from_ip=from_ip,
                                                    gast_email=email)

            context['email'] = email
            return render(request, TEMPLATE_REGISTREER_GAST_BEVESTIG_EMAIL, context)

        # opnieuw
        context['toon_tip'] = True
        return render(request, TEMPLATE_REGISTREER_GAST, context)


# end of file
