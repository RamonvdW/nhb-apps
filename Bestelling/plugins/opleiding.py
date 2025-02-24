# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module levert functionaliteit voor de Bestel-applicatie, met kennis van de opleidingen """

from django.conf import settings
from django.utils import timezone
from Bestelling.models.product_obsolete import BestellingProduct
from Functie.models import Functie
from Opleiding.definities import (OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE, OPLEIDING_AFMELDING_STATUS_AFGEMELD,
                                  OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF, OPLEIDING_AFMELDING_STATUS_GEANNULEERD,
                                  OPLEIDING_INSCHRIJVING_STATUS_TO_STR, OPLEIDING_AFMELDING_STATUS_TO_STR)
from Opleiding.models import OpleidingInschrijving, OpleidingAfgemeld
from Mailer.operations import mailer_queue_email, mailer_email_is_valide, render_email_template
from decimal import Decimal

EMAIL_TEMPLATE_INFO_INSCHRIJVING_OPLEIDING = 'email_bestelling/info-inschrijving-opleiding.dtl'


def opleiding_plugin_afmelden(inschrijving: OpleidingInschrijving):
    """ verwerk een afmelding voor een opleiding """

    # (nog) geen aantallen om bij te werken

    now = timezone.now()
    stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
    msg = "[%s] Afgemeld voor deze opleiding\n" % stamp_str

    # zet de inschrijving om in een afmelding
    afmelding = OpleidingAfgemeld(
                    wanneer_aangemeld=inschrijving.wanneer_aangemeld,
                    wanneer_afgemeld=now,
                    nummer=inschrijving.nummer,
                    status=OPLEIDING_AFMELDING_STATUS_AFGEMELD,
                    opleiding=inschrijving.opleiding,
                    sporter=inschrijving.sporter,
                    koper=inschrijving.koper,
                    bedrag_ontvangen=inschrijving.bedrag_ontvangen,
                    log=inschrijving.log + msg)
    afmelding.save()

    # verwijder de inschrijving
    inschrijving.delete()


def opleiding_plugin_inschrijving_is_betaald(stdout, product: BestellingProduct):
    """ Deze functie wordt aangeroepen vanuit de achtergrondtaak als een bestelling betaald is,
        of als een bestelling niet betaald hoeft te worden (totaal bedrag nul)
    """
    inschrijving = product.opleiding_inschrijving
    inschrijving.bedrag_ontvangen = product.prijs_euro - product.korting_euro
    inschrijving.status = OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF

    stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
    msg = "[%s] Betaling ontvangen (euro %s); status is nu definitief\n" % (stamp_str, inschrijving.bedrag_ontvangen)

    inschrijving.log += msg
    inschrijving.save(update_fields=['bedrag_ontvangen', 'status', 'log'])

    opleiding = inschrijving.opleiding

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

            functie_mo = Functie.objects.filter(rol="MO").first()
            if functie_mo and functie_mo.bevestigde_email:
                email = functie_mo.bevestigde_email
            else:
                email = settings.EMAIL_BONDSBUREAU

            context = {
                'voornaam': sporter.voornaam,
                'koper_volledige_naam': koper_account.volledige_naam(),
                'reserveringsnummer': settings.TICKET_NUMMER_START__OPLEIDING + inschrijving.nummer,
                'opleiding_beschrijving': opleiding.beschrijving,
                'contact_email': email,
                'geen_account': sporter.account is None,
                'naam_site': settings.NAAM_SITE,
            }

            mail_body = render_email_template(context, EMAIL_TEMPLATE_INFO_INSCHRIJVING_OPLEIDING)

            mailer_queue_email(email,
                               'Inschrijving voor opleiding',
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


def opleiding_plugin_beschrijf_product(obj: OpleidingInschrijving | OpleidingAfgemeld):
    """
        Geef een lijst van tuples terug waarin aspecten van het product beschreven staan.
    """

    opleiding = obj.opleiding
    sporter = obj.sporter
    nummer = obj.nummer

    beschrijving = list()

    tup = ('Reserveringsnummer', settings.TICKET_NUMMER_START__OPLEIDING + nummer)
    beschrijving.append(tup)

    tup = ('Opleiding', opleiding.titel)
    beschrijving.append(tup)

    tup = ('Periode', opleiding.periode_str())
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

    functie_mo = Functie.objects.filter(rol="MO").first()
    if functie_mo and functie_mo.bevestigde_email:
        email = functie_mo.bevestigde_email
    else:
        email = settings.EMAIL_BONDSBUREAU

    tup = ('E-mail organisatie', email)
    beschrijving.append(tup)

    # tup = ('Telefoon organisatie', opleiding.contact_telefoon)
    # beschrijving.append(tup)

    return beschrijving


# end of file
