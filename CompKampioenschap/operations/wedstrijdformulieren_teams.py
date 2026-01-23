# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helper functies """

from django.utils import timezone
from Competitie.definities import DEEL_BK, DEEL_RK, DEELNAME_NEE
from Competitie.models import (Competitie, CompetitieTeamKlasse, CompetitieMatch,
                               Kampioenschap, KampioenschapTeamKlasseLimiet,
                               KampioenschapTeam, KampioenschapSporterBoog)
from Geo.models import Rayon
from GoogleDrive.models import Bestand
from GoogleDrive.operations import StorageGoogleSheet
from Sporter.models import SporterVoorkeuren


def iter_teams_wedstrijdformulieren(comp: Competitie):
    """ generator voor alle teams wedstrijdformulieren

        generates tuples:
            (afstand, is_bk, klasse_pk, rayon_nr, fname)
    """
    # uitgezet omdat we het Excel formulier nog gebruiken
    return

    afstand = int(comp.afstand)
    rayon_nrs = list(Rayon.objects.all().values_list('rayon_nr', flat=True))

    for klasse in CompetitieTeamKlasse.objects.filter(competitie=comp, is_voor_teams_rk_bk=True):
        klasse_str = klasse.beschrijving.lower().replace(' ', '-')

        # RK programma's
        is_bk = False
        for rayon_nr in rayon_nrs:
            fname = "rk-programma_teams-rayon%s_" % rayon_nr
            fname += klasse_str
            yield afstand, is_bk, klasse.pk, rayon_nr, fname
        # for

        # BK programma's
        is_bk = True
        rayon_nr = 0
        fname = "bk-programma_teams_" + klasse_str
        yield afstand, is_bk, klasse.pk, rayon_nr, fname
    # for


class UpdateTeamsWedstrijdFormulier:

    def __init__(self, stdout, sheet: StorageGoogleSheet):
        self.stdout = stdout
        self.sheet = sheet              # kan google sheets bijwerken

        self.klasse = None
        self.boog_pks = list()          # toegestane bogen in deze klasse
        self.competitie = None
        self.kampioenschap = None
        self.limiet = 0                 # maximaal aantal teams
        self.teams = list()
        self.ver_nrs = list()

        self.ranges = {
            'titel': 'C2',
            'info': 'D4:D7',
            'bijgewerkt': 'A37',
            'toegestaan_wis': 'B17:I1000',
            'scores_totaal': 'K14:K21',
        }

        vastgesteld = timezone.localtime(timezone.now())
        self.vastgesteld_str = vastgesteld.strftime('%Y-%m-%d %H:%M:%S')

    def _laad_klasse(self, bestand: Bestand):
        self.klasse = CompetitieTeamKlasse.objects.get(pk=bestand.klasse_pk)

        self.competitie = self.klasse.competitie
        if bestand.is_bk:
            self.kampioenschap = Kampioenschap.objects.filter(competitie=self.competitie, deel=DEEL_BK).first()
        else:
            self.kampioenschap = Kampioenschap.objects.filter(competitie=self.competitie, deel=DEEL_RK,
                                                              rayon__rayon_nr=bestand.rayon_nr).first()

        # haal de limiet op (maximum aantal deelnemers)
        self.limiet = 8
        lim = KampioenschapTeamKlasseLimiet.objects.filter(kampioenschap=self.kampioenschap,
                                                           team_klasse=self.klasse).first()
        if lim:
            self.limiet = lim.limiet

        if bestand.is_bk:
            self.titel = 'BK'
        else:
            self.titel = 'RK'
        self.titel += ' teams, %s' % self.competitie.beschrijving.replace('competitie ', '')    # is inclusief seizoen

        if not bestand.is_bk:
            # benoem het rayon
            self.titel += ', Rayon %s' % bestand.rayon_nr

        self.teams = (KampioenschapTeam
                      .objects
                      .filter(kampioenschap=self.kampioenschap,
                              team_klasse=self.klasse)
                      .exclude(deelname=DEELNAME_NEE)
                      .select_related('vereniging')
                      .prefetch_related('gekoppelde_leden')
                      .order_by('-aanvangsgemiddelde'))         # sterkste team bovenaan

        # maximaal 8 teams in het google sheet zetten
        self.teams = list(self.teams)[:8]

        self.ver_nrs = list()
        for team in self.teams:
            self.ver_nrs.append(team.vereniging.ver_nr)
        # for

        boog_typen = self.klasse.team_type.boog_typen.all()
        self.boog_pks = list(boog_typen.values_list('pk', flat=True))

        self.lid2voorkeuren = dict()  # [lid_nr] = SporterVoorkeuren
        for voorkeuren in (SporterVoorkeuren
                           .objects
                           .filter(sporter__bij_vereniging__ver_nr__in=self.ver_nrs)
                           .select_related('sporter')):
            self.lid2voorkeuren[voorkeuren.sporter.lid_nr] = voorkeuren
        # for

    def _get_sporter_para_notities(self, sporter):
        para_notities = ''

        voorkeuren = self.lid2voorkeuren.get(sporter.lid_nr, None)
        if voorkeuren:      # pragma: no branch
            if voorkeuren.para_voorwerpen:
                para_notities = 'Sporter laat voorwerpen op de schietlijn staan'

            if voorkeuren.opmerking_para_sporter:
                if para_notities != '':
                    para_notities += '\n'
                para_notities += voorkeuren.opmerking_para_sporter

        return para_notities

    def _schrijf_kopje(self, match: CompetitieMatch):
        self.sheet.selecteer_sheet('Deelnemers')

        # zet de titel
        self.sheet.wijzig_cellen(self.ranges['titel'], [[self.titel]])

        # schrijf de info in de heading
        regels = list()

        # wedstrijdklasse
        regels.append([self.klasse.beschrijving])

        # datum
        regels.append([match.datum_wanneer.strftime('%Y-%m-%d')])

        # organisatie
        ver = match.vereniging
        if ver:
            regels.append([ver.ver_nr_en_naam()])
        else:
            regels.append(['Nog niet toegekend'])

        # adres
        loc = match.locatie
        if loc:
            regels.append([loc.adres])
        else:
            regels.append(['Onbekend'])

        self.sheet.wijzig_cellen(self.ranges['info'], regels)

    def _schrijf_toegestane_deelnemers(self):
        self.sheet.selecteer_sheet('Toegestane deelnemers')
        self.sheet.clear_range(self.ranges['toegestaan_wis'])

        a1 = self.ranges['toegestaan_wis'].split(':')[0]     # B17
        regel = int(a1[1:])      # converteer 17 naar getal

        prev_ver = None
        regel -= 1          # bij nieuwe vereniging volgt een lege regel

        # op het BK mogen alle RK deelnemers schieten in het team
        # (sporter hoeft niet persoonlijk geplaatst te zijn voor het BK)
        for deelnemer in (KampioenschapSporterBoog
                          .objects
                          .filter(kampioenschap__competitie=self.competitie,
                                  kampioenschap__deel=DEEL_RK,
                                  bij_vereniging__ver_nr__in=self.ver_nrs,
                                  sporterboog__boogtype__pk__in=self.boog_pks)     # filter op toegestane boogtypen
                          .select_related('bij_vereniging',
                                          'sporterboog__sporter',
                                          'sporterboog__boogtype')
                          .order_by('bij_vereniging',
                                    '-gemiddelde')):                            # hoogste eerst

            # vereniging
            ver = deelnemer.bij_vereniging
            if ver != prev_ver:
                regel += 1      # extra lege regel

                range_a1 = 'C%s:D%s' % (regel, regel)
                values = [[ver.regio.regio_nr, ver.ver_nr_en_naam()]]
                self.sheet.wijzig_cellen(range_a1, values)
                prev_ver = ver

            # sporter
            sporter = deelnemer.sporterboog.sporter
            naam_str = sporter.volledige_naam()
            gemiddelde_str = str(deelnemer.gemiddelde).replace('.', ',')
            para_notities = self._get_sporter_para_notities(sporter)

            range_a1 = 'E%s:I%s' % (regel, regel)
            values = [[str(sporter.lid_nr),
                       naam_str,
                       gemiddelde_str,
                       deelnemer.sporterboog.boogtype.beschrijving,
                       para_notities]]
            self.sheet.wijzig_cellen(range_a1, values)

            regel += 1
        # for

        regel += 1
        range_a1 = 'B%s' % regel
        values = [['Deze gegevens zijn opgehaald op ' + self.vastgesteld_str]]
        self.sheet.wijzig_cellen(range_a1, values)

    def _schrijf_deelnemers(self):
        self.sheet.selecteer_sheet('Deelnemers')

        volg_nr = 0
        for team in self.teams:         # TODO: begrens tot 8 teams max; rest is reserve. Wel in sheet zetten?
            regel = 12 + volg_nr * 5
            volg_nr += 1

            ver = team.vereniging

            range_a1 = 'C%s:E%s' % (regel, regel)
            values = [[ver.ver_nr_en_naam(), '', team.team_naam]]
            self.sheet.wijzig_cellen(range_a1, values)

            # vul de 3 sporters in
            aantal = 0
            for deelnemer in team.gekoppelde_leden.select_related('sporterboog__sporter').order_by('-gemiddelde'):
                sporter = deelnemer.sporterboog.sporter
                naam_str = sporter.volledige_naam()
                gemiddelde_str = str(deelnemer.gemiddelde).replace('.', ',')
                para_notities = self._get_sporter_para_notities(sporter)

                regel += 1
                range_a1 = 'D%s:G%s' % (regel, regel)
                values = [[str(sporter.lid_nr),
                           naam_str,
                           gemiddelde_str,
                           para_notities]]
                self.sheet.wijzig_cellen(range_a1, values)

                aantal += 1
                if aantal == 3:     # TODO: is tijdelijk, voor testen met oude data
                    break
            # for

            while aantal < 3:
                regel += 1
                range_a1 = 'D%s:G%s' % (regel, regel)
                values = ['?', '?', '?', '']
                self.sheet.wijzig_cellen(range_a1, values)

                aantal += 1
            # while
        # for

        # ongebruikte slots leeg maken
        while volg_nr < 8:
            regel = 12 + volg_nr * 5
            volg_nr += 1

            self.sheet.clear_range('C%s:G%s' % (regel, regel+3))
        # while

    def _heeft_scores(self):
        self.sheet.selecteer_sheet('Stand')
        values = self.sheet.get_range(self.ranges['scores_totaal'])
        if values:
            values = values[0]      # eerste (en enige) kolom
            for value in values:
                if value:
                    return True
            # for
        return False

    def _hide_show_sheets(self):
        # er zijn wedstrijd sheets voor 3, 4, 5, 6, 7 en 8 teams
        # toon alleen de het benodigde sheet
        aantal_teams = len(self.teams)

        if 3 <= aantal_teams <= 8:
            for aantal in (3, 4, 5, 6, 7, 8):
                sheet_name = '%s teams' % aantal
                if aantal == aantal_teams:
                    self.sheet.toon_sheet(sheet_name)
                else:
                    self.sheet.hide_sheet(sheet_name)
            # for

    def _schrijf_update(self, _bestand: Bestand, match: CompetitieMatch):
        self._schrijf_kopje(match)
        self._schrijf_toegestane_deelnemers()
        self._schrijf_deelnemers()
        self._hide_show_sheets()

        # voer alle wijzigingen door met 1 transactie
        self.sheet.stuur_wijzigingen()

    def update_wedstrijdformulier(self, bestand: Bestand, match: CompetitieMatch):
        # zoek de wedstrijdklasse, kampioenschap, limiet, etc. erbij
        self._laad_klasse(bestand)

        if self._heeft_scores():
            self.stdout.write('[DEBUG] heeft scores')
            return "NOK: Heeft scores"

        # update het bestand
        self._schrijf_update(bestand, match)
        return "OK"


class LeesTeamsWedstrijdFormulier:

    def __init__(self, stdout, sheet: StorageGoogleSheet):
        self.stdout = stdout
        self.sheet = sheet              # kan google sheets bijwerken

    # TODO: implement


# end of file
