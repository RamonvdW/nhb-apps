# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# verwijder onnodige (oude) data van voorgaande competities

from django.core.management.base import BaseCommand
from Competitie.models import Competitie, CompetitieMatch, CompetitieIndivKlasse, CompetitieTeamKlasse
from CompKamp.operations.wedstrijdformulieren_indiv import UpdateIndivWedstrijdFormulier
from CompKamp.operations.wedstrijdformulieren_teams import UpdateTeamsWedstrijdFormulier
from GoogleDrive.models import Bestand
from GoogleDrive.operations.google_sheets import GoogleSheet
from Locatie.definities import BAAN_TYPE_BINNEN_VOLLEDIG_OVERDEKT
from Vereniging.models import Vereniging
import datetime


class Command(BaseCommand):
    help = "Vul google sheet"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        # organiserende vereniging
        self._ver = None
        self._loc = None

    def _indiv(self):
        for bestand in Bestand.objects.filter(is_dirty=True, afstand=25, is_teams=False).order_by('pk')[:5]:
            print('bestand: %s' % bestand)

            comp = Competitie.objects.filter(afstand=25).order_by('begin_jaar').first()
            print('comp: %s' % comp)

            match, _ = CompetitieMatch.objects.get_or_create(
                                        competitie=comp,
                                        beschrijving='vul_sheet',
                                        vereniging=self._ver,
                                        locatie=self._loc,
                                        datum_wanneer=datetime.date(year=2025, month=12, day=31),
                                        tijd_begin_wedstrijd='10:00')

            klasse = CompetitieIndivKlasse.objects.get(pk=bestand.klasse_pk)

            if klasse not in match.indiv_klassen.all():
                match.indiv_klassen.clear()
                match.indiv_klassen.add(klasse)

            sheet = GoogleSheet(self.stdout)
            sheet.selecteer_file(bestand.file_id)

            updater = UpdateWedstrijdFormulierIndiv(self.stdout, sheet)
            updater.update_wedstrijdformulier(bestand, match)
        # for

    def _teams(self):
        for bestand in Bestand.objects.filter(is_dirty=True, afstand=25, is_teams=True).order_by('pk')[:5]:
            print('bestand: %s' % bestand)

            comp = Competitie.objects.filter(afstand=25).order_by('begin_jaar').first()
            print('comp: %s' % comp)

            match, _ = CompetitieMatch.objects.get_or_create(
                                        competitie=comp,
                                        beschrijving='vul_sheet',
                                        vereniging=self._ver,
                                        locatie=self._loc,
                                        datum_wanneer=datetime.date(year=2025, month=12, day=31),
                                        tijd_begin_wedstrijd='10:00')

            klasse = CompetitieTeamKlasse.objects.get(pk=bestand.klasse_pk)

            if klasse not in match.indiv_klassen.all():
                match.team_klassen.clear()
                match.team_klassen.add(klasse)

            sheet = GoogleSheet(self.stdout)
            sheet.selecteer_file(bestand.file_id)

            updater = UpdateTeamsWedstrijdFormulier(self.stdout, sheet)
            updater.update_wedstrijdformulier(bestand, match)
        # for

    def handle(self, *args, **options):
        # organisatie
        self._ver = Vereniging.objects.get(ver_nr=1231)
        print('ver: %s' % self._ver)

        self._loc = self._ver.wedstrijdlocatie_set.filter(zichtbaar=True,
                                                          baan_type=BAAN_TYPE_BINNEN_VOLLEDIG_OVERDEKT).first()
        print('loc: %s' % self._loc)

        #self._indiv()
        self._teams()

# end of file
