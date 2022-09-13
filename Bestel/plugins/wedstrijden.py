# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module levert functionaliteit voor de Bestel applicatie met kennis van de Kalender, zoals kortingen. """

from django.utils import timezone
from Wedstrijden.models import (WedstrijdKortingscode, WedstrijdInschrijving, WEDSTRIJD_KORTING_COMBI,
                                INSCHRIJVING_STATUS_DEFINITIEF, INSCHRIJVING_STATUS_AFGEMELD,
                                INSCHRIJVING_STATUS_TO_STR)
from decimal import Decimal


def wedstrijden_plugin_automatische_kortingscodes_toepassen(stdout, mandje):

    # analyseer de inhoud van het mandje
    inschrijvingen = dict()                 # [lid_nr] = [wedstrijd.pk, ...]
    lid_wedstrijd2inschrijving = dict()     # [(lid_nr, wedstrijd_pk)] = inschrijving
    ver_nrs = list()                        # verenigingen die voorkomen in het mandje
    inschrijving2product = dict()           # [inschrijving.pk] = BestelProduct
    if True:
        for product in mandje.producten.exclude(wedstrijd_inschrijving=None).all():
            inschrijving = product.wedstrijd_inschrijving
            inschrijving2product[inschrijving.pk] = product

            # verwijder automatische kortingen
            if inschrijving.gebruikte_code:
                korting = inschrijving.gebruikte_code
                if korting.combi_basis_wedstrijd:
                    inschrijving.gebruikte_code = None
                    inschrijving.save(update_fields=['gebruikte_code'])

                    product.korting_euro = Decimal(0)
                    product.save(update_fields=['korting_euro'])

            ver_nr = inschrijving.wedstrijd.organiserende_vereniging.ver_nr
            if ver_nr not in ver_nrs:
                ver_nrs.append(ver_nr)

            lid_nr = inschrijving.sporterboog.sporter.lid_nr

            try:
                inschrijvingen[lid_nr].append(inschrijving.wedstrijd.pk)
            except KeyError:
                inschrijvingen[lid_nr] = [inschrijving.wedstrijd.pk]

            tup = (lid_nr, inschrijving.wedstrijd.pk)
            lid_wedstrijd2inschrijving[tup] = inschrijving
        # for

        # naast wat er in het mandje ligt ook kijken waar al op ingeschreven is
        for lid_nr, nieuwe_pks in inschrijvingen.items():
            pks = list(WedstrijdInschrijving
                       .objects
                       .filter(sporterboog__sporter__lid_nr=lid_nr)
                       .exclude(status=INSCHRIJVING_STATUS_AFGEMELD)
                       .exclude(wedstrijd__pk__in=nieuwe_pks)
                       .values_list('wedstrijd__pk', flat=True))
            inschrijvingen[lid_nr].extend(pks)
        # for

    # doorloop alle combi-kortingen van de organiserende verenigingen die voorkomen in het mandje
    for korting in (WedstrijdKortingscode
                    .objects
                    .exclude(combi_basis_wedstrijd=None)
                    .filter(uitgegeven_door__ver_nr__in=ver_nrs)):

        vereiste_pks = list(korting.voor_wedstrijden.all().values_list('pk', flat=True))

        # doorloop alle inschrijvingen en kijk of voldaan wordt aan de eisen van de combi-korting
        for lid_nr, pks in inschrijvingen.items():
            alle_gevonden = True
            for pk in vereiste_pks:
                if pk not in pks:
                    alle_gevonden = False
                    break
            # for

            if alle_gevonden:
                tup = (lid_nr, korting.combi_basis_wedstrijd.pk)
                try:
                    inschrijving = lid_wedstrijd2inschrijving[tup]
                except KeyError:
                    # toch niet..
                    pass
                else:
                    # combi-korting is van toepassing op deze wedstrijd
                    vervang = True
                    if inschrijving.gebruikte_code:
                        huidige_code = inschrijving.gebruikte_code

                        # controleer welke de hoogste korting geeft
                        if huidige_code.percentage > korting.percentage:
                            vervang = False

                    if vervang:
                        product = inschrijving2product[inschrijving.pk]

                        # pas de code toe op deze inschrijving
                        stdout.write('[INFO] Kalender combi-korting pk=%s toepassen op inschrijving van product pk=%s' % (
                                            korting.pk, product.pk))

                        inschrijving.gebruikte_code = korting
                        inschrijving.save(update_fields=['gebruikte_code'])

                        # bereken de korting voor dit product
                        procent = korting.percentage / Decimal('100')
                        product.korting_euro = product.prijs_euro * procent
                        product.korting_euro = min(product.korting_euro, product.prijs_euro)  # voorkom korting > prijs
                        product.save(update_fields=['korting_euro'])
        # for
    # for


def wedstrijden_plugin_inschrijven(inschrijving):
    """ verwerk een nieuwe inschrijving op een wedstrijdsessie """
    # verhoog het aantal inschrijvingen op deze sessie
    # hiermee geven we een garantie op een plekje
    # Noteer: geen concurrency risico want serialisatie via deze achtergrondtaak
    sessie = inschrijving.sessie
    sessie.aantal_inschrijvingen += 1
    sessie.save(update_fields=['aantal_inschrijvingen'])

    wedstrijd = inschrijving.wedstrijd
    sporter = inschrijving.sporterboog.sporter

    leeftijd = sporter.bereken_wedstrijdleeftijd(wedstrijd.datum_begin, wedstrijd.organisatie)
    if leeftijd < 18:
        prijs = wedstrijd.prijs_euro_onder18
    else:
        prijs = wedstrijd.prijs_euro_normaal

    return prijs


def wedstrijden_plugin_afmelden(inschrijving):
    """ verwerk een afmelding voor een wedstrijdsessie """
    # verlaag het aantal inschrijvingen op deze sessie
    # Noteer: geen concurrency risico want serialisatie via deze achtergrondtaak
    sessie = inschrijving.sessie
    sessie.aantal_inschrijvingen -= 1
    sessie.save(update_fields=['aantal_inschrijvingen'])

    stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
    msg = "[%s] Afgemeld voor de wedstrijd\n" % stamp_str

    # inschrijving.sessie en inschrijving.klasse kunnen niet op None gezet worden
    inschrijving.status = INSCHRIJVING_STATUS_AFGEMELD
    inschrijving.log += msg
    inschrijving.save(update_fields=['status', 'log'])


def wedstrijden_plugin_verwijder_reservering(stdout, inschrijving):

    # zet de inschrijving om in status=afgemeld
    # dit heeft de voorkeur over het verwijderen van inschrijvingen,
    # want als er wel een betaling volgt dan kunnen we die nergens aan koppelen
    oude_status = inschrijving.status

    stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
    msg = "[%s] Afgemeld voor de wedstrijd en reservering verwijderd\n" % stamp_str

    inschrijving.status = INSCHRIJVING_STATUS_AFGEMELD
    inschrijving.log += msg
    inschrijving.save(update_fields=['status', 'log'])

    # schrijf de sporter uit bij de sessie
    # Noteer: geen concurrency risico want serialisatie via deze achtergrondtaak
    sessie = inschrijving.sessie
    if sessie.aantal_inschrijvingen > 0:  # voorkom ongelukken: kan negatief niet opslaan
        sessie.aantal_inschrijvingen -= 1
        sessie.save(update_fields=['aantal_inschrijvingen'])

    stdout.write('[INFO] Inschrijving pk=%s status %s --> Afgemeld' % (inschrijving.pk,
                                                                       INSCHRIJVING_STATUS_TO_STR[oude_status]))


def wedstrijden_plugin_kortingscode_toepassen(stdout, kortingscode_str, producten):

    for korting in (WedstrijdKortingscode
                    .objects
                    .exclude(soort=WEDSTRIJD_KORTING_COMBI)      # wordt apart bekeken
                    .filter(code__iexact=kortingscode_str,
                            geldig_tot_en_met__gte=timezone.now().date())):

        # korting = mutatie.korting
        # account = mutatie.korting_voor_koper

        for product in producten:

            inschrijving = product.wedstrijd_inschrijving

            # kijk of deze korting van toepassing is op deze inschrijving
            toepassen = False

            if korting.voor_sporter:
                # code voor een specifieke sporter
                if korting.voor_sporter == inschrijving.sporterboog.sporter:
                    toepassen = True
                    stdout.write('[DEBUG] Kalender korting: past voor_sporter lid_nr=%s' % korting.voor_sporter.lid_nr)

            if korting.voor_vereniging:
                # alle sporters van deze vereniging mogen deze code gebruiken
                # (bijvoorbeeld de organiserende vereniging)
                if korting.voor_vereniging == inschrijving.sporterboog.sporter.bij_vereniging:
                    toepassen = True
                    stdout.write('[DEBUG] Kalende korting: past voor_vereniging %s' % korting.voor_vereniging.ver_nr)

            if korting.combi_basis_wedstrijd:
                # we hebben een aparte
                toepassen = False

            elif korting.voor_wedstrijden.count() > 0:
                # korting is begrensd tot 1 wedstrijd of een serie wedstrijden
                if korting.voor_wedstrijden.filter(id=inschrijving.wedstrijd.id).exists():
                    # code voor deze wedstrijd
                    pass
                else:
                    # leuke code, maar niet bedoeld voor deze wedstrijd
                    toepassen = False

            if toepassen:
                vervang = True
                if inschrijving.gebruikte_code:
                    # geen controle geldigheid huidige code

                    # controleer welke de hoogste korting geeft
                    huidige_code = inschrijving.gebruikte_code
                    if huidige_code.percentage > korting.percentage:
                        vervang = False

                if vervang:
                    # pas de code toe op deze inschrijving
                    stdout.write('[INFO] Kalender korting pk=%s toepassen op inschrijving van product pk=%s' % (
                                    korting.pk, product.pk))

                    inschrijving.gebruikte_code = korting
                    inschrijving.save(update_fields=['gebruikte_code'])

                    # bereken de korting voor dit product
                    procent = korting.percentage / Decimal('100')
                    product.korting_euro = product.prijs_euro * procent
                    product.korting_euro = min(product.korting_euro, product.prijs_euro)   # voorkom korting > prijs
                    product.save(update_fields=['korting_euro'])

        # for product
    # for korting


def wedstrijden_plugin_inschrijving_is_betaald(product):
    """ Deze functie wordt aangeroepen als een bestelling betaald is,
        of als een bestelling niet betaald hoeft te worden (totaal bedrag nul)
    """
    inschrijving = product.wedstrijd_inschrijving
    inschrijving.ontvangen_euro = product.prijs_euro - product.korting_euro
    inschrijving.status = INSCHRIJVING_STATUS_DEFINITIEF

    stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
    msg = "[%s] Betaling ontvangen (euro %s); status is nu definitief\n" % (stamp_str, inschrijving.ontvangen_euro)

    inschrijving.log += msg
    inschrijving.save(update_fields=['ontvangen_euro', 'status', 'log'])


# end of file
