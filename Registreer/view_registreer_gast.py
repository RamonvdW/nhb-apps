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
from Mailer.operations import mailer_email_is_valide, mailer_queue_email, render_email_template
from Overig.helpers import get_safe_from_ip
from Plein.menu import menu_dynamics
from Registreer.definities import REGISTRATIE_FASE_EMAIL, REGISTRATIE_FASE_PASSWORD
from Registreer.forms import RegistreerGastForm
from Registreer.models import GastLidNummer, GastRegistratie, GastRegistratieRateTracker, GAST_LID_NUMMER_FIXED_PK
from Sporter.models import Sporter, SporterGeenEmail, SporterInactief
from TijdelijkeCodes.operations import (set_tijdelijke_codes_receiver, RECEIVER_BEVESTIG_GAST_EMAIL,
                                        maak_tijdelijke_code_registreer_gast_email)
import datetime
import logging


TEMPLATE_REGISTREER_GAST = 'registreer/registreer-gast.dtl'
TEMPLATE_REGISTREER_GAST_BEVESTIG_EMAIL = 'registreer/registreer-gast-1-bevestig-email.dtl'
TEMPLATE_REGISTREER_GAST_EMAIL_BEVESTIGD = 'registreer/registreer-gast-2-email-bevestigd.dtl'

EMAIL_TEMPLATE_GAST_BEVESTIG_EMAIL = 'email_registreer/gast-bevestig-toegang-email.dtl'
EMAIL_TEMPLATE_GAST_LID_NR = 'email_registreer/gast-lid-nr.dtl'

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
        mag_door = False

        now = timezone.now()
        uur = now.hour
        minuut = uur * 60 + now.minute      # sinds middernacht

        # ga er vanuit dat er meerdere threads zijn die tegelijkertijd bezig willen!
        with transaction.atomic():
            tracker, _ = GastRegistratieRateTracker.objects.get_or_create(from_ip=from_ip)

            if tracker.teller_minuut <= 5 and tracker.teller_uur <= 30:
                mag_door = True

                if tracker.minuut != minuut:
                    tracker.teller_minuut = 0
                    tracker.minuut = minuut

                if tracker.uur != uur:
                    tracker.teller_uur = 0
                    tracker.uur = uur

                tracker.teller_minuut += 1
                tracker.teller_uur += 1

                tracker.save()
            else:
                # geblokkeerd --> voorkom onnodig loggen
                pass

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

        if not form.is_valid():
            # opnieuw
            context['toon_tip'] = True
            return render(request, TEMPLATE_REGISTREER_GAST, context)

        from_ip = get_safe_from_ip(request)

        # begrens de frequentie
        mag_door = self._check_rate_limit(from_ip)
        if not mag_door:
            # verzoek moet geblokkeerd worden
            form.add_error(None, 'te snel. Wacht 1 minuut.')
            return render(request, TEMPLATE_REGISTREER_GAST, context)

        # compleetheid is gecontroleerd door het formulier
        voornaam = form.cleaned_data.get('voornaam')
        achternaam = form.cleaned_data.get('achternaam')
        email = form.cleaned_data.get('email')

        # kijk of er al een verzoek loopt van dezelfde gebruiker
        gast, is_created = GastRegistratie.objects.get_or_create(voornaam=voornaam,
                                                                 achternaam=achternaam,
                                                                 email=email)
        if not is_created:
            # verzoek moet geblokkeerd worden
            form.add_error(None, 'dubbel verzoek.')
            return render(request, TEMPLATE_REGISTREER_GAST, context)

        # het is een nieuw verzoek
        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        gast.fase = REGISTRATIE_FASE_EMAIL
        gast.logboek = '[%s] IP=%s: aangemaakt met naam en e-mail\n' % (stamp_str, from_ip)
        gast.save()

        # begin een nieuwe gast-account registratie

        # laat het e-mailadres bevestigen (ook al accepteren we deze straks niet)

        # schrijf in syslog om database vervuiling te voorkomen
        my_logger.info('%s REGISTREER gast-account aanmaken; stuur e-mail' % from_ip)

        # maak de url aan om het e-mailadres te bevestigen
        url = maak_tijdelijke_code_registreer_gast_email(gast,
                                                         naam=voornaam + achternaam,
                                                         stamp=stamp_str,
                                                         from_ip=from_ip,
                                                         gast_email=email)

        # maak de e-mail aan
        context = {
            'url': url,
            'voornaam': gast.voornaam,
            'naam_site': settings.NAAM_SITE,
            'contact_email': settings.EMAIL_BONDSBUREAU,
        }
        mail_body = render_email_template(context, EMAIL_TEMPLATE_GAST_BEVESTIG_EMAIL)

        # stuur de e-mail
        mailer_queue_email(gast.email,
                           'Aanmaken gast-account voltooien',
                           mail_body,
                           enforce_whitelist=False)     # deze mails altijd doorlaten

        context['email'] = email
        return render(request, TEMPLATE_REGISTREER_GAST_BEVESTIG_EMAIL, context)


def receive_bevestiging_gast_email(request, gast):
    """ deze functie wordt aangeroepen als een tijdelijke url gevolgd wordt
        om het email adres van een nieuw gast-account te bevestigen.
            gast is een GastRegistratie object.
        We moeten een url teruggeven waar een http-redirect naar gedaan kan worden
        of een HttpResponse object.
    """
    from_ip = get_safe_from_ip(request)

    # schrijf in syslog om database vervuiling te voorkomen
    my_logger.info('%s REGISTREER gast-account e-mail is bevestigd' % from_ip)

    # schrijf in het logboek
    msg = "E-mail voor gast-account e-mail %s bevestigd vanaf IP %s" % (gast.email, from_ip)
    schrijf_in_logboek(account=None,
                       gebruikte_functie="Registreer gast-account",
                       activiteit=msg)

    now = timezone.now()
    stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

    gast.email_is_bevestigd = True
    gast.lid_nr = registratie_gast_volgende_lid_nr()
    gast.logboek += '[%s] IP=%s: e-mail is bevestigd; lidnummer %s toegekend\n' % (stamp_str, from_ip, gast.lid_nr)
    gast.fase = REGISTRATIE_FASE_PASSWORD
    gast.save(update_fields=['email_is_bevestigd', 'lid_nr', 'logboek', 'fase'])

    # stuur een e-mail met het bondsnummer
    # maak de e-mail aan
    context = {
        'url': reverse('Account:wachtwoord-vergeten'),
        'voornaam': gast.voornaam,
        'lid_nr': gast.lid_nr,
        'naam_site': settings.NAAM_SITE,
        'contact_email': settings.EMAIL_BONDSBUREAU,
    }
    mail_body = render_email_template(context, EMAIL_TEMPLATE_GAST_LID_NR)

    # stuur de e-mail
    mailer_queue_email(gast.email,
                       'Bondsnummer %s toegekend' % gast.lid_nr,
                       mail_body,
                       enforce_whitelist=False)  # deze mails altijd doorlaten

    now = timezone.now()
    stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
    gast.logboek += '[%s] e-mail verstuurd met bondsnummer\n' % stamp_str
    gast.save(update_fields=['logboek'])

    context = {
        'verberg_login_knop': True,
        'toon_broodkruimels': False,
        'lid_nr': gast.lid_nr,
        'url_volgende': reverse('Registreer:gast-meer-vragen'),
    }

    menu_dynamics(request, context)
    return render(request, TEMPLATE_REGISTREER_GAST_EMAIL_BEVESTIGD, context)


set_tijdelijke_codes_receiver(RECEIVER_BEVESTIG_GAST_EMAIL, receive_bevestiging_gast_email)


class RegistreerGastMeerView(TemplateView):
    pass


# end of file
