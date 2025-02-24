# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module levert functionaliteit voor de Bestel-applicatie, met kennis van de Wedstrijden, zoals kortingen. """

from django.conf import settings
from django.utils import timezone
from BasisTypen.definities import ORGANISATIE_IFAA
from Bestelling.models.product_obsolete import BestellingProduct
from Mailer.operations import mailer_queue_email, mailer_email_is_valide, render_email_template
from Wedstrijden.definities import WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF, WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD
from Wedstrijden.models import WedstrijdInschrijving, beschrijf_korting
import datetime

EMAIL_TEMPLATE_INFO_INSCHRIJVING_WEDSTRIJD = 'email_bestelling/info-inschrijving-wedstrijd.dtl'


def wedstrijden_plugin_afmelden(inschrijving: WedstrijdInschrijving):
    """ verwerk een afmelding voor een wedstrijdsessie """
    # verlaag het aantal inschrijvingen op deze sessie
    # Noteer: geen concurrency risico want serialisatie via deze achtergrondtaak
    sessie = inschrijving.sessie
    sessie.aantal_inschrijvingen -= 1
    sessie.save(update_fields=['aantal_inschrijvingen'])

    stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
    msg = "[%s] Afgemeld voor de wedstrijd\n" % stamp_str

    # inschrijving.sessie en inschrijving.klasse kunnen niet op None gezet worden
    inschrijving.status = WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD
    inschrijving.log += msg
    inschrijving.save(update_fields=['status', 'log'])


def wedstrijden_plugin_inschrijving_is_betaald(stdout, product: BestellingProduct):
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
                'wed_adres': inschrijving.wedstrijd.locatie.adres_oneliner(),
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


def wedstrijden_plugin_beschrijf_product(inschrijving: WedstrijdInschrijving):
    """
        Geef een lijst van tuples terug waarin aspecten van het product beschreven staan.
    """
    beschrijving = list()

    tup = ('Reserveringsnummer', settings.TICKET_NUMMER_START__WEDSTRIJD + inschrijving.pk)
    beschrijving.append(tup)

    tup = ('Wedstrijd', inschrijving.wedstrijd.titel)
    beschrijving.append(tup)

    tup = ('Bij vereniging', inschrijving.wedstrijd.organiserende_vereniging)
    beschrijving.append(tup)

    sessie = inschrijving.sessie
    tup = ('Sessie', '%s vanaf %s' % (sessie.datum, sessie.tijd_begin.strftime('%H:%M')))
    beschrijving.append(tup)

    aanwezig = datetime.datetime.combine(inschrijving.sessie.datum, inschrijving.sessie.tijd_begin)
    aanwezig -= datetime.timedelta(minutes=inschrijving.wedstrijd.minuten_voor_begin_sessie_aanwezig_zijn)
    tup = ('Aanwezig zijn om', aanwezig.strftime('%H:%M'))
    beschrijving.append(tup)

    sporterboog = inschrijving.sporterboog
    tup = ('Sporter', '%s' % sporterboog.sporter.lid_nr_en_volledige_naam())
    beschrijving.append(tup)

    sporter_ver = sporterboog.sporter.bij_vereniging
    if sporter_ver:
        ver_naam = sporter_ver.ver_nr_en_naam()
    else:
        ver_naam = 'Onbekend'
    tup = ('Lid bij vereniging', ver_naam)
    beschrijving.append(tup)

    if inschrijving.wedstrijd.organisatie == ORGANISATIE_IFAA:
        tup = ('Schietstijl', '%s' % sporterboog.boogtype.beschrijving)
    else:
        tup = ('Boog', '%s' % sporterboog.boogtype.beschrijving)
    beschrijving.append(tup)

    if inschrijving.wedstrijd.organisatie == ORGANISATIE_IFAA:
        tup = ('Wedstrijdklasse', '%s [%s]' % (inschrijving.wedstrijdklasse.beschrijving,
                                               inschrijving.wedstrijdklasse.afkorting))
    else:
        tup = ('Wedstrijdklasse', '%s' % inschrijving.wedstrijdklasse.beschrijving)
    beschrijving.append(tup)

    tup = ('Locatie', inschrijving.wedstrijd.locatie.adres_oneliner())
    beschrijving.append(tup)

    tup = ('E-mail organisatie', inschrijving.wedstrijd.contact_email)
    beschrijving.append(tup)

    tup = ('Telefoon organisatie', inschrijving.wedstrijd.contact_telefoon)
    beschrijving.append(tup)

    return beschrijving


def wedstrijden_plugin_beschrijf_korting(inschrijving: WedstrijdInschrijving) -> (str | None, []):
    """
        Geef de beschrijving van de korting terug:
            kort_str: een tekst string, bijvoorbeeld "Persoonlijke korting 10%"
            redenen: een lijst van redenen (bedoeld om op opeenvolgende regels te tonen)
    """

    if inschrijving.korting:
        return beschrijf_korting(inschrijving.korting)

    return '', []


# end of file
