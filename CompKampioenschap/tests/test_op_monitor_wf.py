# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from django.core.management.base import OutputWrapper
from CompKampioenschap.models import SheetStatus
from CompKampioenschap.operations.monitor_wedstrijdformulieren import MonitorGoogleSheetsWedstrijdformulieren
from GoogleDrive.models import Bestand
from GoogleDrive.operations import StorageGoogleSheet
from TestHelpers.e2ehelpers import E2EHelpers
from unittest.mock import patch
import datetime
import io


class MockMonitorDriveFiles:

    def __init__(self, stdout, retry_delay:float=1.0):
        self.stdout = stdout

    def get_laatste_wijziging(self, file_id):
        op = timezone.now()
        door = 'Anoniem'

        return op, door


class MockLeesIndivWedstrijdFormulier:

    def __init__(self, stdout, bestand: Bestand, sheet: StorageGoogleSheet, lees_oppervlakkig: bool):
        self.stdout = stdout
        self.bestand = bestand
        self.sheet = sheet      # kan google sheets bijwerken
        self.afstand = bestand.afstand
        self.lees_oppervlakkig = lees_oppervlakkig

    def heeft_scores(self):
        return False

    def heeft_uitslag(self):
        return False

    def tel_deelnemers(self):
        return 1

    def bepaal_wedstrijd_fase(self):
        return 'hoi'


class TestCompKampioenschapImportUitslag(E2EHelpers, TestCase):

    """ tests voor de CompKampioenschap module, operations Monitor Wedstrijdformulieren """

    def setUp(self):
        # Indoor, RK Rayon 1
        self.bestand1 = Bestand.objects.create(
                                    begin_jaar=2026,
                                    afstand=18,
                                    rayon_nr=1,
                                    is_teams=False,
                                    is_bk=False,
                                    klasse_pk=1,
                                    is_dirty=False,
                                    fname='fname_1',
                                    file_id='file_id_1')

        self.status1 = SheetStatus.objects.create(
                                    bestand=self.bestand1,
                                    gewijzigd_op='2000-01-01T00:00:00Z')

        self.status2 = SheetStatus.objects.create(
                                    bestand=self.bestand1,
                                    uitslag_is_compleet=True,
                                    gewijzigd_op='2000-01-01T00:00:01Z',
                                    bekeken_op='2000-01-01T00:00:00Z')

        self.status2 = SheetStatus.objects.create(
                                    bestand=self.bestand1,
                                    uitslag_ingelezen_op='2001-01-01T00:00:01Z')    # moet zijn > 2000

        # Bestand zonder SheetStatus
        self.bestand2 = Bestand.objects.create(
                                    begin_jaar=2026,
                                    afstand=25,
                                    rayon_nr=1,
                                    is_teams=False,
                                    is_bk=False,
                                    klasse_pk=1,
                                    is_dirty=False,
                                    fname='fname_2',
                                    file_id='file_id_2')

    def test_monitor(self):
        out = OutputWrapper(io.StringIO())

        werk = [
            (self.bestand1.begin_jaar, self.bestand1.afstand, self.bestand1.is_bk, self.bestand1.is_teams),
            (self.bestand2.begin_jaar, self.bestand2.afstand, self.bestand2.is_bk, self.bestand2.is_teams)
        ]
        with patch('CompKampioenschap.operations.monitor_wedstrijdformulieren.MonitorDriveFiles', MockMonitorDriveFiles):
            monitor = MonitorGoogleSheetsWedstrijdformulieren(out, werk)

        with patch('CompKampioenschap.operations.monitor_wedstrijdformulieren.LeesIndivWedstrijdFormulier', MockLeesIndivWedstrijdFormulier):
            monitor.doe_beetje_werk()       # sheet
            monitor.doe_beetje_werk()       # nieuw bestand
            monitor.doe_beetje_werk()       # sheet
            monitor.doe_beetje_werk()       # bestand
            monitor.doe_beetje_werk()       # bestand
            monitor.doe_beetje_werk()       # geen werk

        #print(out.getvalue())

# end of file
