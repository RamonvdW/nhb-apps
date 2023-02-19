# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Competitie.models import Competitie, CompetitieMatch, CompetitieIndivKlasse, KampioenschapIndivKlasseLimiet
from Competitie.tijdlijn import zet_competitie_fases
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers.testdata import TestData


class TestCompUitslagenRK(E2EHelpers, TestCase):

    """ tests voor de CompUitslagen applicatie, module Uitslagen RK """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_beheerders')

    url_uitslagen_rayon = '/bondscompetities/uitslagen/%s/%s/rk-individueel/'                    # comp_pk, comp_boog
    url_uitslagen_rayon_n = '/bondscompetities/uitslagen/%s/%s/rk-individueel/%s/'               # comp_pk, comp_boog, rayon_nr
    url_uitslagen_rayon_teams = '/bondscompetities/uitslagen/%s/%s/rk-teams/'                    # comp_pk, team_type
    url_uitslagen_rayon_teams_n = '/bondscompetities/uitslagen/%s/%s/rk-teams/%s/'               # comp_pk, team_type, rayon_nr
    url_doorzetten_regio_naar_rk = '/bondscompetities/beheer/%s/doorzetten/regio-naar-rk/'       # comp_pk
    url_teams_klassengrenzen_vaststellen = '/bondscompetities/beheer/%s/doorzetten/rk-bk-teams-klassengrenzen-vaststellen/'  # comp_pk

    regio_nr = 101
    ver_nr = 0      # wordt in setupTestData ingevuld

    testdata = None

    @classmethod
    def setUpTestData(cls):
        print('%s: populating testdata start' % cls.__name__)
        s1 = timezone.now()
        cls.testdata = data = TestData()
        data.maak_accounts()
        data.maak_clubs_en_sporters()
        cls.ver_nr = ver_nr = data.regio_ver_nrs[cls.regio_nr][2]
        data.maak_bondscompetities()
        data.maak_inschrijvingen_regiocompetitie(18, ver_nr=ver_nr)     # tijdelijke RK deelnemerslijst
        # data.maak_inschrijvingen_regiocompetitie(25, ver_nr=ver_nr)
        data.maak_rk_deelnemers(18, ver_nr, cls.regio_nr)
        s2 = timezone.now()
        d = s2 - s1
        print('%s: populating testdata took %s seconds' % (cls.__name__, d.seconds))

    def test_indiv(self):
        self.testdata.geef_regio_deelnemers_genoeg_scores_voor_rk(18)

        # anon
        self.client.logout()

        url = self.url_uitslagen_rayon % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rk-indiv.dtl', 'plein/site_layout.dtl'))

        # sporter
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_sporter()

        url = self.url_uitslagen_rayon % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rk-indiv.dtl', 'plein/site_layout.dtl'))

        # slecht boogtype
        url = self.url_uitslagen_rayon % (self.testdata.comp18.pk, 'XXX')
        resp = self.client.get(url)
        self.assert404(resp, 'Boogtype niet bekend')

        url = self.url_uitslagen_rayon % ('x', 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_uitslagen_rayon % (99, 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_uitslagen_rayon_n % (self.testdata.comp18.pk, 'TR', 1)      # bevat onze enige deelnemer met 6 scores
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rk-indiv.dtl', 'plein/site_layout.dtl'))

        url = self.url_uitslagen_rayon_n % (self.testdata.comp18.pk, 'R', 'x')
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerd rayonnummer')

        url = self.url_uitslagen_rayon_n % (self.testdata.comp18.pk, 'R', '0')
        resp = self.client.get(url)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        # maak een wedstrijdlocatie aan
        locatie = self.testdata.maak_wedstrijd_locatie(self.ver_nr)

        # maak een RK match aan
        indiv_klasse = CompetitieIndivKlasse.objects.filter(competitie=self.testdata.comp18, is_voor_rk_bk=True)[0]

        match = CompetitieMatch(
                    competitie=self.testdata.comp18,
                    beschrijving='test match 1',
                    vereniging=self.testdata.vereniging[self.ver_nr],
                    locatie=locatie,
                    datum_wanneer="2000-01-01",
                    tijd_begin_wedstrijd="10:00")
        match.save()
        match.indiv_klassen.add(indiv_klasse)

        deelkamp = self.testdata.deelkamp18_rk[1]
        deelkamp.rk_bk_matches.add(match)

        KampioenschapIndivKlasseLimiet(
                kampioenschap=deelkamp,
                indiv_klasse=indiv_klasse,
                limiet=8).save()

        # als BKO: doorzetten naar RK fase (G --> J) en bepaal de klassengrenzen (fase J --> K)
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_bko)
        zet_competitie_fases(self.testdata.comp18, 'G', 'G')

        url = self.url_doorzetten_regio_naar_rk % self.testdata.comp18.pk
        resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)
        self.verwerk_regiocomp_mutaties()

        comp = Competitie.objects.get(pk=self.testdata.comp18.pk)
        comp.bepaal_fase()
        self.assertEqual(comp.fase_indiv, 'J')

        # ophalen in fase J geeft "bevestig tot datum"
        url = self.url_uitslagen_rayon % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rk-indiv.dtl', 'plein/site_layout.dtl'))

        # als BKO: klassegrenzen RK/BK teams vaststellen (J --> K)
        url = self.url_teams_klassengrenzen_vaststellen % self.testdata.comp18.pk
        resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        comp = Competitie.objects.get(pk=self.testdata.comp18.pk)
        comp.bepaal_fase()
        self.assertEqual(comp.fase_teams, 'K')

        url = self.url_uitslagen_rayon % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rk-indiv.dtl', 'plein/site_layout.dtl'))

        # uitslagen toevoegen
        self.testdata.maak_uitslag_rk_indiv(18)

        url = self.url_uitslagen_rayon % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rk-indiv.dtl', 'plein/site_layout.dtl'))

    def test_teams(self):
        # anon
        self.client.logout()

        url = self.url_uitslagen_rayon_teams % (self.testdata.comp18.pk, 'R2')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rk-teams.dtl', 'plein/site_layout.dtl'))

        # sporter
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_sporter()

        url = self.url_uitslagen_rayon_teams % (self.testdata.comp18.pk, 'R2')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rk-teams.dtl', 'plein/site_layout.dtl'))

        url = self.url_uitslagen_rayon_teams % (999999, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_uitslagen_rayon_teams % (self.testdata.comp18.pk, 'X')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Team type niet bekend')

        url = self.url_uitslagen_rayon_teams_n % (self.testdata.comp18.pk, 'R2', 1)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rk-teams.dtl', 'plein/site_layout.dtl'))

        url = self.url_uitslagen_rayon_teams_n % (self.testdata.comp18.pk, 'R2', 'X')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Verkeerd rayonnummer')

        url = self.url_uitslagen_rayon_teams_n % (self.testdata.comp18.pk, 'R2', 999999)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # maak een paar teams aan
        self.testdata.maak_voorinschrijvingen_rk_teamcompetitie(25, self.ver_nr, ook_incomplete_teams=False)
        self.testdata.geef_rk_team_tijdelijke_sporters_genoeg_scores(25, self.ver_nr)

        url = self.url_uitslagen_rayon_teams_n % (self.testdata.comp25.pk, 'R2', 1)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rk-teams.dtl', 'plein/site_layout.dtl'))

        # als BKO doorzetten naar RK fase (G --> J) en bepaal de klassengrenzen (fase J --> K)
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_bko)
        zet_competitie_fases(self.testdata.comp25, 'G', 'G')

        url = self.url_doorzetten_regio_naar_rk % self.testdata.comp25.pk
        resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)
        self.verwerk_regiocomp_mutaties()

        comp = Competitie.objects.get(pk=self.testdata.comp25.pk)
        comp.bepaal_fase()
        self.assertEqual(comp.fase_teams, 'J')

        url = self.url_teams_klassengrenzen_vaststellen % self.testdata.comp25.pk
        resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        url = self.url_uitslagen_rayon_teams_n % (self.testdata.comp25.pk, 'R2', 1)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rk-teams.dtl', 'plein/site_layout.dtl'))

        # wissel naar een HWL
        self.e2e_login_and_pass_otp(self.testdata.account_hwl[self.ver_nr])
        self.e2e_wissel_naar_functie(self.testdata.functie_hwl[self.ver_nr])

        url = self.url_uitslagen_rayon_teams_n % (self.testdata.comp25.pk, 'R2', 1)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rk-teams.dtl', 'plein/site_layout.dtl'))

        # wissel naar een sporter
        self.e2e_wisselnaarrol_sporter()

        url = self.url_uitslagen_rayon_teams_n % (self.testdata.comp25.pk, 'R2', 1)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rk-teams.dtl', 'plein/site_layout.dtl'))

        # corner case: sporter is niet meer actief
        sporter = self.testdata.account_hwl[self.ver_nr].sporter_set.all()[0]
        sporter.is_actief_lid = False
        sporter.save(update_fields=['is_actief_lid'])

        url = self.url_uitslagen_rayon_teams_n % (self.testdata.comp25.pk, 'R2', 1)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rk-teams.dtl', 'plein/site_layout.dtl'))

    def test_beheerders(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)

        for functie in (self.testdata.comp18_functie_rcl[111],
                        self.testdata.comp18_functie_rko[3],
                        self.testdata.comp18_functie_bko,
                        self.testdata.functie_hwl[self.ver_nr]):

            self.e2e_wissel_naar_functie(functie)

            url = self.url_uitslagen_rayon % (self.testdata.comp18.pk, 'R')
            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('compuitslagen/uitslagen-rk-indiv.dtl', 'plein/site_layout.dtl'))
        # for

# end of file
