# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Competitie.definities import DEEL_RK, DEEL_BK
from Competitie.models import (CompetitieIndivKlasse, CompetitieTeamKlasse, CompetitieMatch, Regiocompetitie,
                               Kampioenschap, KampioenschapIndivKlasseLimiet, KampioenschapTeamKlasseLimiet)
from Functie.tests.helpers import maak_functie
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
from Wedstrijden.models import Uitslag
import datetime


class TestCompetitiePlanningBond(E2EHelpers, TestCase):

    """ tests voor de CompLaagBond applicatie, planning voor het BK """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_tijdlijn')

    url_competitie_overzicht = '/bondscompetities/%s/'                                          # comp_pk
    url_planning = '/bondscompetities/bk/planning/%s/'                                          # deelkamp_pk
    url_limieten = '/bondscompetities/bk/planning/%s/limieten/'                                 # deelkamp_pk
    url_wijzig_wedstrijd = '/bondscompetities/bk/planning/wedstrijd/wijzig/%s/'                 # match.pk
    url_verwijder_wedstrijd = '/bondscompetities/bk/planning/wedstrijd/verwijder/%s/'           # match.pk
    url_klassengrenzen_vaststellen = '/bondscompetities/beheer/%s/klassengrenzen-vaststellen/'  # comp.pk

    testdata = None

    @classmethod
    def setUpTestData(cls):
        print('%s: populating testdata start' % cls.__name__)
        s1 = timezone.now()
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()
        data.maak_bondscompetities()

        #data.maak_rk_deelnemers()
        s2 = timezone.now()
        d = s2 - s1
        print('%s: populating testdata took %.1f seconds' % (cls.__name__, d.total_seconds()))

    def _prep_beheerder_lid(self, voornaam):
        lid_nr = self._next_lid_nr
        self._next_lid_nr += 1

        sporter = Sporter(
                    lid_nr=lid_nr,
                    geslacht="M",
                    voornaam=voornaam,
                    achternaam="Tester",
                    email=voornaam.lower() + "@test.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=self.ver_101)
        sporter.save()

        return self.e2e_create_account(lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self._next_lid_nr = 100001

        self.rayon_1 = self.testdata.rayon[1]
        self.rayon_2 = self.testdata.rayon[2]
        self.regio_101 = self.testdata.regio[101]
        self.regio_105 = self.testdata.regio[105]
        self.regio_112 = self.testdata.regio[112]

        ver_nr = self.testdata.regio_ver_nrs[112][0]
        self.ver_112 = self.testdata.vereniging[ver_nr]

        ver_nr = self.testdata.regio_ver_nrs[101][0]
        self.ver_101 = ver = self.testdata.vereniging[ver_nr]

        loc = WedstrijdLocatie(banen_18m=1,
                               banen_25m=1,
                               adres='De Spanning 1, Houtdorp')
        loc.save()
        loc.verenigingen.add(ver)
        self.loc = loc

        # maak HWL functie aan voor deze vereniging
        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_bko_18 = self._prep_beheerder_lid('BKO')
        self.account_bko_25 = self._prep_beheerder_lid('BKO')
        self.account_rko1_18 = self._prep_beheerder_lid('RKO1')
        self.account_rko2_18 = self._prep_beheerder_lid('RKO2')
        self.account_rcl101_18 = self._prep_beheerder_lid('RCL101')
        self.account_rcl101_25 = self._prep_beheerder_lid('RCL101-25')
        self.account_rcl112_18 = self._prep_beheerder_lid('RCL112')
        self.account_schutter = self._prep_beheerder_lid('Schutter')
        self.lid_sporter_1 = Sporter.objects.get(lid_nr=self.account_schutter.username)

        self.account_schutter2 = self._prep_beheerder_lid('Schutter2')
        self.lid_sporter_2 = Sporter.objects.get(lid_nr=self.account_schutter2.username)

        self.boog_r = self.testdata.afkorting2boogtype_khsn['R']

        self.sporterboog = SporterBoog(sporter=self.lid_sporter_1,
                                       boogtype=self.boog_r,
                                       voor_wedstrijd=True)
        self.sporterboog.save()

        # klassengrenzen vaststellen om de competitie voorbij fase A te krijgen
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        url_klassengrenzen_vaststellen = self.url_klassengrenzen_vaststellen % self.testdata.comp18.pk
        resp = self.client.post(url_klassengrenzen_vaststellen)
        self.assert_is_redirect_not_plein(resp)  # check for success

        # BK wedstrijden datums
        bk_datum = timezone.now() + datetime.timedelta(days=7)
        self.testdata.comp18.begin_fase_P_indiv = bk_datum
        self.testdata.comp18.einde_fase_P_indiv = bk_datum + datetime.timedelta(days=1)

        bk_datum += datetime.timedelta(days=7)
        self.testdata.comp18.begin_fase_P_teams = bk_datum
        self.testdata.comp18.einde_fase_P_teams = bk_datum + datetime.timedelta(days=1)
        self.testdata.comp18.save(update_fields=['begin_fase_P_indiv', 'einde_fase_P_indiv',
                                                 'begin_fase_P_teams', 'einde_fase_P_teams'])

        self.deelkamp_bk_18 = Kampioenschap.objects.filter(competitie=self.testdata.comp18,
                                                           deel=DEEL_BK)[0]
        self.deelcomp_rayon1_18 = Kampioenschap.objects.filter(competitie=self.testdata.comp18,
                                                               deel=DEEL_RK,
                                                               rayon=self.rayon_1)[0]
        self.deelcomp_regio_101 = Regiocompetitie.objects.filter(competitie=self.testdata.comp18,
                                                                 regio=self.regio_101)[0]
        self.deelcomp_regio_105 = Regiocompetitie.objects.filter(competitie=self.testdata.comp18,
                                                                 regio=self.regio_105)[0]

        self.functie_bko_18 = self.deelkamp_bk_18.functie
        self.functie_bko_18.accounts.add(self.account_bko_18)

        self.deelkamp_bk_25 = Kampioenschap.objects.filter(competitie=self.testdata.comp25,
                                                           deel=DEEL_BK)[0]
        self.functie_bko_25 = self.deelkamp_bk_25.functie
        self.functie_bko_25.accounts.add(self.account_bko_25)

        self.functie_rko1_18 = self.deelcomp_rayon1_18.functie
        self.functie_rko1_18.accounts.add(self.account_rko1_18)

        # maak nog een test vereniging, zonder HWL functie
        ver = Vereniging(
                    naam="Kleine Club",
                    ver_nr=1100,
                    regio=self.regio_101)
        ver.save()

        qset = CompetitieIndivKlasse.objects.filter(competitie=self.testdata.comp18,
                                                    boogtype__afkorting='R',
                                                    is_ook_voor_rk_bk=True)
        self.klasse_indiv_r0 = qset[0]
        self.klasse_indiv_r1 = qset[1]

        qset = CompetitieTeamKlasse.objects.filter(competitie=self.testdata.comp18,
                                                   team_afkorting='C',
                                                   is_voor_teams_rk_bk=True)
        self.klasse_team_c0 = qset[0]
        self.klasse_team_c1 = qset[1]

        KampioenschapIndivKlasseLimiet(
            kampioenschap=self.deelkamp_bk_18,
            indiv_klasse=self.klasse_indiv_r0,
            limiet=24).save()

        KampioenschapTeamKlasseLimiet(
            kampioenschap=self.deelkamp_bk_18,
            team_klasse=self.klasse_team_c0,
            limiet=8).save()

        self.match = CompetitieMatch(
                        competitie=self.testdata.comp18,
                        beschrijving='test',
                        datum_wanneer='2000-01-01',
                        tijd_begin_wedstrijd='01:01')
        self.match.save()
        # add to Kampioenschap.rk_bk_matches ?

    def test_anon(self):
        self.client.logout()

        resp = self.client.get(self.url_wijzig_wedstrijd % 999999)
        self.assert403(resp)

        resp = self.client.post(self.url_verwijder_wedstrijd % 999999)
        self.assert403(resp)

        resp = self.client.get(self.url_planning % 999999)
        self.assert403(resp)

        resp = self.client.get(self.url_limieten % 999999)
        self.assert403(resp)

    def test_planning(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        url = self.url_planning % self.deelkamp_bk_18.pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/planning-landelijk.dtl', 'plein/site_layout.dtl'))

        # maak een nieuwe wedstrijd aan
        CompetitieMatch.objects.all().delete()
        resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        self.assertTrue(1, CompetitieMatch.objects.count())
        match = CompetitieMatch.objects.first()
        self.assert_is_redirect(resp, self.url_wijzig_wedstrijd % match.pk)

        # get met deze nieuwe wedstrijd
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/planning-landelijk.dtl', 'plein/site_layout.dtl'))

        # verkeerde deelcomp
        resp = self.client.get(self.url_planning % self.deelcomp_rayon1_18.pk)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        resp = self.client.get(self.url_planning % 999999)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        resp = self.client.post(self.url_planning % 999999)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        # verkeerde BKO
        url = self.url_planning % self.deelkamp_bk_25.pk
        resp = self.client.get(url)
        self.assert404(resp, 'Niet de beheerder')

        resp = self.client.post(url)
        self.assert404(resp, 'Niet de beheerder')

        # probeer als BB
        self.e2e_wisselnaarrol_bb()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/planning-landelijk.dtl', 'plein/site_layout.dtl'))

    def test_wijzig_wedstrijd(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        self.deelkamp_bk_18.rk_bk_matches.add(self.match)

        url = self.url_wijzig_wedstrijd % self.match.pk
        url_redir_expected = self.url_planning % self.deelkamp_bk_18.pk

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # probeer te wijzigen
        resp = self.client.post(url)
        self.assert404(resp, 'Incompleet verzoek')

        resp = self.client.post(url, {'weekdag': 'x', 'aanvang': '10:00', 'ver_pk': '1', 'loc_pk': '1'})
        self.assert404(resp, 'Geen valide verzoek')

        resp = self.client.post(url, {'weekdag': '-1', 'aanvang': '10:00', 'ver_pk': '1', 'loc_pk': '1'})
        self.assert404(resp, 'Geen valide verzoek')

        resp = self.client.post(url, {'weekdag': '1', 'aanvang': '24:00', 'ver_pk': '1', 'loc_pk': '1'})
        self.assert404(resp, 'Geen valide verzoek')

        resp = self.client.post(url, {'weekdag': '1', 'aanvang': '10:60', 'ver_pk': '1', 'loc_pk': '1'})
        self.assert404(resp, 'Geen valide tijdstip')

        # standaard duurt fase P 7 dagen
        resp = self.client.post(url, {'weekdag': '20', 'aanvang': '10:00', 'ver_pk': '1', 'loc_pk': '1'})
        self.assert404(resp, 'Geen valide datum')

        resp = self.client.post(url, {'weekdag': '1', 'aanvang': '10:00',
                                      'ver_pk': 'geen', 'loc_pk': '1',
                                      'wkl_indiv_#': 1, 'wkl_team_#': 1})
        self.assert_is_redirect(resp, url_redir_expected)

        resp = self.client.post(url, {'weekdag': '1', 'aanvang': '10:00',
                                      'ver_pk': '99999', 'loc_pk': '1'})
        self.assert404(resp, 'Vereniging niet gevonden')

        resp = self.client.post(url, {'weekdag': 0, 'aanvang': '10:00',
                                      'ver_pk': self.ver_112.ver_nr, 'loc_pk': '1'})
        self.assert404(resp, 'Locatie niet gevonden')

        resp = self.client.post(url, {'weekdag': 0, 'aanvang': '10:00',
                                      'ver_pk': self.ver_112.ver_nr, 'loc_pk': '',
                                      'wkl_indiv_999999': 1, 'wkl_team_999999': 1})
        self.assert_is_redirect(resp, url_redir_expected)

        resp = self.client.post(url, {'weekdag': 0, 'aanvang': '10:00',
                                      'ver_pk': self.ver_112.ver_nr, 'loc_pk': '',
                                      'wkl_indiv_%s' % self.klasse_indiv_r0.pk: '1',
                                      'wkl_team_%s' % self.klasse_team_c0.pk: '1'})
        self.assert_is_redirect(resp, url_redir_expected)

        # nog een keer dezelfde wedstrijdklassen zetten
        resp = self.client.post(url, {'weekdag': 0, 'aanvang': '10:00',
                                      'ver_pk': self.ver_112.ver_nr, 'loc_pk': '',
                                      'wkl_indiv_%s' % self.klasse_indiv_r0.pk: '1',
                                      'wkl_team_%s' % self.klasse_team_c0.pk: '1'})
        self.assert_is_redirect(resp, url_redir_expected)

        # doe een get met de wedstrijdklassen gekoppeld
        # resp = self.client.get(url)
        # self.assertEqual(resp.status_code, 200)     # 200 = OK
        # self.assert_html_ok(resp)
        # self.assert_template_used(resp, ('complaagbond/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # wedstrijdklassen weer verwijderen
        resp = self.client.post(url, {'weekdag': 0, 'aanvang': '10:00',
                                      'ver_pk': self.ver_112.ver_nr, 'loc_pk': ''})
        self.assert_is_redirect(resp, url_redir_expected)

        # verkeerde deelcomp
        resp = self.client.get(self.url_wijzig_wedstrijd % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        resp = self.client.post(self.url_wijzig_wedstrijd % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # verkeerde BKO
        self.e2e_wissel_naar_functie(self.functie_bko_25)
        resp = self.client.get(url)
        self.assert404(resp, 'Niet de beheerder')

        resp = self.client.post(url)
        self.assert404(resp, 'Niet de beheerder')

        # geen BK match
        self.deelkamp_bk_18.rk_bk_matches.clear()
        resp = self.client.get(url)
        self.assert404(resp, 'Geen BK wedstrijd')

        resp = self.client.post(url)
        self.assert404(resp, 'Geen BK wedstrijd')

    def test_limieten(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        # verkeerde BKO
        url = self.url_limieten % self.deelkamp_bk_25.pk
        resp = self.client.get(url)
        self.assert404(resp, 'Niet de beheerder')

        resp = self.client.post(url)
        self.assert404(resp, 'Niet de beheerder')

        url = self.url_limieten % self.deelkamp_bk_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/wijzig-limieten.dtl', 'plein/site_layout.dtl'))

        isel_r0 = 'isel_%s' % self.klasse_indiv_r0.pk
        isel_r1 = 'isel_%s' % self.klasse_indiv_r1.pk
        tsel_c0 = 'tsel_%s' % self.klasse_team_c0.pk
        tsel_c1 = 'tsel_%s' % self.klasse_team_c1.pk

        # wijzig limieten
        with self.assert_max_queries(20):
            resp = self.client.post(url, {isel_r0: 24, isel_r1: 8, tsel_c0: 8, tsel_c1: 10, 'snel': '1'})
        self.assert_is_redirect_not_plein(resp)

        # corner cases
        resp = self.client.post(url, {isel_r0: 0})
        self.assert404(resp, 'Geen valide keuze voor indiv')

        resp = self.client.post(url, {tsel_c0: 0})
        self.assert404(resp, 'Geen valide keuze voor team')

        resp = self.client.post(url, {isel_r0: 'xx', tsel_c0: 'xx'})
        self.assert_is_redirect_not_plein(resp)

        url = self.url_limieten % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        resp = self.client.post(url)
        self.assert404(resp, 'Kampioenschap niet gevonden')

    def test_verwijder_wedstrijd(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        url = self.url_verwijder_wedstrijd % 999999
        resp = self.client.post(url)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        url = self.url_verwijder_wedstrijd % self.match.pk
        resp = self.client.post(url)
        self.assert404(resp, 'Geen BK wedstrijd')

        # verkeerde BKO
        self.deelkamp_bk_25.rk_bk_matches.add(self.match)
        resp = self.client.post(url)
        self.assert404(resp, 'Niet de beheerder')
        self.deelkamp_bk_25.rk_bk_matches.clear()

        self.deelkamp_bk_18.rk_bk_matches.add(self.match)

        uitslag = Uitslag(
                    max_score=300,
                    afstand=18,
                    is_bevroren=True)
        uitslag.save()
        self.match.uitslag = uitslag
        self.match.save(update_fields=['uitslag'])

        resp = self.client.post(url)
        self.assert404(resp, 'Uitslag mag niet meer gewijzigd worden')

        # echt verwijderen
        resp = self.client.post(url)
        uitslag.is_bevroren = False
        uitslag.save(update_fields=['is_bevroren'])
        resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        self.match.uitslag = None
        self.match.pk = 0
        self.match.save()
        self.deelkamp_bk_18.rk_bk_matches.add(self.match)

        url = self.url_verwijder_wedstrijd % self.match.pk
        resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

# end of file
