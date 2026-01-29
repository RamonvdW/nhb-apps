# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.models import CompetitieMatch, CompetitieIndivKlasse, CompetitieTeamKlasse
from Competitie.test_utils.tijdlijn import zet_competitie_fase_rk_prep, zet_competitie_fase_bk_prep
from CompKampioenschap.models import SheetStatus
from Geo.models import Regio
from GoogleDrive.models import Bestand
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
from unittest.mock import patch


class TestCompKampioenschapImportUitslag(E2EHelpers, TestCase):

    """ tests voor de CompKampioenschap module, operations Import Uitslag (uit Google Sheet) """

    url_import_indiv = '/bondscompetities/kampioenschappen/importeer-uitslag/indiv/%s/'   # status_pk
    url_import_teams = '/bondscompetities/kampioenschappen/importeer-uitslag/teams/%s/'   # status_pk

    testdata = None

    @classmethod
    def setUpTestData(cls):
        print('%s: populating testdata start' % cls.__name__)
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()
        cls.testdata.maak_bondscompetities(2020)

    def setUp(self):
        zet_competitie_fase_rk_prep(self.testdata.comp18)
        zet_competitie_fase_bk_prep(self.testdata.comp25)

        indiv_klasse18 = CompetitieIndivKlasse.objects.filter(competitie=self.testdata.comp18).first()
        indiv_klasse25 = CompetitieIndivKlasse.objects.filter(competitie=self.testdata.comp25).first()
        team_klasse25 = CompetitieTeamKlasse.objects.filter(competitie=self.testdata.comp25).first()

        ver = Vereniging.objects.create(
                                    ver_nr=1001,
                                    naam='Grote club',
                                    plaats='',
                                    regio=Regio.objects.get(regio_nr=106))

        # Indoor, RK Rayon 1
        bestand1 = Bestand.objects.create(
                                    begin_jaar=self.testdata.comp18.begin_jaar,
                                    afstand=18,
                                    rayon_nr=1,
                                    is_teams=False,
                                    is_bk=False,
                                    klasse_pk=indiv_klasse18.pk,
                                    is_dirty=False)

        self.status1 = SheetStatus.objects.create(
                                    bestand=bestand1,
                                    uitslag_is_compleet=True,
                                    wedstrijd_fase='Geen invoer')
        # 25m1pijl, BK
        bestand2 = Bestand.objects.create(
                                    begin_jaar=self.testdata.comp25.begin_jaar,
                                    afstand=25,
                                    rayon_nr=0,
                                    is_teams=False,
                                    is_bk=True,
                                    klasse_pk=indiv_klasse25.pk,
                                    is_dirty=False)

        self.status2 = SheetStatus.objects.create(
                                    bestand=bestand2,
                                    gewijzigd_door='user@somewhere.nl',
                                    uitslag_is_compleet=True,
                                    uitslag_ingelezen_op='2022-02-22T02:22:00Z',
                                    gewijzigd_op='2022-02-22T02:22:01Z')
        deelkamp = self.testdata.deelkamp18_rk[1]
        match = CompetitieMatch.objects.create(
                                    competitie=self.testdata.comp18,
                                    beschrijving='test 1',
                                    datum_wanneer='2022-02-22',
                                    tijd_begin_wedstrijd='02:22',
                                    vereniging=ver)
        match.indiv_klassen.add(indiv_klasse18)
        deelkamp.rk_bk_matches.add(match)

        deelkamp = self.testdata.deelkamp25_bk
        match = CompetitieMatch.objects.create(
                                    competitie=self.testdata.comp25,
                                    beschrijving='test 2',
                                    datum_wanneer='2022-02-23',
                                    tijd_begin_wedstrijd='02:22')
        match.indiv_klassen.add(indiv_klasse25)
        match.team_klassen.add(team_klasse25)
        deelkamp.rk_bk_matches.add(match)

        bestand3 = Bestand.objects.create(
                                    begin_jaar=self.testdata.comp25.begin_jaar,
                                    afstand=25,
                                    rayon_nr=0,
                                    is_teams=True,
                                    is_bk=True,
                                    klasse_pk=team_klasse25.pk,
                                    is_dirty=False)

        self.status3 = SheetStatus.objects.create(
                                    bestand=bestand3)

    def test_anon(self):
        resp = self.client.get(self.url_import_indiv % 99999)
        self.assert403(resp, 'Geen toegang')

        resp = self.client.get(self.url_import_teams % 99999)
        self.assert403(resp, 'Geen toegang')

    def test_indiv(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        # no GET
        resp = self.client.get(self.url_import_indiv % 99999)
        self.assert405(resp)

        # non-existing
        resp = self.client.post(self.url_import_indiv % 99999)
        self.assert404(resp, 'Niet gevonden')

        with patch('CompKampioenschap.view_import_uitslag.importeer_sheet_uitslag_indiv') as mock_importeer:
            mock_importeer.return_value = (True, [['regel']])
            resp = self.client.post(self.url_import_indiv % self.status1.pk)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assert_template_used(resp, ('compkampioenschap/wf-resultaat-import.dtl', 'design/site_layout.dtl'))
            self.assert_html_ok(resp)

        with patch('CompKampioenschap.view_import_uitslag.importeer_sheet_uitslag_indiv') as mock_importeer:
            mock_importeer.return_value = (False, [])
            resp = self.client.post(self.url_import_indiv % self.status2.pk)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assert_template_used(resp, ('compkampioenschap/wf-resultaat-import.dtl', 'design/site_layout.dtl'))
            self.assert_html_ok(resp)

        # corner case
        self.status2.bestand.klasse_pk = 99999
        self.status2.bestand.save()

        resp = self.client.post(self.url_import_indiv % self.status2.pk)
        self.assert404(resp, 'Kampioenschap niet gevonden')

    def test_teams(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        # no GET
        resp = self.client.get(self.url_import_teams % 99999)
        self.assert405(resp)

        # non-existing
        resp = self.client.post(self.url_import_teams % 99999)
        self.assert404(resp, 'Niet gevonden')

        # mismatch
        self.status1.bestand.is_teams = True
        self.status1.bestand.save()
        resp = self.client.post(self.url_import_teams % self.status1.pk)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        resp = self.client.post(self.url_import_teams % self.status3.pk)
        self.assert404(resp, 'Not implemented')

        # RK
        self.status3.bestand.is_bk = False
        self.status3.bestand.rayon_nr = 3
        self.status3.bestand.save()
        resp = self.client.post(self.url_import_teams % self.status3.pk)
        self.assert404(resp, 'Not implemented')

# end of file
