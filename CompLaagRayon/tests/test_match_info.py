# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.utils import timezone
from Competitie.definities import DEELNAME_NEE
from Competitie.models import CompetitieMatch, KampioenschapSporterBoog, KampioenschapIndivKlasseLimiet
from Competitie.test_utils.tijdlijn import zet_competitie_fase_rk_prep, zet_competitie_fase_rk_wedstrijden
from Locatie.models import WedstrijdLocatie
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import zipfile
import os


class TestCompLaagRayonMatchInfo(E2EHelpers, TestCase):

    """ tests voor de CompLaagRayon applicatie, Match Info view """

    test_after = ('Competitie.tests.test_overzicht', 'CompBeheer.tests.test_bko', 'CompLaagRayon.tests.test_teams_rko',
                  'CompLaagRayon.tests.test_teams_rko')

    url_match_info = '/bondscompetities/rk/wedstrijd-informatie/%s/'     # match_pk

    testdata = None
    regio_nr = 113
    rayon_nr = 4
    ver_nr = 0

    url_klassengrenzen_teams_vaststellen = '/bondscompetities/beheer/%s/doorzetten/rk-bk-teams-klassengrenzen-vaststellen/'  # comp_pk

    @classmethod
    def setUpTestData(cls):
        print('%s: populating testdata start' % cls.__name__)
        s1 = timezone.now()

        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()
        data.maak_bondscompetities()

        cls.ver_nr = ver_nr = data.regio_ver_nrs[cls.regio_nr][0]
        cls.ver = data.vereniging[ver_nr]

        data.maak_rk_deelnemers(18, ver_nr, cls.regio_nr, limit_boogtypen=['R', 'BB'])
        data.maak_rk_teams(18, ver_nr, per_team=3, limit_teamtypen=['R2'])

        ver_nr = data.regio_ver_nrs[cls.regio_nr][1]
        data.maak_rk_deelnemers(18, ver_nr, cls.regio_nr, limit_boogtypen=['R', 'BB'])
        data.maak_rk_teams(18, ver_nr, per_team=3, limit_teamtypen=['R2'])

        s2 = timezone.now()
        d = s2 - s1
        print('%s: populating testdata took %.1f seconds' % (cls.__name__, d.total_seconds()))

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_bko)
        self.e2e_check_rol('BKO')

        # zet de competitie in fase J (=vereiste vaststellen klassengrenzen)
        zet_competitie_fase_rk_prep(self.testdata.comp18)

        # stel de klassengrenzen vast
        resp = self.client.post(self.url_klassengrenzen_teams_vaststellen % self.testdata.comp18.pk)
        # self.e2e_dump_resp(resp)
        self.assert_is_redirect_not_plein(resp)

        # zet de competities in fase L
        zet_competitie_fase_rk_wedstrijden(self.testdata.comp18)
        zet_competitie_fase_rk_wedstrijden(self.testdata.comp25)

        loc = WedstrijdLocatie(banen_18m=8,
                               banen_25m=8,
                               adres='De Spanning 1, Houtdorp')
        loc.save()
        loc.verenigingen.add(self.ver)

        # maak een RK wedstrijd aan
        self.match = CompetitieMatch(
                        competitie=self.testdata.comp18,
                        beschrijving='test wedstrijd RK',
                        datum_wanneer='2020-01-01',
                        tijd_begin_wedstrijd='10:00',
                        vereniging=self.ver,              # koppelt wedstrijd aan de vereniging
                        locatie=loc)
        self.match.save()

        # koppel de wedstrijdklassen aan de match
        match_klassen = list()
        for klasse in self.testdata.comp18_klassen_indiv['R']:
            if klasse.is_ook_voor_rk_bk:
                match_klassen.append(klasse)
        # for
        self.match.indiv_klassen.add(*match_klassen)
        self.comp18_klassen_indiv_rk = match_klassen

        self.deelkamp_18 = self.testdata.deelkamp18_rk[self.rayon_nr]
        self.deelkamp_18.rk_bk_matches.add(self.match.pk)

        self.deelkamp_25 = self.testdata.deelkamp25_rk[self.rayon_nr]

    def test_match_info(self):
        url = self.url_match_info % self.match.pk

        self.e2e_login_and_pass_otp(self.testdata.account_hwl[self.ver_nr])
        self.e2e_wissel_naar_functie(self.testdata.functie_hwl[self.ver_nr])

        # geen klassen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('complaagrayon/hwl-rk-match-info.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # alleen indiv klassen
        self.match.indiv_klassen.set([self.comp18_klassen_indiv_rk[0],
                                      self.comp18_klassen_indiv_rk[-1]])
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('complaagrayon/hwl-rk-match-info.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # indiv + teams klassen
        self.match.team_klassen.set([self.testdata.comp18_klassen_teams['R2'][0],
                                     self.testdata.comp18_klassen_teams['R2'][1]])       # Recurve A met 2 teams
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('complaagrayon/hwl-rk-match-info.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # alleen teams klassen
        self.match.indiv_klassen.set([])
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('complaagrayon/hwl-rk-match-info.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # wedstrijd niet in een plan
        self.deelkamp_18.rk_bk_matches.remove(self.match.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Geen kampioenschap')

        # 25m1p plan
        self.deelkamp_25.rk_bk_matches.add(self.match.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # zonder locatie
        self.match.locatie = None
        self.match.save(update_fields=['locatie'])
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.deelkamp_25.rk_bk_matches.remove(self.match.pk)

        # wedstrijd van een niet-RK kampioenschap
        self.testdata.deelkamp18_bk.rk_bk_matches.add(self.match.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Geen kampioenschap')

        # niet bestaande wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_match_info % 'xxx')
        self.assert404(resp, 'Wedstrijd niet gevonden')

    def test_bad(self):
        url = self.url_match_info % self.match.pk

        # ophalen zonder inlog
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        self.e2e_login_and_pass_otp(self.testdata.account_hwl[self.ver_nr])
        self.e2e_wissel_naar_functie(self.testdata.functie_hwl[self.ver_nr])

        # creëer wat corner-cases
        self.match.locatie = None
        self.match.save(update_fields=['locatie'])

        # enable teams
        self.match.team_klassen.set([self.testdata.comp18_klassen_teams['R2'][0],
                                     self.testdata.comp18_klassen_teams['R2'][1]])       # Recurve A met 2 teams

        # geen klassengrenzen vastgesteld
        self.testdata.comp18.klassengrenzen_vastgesteld_rk_bk = False
        self.testdata.comp18.save(update_fields=['klassengrenzen_vastgesteld_rk_bk'])

        # ophalen met alle corner-cases
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('complaagrayon/hwl-rk-match-info.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)


# end of file
