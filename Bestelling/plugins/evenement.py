# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module levert functionaliteit voor de Bestel-applicatie, met kennis van de evenementen """

from django.conf import settings
from django.utils import timezone
from Bestelling.models import BestellingProduct
from Evenement.definities import (EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF,
                                  EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                  EVENEMENT_AFMELDING_STATUS_GEANNULEERD, EVENEMENT_AFMELDING_STATUS_AFGEMELD,
                                  EVENEMENT_INSCHRIJVING_STATUS_TO_STR, EVENEMENT_AFMELDING_STATUS_TO_STR)
from Evenement.models import EvenementInschrijving, EvenementAfgemeld
from Mailer.operations import mailer_queue_email, mailer_email_is_valide, render_email_template
from decimal import Decimal

EMAIL_TEMPLATE_INFO_INSCHRIJVING_EVENEMENT = 'email_bestelling/info-inschrijving-evenement.dtl'


def evenement_plugin_inschrijven(inschrijving: EvenementInschrijving) -> Decimal:
    """ verwerk een nieuwe inschrijving op een evenement """

    # (nog) geen aantallen om bij te werken

    prijs = inschrijving.evenement.bepaal_prijs_voor_sporter(inschrijving.sporter)
    return prijs


def evenement_plugin_verwijder_reservering(stdout, inschrijving: EvenementInschrijving) -> EvenementAfgemeld | None:
    # wordt gebruikt bij:
    # - inschrijving uit het mandje
    # - annuleren van een bestelling

    afmelding = None

    now = timezone.now()
    stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
    msg = "[%s] Verwijder reservering voor dit evenement\n" % stamp_str

    if inschrijving.status == EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE:
        # verwijdering uit mandje
        stdout.write('[INFO] Inschrijving evenement pk=%s status %s --> verwijderd uit mandje' % (
            inschrijving.pk,
            EVENEMENT_INSCHRIJVING_STATUS_TO_STR[inschrijving.status]))
    else:
        # zet de inschrijving om in een afmelding
        afmelding = EvenementAfgemeld(
                        wanneer_inschrijving=inschrijving.wanneer,
                        nummer=inschrijving.nummer,
                        wanneer_afgemeld=now,
                        status=EVENEMENT_AFMELDING_STATUS_AFGEMELD,
                        evenement=inschrijving.evenement,
                        sporter=inschrijving.sporter,
                        koper=inschrijving.koper,
                        bedrag_ontvangen=inschrijving.bedrag_ontvangen,
                        log=inschrijving.log + msg)

        if inschrijving.status != EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF:
            # nog niet betaald
            afmelding.status = EVENEMENT_AFMELDING_STATUS_GEANNULEERD

        afmelding.save()

        stdout.write('[INFO] Inschrijving evenement pk=%s status %s --> afgemeld pk=%s status %s' % (
            inschrijving.pk,
            EVENEMENT_INSCHRIJVING_STATUS_TO_STR[inschrijving.status],
            afmelding.pk,
            EVENEMENT_AFMELDING_STATUS_TO_STR[afmelding.status]))

    # verwijder de inschrijving
    inschrijving.delete()

    return afmelding


def evenement_plugin_afmelden(inschrijving: EvenementInschrijving):
    """ verwerk een afmelding voor een evenement """

    # (nog) geen aantallen om bij te werken

    now = timezone.now()
    stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
    msg = "[%s] Afgemeld voor dit evenement\n" % stamp_str

    # zet de inschrijving om in een afmelding
    afmelding = EvenementAfgemeld(
                    wanneer_inschrijving=inschrijving.wanneer,
                    wanneer_afgemeld=now,
                    nummer=inschrijving.nummer,
                    status=EVENEMENT_AFMELDING_STATUS_AFGEMELD,
                    evenement=inschrijving.evenement,
                    sporter=inschrijving.sporter,
                    koper=inschrijving.koper,
                    bedrag_ontvangen=inschrijving.bedrag_ontvangen,
                    log=inschrijving.log + msg)
    afmelding.save()

    # verwijder de inschrijving
    inschrijving.delete()


def evenement_plugin_inschrijving_is_betaald(stdout, product: BestellingProduct):
    """ Deze functie wordt aangeroepen vanuit de achtergrondtaak als een bestelling betaald is,
        of als een bestelling niet betaald hoeft te worden (totaal bedrag nul)
    """
    inschrijving = product.evenement_inschrijving
    inschrijving.bedrag_ontvangen = product.prijs_euro - product.korting_euro
    inschrijving.status = EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF

    stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
    msg = "[%s] Betaling ontvangen (euro %s); status is nu definitief\n" % (stamp_str, inschrijving.bedrag_ontvangen)

    inschrijving.log += msg
    inschrijving.save(update_fields=['bedrag_ontvangen', 'status', 'log'])

    evenement = inschrijving.evenement

    # stuur een e-mail naar de sporter, als dit niet de koper is
    sporter = inschrijving.sporter
    sporter_account = sporter.account
    koper_account = inschrijving.koper
    if sporter_account != koper_account:
        email = None
        if sporter_account and sporter_account.email_is_bevestigd:
            email = sporter_account.bevestigde_email
        else:
            if mailer_email_is_valide(sporter.email):
                email = sporter.email

        if email:
            # maak de e-mail en stuur deze naar sporter.

            context = {
                'voornaam': sporter.voornaam,
                'koper_volledige_naam': koper_account.volledige_naam(),
                'reserveringsnummer': settings.TICKET_NUMMER_START__EVENEMENT + inschrijving.nummer,
                'evenement_titel': evenement.titel,
                'evenement_adres': evenement.locatie.adres_oneliner(),
                'evenement_datum': evenement.datum,
                'evenement_org_ver': evenement.organiserende_vereniging,
                'begin_tijd': evenement.aanvang.strftime('%H:%M'),
                'contact_email': evenement.contact_email,
                'contact_tel': evenement.contact_telefoon,
                'geen_account': sporter.account is None,
                'naam_site': settings.NAAM_SITE,
            }

            mail_body = render_email_template(context, EMAIL_TEMPLATE_INFO_INSCHRIJVING_EVENEMENT)

            mailer_queue_email(email,
                               'Inschrijving voor evenement',
                               mail_body)

            stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
            msg = "[%s] Informatieve e-mail is gestuurd naar sporter %s\n" % (stamp_str, sporter.lid_nr)
            inschrijving.log += msg
            inschrijving.save(update_fields=['log'])

            stdout.write('[INFO] Informatieve e-mail is gestuurd naar sporter %s' % sporter.lid_nr)
        else:
            msg = "[%s] Kan geen informatieve e-mail sturen naar sporter %s (geen e-mail beschikbaar)\n" % (
                        sporter.lid_nr, stamp_str)
            inschrijving.log += msg
            inschrijving.save(update_fields=['log'])

            stdout.write('[INFO] Kan geen informatieve e-mail sturen naar sporter %s (geen e-mail beschikbaar)' %
                         sporter.lid_nr)


def evenement_plugin_beschrijf_product(inschrijving_of_afgemeld: EvenementInschrijving | EvenementAfgemeld) -> list:
    """
        Geef een lijst van tuples terug waarin aspecten van het product beschreven staan.
    """

    evenement = inschrijving_of_afgemeld.evenement
    sporter = inschrijving_of_afgemeld.sporter
    nummer = inschrijving_of_afgemeld.nummer

    beschrijving = list()

    tup = ('Reserveringsnummer', settings.TICKET_NUMMER_START__EVENEMENT + nummer)
    beschrijving.append(tup)

    tup = ('Evenement', evenement.titel)
    beschrijving.append(tup)

    tup = ('Datum', evenement.datum.strftime('%Y-%m-%d'))
    beschrijving.append(tup)

    tup = ('Aanvang', evenement.aanvang.strftime('%H:%M'))
    beschrijving.append(tup)

    tup = ('Sporter', sporter.lid_nr_en_volledige_naam())
    beschrijving.append(tup)

    sporter_ver = sporter.bij_vereniging
    if sporter_ver:
        ver_naam = sporter_ver.ver_nr_en_naam()
    else:
        ver_naam = 'Onbekend'
    tup = ('Lid bij vereniging', ver_naam)
    beschrijving.append(tup)

    tup = ('Locatie', evenement.locatie.adres_oneliner())
    beschrijving.append(tup)

    tup = ('E-mail organisatie', evenement.contact_email)
    beschrijving.append(tup)

    tup = ('Telefoon organisatie', evenement.contact_telefoon)
    beschrijving.append(tup)

    return beschrijving


# end of file
