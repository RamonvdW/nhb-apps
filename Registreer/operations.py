# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import transaction
from django.conf import settings
from django.utils import timezone
from django.db.models import ProtectedError
from Logboek.models import schrijf_in_logboek
from Mailer.operations import mailer_queue_email, render_email_template
from Registreer.definities import GAST_LID_NUMMER_FIXED_PK, REGISTRATIE_FASE_COMPLEET, REGISTRATIE_FASE_AFGEWEZEN
from Registreer.models import GastLidNummer, GastRegistratie, GastRegistratieRateTracker
import datetime


EMAIL_TEMPLATE_GAST_VERWIJDER = 'email_registreer/gast-verwijder.dtl'


def registratie_gast_volgende_lid_nr():
    """ Neem het volgende lid_nr voor gast accounts uit """
    with transaction.atomic():
        volgende = (GastLidNummer
                    .objects
                    .select_for_update()                 # lock tegen concurrency
                    .get(pk=GAST_LID_NUMMER_FIXED_PK))

        # het volgende nummer is het nieuwe unieke nummer
        volgende.volgende_lid_nr += 1
        volgende.save()

        nummer = volgende.volgende_lid_nr

    return nummer


def registratie_gast_is_open():
    """
        Deze functie vertelt of nieuwe gast-accounts aangemaakt mogen worden.
        Return value:
            True  = Registratie is open
            False = Geen nieuwe gast-accounts meer registreren
    """
    volgende = (GastLidNummer
                .objects
                .get(pk=GAST_LID_NUMMER_FIXED_PK))

    return volgende.kan_aanmaken


def registreer_opschonen_incompleet(stdout):
    now = timezone.now()
    max_age = now - datetime.timedelta(days=7)

    for gast in (GastRegistratie
                 .objects
                 .filter(fase__lt=REGISTRATIE_FASE_COMPLEET,        # skip COMPLEET of AFGEWEZEN
                         aangemaakt__lt=max_age)
                 .select_related('sporter',
                                 'account')):

        stdout.write('[INFO] Verwijder niet afgeronde gast-account registratie %s in fase %s' % (
                        gast.lid_nr, gast.fase))

        # schrijf in het logboek
        msg = "Incompleet gast-account %s wordt verwijderd" % gast.lid_nr
        schrijf_in_logboek(account=None,
                           gebruikte_functie="Registreer gast-account",
                           activiteit=msg)

        if gast.email_is_bevestigd:

            # stuur een e-mail over het verwijderen van het gast-account
            context = {
                'voornaam': gast.voornaam,
                'gast_lid_nr': gast.lid_nr,
                'naam_site': settings.NAAM_SITE,
                'contact_email': settings.EMAIL_BONDSBUREAU,
            }
            mail_body = render_email_template(context, EMAIL_TEMPLATE_GAST_VERWIJDER)

            # stuur de e-mail
            mailer_queue_email(gast.email,
                               'Gast-account verwijderd',
                               mail_body)

        # echt verwijderen
        if gast.sporter:
            gast.sporter.delete()           # verwijdert ook SporterVoorkeuren en SporterBoog
        if gast.account:
            gast.account.delete()
        gast.delete()
    # for


def registreer_opschonen_afgewezen(stdout):
    now = timezone.now()
    max_age = now - datetime.timedelta(days=183)    # 6 maanden

    for gast in (GastRegistratie
                 .objects
                 .filter(fase=REGISTRATIE_FASE_AFGEWEZEN,
                         aangemaakt__lt=max_age)
                 .select_related('sporter',
                                 'account')):

        stdout.write('[INFO] Verwijder afgewezen gast-account registratie %s' % gast.lid_nr)

        # echt verwijderen
        skip = False
        if gast.sporter:
            try:
                stdout.write('[INFO] Verwijder sporter %s' % gast.sporter)
                gast.sporter.delete()           # verwijdert ook SporterVoorkeuren en SporterBoog
            except ProtectedError as exc:       # pragma: no cover
                stdout.write('[ERROR] %s' % exc)
                skip = True

        if gast.account:
            try:
                stdout.write('[INFO] Verwijder account %s' % gast.account)
                gast.account.delete()
            except ProtectedError as exc:       # pragma: no cover
                stdout.write('[ERROR] %s' % exc)
                skip = True

        if not skip:                            # pragma: no branch
            # schrijf in het logboek
            msg = "Afgewezen gast-account %s wordt verwijderd" % gast.lid_nr
            schrijf_in_logboek(account=None,
                               gebruikte_functie="Registreer gast-account",
                               activiteit=msg)

            gast.delete()
    # for


def registreer_opschonen(stdout):
    """ deze functie wordt typisch 1x per dag aangeroepen om de database
        tabellen van deze applicatie op te kunnen schonen.

        We verwijderen gast registratie die na 7 dagen nog niet voltooid zijn
        We verwijderen afgewezen registraties na 6 maanden
        We verwijderen rate tracker records die niet meer nodig zijn
    """

    registreer_opschonen_incompleet(stdout)
    #registreer_opschonen_afgewezen(stdout)

    # alle rate trackers opruimen
    GastRegistratieRateTracker.objects.all().delete()


# end of file
