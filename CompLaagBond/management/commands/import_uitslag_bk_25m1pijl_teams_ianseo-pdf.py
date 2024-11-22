# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.definities import DEEL_BK, DEEL_RK
from Competitie.models import KampioenschapSporterBoog, KampioenschapTeam
from pypdf import PdfReader
import sys


class LeesPdf(object):

    def __init__(self, start_at="", stop_at=""):
        self.start_at = start_at
        self.stop_at = stop_at

        self.found_start = False
        self.found_stop = False

        self.huidige_regel = list()
        self.regels = list()

    def _visitor(self, text, cm, tm, font_dict, font_size):
        if self.found_stop:
            return

        if not text:
            # skip lege regel
            return

        # print(self.found_start, text)
        if self.stop_at in text:
            self.found_stop = True
            return

        if text == '\n':
            if self.found_start:
                self.regels.append(self.huidige_regel)
            else:
                if self.start_at in " ".join(self.huidige_regel):
                    self.found_start = True

            self.huidige_regel = list()
        else:
            text = text.strip()
            if not text:
                # skip lege regel
                return

            self.huidige_regel.append(text)

    def extract_from_pdf(self, fpath):
        self.found_start = False
        self.found_stop = False

        reader = PdfReader(fpath)
        for page in reader.pages:
            page.extract_text(visitor_text=self._visitor)
            if self.found_stop:
                break
        # for

        if len(self.huidige_regel):
            self.regels.append(self.huidige_regel)
            self.huidige_regel = list()

        tabs = list()
        lst = list()

        for regel in self.regels:
            # print('(%s) %s' % (len(regel), repr(regel)))

            # verwachte kolommen:
            #   pos, baan, naam, team_afkorting, team naam, score1/rank, score2/rank, totaal, aantal-10, aantal-9
            if len(regel) >= 10:
                _, _, naam, _, team_naam, score1, score2, _, count10, count9 = regel[:10]

                score1 = int(score1[:score1.find('/')])
                score2 = int(score2[:score2.find('/')])
                count10 = int(count10)
                count9 = int(count9)

                tup = (naam, team_naam, score1, score2, count10, count9)
                lst.append(tup)
            else:
                # nieuwe tabel
                if 'Land / Vereniging' in regel:
                    tabs.append(lst)
                    lst = list()
        # for

        if len(lst):
            tabs.append(lst)

        return tabs


class Command(BaseCommand):
    help = "Importeer uitslag team kampioenschap 25m1pijl Ianseo pdf"

    # PDF moet individuele bijdrage aan de teams bevatten
    # kolommen: Pos, Baan, Naam, VerNr++, Team naam, Score1/rank, Score2/rank, aantal 10, aantal 9

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.dryrun = True
        self.verbose = False
        self.deelnemers = dict()            # [lid_nr] = [KampioenschapSporterBoog, ...]
        self.teams_cache = list()           # [KampioenschapTeam, ...]
        self.pk2team: dict[int, KampioenschapTeam] = dict()    # [team.pk] = KampioenschapTeam
        self.team_gekoppelde_pks = dict()   # [team.pk] = [KampioenschapSporterBoog.pk, ...]
        self.ver_lid_nrs = dict()           # [ver_nr] = [lid_nr, ...]
        self.kamp_lid_nrs = list()          # [lid_nr, ...]     iedereen die geplaatst is voor de kampioenschappen

    def add_arguments(self, parser):
        parser.add_argument('--dryrun', action='store_true')
        parser.add_argument('--verbose', action='store_true')
        parser.add_argument('bestand', type=str,
                            help='Pad naar het pdf bestand')

    def _deelnemers_ophalen(self):
        # alle deelnemers van de RK individueel mogen meedoen met de BK teams
        # daarom halen we de DEEL_RK sporters op
        for deelnemer in (KampioenschapSporterBoog
                          .objects
                          .filter(kampioenschap__competitie__afstand='25',
                                  kampioenschap__deel=DEEL_RK)
                          .select_related('kampioenschap',
                                          'kampioenschap__rayon',
                                          'sporterboog__sporter',
                                          'sporterboog__boogtype',
                                          'indiv_klasse',
                                          'bij_vereniging')):

            lid_nr = deelnemer.sporterboog.sporter.lid_nr
            ver_nr = deelnemer.bij_vereniging.ver_nr

            try:
                self.deelnemers[lid_nr].append(deelnemer)
            except KeyError:
                self.deelnemers[lid_nr] = [deelnemer]

            try:
                if lid_nr not in self.ver_lid_nrs[ver_nr]:
                    self.ver_lid_nrs[ver_nr].append(lid_nr)
            except KeyError:
                self.ver_lid_nrs[ver_nr] = [lid_nr]

            self.kamp_lid_nrs.append(lid_nr)
        # for

    def _filter_deelnemers(self, team_klasse):
        # reduceer aantal KampioenschapSporterBoog aan de hand van de toegestaan bogen in deze wedstrijdklasse
        afkortingen = list(team_klasse.boog_typen.values_list('afkorting', flat=True))
        self.stdout.write('[INFO] Toegestane bogen: %s' % ",".join(afkortingen))

        # count1 = sum([len(deelnemers) for deelnemers in self.deelnemers.values()])

        for lid_nr in self.deelnemers.keys():
            deelnemers = self.deelnemers[lid_nr]
            self.deelnemers[lid_nr] = [deelnemer
                                       for deelnemer in deelnemers
                                       if deelnemer.sporterboog.boogtype.afkorting in afkortingen]
        # for

        # count2 = sum([len(deelnemers) for deelnemers in self.deelnemers.values()])
        # self.stdout.write('[INFO] Aantal KampioenschapSporterBoog verwijderd: %s' % (count1 - count2))

    def _teams_ophalen(self):
        for team in (KampioenschapTeam
                     .objects
                     .filter(kampioenschap__competitie__afstand='25',
                             kampioenschap__deel=DEEL_BK)
                     .select_related('kampioenschap',
                                     'kampioenschap__rayon',
                                     'vereniging',
                                     'team_type',
                                     'team_klasse')
                     .prefetch_related('gekoppelde_leden',
                                       'feitelijke_leden')):

            self.teams_cache.append(team)
            self.pk2team[team.pk] = team
            self.team_gekoppelde_pks[team.pk] = [deelnemer.pk for deelnemer in team.gekoppelde_leden.all()]

            # print('team: %s' % team, team.team_klasse)
            # for deelnemer in team.gekoppelde_leden.all():
            #     print('  deelnemer: %s' % deelnemer)
        # for

    def _sort_op_gemiddelde(self, lid_nrs):
        gem = list()
        for lid_nr in lid_nrs:
            deelnemer_all = self.deelnemers[lid_nr]
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

    def _bepaal_klasse(self, regels):
        """ zoek uit (met een majority vote) welke klasse dit zou moeten zijn """

        pk2klasse = dict()          # [klasse.pk] = klasse
        klasse2count = dict()       # [klasse.pk] = count

        for regel in regels:
            team_naam = regel[1]
            team_naam_upper = team_naam.upper()

            for team in self.teams_cache:
                if team_naam_upper in team.team_naam.upper():
                    klasse = team.team_klasse
                    pk2klasse[klasse.pk] = klasse
                    try:
                        klasse2count[klasse.pk] += 1
                    except KeyError:
                        klasse2count[klasse.pk] = 1
            # for
        # for

        team_klasse = None
        hoogste = 0
        for pk, count in klasse2count.items():
            if count > hoogste:
                hoogste = count
                team_klasse = pk2klasse[pk]
        # for

        return team_klasse

    def _bepaal_deelnemer(self, team, sporter_naam):
        """ zoek een KampioenschapSporterBoog die het beste bij de naam van de sporter past """

        gekoppelde_deelnemer_pks = self.team_gekoppelde_pks[team.pk]

        naam_upper_delen = sporter_naam.upper().split()
        deze_deelnemer = None
        deze_match_count = 0

        for lid_nr in self.ver_lid_nrs[team.vereniging.ver_nr]:
            # lid_nr kan meerdere keren voorkomen, met verschillende boog
            matches = list()
            for deelnemer in self.deelnemers[lid_nr]:
                match_count = 0
                naam_delen = deelnemer.sporterboog.sporter.volledige_naam().upper().split()
                for naam_deel in naam_delen:
                    if naam_deel in naam_upper_delen:
                        match_count += 1
                # for
                if deelnemer.pk in gekoppelde_deelnemer_pks:
                    match_count += 1
                elif deelnemer.sporterboog.boogtype.afkorting in team.team_type.afkorting:
                    match_count += 1
                if match_count > 1:
                    # print('   (%s) %s' % (match_count, deelnemer))
                    tup = (match_count, deelnemer.pk, len(matches), deelnemer)
                    matches.append(tup)
            # for
            if len(matches) > 0:
                matches.sort(reverse=True)      # hoogste aantal eerst
                # print('matches: %s' % repr(matches))
                match_count, _, _, deelnemer = matches[0]
                if match_count > deze_match_count:
                    deze_match_count = match_count
                    deze_deelnemer = deelnemer
        # for

        if not deze_deelnemer:
            self.stderr.write('[ERROR] Geen match voor sporter %s van team %s' % (sporter_naam, team))
            sys.exit(1)

        if self.verbose:
            self.stdout.write('[INFO] Gevonden deelnemer: %s' % deze_deelnemer)

        return deze_deelnemer

    def _verwerk_uitslag(self, regels):

        team_klasse = self._bepaal_klasse(regels)
        if not team_klasse:
            self.stderr.write('[ERROR] Kan team klasse niet bepalen (0 matches op team naam)')
            return
        self.stdout.write('[INFO] Uitslag voor team klasse: %s' % team_klasse.beschrijving)

        self._filter_deelnemers(team_klasse)

        team2sporters = dict()       # [team.pk] = [sporter_naam, ...]

        for regel in regels:
            sporter_naam, team_naam, score1, score2, count10, count9 = regel
            if self.verbose:
                self.stdout.write('[INFO] Data in: %s %s %s %s %s %s' % (
                                    repr(sporter_naam), repr(team_naam), score1, score2, count10, count9))

            dit_team = None
            for team in self.teams_cache:
                if team.team_klasse.pk == team_klasse.pk:
                    if team_naam.upper() in team.team_naam.upper():
                        dit_team = team
            # for
            if not dit_team:
                self.stderr.write('[ERROR] Kan team niet vinden met naam %s' % repr(team_naam))
                sys.exit(1)

            if score1 + score2 > 0:
                deelnemer = self._bepaal_deelnemer(dit_team, sporter_naam)

                try:
                    team2sporters[dit_team.pk].append(deelnemer)
                except KeyError:
                    team2sporters[dit_team.pk] = [deelnemer]

                deelnemer.result_bk_teamscore_1 = score1
                deelnemer.result_bk_teamscore_2 = score2

                # voor doorgave naar teamresultaat
                deelnemer._count_10 = count10
                deelnemer._count_9 = count9
        # for

        # werk elk van de teams bij
        kamp_teams = list()
        for team_pk, deelnemers in team2sporters.items():
            team = self.pk2team[team_pk]
            gekoppeld = list(team.gekoppelde_leden.all())

            invallers = list()
            for deelnemer in deelnemers:
                if deelnemer in gekoppeld:
                    gekoppeld.remove(deelnemer)
                else:
                    invallers.append(deelnemer)
            # for

            if len(invallers) > 0:
                if len(invallers) > 1:
                    self.stderr.write('[ERROR] Meer dan 1 invallers is nog niet ondersteund')
                    return

                if len(gekoppeld) > 1:
                    self.stderr.write('[ERROR] Meer dan 1 overgebleven uitvaller is nog niet ondersteund')
                    return

                if len(invallers) > len(gekoppeld):
                    self.stderr.write('[ERROR] Te veel invallers voor team %s' % team)
                    return

                uitvaller = gekoppeld[0]
                invaller = invallers[0]

                if invaller.gemiddelde > uitvaller.gemiddelde:
                    self.stdout.write('[INFO] Uitvaller %s heeft gemiddelde %s' % (uitvaller, uitvaller.gemiddelde))
                    self.stderr.write('[ERROR] Invaller %s heeft hoger gemiddelde (%s) dan uitvaller' % (
                                            invaller, invaller.gemiddelde))
                    return

            # sla de team leden en hun bijdrage op
            if not self.dryrun:
                for deelnemer in deelnemers:
                    deelnemer.save(update_fields=['result_bk_teamscore_1', 'result_bk_teamscore_2'])
                # for

            team.feitelijke_leden.set(deelnemers)

            # bepaal de team score
            bijdragen = [(deelnemer.result_bk_teamscore_1 + deelnemer.result_bk_teamscore_2, deelnemer._count_10, deelnemer._count_9)
                         for deelnemer in deelnemers]
            bijdragen.sort(reverse=True)    # hoogste eerst

            score = sum([tup[0] for tup in bijdragen[:3]])
            count_10 = sum([tup[1] for tup in bijdragen[:3]])
            count_9 = sum([tup[2] for tup in bijdragen[:3]])

            team.result_teamscore = score
            team.result_counts = '%sx10 %sx9' % (count_10, count_9)

            tup = (score, count_10, count_9, team)
            kamp_teams.append(tup)
        # for

        scores2count = dict()
        for tup in kamp_teams:
            score = tup[0]
            try:
                scores2count[score] += 1
            except KeyError:
                scores2count[score] = 1
        # for

        # bepaal de uitslag
        self.stdout.write('Uitslag:')
        kamp_teams.sort(reverse=True)               # hoogste eerste
        rank = 0
        for tup in kamp_teams:
            kamp_team = tup[-1]
            if kamp_team.result_teamscore > 0:
                rank += 1
                kamp_team.result_rank = rank
                kamp_team.result_volgorde = rank

                if scores2count[kamp_team.result_teamscore] <= 1:
                    # maar 1 team met deze score, dus telling 10-en / 9-ens is niet relevant
                    kamp_team.result_counts = ''
            else:
                kamp_team.result_rank = 0
                kamp_team.result_volgorde = 0
            self.stdout.write(" %2d. (%s %s) %s" % (kamp_team.result_rank, kamp_team.result_teamscore, kamp_team.result_counts, kamp_team))
            if not self.dryrun:
                kamp_team.save(update_fields=['result_rank', 'result_teamscore', 'result_counts'])
        # for

    def _merge_tabs(self, tabs):
        self._teams_ophalen()

        tabs2 = list()
        prev_klasse = None
        for regels in tabs:
            team_klasse = self._bepaal_klasse(regels)
            if team_klasse and team_klasse == prev_klasse:
                # merge!
                self.stdout.write(
                    "[INFO] Uitslag voor klasse %s stond verdeeld over 2 pagina's" % team_klasse.beschrijving)
                tabs2[-1].extend(regels)
            else:
                tabs2.append(regels)
            prev_klasse = team_klasse
        # for

        return tabs2

    def handle(self, *args, **options):

        self.dryrun = options['dryrun']
        self.verbose = options['verbose']

        # open de kopie, zodat we die aan kunnen passen
        fpath = options['bestand']
        self.stdout.write('[INFO] Lees bestand %s' % repr(fpath))
        lees = LeesPdf(start_at="Totale score", stop_at="150 pijlen")
        try:
            tabs = lees.extract_from_pdf(fpath)
        except FileNotFoundError:
            self.stderr.write('[ERROR] Kan bestand niet vinden')
            return
        del lees

        # combineer tabellen die over twee bladzijden verdeeld zijn
        tabs = self._merge_tabs(tabs)

        # elke klasse apart verwerken
        for regels in tabs:
            # verse lijsten ophalen, want verwerk_uitslag past deze aan
            self._deelnemers_ophalen()
            self._teams_ophalen()

            self._verwerk_uitslag(regels)
        # for

# end of file
