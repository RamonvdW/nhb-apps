# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.models import CompetitieMatch, CompetitieIndivKlasse
from Competitie.test_utils.tijdlijn import zet_competitie_fase_rk_prep, zet_competitie_fase_bk_prep
from CompKampioenschap.models import SheetStatus
from Geo.models import Regio
from GoogleDrive.models import Bestand
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging


class TestCompKampioenschapWfStatus(E2EHelpers, TestCase):

    """ tests voor de CompKampioenschap module, operations Storage Wedstrijdformulieren """

    url_wf_status = '/bondscompetities/kampioenschappen/wedstrijdformulieren/status/'

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

        indiv_klasse = CompetitieIndivKlasse.objects.first()

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
                                    klasse_pk=indiv_klasse.pk,
                                    is_dirty=False)

        status = SheetStatus.objects.create(
                                    bestand=bestand1,
                                    uitslag_is_compleet=True)

        # 25m1pijl, BK
        bestand2 = Bestand.objects.create(
                                    begin_jaar=self.testdata.comp25.begin_jaar,
                                    afstand=25,
                                    rayon_nr=0,
                                    is_teams=False,
                                    is_bk=True,
                                    klasse_pk=indiv_klasse.pk,
                                    is_dirty=False)

        status = SheetStatus.objects.create(
                                    bestand=bestand2,
                                    gewijzigd_door='user@somewhere.nl',
                                    uitslag_is_compleet=True)

        # niet in "werk"
        bestand3 = Bestand.objects.create(
                                    begin_jaar=self.testdata.comp25.begin_jaar,
                                    afstand=25,
                                    rayon_nr=2,
                                    is_teams=False,
                                    is_bk=False,
                                    klasse_pk=1,
                                    is_dirty=False)

        status = SheetStatus.objects.create(
                                    bestand=bestand3)

        deelkamp = self.testdata.deelkamp18_rk[1]
        match = CompetitieMatch.objects.create(
                                    competitie=self.testdata.comp18,
                                    beschrijving='test 1',
                                    datum_wanneer='2022-02-22',
                                    tijd_begin_wedstrijd='02:22',
                                    vereniging=ver)
        match.indiv_klassen.add(indiv_klasse)
        deelkamp.rk_bk_matches.add(match)

        deelkamp = self.testdata.deelkamp25_bk
        match = CompetitieMatch.objects.create(
                                    competitie=self.testdata.comp25,
                                    beschrijving='test 2',
                                    datum_wanneer='2022-02-23',
                                    tijd_begin_wedstrijd='02:22')
        deelkamp.rk_bk_matches.add(match)
        match.indiv_klassen.add(indiv_klasse)

    def test_anon(self):
        resp = self.client.get(self.url_wf_status)
        self.assert403(resp, 'Geen toegang')

    def test_status(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        resp = self.client.get(self.url_wf_status)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('compkampioenschap/wf-status.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

# end of file
