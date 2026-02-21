# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Competitie.models import CompetitieMatch
from Competitie.test_utils.tijdlijn import zet_competitie_fase_bk_prep
from Locatie.models import WedstrijdLocatie
from Scheidsrechter.models import MatchScheidsrechters
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompLaagMatchInfo(E2EHelpers, TestCase):

    """ tests voor de CompLaagBond applicatie, Match Info view """

    test_after = ('Competitie.tests.test_overzicht', 'CompBeheer.tests.test_bko')

    url_match_info = '/bondscompetities/bk/wedstrijd-informatie/%s/'     # match_pk

    testdata = None
    ver_nr = 0

    @classmethod
    def setUpTestData(cls):
        print('%s: populating testdata start' % cls.__name__)
        s1 = timezone.now()

        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()
        data.maak_bondscompetities()

        for regio_nr in (111, 113):
            ver_nr = data.regio_ver_nrs[regio_nr][0]
            data.maak_rk_deelnemers(18, ver_nr, regio_nr, limit_boogtypen=['R', 'BB'])
            data.maak_rk_teams(18, ver_nr, zet_klasse=True)
        # for

        data.maak_uitslag_rk_indiv(18)
        data.maak_bk_deelnemers(18)
        data.maak_bk_teams(18)

        cls.ver_nr = data.regio_ver_nrs[111][0]
        cls.ver = data.vereniging[cls.ver_nr]

        cls.functie_hwl = data.functie_hwl[cls.ver_nr]

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

        # zet de competitie in fase O (=vereiste vaststellen klassengrenzen)
        zet_competitie_fase_bk_prep(self.testdata.comp18)

        # stel de klassengrenzen vast
        # resp = self.client.post(self.url_klassengrenzen_teams_vaststellen % self.testdata.comp18.pk)
        # self.e2e_dump_resp(resp)
        # self.assert_is_redirect_not_plein(resp)

        # zet de competities in fase P
        # zet_competitie_fase_bk_wedstrijden(self.testdata.comp18)
        # zet_competitie_fase_bk_wedstrijden(self.testdata.comp25)

        loc = WedstrijdLocatie(banen_18m=8,
                               banen_25m=8,
                               adres='De Spanning 1, Houtdorp')
        loc.save()
        loc.verenigingen.add(self.ver)
        self.loc = loc

        # maak een BK wedstrijd aan
        self.match = CompetitieMatch(
                        competitie=self.testdata.comp18,
                        beschrijving='test wedstrijd BK',
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
        self.comp18_klassen_indiv_bk = match_klassen

        match_klassen = list()
        for klasse in self.testdata.comp18_klassen_teams['R2']:
            match_klassen.append(klasse)
        # for
        self.match.team_klassen.add(*match_klassen)
        self.comp18_klassen_teams_bk = match_klassen

        self.deelkamp18_bk = self.testdata.deelkamp18_bk
        self.deelkamp18_bk.rk_bk_matches.add(self.match.pk)

        self.deelkamp25_bk = self.testdata.deelkamp25_bk

    def test_anon(self):
        self.client.logout()

        resp = self.client.get(self.url_match_info % 999999)
        self.assert_is_redirect_login(resp)

    def test_match_info(self):
        self.e2e_wissel_naar_functie(self.functie_hwl)

        url = self.url_match_info % self.match.pk
        with self.assert_max_queries(26):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/hwl-bk-match-info.dtl', 'design/site_layout.dtl'))

        # SR nodig
        self.match.aantal_scheids = 1
        self.match.locatie = None
        self.match.save(update_fields=['aantal_scheids', 'locatie'])

        with self.assert_max_queries(27):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/hwl-bk-match-info.dtl', 'design/site_layout.dtl'))

        # 25m1p
        self.match.competitie = self.testdata.comp25
        self.match.save(update_fields=['competitie'])

        msr = MatchScheidsrechters.objects.create(match=self.match,
                                                  gekozen_hoofd_sr=self.testdata.ver_sporters[self.ver_nr][0])

        with self.assert_max_queries(27):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/hwl-bk-match-info.dtl', 'design/site_layout.dtl'))

        self.match.locatie = self.loc
        self.match.save(update_fields=['locatie'])

        msr.gekozen_sr1 = self.testdata.ver_sporters[self.ver_nr][1]
        msr.save(update_fields=['gekozen_sr1'])

        with self.assert_max_queries(27):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/hwl-bk-match-info.dtl', 'design/site_layout.dtl'))

        # niet bestaande match
        resp = self.client.get(self.url_match_info % 999999)
        self.assert404(resp, "Wedstrijd niet gevonden")

        # niet een BK match
        match = CompetitieMatch.objects.create(
                        competitie=self.match.competitie,
                        beschrijving='test',
                        vereniging=self.functie_hwl.vereniging,
                        datum_wanneer='2000-01-01',
                        tijd_begin_wedstrijd='00:00')
        resp = self.client.get(self.url_match_info % match.pk)
        self.assert404(resp, "Geen kampioenschap")

        # verkeerde HWL
        self.e2e_wissel_naar_functie(self.testdata.functie_hwl[self.ver.ver_nr + 1])
        resp = self.client.get(self.url_match_info % self.match.pk)
        self.assert404(resp, 'Niet de beheerder')


# end of file
