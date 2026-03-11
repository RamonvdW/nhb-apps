# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from .lees_teams_excel import LeesTeamsExcel
from Competitie.definities import KAMP_RANK_NO_SHOW
from CompLaagBond.models import TeamBK
from CompLaagRayon.models import DeelnemerRK, TeamRK
from openpyxl.utils.exceptions import InvalidFileException
from decimal import Decimal, InvalidOperation
import openpyxl
import zipfile


class ImporteerUitslagTeamsExcel:

    def __init__(self, stdout, stderr, dryrun: bool, verbose: bool, afstand: str, is_bk: bool):
        self.stdout = stdout
        self.stderr = stderr
        self.dryrun = dryrun
        self.verbose = verbose
        self.afstand = afstand
        self.is_bk = is_bk

        self.has_error = False
        self.team_klasse = None
        self.rayon_nr = 0

        self.deelnemers = dict()            # [lid_nr] = [DeelnemerRK of DeelnemerBK, ...]
        self.teams_cache = list()           # [TeamRK/TeamBK, ...]
        self.team_lid_nrs = dict()          # [team.pk] = [lid_nr, ...]
        self.ver_lid_nrs = dict()           # [ver_nr] = [lid_nr, ...]
        self.kamp_lid_nrs = list()          # [lid_nr, ...]     iedereen die geplaatst is voor de kampioenschappen
        self.deelnemende_teams = dict()     # [team naam] = TeamRK/TeamBK
        self.toegestane_bogen = list()

    def _zet_team_klasse(self, klasse):
        self.team_klasse = klasse
        self.toegestane_bogen = list(klasse.boog_typen.values_list('afkorting', flat=True))
        if self.verbose:
            self.stdout.write('[DEBUG] toegestane bogen: %s' % repr(self.toegestane_bogen))

    def _deelnemers_ophalen(self):
        # teamleden zijn altijd de sporters gekwalificeerd voor het RK individueel
        # ook voor het BK
        for deelnemer in (DeelnemerRK
                          .objects
                          .filter(kamp__competitie__afstand=self.afstand)
                          .select_related('kamp',
                                          'kamp__rayon',
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
        if self.is_bk:
            qset = TeamBK.objects.filter(kamp__competitie__afstand=self.afstand).select_related('kamp')
        else:
            qset = TeamRK.objects.filter(kamp__competitie__afstand=self.afstand).select_related('kamp', 'kamp__rayon')

        for team in (qset
                     .select_related('vereniging',
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
                if len(deelnemer_all) == 0:
                    self.stderr.write('[ERROR] Geen deelnemers gevonden voor lid %s' % lid_nr)
                    self.has_error = True
                    continue

                self.stdout.write('[WARNING] Neem de eerste want kan niet kiezen uit: %s' % repr(deelnemer_all))
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

        self.stdout.write('[WARNING] TODO: bepaal juiste deelnemer met ag=%s uit\n%s' % (
                            lid_ag,
                            "\n".join(["%s / %s / %s" % (deelnemer,
                                                         deelnemer.sporterboog.boogtype.afkorting,
                                                         deelnemer.gemiddelde) for deelnemer in deelnemer_all])))
        deelnemer = deelnemer_all[0]
        return deelnemer

    def _get_team(self, team_naam: str, ver_nr: int, row_nr: int):
        up_naam = team_naam.upper()
        sel_teams = list()
        for team in self.teams_cache:
            # self.stdout.write('[DEBUG] cached team: %s' % repr(team))
            if team.vereniging.ver_nr == ver_nr:
                if team.team_naam.upper() == up_naam:
                    if team.team_klasse == self.team_klasse:
                        sel_teams.append(team)
        # for

        if len(sel_teams) == 0:
            # niet gevonden, dus waarschijnlijk is de naam aangepast
            for team in self.teams_cache:
                # self.stdout.write('[DEBUG] cached team: %s' % repr(team))
                if team.vereniging.ver_nr == ver_nr:
                    team_up_naam = team.team_naam.upper()
                    if team_up_naam in up_naam or up_naam in team_up_naam:
                        if team.team_klasse == self.team_klasse:
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
            self.has_error = True

        if kamp_team is None:
            self.stderr.write('[ERROR] Kan team %s van vereniging %s op regel %s niet vinden' % (
                repr(team_naam), ver_nr, row_nr))
            self.has_error = True

        return kamp_team

    def _bepaal_klasse_en_rayon(self, lees: LeesTeamsExcel):
        mogelijke_klassen = list()

        # loop alle teams af
        for lees_team in lees.teams:
            team_naam = lees_team.team_naam
            ver_nr = lees_team.ver_nr

            # zoek de teams van de vereniging erbij
            up_naam = team_naam.upper()
            ver_teams = list()
            for team in self.teams_cache:
                # self.stdout.write('[DEBUG] cached team: %s' % repr(team))
                if team.vereniging.ver_nr == ver_nr:
                    if team.team_naam.upper() == up_naam:
                        ver_teams.append(team)
            # for

            if len(ver_teams) == 1:
                # duidelijk
                team_klasse = ver_teams[0].team_klasse
                if team_klasse not in mogelijke_klassen:
                    mogelijke_klassen.append(team_klasse)

                self.rayon_nr = ver_teams[0].vereniging.regio.rayon_nr
        # for team row

        if len(mogelijke_klassen) == 0:
            self.stderr.write('[ERROR] Team klasse niet kunnen bepalen (geen teams)')
            self.has_error = True
            return

        if len(mogelijke_klassen) != 1:
            self.stderr.write('[ERROR] Kan team klasse niet kiezen uit: %s' % repr(mogelijke_klassen))
            self.has_error = True
            return

        self._zet_team_klasse(mogelijke_klassen[0])

        if not self.is_bk:
            self.stdout.write('[INFO] Rayon: %s' % self.rayon_nr)

        self.stdout.write('[INFO] Klasse: %s' % self.team_klasse)

    def _bepaal_teams_en_sporters(self, lees: LeesTeamsExcel):
        # loop alle teams af
        for lees_team in lees.teams:
            # vind het team
            kamp_team = self._get_team(lees_team.team_naam, lees_team.ver_nr, lees_team.row_nr)
            if kamp_team is None:
                continue

            self.deelnemende_teams[lees_team.team_naam] = kamp_team
            self.stdout.write('[INFO] Gevonden team: %s van ver %s' % (repr(lees_team.team_naam), lees_team.ver_nr))

            if self.team_klasse != kamp_team.team_klasse:
                self.stderr.write('[ERROR] Inconsistente team klasse op regel %s: %s (eerdere teams: %s)' % (
                                    lees_team.row_nr, kamp_team.team_klasse, self.team_klasse))
                self.has_error = True
                continue

            # lees de deelnemers van dit team
            ver_lid_nrs = self.ver_lid_nrs[lees_team.ver_nr]
            team_lid_nrs = self.team_lid_nrs[kamp_team.pk]
            aantal_gekoppeld = len(team_lid_nrs)
            gevonden_lid_nrs = list()
            feitelijke_deelnemers = list()

            for lees_lid in lees_team.leden:

                if lees_lid.lid_nr not in self.kamp_lid_nrs:
                    self.stderr.write('[ERROR] Lid %s is niet gekwalificeerd voor dit kampioenschap!' % lees_lid.lid_nr)
                    self.has_error = True
                    continue

                if lees_lid.lid_nr not in ver_lid_nrs:
                    self.stderr.write('[ERROR] Lid %s is niet van vereniging %s!' % (lees_lid.lid_nr, lees_team.ver_nr))
                    self.has_error = True
                    continue

                deelnemer = self._get_deelnemer(lees_lid.lid_nr, lees_lid.lid_ag)
                self.stdout.write('[INFO] team lid: %s' % deelnemer.sporterboog.sporter.lid_nr_en_volledige_naam())

                feitelijke_deelnemers.append(deelnemer)
                gevonden_lid_nrs.append(lees_lid.lid_nr)
            # for sporter

            # haal de verwachte lid_nrs eruit
            feitelijke_lid_nrs = [lid_nr
                                  for lid_nr in gevonden_lid_nrs
                                  if lid_nr in team_lid_nrs]
            if self.verbose:
                self.stdout.write('[DEBUG] feitelijke_lid_nrs van team [%s] %s: %s' % (
                                        lees_team.ver_nr, lees_team.team_naam, repr(feitelijke_lid_nrs)))

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
                                        repr(lees_team.team_naam), aantal_gekoppeld, lees_team.ver_nr))
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
                                        gemiddelde_in, lid_nr_in, lees_team.team_naam, lees_team.ver_nr))
                            for gemiddelde, lid_nr in uitvallers:
                                self.stderr.write('        Uitvaller %s heeft gemiddelde %s' % (lid_nr, gemiddelde))
                            self.has_error = True
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
                self.has_error = True
                return

            if not self.dryrun:
                if len(feitelijke_deelnemers) > 0:
                    kamp_team.feitelijke_leden.set(feitelijke_deelnemers)
        # for team row

    def _bepaal_eindstand(self, lees: LeesTeamsExcel):

        if len(self.deelnemende_teams) == 0:
            self.stderr.write('[ERROR] Geen deelnemende teams gevonden!')
            self.has_error = True
            return

        first_team = next(iter(self.deelnemende_teams.values()))
        deelkamp = first_team.kamp
        self.stdout.write('[INFO] Deelkamp: %s' % deelkamp)

        # begin met alle teams in deze klasse op "no-show" te zetten
        # let op: dit kunnen ook reserve teams zijn (>8 deelnemers)
        expected_teams = list()
        for kamp_team in self.teams_cache:
            if kamp_team.kamp == deelkamp and kamp_team.team_klasse == self.team_klasse:
                if self.verbose:
                    self.stdout.write('[DEBUG] Verwacht team in deze klasse: %s' % kamp_team)
                kamp_team.result_rank = KAMP_RANK_NO_SHOW
                kamp_team.result_volgorde = 50 + kamp_team.volgorde
                kamp_team.result_teamscore = 0
                expected_teams.append(kamp_team)
        # for

        eindstand = list()
        alle_matchpunten = list()
        toon_shootoff = dict()  # [matchpunten] = True

        # loop alle regels af in de eindstand
        for stand in lees.eindstand:
            kamp_team = self.deelnemende_teams[stand.team_naam]

            # 100=blanco, 32000=no show, 32001=reserve
            kamp_team.result_teamscore = stand.matchpunten
            expected_teams.remove(kamp_team)
            alle_matchpunten.append(stand.matchpunten)

            if not stand.shootoff is None:
                toon_shootoff[stand.matchpunten] = True
                shootoff_str = str(stand.shootoff)
            else:
                shootoff_str = ''

            tup = (stand.matchpunten, shootoff_str, kamp_team.pk, kamp_team)
            eindstand.append(tup)
        # for

        # zet de uiteindelijke ranking
        eindstand.sort(reverse=True)        # hoogste eerst
        rank = volgorde = 1
        prev_score_tup = (-1, '')
        for tup in eindstand:
            matchpunten, shootoff_str, _, kamp_team = tup

            score_tup = (matchpunten, shootoff_str)
            if score_tup != prev_score_tup:
                rank = volgorde
            prev_score_tup = score_tup

            kamp_team.result_rank = rank
            kamp_team.result_volgorde = volgorde
            kamp_team.result_shootoff_str = ''

            if alle_matchpunten.count(matchpunten) == 1:
                # niet nodig, dus niet tonen
                pass
            else:
                if toon_shootoff.get(matchpunten, False):
                    if shootoff_str == '':
                        shootoff_str = '0'
                    kamp_team.result_shootoff_str = '(SO: %s)' % shootoff_str

            self.stdout.write('[INFO] Rank %s: %s punten, shootoff: %s, team %s' % (rank,
                                                                                    kamp_team.result_teamscore,
                                                                                    repr(kamp_team.result_shootoff_str),
                                                                                    repr(kamp_team.team_naam)))


            if not (self.dryrun or self.has_error):
                kamp_team.save(update_fields=['result_rank', 'result_volgorde',
                                              'result_teamscore', 'result_shootoff_str'])

            volgorde += 1
        # for

        # rapporteer de no-shows
        for kamp_team in expected_teams:
            self.stdout.write('[WARNING] Team %s van ver %s staat niet in de uitslag --> no-show' % (
                                repr(kamp_team.team_naam), kamp_team.vereniging.ver_nr))
            if not (self.dryrun or self.has_error):
                kamp_team.save(update_fields=['result_rank', 'result_volgorde', 'result_teamscore'])
        # for

    def importeer_bestand(self, fname: str):

        self.stdout.write('[INFO] Lees bestand %s' % repr(fname))

        lees = LeesTeamsExcel()
        lees.lees_bestand(fname)

        if lees.issues:
            for regel in lees.issues:
                self.stderr.write(regel)
            # for
        else:
            self._deelnemers_ophalen()
            self._teams_ophalen()

            self._bepaal_klasse_en_rayon(lees)

            if not self.has_error:
                self._bepaal_teams_en_sporters(lees)

            if not self.has_error:
                self._bepaal_eindstand(lees)

# end of file
