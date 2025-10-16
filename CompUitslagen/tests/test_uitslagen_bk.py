# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Competitie.models import CompetitieIndivKlasse, CompetitieMatch, KampioenschapIndivKlasseLimiet
from Competitie.test_utils.tijdlijn import zet_competitie_fase_bk_prep
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers.testdata import TestData


class TestCompUitslagenBK(E2EHelpers, TestCase):

    """ tests voor de CompUitslagen applicatie, module Uitslagen BK """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_tijdlijn')

    url_uitslagen_bond_indiv = '/bondscompetities/uitslagen/%s/bk-individueel/%s/'     # comp_pk, comp_boog
    url_uitslagen_bond_teams = '/bondscompetities/uitslagen/%s/bk-teams/%s/'           # comp_pk, team_type

    regio_nr = 101
    ver_nr = 0      # wordt in setUpTestData ingevuld

    testdata = None

    @classmethod
    def setUpTestData(cls):
        print('%s: populating testdata start' % cls.__name__)
        s1 = timezone.now()
        cls.testdata = data = TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()
        cls.ver_nr = data.regio_ver_nrs[cls.regio_nr][2]
        data.maak_bondscompetities()
        data.maak_rk_deelnemers(18, cls.ver_nr, cls.regio_nr)
        data.maak_rk_teams(18, cls.ver_nr, zet_klasse=True)
        data.maak_bk_deelnemers(18)
        data.maak_bk_teams(18)

        KampioenschapIndivKlasseLimiet(
                kampioenschap=data.deelkamp18_bk,
                indiv_klasse=data.comp18_klassen_indiv['R'][0],
                limiet=4).save()

        s2 = timezone.now()
        d = s2 - s1
        print('%s: populating testdata took %.1f seconds' % (cls.__name__, d.total_seconds()))

    def test_bk_indiv(self):
        url = self.url_uitslagen_bond_indiv % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-bk-indiv.dtl', 'design/site_layout.dtl'))

        # maak een locatie aan
        locatie = self.testdata.maak_wedstrijd_locatie(self.ver_nr)

        # maak een RK match aan
        indiv_klasse = CompetitieIndivKlasse.objects.filter(competitie=self.testdata.comp18, is_ook_voor_rk_bk=True)[0]

        match = CompetitieMatch(
                    competitie=self.testdata.comp18,
                    beschrijving='test match 1',
                    vereniging=self.testdata.vereniging[self.ver_nr],
                    locatie=locatie,
                    datum_wanneer="2000-01-01",
                    tijd_begin_wedstrijd="10:00")
        match.save()
        match.indiv_klassen.add(indiv_klasse)

        self.testdata.deelkamp18_bk.rk_bk_matches.add(match)

        # fase O
        zet_competitie_fase_bk_prep(self.testdata.comp18)
        self.testdata.deelkamp18_bk.heeft_deelnemerslijst = True
        self.testdata.deelkamp18_bk.save(update_fields=['heeft_deelnemerslijst'])

        url = self.url_uitslagen_bond_indiv % (self.testdata.comp18.pk, 'R')
        #with self.assert_max_queries(20):
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-bk-indiv.dtl', 'design/site_layout.dtl'))

        url = self.url_uitslagen_bond_indiv % (self.testdata.comp25.pk, 'R')
        #with self.assert_max_queries(20):
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-bk-indiv.dtl', 'design/site_layout.dtl'))

        # zet een paar resultaten
        kamp = self.testdata.comp18_bk_deelnemers[0]
        kamp.result_rank = 1
        kamp.save(update_fields=['result_rank'])

        kamp = self.testdata.comp18_bk_deelnemers[2]
        kamp.rank = 25       # boven de limiet (24), onder de cut-off (48)
        kamp.save(update_fields=['rank'])

        # nogmaals ophalen, nu met resultaten
        url = self.url_uitslagen_bond_indiv % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-bk-indiv.dtl', 'design/site_layout.dtl'))

        # onbekend boogtype
        url = self.url_uitslagen_bond_indiv % (self.testdata.comp18.pk, 'X')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Boogtype niet bekend')

        # illegale parameters
        url = self.url_uitslagen_bond_indiv % ('x', 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_uitslagen_bond_indiv % (99999, 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # BK voor al afgesloten competitie
        comp = self.testdata.comp18
        comp.is_afgesloten = True
        comp.save(update_fields=['is_afgesloten'])
        url = self.url_uitslagen_bond_indiv % (comp.pk, 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Kampioenschap niet gevonden')

    def test_bk_teams(self):
        url = self.url_uitslagen_bond_teams % (self.testdata.comp18.pk, 'C')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-bk-teams.dtl', 'design/site_layout.dtl'))

        # ingelogd geeft teamleden van eigen vereniging
        functie_hwl = list(self.testdata.functie_hwl.values())[5]
        account = functie_hwl.accounts.first()
        self.e2e_login_and_pass_otp(account)

        url = self.url_uitslagen_bond_teams % (self.testdata.comp25.pk, 'TR')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-bk-teams.dtl', 'design/site_layout.dtl'))

        # in de functie HWL krijg je de teamleden van de vereniging die je beheert
        # (dit hoeft niet hetzelfde te zijn als je eigen vereniging)
        self.e2e_wissel_naar_functie(functie_hwl)

        url = self.url_uitslagen_bond_teams % (self.testdata.comp25.pk, 'LB')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-bk-teams.dtl', 'design/site_layout.dtl'))

        url = self.url_uitslagen_bond_teams % (self.testdata.comp18.pk, 'X')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Team type niet bekend')

        # illegale parameters
        url = self.url_uitslagen_bond_teams % ('x', 'C')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_uitslagen_bond_teams % (99999, 'C')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # BK voor al afgesloten competitie
        comp = self.testdata.comp18
        comp.is_afgesloten = True
        comp.save(update_fields=['is_afgesloten'])
        url = self.url_uitslagen_bond_teams % (comp.pk, 'TR')
        resp = self.client.get(url)
        self.assert404(resp, 'Kampioenschap niet gevonden')

    def test_anon(self):
        self.client.logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_bond_indiv % (self.testdata.comp18.pk, 'r'))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-bk-indiv.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_bond_teams % (self.testdata.comp18.pk, 'c'))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-bk-teams.dtl', 'design/site_layout.dtl'))

    def test_hist(self):
        # test redirect naar HistComp uitslag
        resp = self.client.get(self.url_uitslagen_bond_indiv % ('indoor-2000-2001', 'r'))
        self.assert_is_redirect(resp, '/bondscompetities/hist/2000-2001/indoor-individueel/recurve/bk/')

        resp = self.client.get(self.url_uitslagen_bond_teams % ('25m1pijl-2000-2001', 'c'))
        self.assert_is_redirect(resp, '/bondscompetities/hist/2000-2001/25m1pijl-teams/compound/bk/')


# end of file
