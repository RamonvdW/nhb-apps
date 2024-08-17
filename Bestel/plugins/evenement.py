# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module levert functionaliteit voor de Bestel-applicatie, met kennis van de Wedstrijden, zoals kortingen. """

from django.conf import settings
from django.utils import timezone
from Bestel.models import BestelProduct
from Evenement.definities import (EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF,
                                  EVENEMENT_AFMELDING_STATUS_AFGEMELD, EVENEMENT_AFMELDING_STATUS_VERWIJDERD,
                                  EVENEMENT_INSCHRIJVING_STATUS_TO_STR, EVENEMENT_AFMELDING_STATUS_TO_STR)
from Evenement.models import EvenementInschrijving, EvenementAfgemeld
from Mailer.operations import mailer_queue_email, mailer_email_is_valide, render_email_template
import datetime

EMAIL_TEMPLATE_INFO_INSCHRIJVING_EVENEMENT = 'email_bestel/info-inschrijving-evenement.dtl'


def evenement_plugin_inschrijven(inschrijving: EvenementInschrijving):
    """ verwerk een nieuwe inschrijving op een evenement """

    # (nog) geen aantallen om bij te werken

    prijs = inschrijving.evenement.bepaal_prijs_voor_sporter(inschrijving.sporter)
    return prijs


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
                    status=EVENEMENT_AFMELDING_STATUS_AFGEMELD,
                    evenement=inschrijving.evenement,
                    sporter=inschrijving.sporter,
                    koper=inschrijving.koper,
                    ontvangen_euro=inschrijving.ontvangen_euro,
                    retour_euro=inschrijving.retour_euro,
                    log=inschrijving.log + msg)
    afmelding.save()

    # verwijder de gekozen sessies
    for sessie in inschrijving.gekozen_sessies.all():
        sessie.aantal_inschrijvingen = max(0, sessie.aantal_inschrijvingen - 1)
        sessie.save(update_fields=['aantal_inschrijvingen'])
    # for
    inschrijving.gekozen_sessies.clear()

    # verwijder de inschrijving
    inschrijving.delete()


def evenement_plugin_verwijder_reservering(stdout, inschrijving: EvenementInschrijving):

    now = timezone.now()
    stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
    msg = "[%s] Afgemeld voor dit evenement\n" % stamp_str

    # zet de inschrijving om in een afmelding
    afmelding = EvenementAfgemeld(
                    wanneer_inschrijving=inschrijving.wanneer,
                    wanneer_afgemeld=now,
                    status=EVENEMENT_AFMELDING_STATUS_AFGEMELD,
                    evenement=inschrijving.evenement,
                    sporter=inschrijving.sporter,
                    koper=inschrijving.koper,
                    ontvangen_euro=inschrijving.ontvangen_euro,
                    retour_euro=inschrijving.retour_euro,
                    log=inschrijving.log + msg)

    if inschrijving.status == EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF:
        # was al betaald
        pass
    else:
        # nog niet betaald
        # verwijdering uit mandje af annulering van bestelling
        afmelding.status = EVENEMENT_AFMELDING_STATUS_VERWIJDERD

    afmelding.save()

    stdout.write('[INFO] Inschrijving pk=%s status %s --> afgemeld pk=%s status %s' % (
        inschrijving.pk,
        EVENEMENT_INSCHRIJVING_STATUS_TO_STR[inschrijving.status],
        afmelding.pk,
        EVENEMENT_AFMELDING_STATUS_TO_STR[afmelding.status]))

    # verwijder de gekozen sessies
    for sessie in inschrijving.gekozen_sessies.all():
        sessie.aantal_inschrijvingen = max(0, sessie.aantal_inschrijvingen - 1)
        sessie.save(update_fields=['aantal_inschrijvingen'])
    # for
    inschrijving.gekozen_sessies.clear()

    # verwijder de inschrijving
    inschrijving.delete()


def wedstrijden_plugin_inschrijving_is_betaald(stdout, product: BestelProduct):
    """ Deze functie wordt aangeroepen vanuit de achtergrondtaak als een bestelling betaald is,
        of als een bestelling niet betaald hoeft te worden (totaal bedrag nul)
    """
    inschrijving = product.wedstrijd_inschrijving
    inschrijving.ontvangen_euro = product.prijs_euro - product.korting_euro
    inschrijving.status = WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF

    stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
    msg = "[%s] Betaling ontvangen (euro %s); status is nu definitief\n" % (stamp_str, inschrijving.ontvangen_euro)

    inschrijving.log += msg
    inschrijving.save(update_fields=['ontvangen_euro', 'status', 'log'])

    # stuur een e-mail naar de sporter, als dit niet de koper is
    sporter = inschrijving.sporterboog.sporter
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

            aanwezig = datetime.datetime.combine(inschrijving.sessie.datum, inschrijving.sessie.tijd_begin)
            aanwezig -= datetime.timedelta(minutes=inschrijving.wedstrijd.minuten_voor_begin_sessie_aanwezig_zijn)

            context = {
                'voornaam': sporter.voornaam,
                'koper_volledige_naam': koper_account.volledige_naam(),
                'reserveringsnummer': settings.TICKET_NUMMER_START__WEDSTRIJD + inschrijving.pk,
                'wed_titel': inschrijving.wedstrijd.titel,
                'wed_adres': inschrijving.wedstrijd.locatie.adres.replace('\n', ', '),
                'wed_datum': inschrijving.sessie.datum,
                'wed_klasse': inschrijving.wedstrijdklasse.beschrijving,
                'wed_org_ver': inschrijving.wedstrijd.organiserende_vereniging,
                'aanwezig_tijd': aanwezig.strftime('%H:%M'),
                'contact_email': inschrijving.wedstrijd.contact_email,
                'contact_tel': inschrijving.wedstrijd.contact_telefoon,
                'geen_account': sporter.account is None,
                'naam_site': settings.NAAM_SITE,
            }

            if inschrijving.wedstrijd.organisatie == ORGANISATIE_IFAA:
                context['wed_klasse'] += ' [%s]' % inschrijving.wedstrijdklasse.afkorting

            mail_body = render_email_template(context, EMAIL_TEMPLATE_INFO_INSCHRIJVING_WEDSTRIJD)

            mailer_queue_email(email,
                               'Inschrijving op wedstrijd',
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


def evenement_plugin_beschrijf_product(inschrijving: EvenementInschrijving):
    """
        Geef een lijst van tuples terug waarin aspecten van het product beschreven staan.
    """

    evenement = inschrijving.evenement

    beschrijving = list()

    tup = ('Reserveringsnummer', settings.TICKET_NUMMER_START__WEDSTRIJD + inschrijving.pk)
    beschrijving.append(tup)

    tup = ('Evenement', evenement.titel)
    beschrijving.append(tup)

    tup = ('Datum', evenement.datum.strftime('%Y-%m-%d'))
    beschrijving.append(tup)

    tup = ('Aanvang', evenement.aanvang.strftime('%H:%M'))
    beschrijving.append(tup)

    sporter = inschrijving.sporter
    tup = ('Sporter', sporter.lid_nr_en_volledige_naam())
    beschrijving.append(tup)

    sporter_ver = sporter.bij_vereniging
    if sporter_ver:
        ver_naam = sporter_ver.ver_nr_en_naam()
    else:
        ver_naam = 'Onbekend'
    tup = ('Lid bij vereniging', ver_naam)
    beschrijving.append(tup)

    tup = ('Locatie', evenement.locatie.adres.replace('\n', ', '))
    beschrijving.append(tup)

    tup = ('E-mail organisatie', evenement.contact_email)
    beschrijving.append(tup)

    tup = ('Telefoon organisatie', evenement.contact_telefoon)
    beschrijving.append(tup)

    return beschrijving


def wedstrijden_beschrijf_korting(inschrijving):

    korting_str = None
    korting_redenen = list()

    if inschrijving.korting:
        korting = inschrijving.korting

        if korting.soort == WEDSTRIJD_KORTING_SPORTER:
            korting_str = "Persoonlijke korting: %d%%" % korting.percentage

        elif korting.soort == WEDSTRIJD_KORTING_VERENIGING:
            korting_str = "Verenigingskorting: %d%%" % korting.percentage

        elif korting.soort == WEDSTRIJD_KORTING_COMBI:              # pragma: no branch
            korting_str = "Combinatiekorting: %d%%" % korting.percentage
            korting_redenen = [wedstrijd.titel for wedstrijd in korting.voor_wedstrijden.all()]

    return korting_str, korting_redenen

# end of file
