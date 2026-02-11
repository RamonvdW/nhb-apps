# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.definities import DEEL_RK
from Competitie.models import KampioenschapSporterBoog, KampioenschapTeam
from openpyxl.utils.exceptions import InvalidFileException
from decimal import Decimal, InvalidOperation
import openpyxl
import zipfile


class Command(BaseCommand):
    help = "Importeer uitslag RK Indoor Teams"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.dryrun = True
        self.verbose = False
        self.deelnemers = dict()            # [lid_nr] = [KampioenschapSporterBoog, ...]
        self.teams_cache = list()           # [KampioenschapTeam, ...]
        self.team_lid_nrs = dict()          # [team.pk] = [lid_nr, ...]
        self.ver_lid_nrs = dict()           # [ver_nr] = [lid_nr, ...]
        self.kamp_lid_nrs = list()          # [lid_nr, ...]     iedereen die geplaatst is voor de kampioenschappen
        self.deelnemende_teams = dict()     # [team naam] = KampioenschapTeam
        self.team_klasse = None
        self.toegestane_bogen = list()

    def add_arguments(self, parser):
        parser.add_argument('--dryrun', action='store_true')
        parser.add_argument('--verbose', action='store_true')
        parser.add_argument('bestand', type=str,
                            help='Pad naar het Excel bestand')

    def _zet_team_klasse(self, klasse):
        self.team_klasse = klasse
        self.toegestane_bogen = list(klasse.boog_typen.values_list('afkorting', flat=True))
        # self.stdout.write('[DEBUG] toegestane bogen: %s' % repr(self.toegestane_bogen))

    def _deelnemers_ophalen(self):
        for deelnemer in (KampioenschapSporterBoog
                          .objects
                          .filter(kampioenschap__competitie__afstand='18',
                                  kampioenschap__deel=DEEL_RK)
                          .select_related('kampioenschap',
                                          'kampioenschap__rayon',
                                          'sporterboog__sporter',
                                          'sporterboog__boogtype',
                                          'indiv_klasse')):

            lid_nr = deelnemer.sporterboog.sporter.lid_nr
            ver_nr = deelnemer.bij_vereniging.ver_nr

            try:
                self.deelnemers[lid_nr].append(deelnemer)
            except KeyError:
                self.deelnemers[lid_nr] = [deelnemer]

            try:
                self.ver_lid_nrs[ver_nr].append(lid_nr)
            except KeyError:
                self.ver_lid_nrs[ver_nr] = [lid_nr]

            self.kamp_lid_nrs.append(lid_nr)
        # for

    def _teams_ophalen(self):
        for team in (KampioenschapTeam
                     .objects
                     .filter(kampioenschap__competitie__afstand='18',
                             kampioenschap__deel=DEEL_RK)
                     .select_related('kampioenschap',
                                     'kampioenschap__rayon',
                                     'vereniging',
                                     'team_type',
                                     'team_klasse')
                     .prefetch_related('gekoppelde_leden',
                                       'feitelijke_leden')):

            self.teams_cache.append(team)
            self.team_lid_nrs[team.pk] = [deelnemer.sporterboog.sporter.lid_nr
                                          for deelnemer in team.gekoppelde_leden.all()]
        # for

    def _sort_op_gemiddelde(self, lid_nrs):
        gem = list()
        for lid_nr in lid_nrs:
            deelnemer_all = [deelnemer
                             for deelnemer in self.deelnemers[lid_nr]
                             if deelnemer.sporterboog.boogtype.afkorting in self.toegestane_bogen]

            if len(deelnemer_all) == 1:
                deelnemer = deelnemer_all[0]
            else:
                self.stderr.write('[WARNING] TODO: bepaal juiste deelnemer uit %s' % repr(deelnemer_all))
                deelnemer = deelnemer_all[0]
            tup = (deelnemer.gemiddelde, lid_nr)
            gem.append(tup)
        # for
        gem.sort(reverse=True)
        return gem

    def _get_deelnemer(self, lid_nr, lid_ag):
        deelnemer_all = self.deelnemers[lid_nr]
        for deelnemer in deelnemer_all:
            if abs(deelnemer.gemiddelde - lid_ag) < 0.0001:
                return deelnemer
        # for

        self.stderr.write('[WARNING] TODO: bepaal juiste deelnemer met ag=%s uit\n%s' % (
                            lid_ag,
                            "\n".join(["%s / %s / %s" % (deelnemer,
                                                         deelnemer.sporterboog.boogtype.afkorting,
                                                         deelnemer.gemiddelde) for deelnemer in deelnemer_all])))
        deelnemer = deelnemer_all[0]
        return deelnemer

    def _get_team(self, team_naam: str, ver_nr: int, row_nr: int):
        # if self.verbose:
        #     self.stdout.write('[DEBUG] get_team: team_klasse=%s' % repr(self.team_klasse))

        up_naam = team_naam.upper()
        sel_teams = list()
        for team in self.teams_cache:
            # self.stdout.write('[DEBUG] cached team: %s' % repr(team))
            if team.vereniging.ver_nr == ver_nr:
                if team.team_naam.upper() == up_naam:
                    if self.team_klasse is None or team.team_klasse == self.team_klasse:
                        sel_teams.append(team)
        # for

        if len(sel_teams) == 0:
            # niet gevonden, dus waarschijnlijk is de naam aangepast
            for team in self.teams_cache:
                # self.stdout.write('[DEBUG] cached team: %s' % repr(team))
                if team.vereniging.ver_nr == ver_nr:
                    team_up_naam = team.team_naam.upper()
                    if team_up_naam in up_naam or up_naam in team_up_naam:
                        if self.team_klasse is None or team.team_klasse == self.team_klasse:
                            sel_teams.append(team)
                            self.stdout.write('[WARNING] Aangepaste team naam: %s --> %s' % (
                                                repr(team.team_naam), repr(team_naam)))
            # for

        kamp_team = None
        if len(sel_teams) == 1:
            kamp_team = sel_teams[0]
        elif len(sel_teams) > 1:
            self.stderr.write('[ERROR] Kan team %s van vereniging %s op regel %s niet kiezen uit\n%s' % (
                repr(team_naam), ver_nr, row_nr, "\n".join([str(team) for team in sel_teams])))

        if kamp_team is None:
            self.stderr.write('[ERROR] Kan team %s van vereniging %s op regel %s niet vinden' % (
                repr(team_naam), ver_nr, row_nr))

        return kamp_team

    def _zet_rank_en_volgorde(self, goud, zilver, brons, vierde, vijfden):

        if self.verbose:
            self.stdout.write('[DEBUG] goud: %s' % repr(goud))
            self.stdout.write('[DEBUG] zilver: %s' % repr(zilver))
            self.stdout.write('[DEBUG] brons: %s' % repr(brons))
            self.stdout.write('[DEBUG] vierde: %s' % repr(vierde))
            self.stdout.write('[DEBUG] vijfden: %s' % repr(vijfden))

        rank = 1
        for team_naam in (goud, zilver, brons, vierde):
            if team_naam:
                try:
                    kamp_team = self.deelnemende_teams[team_naam]
                except KeyError:
                    self.stderr.write('[ERROR] Kan team %s niet vinden!' % repr(team_naam))
                else:
                    kamp_team.result_rank = rank
                    kamp_team.result_volgorde = rank
                    if not self.dryrun:
                        kamp_team.save(update_fields=['result_rank', 'result_volgorde'])
            rank += 1
        # for

        # de rest is 5e
        # result_volgorde is al gezet, gebaseerd op aflopende scores
        for team_naam in vijfden:
            try:
                kamp_team = self.deelnemende_teams[team_naam]
            except KeyError:
                self.stderr.write('[ERROR] Kan team %s niet vinden!' % repr(team_naam))
            else:
                kamp_team.result_rank = 5
                if not self.dryrun:
                    kamp_team.save(update_fields=['result_rank'])
        # for

    @staticmethod
    def _lees_team_naam(ws, cell):
        team_naam = ws[cell].value
        if team_naam is None:
            team_naam = ''
        elif team_naam.upper() in ('N.V.T.', 'NVT', 'BYE'):
            team_naam = ''
        return team_naam

    def _importeer_teams_en_sporters(self, ws):
        for row_nr in range(8, 43+1, 5):

            # team naam
            team_naam = self._lees_team_naam(ws, 'B' + str(row_nr))
            if not team_naam:
                continue

            # ver_nr
            try:
                ver_nr = int(ws['C' + str(row_nr)].value)
            except ValueError:
                continue

            # zoek het team erbij
            kamp_team = self._get_team(team_naam, ver_nr, row_nr)
            if kamp_team is None:
                continue

            self.deelnemende_teams[team_naam] = kamp_team
            self.stdout.write('[DEBUG] Gevonden team: %s van ver %s' % (repr(team_naam), ver_nr))

            if self.team_klasse is None:
                self._zet_team_klasse(kamp_team.team_klasse)
            else:
                if self.team_klasse != kamp_team.team_klasse:
                    self.stderr.write('[ERROR] Inconsistente team klasse op regel %s: %s (eerdere teams: %s)' % (
                                        row_nr, kamp_team.team_klasse, self.team_klasse))
                    continue

            # lees de deelnemers van dit team
            ver_lid_nrs = self.ver_lid_nrs[ver_nr]
            team_lid_nrs = self.team_lid_nrs[kamp_team.pk]
            aantal_gekoppeld = len(team_lid_nrs)
            gevonden_lid_nrs = list()
            feitelijke_deelnemers = list()

            for sporter_row in range(row_nr+1, row_nr+4):
                lid_nr_str = ws['C' + str(sporter_row)].value
                lid_ag_str = ws['D' + str(sporter_row)].value
                lid_ag_str = lid_ag_str.replace(',', '.')       # decimale komma naar punt

                try:
                    lid_nr = int(lid_nr_str)
                except ValueError:
                    self.stderr.write('[ERROR] Geen valide lid_nr %s op regel %s' % (repr(lid_nr_str), sporter_row))
                    continue
                else:
                    if lid_nr not in self.kamp_lid_nrs:
                        self.stderr.write('[ERROR] Lid %s is niet gekwalificeerd voor dit kampioenschap!' % lid_nr)
                        continue

                    if lid_nr not in ver_lid_nrs:
                        self.stderr.write('[ERROR] Lid %s is niet van vereniging %s!' % (lid_nr, ver_nr))
                        continue

                    try:
                        lid_ag = round(Decimal(lid_ag_str), 3)  # 3 cijfers achter de komma
                    except (TypeError, InvalidOperation):
                        self.stderr.write('[ERROR] Geen valide AG %s op regel %s' % (repr(lid_ag_str), sporter_row))
                        continue

                    deelnemer = self._get_deelnemer(lid_nr, lid_ag)
                    self.stdout.write('[DEBUG] Gevonden sporter: %s' % deelnemer.sporterboog.sporter.lid_nr_en_volledige_naam())

                    feitelijke_deelnemers.append(deelnemer)
                    gevonden_lid_nrs.append(lid_nr)
            # for sporter

            # haal de verwachte lid_nrs eruit
            feitelijke_lid_nrs = [lid_nr
                                  for lid_nr in gevonden_lid_nrs
                                  if lid_nr in team_lid_nrs]
            if self.verbose:
                self.stdout.write('[DEBUG] feitelijke_lid_nrs van team [%s] %s: %s' % (
                                        ver_nr, team_naam, repr(feitelijke_lid_nrs)))

            for lid_nr in feitelijke_lid_nrs:
                gevonden_lid_nrs.remove(lid_nr)
                team_lid_nrs.remove(lid_nr)
            # for

            if len(gevonden_lid_nrs):
                uitvallers = self._sort_op_gemiddelde(team_lid_nrs)
                invallers = self._sort_op_gemiddelde(gevonden_lid_nrs)
                afgekeurd = list()

                if len(invallers) > len(uitvallers):
                    self.stderr.write('[ERROR] Te veel invallers voor team %s met max %s sporters (ver: %s)' % (
                                        repr(team_naam), aantal_gekoppeld, ver_nr))
                    feitelijke_deelnemers = list()
                else:
                    while len(invallers) > 0:
                        gemiddelde_in, lid_nr_in = invallers.pop(0)
                        gemiddelde_uit, lid_nr_uit = uitvallers[0]
                        if gemiddelde_in > gemiddelde_uit:
                            # mag niet invallen
                            afgekeurd.append(lid_nr_in)
                            self.stderr.write(
                                '[ERROR] Te hoog gemiddelde %s voor invaller %s voor team %s van vereniging %s' % (
                                        gemiddelde_in, lid_nr_in, team_naam, ver_nr))
                            for gemiddelde, lid_nr in uitvallers:
                                self.stderr.write('        Uitvaller %s heeft gemiddelde %s' % (lid_nr, gemiddelde))
                        else:
                            # mag wel invaller en vervangt de hoogste uitvaller
                            uitvallers.pop(0)
                    # while

                    feitelijke_deelnemers = [deelnemer
                                             for deelnemer in feitelijke_deelnemers
                                             if deelnemer.sporterboog.sporter.lid_nr not in afgekeurd]

            if len(feitelijke_deelnemers) != 3:
                self.stderr.write('[ERROR] Maar %s deelnemers in team %s' % (
                                        len(feitelijke_deelnemers), repr(kamp_team.team_naam)))

            if not self.dryrun:
                if len(feitelijke_deelnemers) > 0:
                    kamp_team.feitelijke_leden.set(feitelijke_deelnemers)
        # for team

    def _importeer_eindstand(self, ws):
        rank = 0

        for row_nr in range(8, 15+1):
            # team naam
            team_naam = self._lees_team_naam(ws, 'B' + str(row_nr))
            if not team_naam:
                continue

            kamp_team = self.deelnemende_teams[team_naam]

            matchpunten_str = ws['D' + str(row_nr)].value
            try:
                matchpunten = int(matchpunten_str)
            except ValueError:
                self.stderr.write('[ERROR] Geen valide matchpunten %s op regel %s' % (repr(matchpunten_str), row_nr))
                continue

            rank += 1
            self.stdout.write('[DEBUG] Rank %s: %s punten, team %s' % (rank,
                                                                       matchpunten,
                                                                       repr(team_naam)))

            # 100=blanco, 32000=no show, 32001=reserve
            kamp_team.result_rank = rank
            kamp_team.result_volgorde = rank
            kamp_team.result_teamscore = matchpunten

            if not self.dryrun:
                kamp_team.save(update_fields=['result_rank', 'result_volgorde', 'result_teamscore'])
        # for

    def handle(self, *args, **options):

        self.dryrun = options['dryrun']
        self.verbose = options['verbose']

        fname = options['bestand']
        self.stdout.write('[INFO] Lees bestand %s' % repr(fname))
        try:
            prg = openpyxl.load_workbook(fname,
                                         data_only=True)        # do not evaluate formulas; use last calculated values
        except (OSError, zipfile.BadZipFile, KeyError, InvalidFileException) as exc:
            self.stderr.write('[ERROR] Kan het excel bestand niet openen (%s)' % str(exc))
            return

        blad = 'Deelnemers'
        try:
            ws_deelnemers = prg[blad]
        except KeyError:        # pragma: no cover
            self.stderr.write('[ERROR] Kan blad %s niet vinden' % repr(blad))
            return

        blad = 'Stand'
        try:
            ws_stand = prg[blad]
        except KeyError:        # pragma: no cover
            self.stderr.write('[ERROR] Kan blad %s niet vinden' % repr(blad))
            return

        self._deelnemers_ophalen()
        self._teams_ophalen()

        self._importeer_teams_en_sporters(ws_deelnemers)
        self._importeer_eindstand(ws_stand)

# end of file
