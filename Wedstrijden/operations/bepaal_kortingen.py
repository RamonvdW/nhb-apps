# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db.utils import DatabaseError
from Bestelling.definities import BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING, BESTELLING_KORT_BREAK
from Bestelling.models import BestellingRegel
from Betaal.format import format_bedrag_euro
from Wedstrijden.definities import (WEDSTRIJD_KORTING_COMBI, WEDSTRIJD_KORTING_SPORTER, WEDSTRIJD_KORTING_VERENIGING,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD, WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD)
from Wedstrijden.models import WedstrijdKorting, WedstrijdInschrijving, beschrijf_korting
from decimal import Decimal


class BepaalAutomatischeKorting(object):

    """
        Bepaal de beste, toegestane wedstrijdkorting voor een sporter uitzoeken.
        Wordt gebruikt vanuit de Bestellingen applicatie, als het mandje wijzigt (toevoegen, verwijderen, opschonen).
    """

    def __init__(self, stdout, verbose=False):
        self._stdout = stdout
        self._verbose = verbose
        self._org_ver_nrs = list()                                # verenigingen die voorkomen in het mandje
        self._lid_nr2ver_nr = dict()                              # [lid_nr] = ver_nr
        self._lid_nr2wedstrijd_pks = dict()                       # [lid_nr] = [wedstrijd.pk, ...]
        self._lid_nr2wedstrijd_pks_eerder = dict()                # [lid_nr] = [wedstrijd.pk, ...]
        self._lid_nr_wedstrijd_pk2inschrijving = dict()           # [(lid_nr, wedstrijd_pk)] = inschrijving
        self._alle_combi_kortingen = list()
        self._max_korting_euro = None
        self._max_korting_pks = None

    def _analyseer_inschrijvingen(self, regel_pks: list):
        self._org_ver_nrs = list()
        self._lid_nr2ver_nr = dict()
        self._lid_nr2wedstrijd_pks = dict()
        self._lid_nr2wedstrijd_pks_eerder = dict()
        self._lid_nr_wedstrijd_pk2inschrijving = dict()

        # laad de inhoud van het mandje en reset all kortingen
        for inschrijving in (WedstrijdInschrijving
                             .objects
                             .filter(bestelling__pk__in=regel_pks)
                             .exclude(sporterboog__sporter__bij_vereniging=None)
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
            ver_nr = sporter.bij_vereniging.ver_nr
            self._lid_nr2ver_nr[lid_nr] = ver_nr

            try:
                self._lid_nr2wedstrijd_pks[lid_nr].append(inschrijving.wedstrijd.pk)
            except KeyError:
                self._lid_nr2wedstrijd_pks[lid_nr] = [inschrijving.wedstrijd.pk]

            tup = (lid_nr, inschrijving.wedstrijd.pk)
            self._lid_nr_wedstrijd_pk2inschrijving[tup] = inschrijving
        # for

        # zoek, i.v.m. combinatiekortingen, ook naar wedstrijden waar al op ingeschreven is
        # maar we willen niet stapelen, dus als een eerdere inschrijving al een korting heeft, dan niet overwegen
        for lid_nr, nieuwe_pks in self._lid_nr2wedstrijd_pks.items():
            pks = list(WedstrijdInschrijving
                       .objects
                       .filter(sporterboog__sporter__lid_nr=lid_nr)
                       .filter(korting=None)                            # voorkom stapelen van kortingen
                       .exclude(status__in=(WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD,
                                            WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD))
                       .exclude(wedstrijd__pk__in=nieuwe_pks)
                       .values_list('wedstrijd__pk', flat=True))
            self._lid_nr2wedstrijd_pks_eerder[lid_nr] = pks
        # for

        if self._verbose:
            self._stdout.write('inschrijvingen:')
            for lid_nr, pks in self._lid_nr2wedstrijd_pks.items():
                self._stdout.write('  %s in wedstrijd pks %s' % (lid_nr, repr(pks)))

            self._stdout.write('inschrijvingen_eerder:')
            for lid_nr, pks in self._lid_nr2wedstrijd_pks_eerder.items():
                self._stdout.write('  %s in wedstrijd pks %s' % (lid_nr, repr(pks)))

            self._stdout.write('org_ver_nrs: %s' % repr(self._org_ver_nrs))

    def _zoek_mogelijke_kortingen(self):
        """ koppel aan elke inschrijving een mogelijke korting """
        self._alle_combi_kortingen = list()

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

        # self._stdout.write('Alle gevonden kortingen:')
        # for tup, inschrijving in self._lid_nr_wedstrijd_pk2inschrijving.items():
        #     lid_nr, wedstrijd_pk = tup
        #     self._stdout.write('  voor %s %s --> %s' % (lid_nr, inschrijving, inschrijving.mogelijke_kortingen))
        # # for

    def _analyseer_kortingen(self, alle_inschrijvingen):
        totaal_korting_euro = Decimal(0)
        toegepaste_korting_pks = list()
        for inschrijving in alle_inschrijvingen:
            if inschrijving.korting:
                toegepaste_korting_pks.append(inschrijving.korting.pk)
                procent = inschrijving.korting.percentage / Decimal('100')
                regel = inschrijving.bestelling
                self._stdout.write(' procent=%s, bedrag=%s' % (procent, regel.bedrag_euro))
                totaal_korting_euro += (regel.bedrag_euro * procent)
        # for

        if self._verbose:
            self._stdout.write('  totaal_korting: %s met kortingen %s' % (format_bedrag_euro(totaal_korting_euro),
                                                                          repr(toegepaste_korting_pks)))

        if totaal_korting_euro > self._max_korting_euro:
            self._max_korting_euro = totaal_korting_euro
            self._max_korting_pks = tuple(toegepaste_korting_pks)

    def _analyseer_kortingen_recursief(self, alle_inschrijvingen, gebruikte_kortingen):
        if self._verbose:
            self._stdout.write('analyseer_kortingen_recursief: gebruikte_kortingen: %s' % gebruikte_kortingen)

        self._analyseer_kortingen(alle_inschrijvingen)

        for inschrijving in alle_inschrijvingen:
            if not inschrijving.korting:
                for korting in inschrijving.mogelijke_kortingen:
                    if korting.pk not in gebruikte_kortingen:
                        gebruikte_kortingen.append(korting.pk)
                        inschrijving.korting = korting
                        self._analyseer_kortingen(alle_inschrijvingen)
                        gebruikte_kortingen.remove(korting.pk)
                # for
                inschrijving.korting = None
        # for

    def _analyseer_kortingen_recursief_combi(self, alle_inschrijvingen, gebruikte_kortingen=()):
        if self._verbose:
            self._stdout.write('analyseer_kortingen_recursief_combi: gebruikte_kortingen: %s' % repr(gebruikte_kortingen))

        gebruikte_kortingen = list(gebruikte_kortingen)     # maak een kopie

        # pas een combi-korting toe
        for korting in self._alle_combi_kortingen:
            if korting.pk not in gebruikte_kortingen:
                gebruikte_kortingen.append(korting.pk)

                # pas deze korting toe
                reset_lijst = list()
                for inschrijving in alle_inschrijvingen:
                    if not inschrijving.korting and inschrijving.heeft_mogelijke_combi_korting:
                        if korting in inschrijving.mogelijke_kortingen:     # pragma: no branch
                            inschrijving.korting = korting
                            reset_lijst.append(inschrijving)
                # for

                # probeer nog meer combi-kortingen
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
        # self._stdout.write('[DEBUG] alle_inschrijvingen:')
        # for inschrijving in alle_inschrijvingen:
        #     self._stdout.write('  %s' % inschrijving)
        # # for
        # self._stdout.write('[DEBUG] geef_korting_pks: %s' % repr(geef_korting_pks))

        nieuwe_regels = list()
        combi_korting_euro = dict()     # [korting.pk] = Decimal
        for inschrijving in alle_inschrijvingen:
            for korting in inschrijving.mogelijke_kortingen:
                if korting.pk in geef_korting_pks:
                    # geef deze korting
                    # self._stdout.write('[DEBUG] gekozen korting: %s' % korting)
                    inschrijving.korting = korting
                    inschrijving.save(update_fields=['korting'])

                    procent = korting.percentage / Decimal(100)
                    korting_euro = inschrijving.bestelling.bedrag_euro * procent
                    korting_euro = 0 - korting_euro     # korting is een negatief bedrag
                    # self._stdout.write('   korting_euro: %s' % korting_euro)

                    if korting.soort == WEDSTRIJD_KORTING_COMBI:
                        try:
                            combi_korting_euro[korting.pk] += korting_euro
                        except KeyError:
                            combi_korting_euro[korting.pk] = korting_euro
                    else:
                        kort_str, redenen_lst = beschrijf_korting(korting)
                        regel = BestellingRegel(
                                        korte_beschrijving=kort_str,
                                        korting_redenen=BESTELLING_KORT_BREAK.join(redenen_lst),
                                        korting_ver_nr=korting.uitgegeven_door.ver_nr,
                                        bedrag_euro=korting_euro,
                                        code=BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING)
                        regel.save()
                        nieuwe_regels.append(regel)
            # for
        # for

        # voeg een regel toe voor het total combi-korting bedrag
        combi_pks = list(combi_korting_euro.keys())
        if len(combi_pks):
            # self._stdout.write('[DEBUG] combi_pks: %s' % repr(combi_pks))
            for inschrijving in alle_inschrijvingen:
                if inschrijving.korting and inschrijving.korting.pk in combi_pks:
                    korting_euro = combi_korting_euro[inschrijving.korting.pk]
                    if korting_euro:
                        kort_str, redenen_lst = beschrijf_korting(inschrijving.korting)
                        regel = BestellingRegel(
                                        korte_beschrijving=kort_str,
                                        korting_redenen=BESTELLING_KORT_BREAK.join(redenen_lst),
                                        korting_ver_nr=inschrijving.korting.uitgegeven_door.ver_nr,
                                        bedrag_euro=korting_euro,
                                        code=BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING)
                        regel.save()
                        nieuwe_regels.append(regel)
                        combi_korting_euro[inschrijving.korting.pk] = None      # niet nog een keer geven
            # for

        for inschrijving in alle_inschrijvingen:
            regel = inschrijving.bestelling
            if inschrijving.korting:
                self._stdout.write('[DEBUG] bestelling regel %s --> korting pk=%s: %s' % (regel,
                                                                                          inschrijving.korting.pk,
                                                                                          inschrijving.korting))
            else:
                self._stdout.write('[DEBUG] bestelling regel %s --> geen korting' % regel)

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

        if self._verbose:
            self._stdout.write('alle_inschrijvingen:')
            for inschrijving in self._lid_nr_wedstrijd_pk2inschrijving.values():
                self._stdout.write('    %s' % inschrijving)
                self._stdout.write('       bestelling regel %s voor %s' % (
                                                format_bedrag_euro(inschrijving.bestelling.bedrag_euro),
                                                inschrijving.bestelling))
                self._stdout.write('       mogelijke kortingen: %s' % inschrijving.mogelijke_kortingen)
            # for

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
