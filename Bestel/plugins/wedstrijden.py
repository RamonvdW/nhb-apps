# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module levert functionaliteit voor de Bestel applicatie met kennis van de Kalender, zoals kortingen. """

from django.utils import timezone
from Wedstrijden.models import (WedstrijdKorting, WedstrijdInschrijving,
                                WEDSTRIJD_KORTING_COMBI, WEDSTRIJD_KORTING_SPORTER, WEDSTRIJD_KORTING_VERENIGING,
                                INSCHRIJVING_STATUS_DEFINITIEF, INSCHRIJVING_STATUS_AFGEMELD,
                                INSCHRIJVING_STATUS_TO_STR)
from decimal import Decimal


class BepaalAutomatischeKorting(object):

    def __init__(self, stdout):
        self._stdout = stdout

        self._org_ver_nrs = list()                                # verenigingen die voorkomen in het mandje
        self._lid_nr2ver_nr = dict()                              # [lid_nr] = ver_nr
        self._lid_nr2wedstrijd_pks = dict()                       # [lid_nr] = [wedstrijd.pk, ...]
        self._lid_nr2wedstrijd_pks_eerder = dict()                # [lid_nr] = [wedstrijd.pk, ...]
        self._lid_nr_wedstrijd_pk2inschrijving = dict()           # [(lid_nr, wedstrijd_pk)] = inschrijving
        self._inschrijving_pk2product = dict()                    # [inschrijving.pk] = BestelProduct
        self._alle_combi_kortingen = list()

    def _bereken_euros_korting(self, combi_korting, alle_inschrijvingen):

        # self._stdout.write('bereken_euros_korting voor combi-korting %s' % combi_korting)
        totaal_prijs_euro = Decimal(0)
        procent = combi_korting.percentage / Decimal('100')

        for inschrijving in alle_inschrijvingen:
            # self._stdout.write('  inschrijving: %s' % inschrijving)
            if combi_korting in inschrijving.mogelijke_kortingen:
                # self._stdout.write('    heeft mogelijke combi-korting')

                product = self._inschrijving_pk2product[inschrijving.pk]
                totaal_prijs_euro += product.prijs_euro
        # for

        # self._stdout.write('  prijs_totaal: %s' % totaal_prijs_euro)
        korting_euro = totaal_prijs_euro
        if totaal_prijs_euro > 0:
            korting_euro = totaal_prijs_euro * procent

        # self._stdout.write('  korting_euro: %s' % korting_euro)
        return korting_euro

    def _laad_mandje(self, mandje):
        """ laad de inhoud van het mandje en reset all kortingen """

        for product in (mandje
                        .producten
                        .exclude(wedstrijd_inschrijving=None)
                        .select_related('wedstrijd_inschrijving',
                                        'wedstrijd_inschrijving__korting',
                                        'wedstrijd_inschrijving__sporterboog',
                                        'wedstrijd_inschrijving__sporterboog__sporter',
                                        'wedstrijd_inschrijving__sporterboog__sporter__bij_vereniging',
                                        'wedstrijd_inschrijving__wedstrijd',
                                        'wedstrijd_inschrijving__wedstrijd__organiserende_vereniging')):

            inschrijving = product.wedstrijd_inschrijving
            self._inschrijving_pk2product[inschrijving.pk] = product

            # verwijder automatische kortingen
            if inschrijving.korting:
                inschrijving.korting = None
                inschrijving.save(update_fields=['korting'])

            product.korting_euro = Decimal(0)
            product.save(update_fields=['korting_euro'])

            inschrijving.mogelijke_kortingen = list()
            inschrijving.mogelijke_combi_korting = False

            ver_nr = inschrijving.wedstrijd.organiserende_vereniging.ver_nr
            if ver_nr not in self._org_ver_nrs:
                self._org_ver_nrs.append(ver_nr)

            sporter = inschrijving.sporterboog.sporter
            lid_nr = sporter.lid_nr
            if sporter.bij_vereniging:
                ver_nr = sporter.bij_vereniging.ver_nr
                self._lid_nr2ver_nr[lid_nr] = ver_nr
            else:
                self._lid_nr2ver_nr[lid_nr] = -1

            try:
                self._lid_nr2wedstrijd_pks[lid_nr].append(inschrijving.wedstrijd.pk)
            except KeyError:
                self._lid_nr2wedstrijd_pks[lid_nr] = [inschrijving.wedstrijd.pk]

            tup = (lid_nr, inschrijving.wedstrijd.pk)
            self._lid_nr_wedstrijd_pk2inschrijving[tup] = inschrijving
        # for

        # zoek, i.v.m. combinatiekortingen, ook naar wedstrijden waar al op ingeschreven is
        for lid_nr, nieuwe_pks in self._lid_nr2wedstrijd_pks.items():
            pks = list(WedstrijdInschrijving
                       .objects
                       .filter(sporterboog__sporter__lid_nr=lid_nr)
                       .exclude(status=INSCHRIJVING_STATUS_AFGEMELD)
                       .exclude(wedstrijd__pk__in=nieuwe_pks)
                       .values_list('wedstrijd__pk', flat=True))
            self._lid_nr2wedstrijd_pks_eerder[lid_nr] = pks
        # for

        # self._stdout.write('inschrijvingen:')
        # for lid_nr, pks in self._lid_nr2wedstrijd_pks.items():
        #     self._stdout.write('  %s: %s' % (lid_nr, repr(pks)))

        # self._stdout.write('inschrijvingen_eerder:')
        # for lid_nr, pks in self._lid_nr2wedstrijd_pks_eerder.items():
        #     self._stdout.write('  %s: %s' % (lid_nr, repr(pks)))

        # self._stdout.write('org_ver_nrs: %s' % repr(self._org_ver_nrs))

    def _zoek_mogelijke_kortingen(self):
        """ koppel aan elke inschrijving een mogelijke korting """
        lid_nrs_in_mandje = list(self._lid_nr2wedstrijd_pks.keys())

        # bepaal alle kortingen die mogelijk van toepassing kunnen zijn
        for korting in (WedstrijdKorting
                        .objects
                        .filter(uitgegeven_door__ver_nr__in=self._org_ver_nrs)
                        .select_related('voor_sporter',
                                        'voor_vereniging')
                        .prefetch_related('voor_wedstrijden')):

            # kijk of deze korting van toepassing is op het mandje
            # self._stdout.write('mogelijke korting: %s (%d%%)' % (korting, korting.percentage))

            voor_wedstrijd_pks = list(korting.voor_wedstrijden.all().values_list('pk', flat=True))

            if korting.soort == WEDSTRIJD_KORTING_SPORTER and korting.voor_sporter:
                lid_nr = korting.voor_sporter.lid_nr
                if lid_nr in lid_nrs_in_mandje:
                    # inschrijving voor deze sporter is aanwezig in het mandje
                    # self._stdout.write('  kandidaat individuele korting voor sporter: %s' % korting.voor_sporter)

                    # kijk of deze korting van toepassing is
                    for pk in voor_wedstrijd_pks:
                        try:
                            tup = (lid_nr, pk)
                            inschrijving = self._lid_nr_wedstrijd_pk2inschrijving[tup]
                        except KeyError:
                            pass
                        else:
                            # self._stdout.write('    gevonden inschrijving: %s' % inschrijving)
                            inschrijving.mogelijke_kortingen.append(korting)

            elif korting.soort == WEDSTRIJD_KORTING_VERENIGING and korting.voor_vereniging:
                # kijk of deze korting van toepassing is op het mandje
                target_ver_nr = korting.voor_vereniging.ver_nr
                for lid_nr in lid_nrs_in_mandje:
                    if self._lid_nr2ver_nr[lid_nr] == target_ver_nr:
                        # inschrijving voor sporter van de bedoelde vereniging is aanwezig in het mandje
                        # self._stdout.write('  kandidaat verenigingskorting voor leden van vereniging: %s' % target_ver_nr)

                        # kijk of deze korting van toepassing is op een van de wedstrijden
                        for wedstrijd_pk in self._lid_nr2wedstrijd_pks[lid_nr]:
                            if wedstrijd_pk in voor_wedstrijd_pks:
                                tup = (lid_nr, wedstrijd_pk)
                                inschrijving = self._lid_nr_wedstrijd_pk2inschrijving[tup]
                                # self._stdout.write('    gevonden inschrijving: %s' % inschrijving)
                                inschrijving.mogelijke_kortingen.append(korting)
                        # for
                # for

            elif korting.soort == WEDSTRIJD_KORTING_COMBI:
                # kijk of deze korting van toepassing is op het mandje
                for lid_nr in lid_nrs_in_mandje:
                    # kijk of voldaan wordt aan de eisen van de combi-korting
                    pks = self._lid_nr2wedstrijd_pks[lid_nr] + self._lid_nr2wedstrijd_pks_eerder[lid_nr]

                    alle_gevonden = True
                    for pk in voor_wedstrijd_pks:
                        if pk not in pks:
                            alle_gevonden = False
                            break
                    # for

                    if alle_gevonden:
                        # dit is een kandidaat-korting
                        # self._stdout.write('  kandidaat combi-korting: %s' % korting)
                        self._alle_combi_kortingen.append(korting)

                        # voeg deze toe aan alle producten in het mandje waar deze bij hoort
                        for wedstrijd_pk in voor_wedstrijd_pks:
                            tup = (lid_nr, wedstrijd_pk)
                            inschrijving = self._lid_nr_wedstrijd_pk2inschrijving[tup]
                            inschrijving.mogelijke_kortingen.append(korting)
                            inschrijving.mogelijke_combi_korting = True
                            # self._stdout.write('    gevonden inschrijving: %s' % inschrijving)
                        # for
                # for
        # for

    def _kies_eenvoudige_kortingen(self, alle_inschrijvingen):
        """ stel alle kortingen vast waar geen combi-korting bij aan te pas kan komen """
        # pas alle kortingen toe waar geen combi-korting in het spel is
        # self._stdout.write('Eenvoudige kortingen toepassen:')
        done = list()
        for inschrijving in alle_inschrijvingen:
            if len(inschrijving.mogelijke_kortingen) == 0:
                done.append(inschrijving)

            elif not inschrijving.mogelijke_combi_korting:
                # self._stdout.write('zonder combi: %s' % inschrijving)
                # geef de hoogste korting
                for korting in inschrijving.mogelijke_kortingen:
                    if not inschrijving.korting:
                        inschrijving.korting = korting
                    else:
                        if korting.percentage > inschrijving.korting.percentage:
                            inschrijving.korting = korting
                # for

                if inschrijving.korting:
                    # self._stdout.write('   gekozen korting: %s' % inschrijving.korting)
                    inschrijving.save(update_fields=['korting'])

                    procent = inschrijving.korting.percentage / Decimal('100')

                    product = self._inschrijving_pk2product[inschrijving.pk]
                    # self._stdout.write('   product: %s' % product)
                    product.korting_euro = product.prijs_euro * procent
                    product.korting_euro = min(product.korting_euro, product.prijs_euro)  # voorkom korting > prijs
                    product.save(update_fields=['korting_euro'])
                    # self._stdout.write('   korting_euro: %s' % product.korting_euro)

                    done.append(inschrijving)
        # for
        for inschrijving in done:
            alle_inschrijvingen.remove(inschrijving)
        # for

    def _kies_combi_kortingen(self, alle_inschrijvingen):
        max_loops = 10
        while max_loops > 0 and len(self._alle_combi_kortingen) > 0 and len(alle_inschrijvingen) > 0:
            max_loops -= 1

            # self._stdout.write('Tijd om te kiezen (combi)!')
            # self._stdout.write('inschrijvingen + mogelijke kortingen:')
            # for inschrijving in alle_inschrijvingen:
            #     self._stdout.write("%s" % inschrijving)
            #     for korting in inschrijving.mogelijke_kortingen:
            #         self._stdout.write('  korting: %s' % korting)
            #     # for
            # # for

            # bereken hoeveel korting er te krijgen is voor elke van de combi-kortingen
            unsorted_euros = list()
            for combi_korting in self._alle_combi_kortingen:
                euros = self._bereken_euros_korting(combi_korting, alle_inschrijvingen)
                tup = (euros, combi_korting.pk, combi_korting)
                unsorted_euros.append(tup)
            # for
            unsorted_euros.sort(reverse=True)       # hoogste eerst
            # self._stdout.write('  sorted: %s' % repr(unsorted_euros))

            # kies de beste combi-korting en pas deze toe
            combi_korting_euro, _, combi_korting = unsorted_euros[0]
            # self._stdout.write('  gekozen korting: %s' % combi_korting_euro)
            # self._stdout.write('  combi_korting_euro: %s' % combi_korting_euro)
            self._alle_combi_kortingen.remove(combi_korting)
            done = list()
            for inschrijving in reversed(alle_inschrijvingen):
                if combi_korting in inschrijving.mogelijke_kortingen:
                    # geeft de combinatie-korting maar 1 keer
                    if len(done) == 0:
                        inschrijving.korting = combi_korting
                        inschrijving.save(update_fields=['korting'])

                        product = self._inschrijving_pk2product[inschrijving.pk]
                        # self._stdout.write('   product: %s' % product)
                        product.korting_euro = combi_korting_euro
                        product.save(update_fields=['korting_euro'])

                    # verwijder alle combinatiekortingen die hier genoemd worden
                    for korting in inschrijving.mogelijke_kortingen:
                        if korting in self._alle_combi_kortingen:
                            self._alle_combi_kortingen.remove(korting)
                    # for

                    done.append(inschrijving)
            # for
            for inschrijving in done:
                alle_inschrijvingen.remove(inschrijving)
            # for
        # while

    def _kies_laatste_kortingen(self, alle_inschrijvingen):
        """ stel alle kortingen vast waar geen combi-korting bij aan te pas gekomen is """
        done = list()
        for inschrijving in alle_inschrijvingen:
            self._stdout.write('laatste inschrijving: %s' % inschrijving)

            # geef de hoogste korting
            for korting in inschrijving.mogelijke_kortingen:
                if korting.soort != WEDSTRIJD_KORTING_COMBI:
                    if not inschrijving.korting:
                        inschrijving.korting = korting
                    else:
                        if korting.percentage > inschrijving.korting.percentage:
                            inschrijving.korting = korting
            # for

            if inschrijving.korting:
                self._stdout.write('   gekozen korting: %s' % inschrijving.korting)
                inschrijving.save(update_fields=['korting'])

                procent = inschrijving.korting.percentage / Decimal('100')

                product = self._inschrijving_pk2product[inschrijving.pk]
                self._stdout.write('   product: %s' % product)
                product.korting_euro = product.prijs_euro * procent
                product.korting_euro = min(product.korting_euro, product.prijs_euro)  # voorkom korting > prijs
                product.save(update_fields=['korting_euro'])
                self._stdout.write('   korting_euro: %s' % product.korting_euro)

                done.append(inschrijving)
        # for
        for inschrijving in done:
            alle_inschrijvingen.remove(inschrijving)
        # for

    def kies_kortingen_voor_mandje(self, mandje):
        """
            bepaal welke kortingen van toepassing zijn en koppel deze aan de producten in het mandje

            kortingen mogen niet stapelen --> daarom heeft elk product maximaal 1 korting
            als meerdere kortingen van toepassing zijn, dan we geven de hoogste korting
        """

        self._laad_mandje(mandje)
        self._zoek_mogelijke_kortingen()

        alle_inschrijvingen = [inschrijving for inschrijving in self._lid_nr_wedstrijd_pk2inschrijving.values()]

        # self._stdout.write('Tijd om te kiezen!')
        # self._stdout.write('inschrijvingen + mogelijke kortingen:')
        # for inschrijving in alle_inschrijvingen:
        #     self._stdout.write("%s" % inschrijving)
        #     for korting in inschrijving.mogelijke_kortingen:
        #         self._stdout.write('  korting: %s' % korting)
        #     # for
        # # for

        self._kies_eenvoudige_kortingen(alle_inschrijvingen)

        self._kies_combi_kortingen(alle_inschrijvingen)

        # gevallen waarbij een (niet geselecteerde) combi-korting en andere korting mogelijk was
        # die zijn nu nog over en analyseren voor de andere korting
        self._kies_laatste_kortingen(alle_inschrijvingen)


def wedstrijden_plugin_automatische_kortingen_toepassen(stdout, mandje):
    BepaalAutomatischeKorting(stdout).kies_kortingen_voor_mandje(mandje)


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
