# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module levert functionaliteit voor de Bestelling-applicatie, met kennis van alle kortingen. """

from Betaal.format import format_bedrag_euro
from Bestelling.definities import BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING, BESTELLING_KORT_BREAK
from Bestelling.models import BestellingRegel
from Wedstrijden.definities import (WEDSTRIJD_KORTING_COMBI, WEDSTRIJD_KORTING_SPORTER, WEDSTRIJD_KORTING_VERENIGING,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD, WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD)
from Wedstrijden.models import WedstrijdKorting, WedstrijdInschrijving, beschrijf_korting
from decimal import Decimal


class BepaalAutomatischeKorting(object):

    def __init__(self, stdout):
        self._stdout = stdout

        self._org_ver_nrs = list()                                # verenigingen die voorkomen in het mandje
        self._lid_nr2ver_nr = dict()                              # [lid_nr] = ver_nr
        self._lid_nr2wedstrijd_pks = dict()                       # [lid_nr] = [wedstrijd.pk, ...]
        self._lid_nr2wedstrijd_pks_eerder = dict()                # [lid_nr] = [wedstrijd.pk, ...]
        self._lid_nr_wedstrijd_pk2inschrijving = dict()           # [(lid_nr, wedstrijd_pk)] = inschrijving
        self._alle_combi_kortingen = list()
        self._max_korting_euro = None
        self._max_korting_pks = None

    def _analyseer_inschrijvingen(self, regel_pks: list):
        """ laad de inhoud van het mandje en reset all kortingen """

        for inschrijving in (WedstrijdInschrijving
                             .objects
                             .filter(bestelling__pk__in=regel_pks)
                             .select_related('korting',
                                             'sporterboog',
                                             'sporterboog__sporter',
                                             'sporterboog__sporter__bij_vereniging',
                                             'wedstrijd',
                                             'wedstrijd__organiserende_vereniging')):

            # verwijder automatische kortingen
            if inschrijving.korting:
                inschrijving.korting = None
                inschrijving.save(update_fields=['korting'])

            inschrijving.mogelijke_kortingen = list()
            inschrijving.heeft_mogelijke_combi_korting = False

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
        # maar we willen niet stapelen, dus als die eerder inschrijving al een korting heeft, dan niet overwegen
        for lid_nr, nieuwe_pks in self._lid_nr2wedstrijd_pks.items():
            pks = list(WedstrijdInschrijving
                       .objects
                       .filter(sporterboog__sporter__lid_nr=lid_nr)
                       .filter(korting=None)                            # niet stapelen
                       .exclude(status__in=(WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD,
                                            WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD))
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
                        .select_related('voor_sporter')
                        .prefetch_related('voor_wedstrijden')):

            # kijk of deze korting van toepassing is op het mandje
            # self._stdout.write('mogelijke korting: %s (%d%%)' % (korting, korting.percentage))

            voor_wedstrijd_pks = list(korting.voor_wedstrijden.all().values_list('pk', flat=True))
            # print('  voor wedstrijd_pks: %s' % repr(voor_wedstrijd_pks))

            if korting.soort == WEDSTRIJD_KORTING_SPORTER and korting.voor_sporter:
                lid_nr = korting.voor_sporter.lid_nr
                if lid_nr in lid_nrs_in_mandje:
                    # inschrijving voor deze sporter is aanwezig in het mandje
                    # print('  kandidaat individuele korting voor sporter: %s' % korting.voor_sporter)

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

            elif korting.soort == WEDSTRIJD_KORTING_VERENIGING:
                # kijk of deze korting van toepassing is op het mandje
                target_ver_nr = korting.uitgegeven_door.ver_nr
                for lid_nr in lid_nrs_in_mandje:
                    if self._lid_nr2ver_nr[lid_nr] == target_ver_nr:
                        # inschrijving voor sporter van de bedoelde vereniging is aanwezig in het mandje
                        # print('  kandidaat verenigingskorting voor leden van vereniging: %s' % target_ver_nr)

                        # kijk of deze korting van toepassing is op een van de wedstrijden
                        for wedstrijd_pk in self._lid_nr2wedstrijd_pks[lid_nr]:
                            if wedstrijd_pk in voor_wedstrijd_pks:
                                tup = (lid_nr, wedstrijd_pk)
                                inschrijving = self._lid_nr_wedstrijd_pk2inschrijving[tup]
                                # self._stdout.write('    gevonden inschrijving: %s' % inschrijving)
                                inschrijving.mogelijke_kortingen.append(korting)
                        # for
                # for

            elif korting.soort == WEDSTRIJD_KORTING_COMBI:                  # pragma: no branch
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
                        # print('  kandidaat combi-korting: %s' % korting)
                        self._alle_combi_kortingen.append(korting)

                        # voeg deze toe aan alle producten in het mandje waar deze bij hoort
                        for wedstrijd_pk in voor_wedstrijd_pks:
                            tup = (lid_nr, wedstrijd_pk)
                            try:
                                inschrijving = self._lid_nr_wedstrijd_pk2inschrijving[tup]
                            except KeyError:
                                # dit is een eerdere inschrijving / bestelling
                                pass
                            else:
                                inschrijving.mogelijke_kortingen.append(korting)
                                inschrijving.heeft_mogelijke_combi_korting = True
                                # print('    gevonden inschrijving: %s' % inschrijving)
                        # for
                # for
        # for

    def _analyseer_kortingen(self, alle_inschrijvingen, gebruikte_kortingen):
        # self._stdout.write('analyseer_kortingen: gebruikte_kortingen: %s' % gebruikte_kortingen)

        totaal_korting_euro = Decimal(0)
        for inschrijving in alle_inschrijvingen:
            if inschrijving.korting:
                procent = inschrijving.korting.percentage / Decimal('100')
                regel = inschrijving.bestelling
                totaal_korting_euro += (regel.bedrag_euro * procent)
        # for

        # print('  totaal_korting: %.2f' % totaal_korting_euro)

        if totaal_korting_euro > self._max_korting_euro:
            self._max_korting_euro = totaal_korting_euro
            self._max_korting_pks = tuple(gebruikte_kortingen)

    def _analyseer_kortingen_recursief(self, alle_inschrijvingen, gebruikte_kortingen):
        # self._stdout.write('zoek_kortingen_recursief: gebruikte_kortingen: %s' % gebruikte_kortingen)
        self._analyseer_kortingen(alle_inschrijvingen, gebruikte_kortingen)

        for inschrijving in alle_inschrijvingen:
            if not inschrijving.korting:
                for korting in inschrijving.mogelijke_kortingen:
                    if korting.pk not in gebruikte_kortingen:
                        gebruikte_kortingen.append(korting.pk)
                        inschrijving.korting = korting
                        self._analyseer_kortingen(alle_inschrijvingen, gebruikte_kortingen)
                        gebruikte_kortingen.remove(korting.pk)
                # for
                inschrijving.korting = None
        # for

    def _analyseer_kortingen_recursief_combi(self, alle_inschrijvingen, gebruikte_kortingen=()):
        # self._stdout.write('zoek_kortingen_recursief_combi: gebruikte_kortingen: %s' % gebruikte_kortingen)

        gebruikte_kortingen = list(gebruikte_kortingen)     # maak een kopie

        # pas een combi-korting toe
        for korting in self._alle_combi_kortingen:
            if korting.pk not in gebruikte_kortingen:
                gebruikte_kortingen.append(korting.pk)

                # pas deze korting toe
                reset_lijst = list()
                for inschrijving in alle_inschrijvingen:
                    if not inschrijving.korting and inschrijving.heeft_mogelijke_combi_korting:
                        if korting in inschrijving.mogelijke_kortingen:
                            inschrijving.korting = korting
                            reset_lijst.append(inschrijving)
                # for

                self._analyseer_kortingen_recursief_combi(alle_inschrijvingen, gebruikte_kortingen)

                for inschrijving in reset_lijst:
                    inschrijving.korting = None
                # for

                gebruikte_kortingen.remove(korting.pk)
        # for

        # alle combi-kortingen als "gebruikt" zetten en de rest doorlopen
        for korting in self._alle_combi_kortingen:
            if korting.pk not in gebruikte_kortingen:
                gebruikte_kortingen.append(korting.pk)
        # for
        self._analyseer_kortingen_recursief(alle_inschrijvingen, gebruikte_kortingen)

    def _kortingen_toepassen(self, alle_inschrijvingen, geef_korting_pks) -> list[BestellingRegel]:
        nieuwe_regels = list()
        combi_korting_euro = dict()     # [korting.pk] = Decimal
        for inschrijving in alle_inschrijvingen:
            for korting in inschrijving.mogelijke_kortingen:
                if korting.pk in geef_korting_pks:
                    # geef deze korting
                    # self._stdout.write('   gekozen korting: %s' % korting)
                    inschrijving.korting = korting
                    inschrijving.save(update_fields=['korting'])

                    procent = korting.percentage / Decimal(100)
                    korting_euro = inschrijving.bestelling.bedrag_euro * procent
                    korting_euro = 0 - korting_euro     # korting is een negatief bedrag
                    # self._stdout.write('   korting_euro: %s' % korting_euro)

                    kort_str, redenen_lst = beschrijf_korting(korting)
                    regel = BestellingRegel(
                                    korte_beschrijving=kort_str,
                                    korting_redenen=BESTELLING_KORT_BREAK.join(redenen_lst),
                                    korting_ver_nr=korting.uitgegeven_door.ver_nr,
                                    bedrag_euro=korting_euro,
                                    code=BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING)
                    regel.save()
                    nieuwe_regels.append(regel)

                    if korting.soort == WEDSTRIJD_KORTING_COMBI:
                        try:
                            combi_korting_euro[korting.pk] += product.korting_euro
                        except KeyError:
                            combi_korting_euro[korting.pk] = product.korting_euro
            # for
        # for

        # voeg alle combi-kortingen samen
        combi_pks = list(combi_korting_euro.keys())
        # self._stdout.write('combi_pks: %s' % repr(combi_pks))
        for inschrijving in alle_inschrijvingen:
            if inschrijving.korting and inschrijving.korting.pk in combi_pks:
                korting_euro = combi_korting_euro[inschrijving.korting.pk]
                regel = inschrijving.bestelling
                if korting_euro:
                    # samenvoegen tot de totale korting
                    product.korting_euro = korting_euro
                    product.save(update_fields=['korting_euro'])
                    combi_korting_euro[inschrijving.korting.pk] = None      # niet nog een keer geven
                else:
                    # deze korting op nul zetten
                    inschrijving.korting = None
                    inschrijving.save(update_fields=['korting'])
                    product.korting_euro = Decimal(0)
                    product.save(update_fields=['korting_euro'])
        # for

        for inschrijving in alle_inschrijvingen:
            regel = inschrijving.bestelling
            self._stdout.write('regel: %s' % regel)
            if inschrijving.korting:
                self._stdout.write('korting: %s' % inschrijving.korting)
                # self._stdout.write('korting_euro: %s' % product.korting_euro)
            else:
                self._stdout.write('korting: geen')

        return nieuwe_regels

    def kies_kortingen(self, regel_pks: list[int]) -> list[BestellingRegel]:
        """
            bepaal welke kortingen van toepassing zijn en koppel deze aan de producten in het mandje

            kortingen mogen niet stapelen --> daarom heeft elk product maximaal 1 korting
            als meerdere kortingen van toepassing zijn, dan we geven de hoogste korting
        """

        self._analyseer_inschrijvingen(regel_pks)
        self._zoek_mogelijke_kortingen()

        alle_inschrijvingen = [inschrijving
                               for inschrijving in self._lid_nr_wedstrijd_pk2inschrijving.values()]

        self._max_korting_euro = Decimal(0)
        self._max_korting_pks = None
        self._analyseer_kortingen_recursief_combi(alle_inschrijvingen)

        if self._max_korting_pks:
            korting_euro_str = format_bedrag_euro(self._max_korting_euro)
            self._stdout.write('[INFO] Maximale korting is %s met korting pks=%s' % (korting_euro_str,
                                                                                     repr(self._max_korting_pks)))
            nieuwe_regels = self._kortingen_toepassen(alle_inschrijvingen, self._max_korting_pks)
        else:
            nieuwe_regels = list()

        return nieuwe_regels


# end of file
