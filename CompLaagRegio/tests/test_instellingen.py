# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.models import (Competitie, DeelCompetitie,
                               CompetitieIndivKlasse, CompetitieTeamKlasse,
                               INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_3,
                               DeelKampioenschap, DEEL_RK, DEEL_BK)
from Competitie.operations import competities_aanmaken
from Competitie.tests.test_helpers import zet_competitie_fase
from Functie.operations import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging
from Sporter.models import Sporter, SporterBoog
from Wedstrijden.models import WedstrijdLocatie
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestCompLaagRegioInstellingen(E2EHelpers, TestCase):

    """ tests voor de CompLaagRegio applicatie, Teams functie """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_beheerders')

    url_regio_instellingen = '/bondscompetities/regio/instellingen/%s/regio-%s/'  # comp_pk, regio-nr
    url_regio_globaal = '/bondscompetities/regio/instellingen/%s/globaal/'        # comp_pk
    url_klassengrenzen_vaststellen = '/bondscompetities/beheer/%s/klassengrenzen-vaststellen/'  # comp_pk

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def _prep_beheerder_lid(self, voornaam):
        lid_nr = self._next_lid_nr
        self._next_lid_nr += 1

        sporter = Sporter()
        sporter.lid_nr = lid_nr
        sporter.geslacht = "M"
        sporter.voornaam = voornaam
        sporter.achternaam = "Tester"
        sporter.email = voornaam.lower() + "@nhb.test"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = self.nhbver_101
        sporter.save()

        return self.e2e_create_account(lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self._next_lid_nr = 100001

        self.rayon_1 = NhbRayon.objects.get(rayon_nr=1)
        self.rayon_2 = NhbRayon.objects.get(rayon_nr=2)
        self.regio_101 = NhbRegio.objects.get(regio_nr=101)
        self.regio_105 = NhbRegio.objects.get(regio_nr=105)
        self.regio_112 = NhbRegio.objects.get(regio_nr=112)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Zuidelijke Club"
        ver.ver_nr = 1111
        ver.regio = self.regio_112
        ver.save()
        self.nhbver_112 = ver

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = 1000
        ver.regio = self.regio_101
        ver.save()
        self.nhbver_101 = ver

        loc = WedstrijdLocatie(banen_18m=1,
                               banen_25m=1,
                               adres='De Spanning 1, Houtdorp')
        loc.save()
        loc.verenigingen.add(ver)
        self.loc = loc

        # maak HWL functie aan voor deze vereniging
        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        self.functie_wl = maak_functie("WL Vereniging %s" % ver.ver_nr, "WL")
        self.functie_wl.nhb_ver = ver
        self.functie_wl.save()

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_bko_18 = self._prep_beheerder_lid('BKO')
        self.account_rko1_18 = self._prep_beheerder_lid('RKO1')
        self.account_rko2_18 = self._prep_beheerder_lid('RKO2')
        self.account_rcl101_18 = self._prep_beheerder_lid('RCL101')
        self.account_rcl101_25 = self._prep_beheerder_lid('RCL101-25')
        self.account_rcl112_18 = self._prep_beheerder_lid('RCL112')
        self.account_schutter = self._prep_beheerder_lid('Schutter')
        self.lid_sporter = Sporter.objects.get(lid_nr=self.account_schutter.username)

        self.boog_r = BoogType.objects.get(afkorting='R')

        self.sporterboog = SporterBoog(sporter=self.lid_sporter,
                                       boogtype=self.boog_r,
                                       voor_wedstrijd=True)
        self.sporterboog.save()

        # creëer een competitie met deelcompetities
        competities_aanmaken(jaar=2019)

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        # een parallel competitie is noodzakelijk om corner-cases te raken
        competities_aanmaken(jaar=2020)

        # klassengrenzen vaststellen om de competitie voorbij fase A te krijgen
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        url_klassengrenzen_vaststellen_18 = self.url_klassengrenzen_vaststellen % self.comp_18.pk
        resp = self.client.post(url_klassengrenzen_vaststellen_18)
        self.assert_is_redirect_not_plein(resp)  # check for success

        klasse = CompetitieTeamKlasse.objects.get(competitie=self.comp_18,
                                                  volgorde=15,                  # Rec ERE
                                                  is_voor_teams_rk_bk=False)
        klasse.min_ag = 29.0
        klasse.save()

        klasse = CompetitieTeamKlasse.objects.get(competitie=self.comp_18,
                                                  volgorde=16,                  # Rec A
                                                  is_voor_teams_rk_bk=False)
        klasse.min_ag = 25.0
        klasse.save()

        self.client.logout()

        self.klasse_recurve_onbekend = (CompetitieIndivKlasse
                                        .objects
                                        .filter(boogtype=self.boog_r,
                                                is_onbekend=True)
                                        .all())[0]

        self.deelcomp_bond_18 = DeelKampioenschap.objects.filter(deel=DEEL_BK, competitie=self.comp_18)[0]
        self.deelcomp_rayon1_18 = DeelKampioenschap.objects.filter(deel=DEEL_RK, competitie=self.comp_18, nhb_rayon=self.rayon_1)[0]
        self.deelcomp_rayon2_18 = DeelKampioenschap.objects.filter(deel=DEEL_RK, competitie=self.comp_18, nhb_rayon=self.rayon_2)[0]
        self.deelcomp_regio101_18 = DeelCompetitie.objects.filter(competitie=self.comp_18, nhb_regio=self.regio_101)[0]
        self.deelcomp_regio101_25 = DeelCompetitie.objects.filter(competitie=self.comp_25, nhb_regio=self.regio_101)[0]
        self.deelcomp_regio112_18 = DeelCompetitie.objects.filter(competitie=self.comp_18, nhb_regio=self.regio_112)[0]

        self.cluster_101a_18 = NhbCluster.objects.get(regio=self.regio_101, letter='a', gebruik='18')
        self.cluster_101e_25 = NhbCluster.objects.get(regio=self.regio_101, letter='e', gebruik='25')

        self.functie_bko_18 = self.deelcomp_bond_18.functie
        self.functie_rko1_18 = self.deelcomp_rayon1_18.functie
        self.functie_rko2_18 = self.deelcomp_rayon2_18.functie
        self.functie_rcl101_18 = self.deelcomp_regio101_18.functie
        self.functie_rcl101_25 = self.deelcomp_regio101_25.functie
        self.functie_rcl112_18 = self.deelcomp_regio112_18.functie

        self.functie_bko_18.accounts.add(self.account_bko_18)
        self.functie_rko1_18.accounts.add(self.account_rko1_18)
        self.functie_rko2_18.accounts.add(self.account_rko2_18)
        self.functie_rcl101_18.accounts.add(self.account_rcl101_18)
        self.functie_rcl101_25.accounts.add(self.account_rcl101_25)
        self.functie_rcl112_18.accounts.add(self.account_rcl112_18)

        # maak nog een test vereniging, zonder HWL functie
        # stop deze in een cluster
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.ver_nr = "1100"
        ver.regio = self.regio_101
        ver.save()
        ver.clusters.add(self.cluster_101e_25)

    def test_regio_instellingen(self):
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        url = self.url_regio_instellingen % (self.comp_18.pk, 112)

        # fase A

        # tijdens competitie fase A mogen alle instellingen aangepast worden
        zet_competitie_fase(self.comp_18, 'A')

        # when the phase is set artificially, some dates are left behind
        # let's repair that here
        self.comp_18 = Competitie.objects.get(pk=self.comp_18.pk)
        self.comp_18.eerste_wedstrijd = self.comp_18.begin_aanmeldingen
        self.comp_18.eerste_wedstrijd += datetime.timedelta(days=1)
        self.comp_18.save()
        post_datum_ok = self.comp_18.begin_aanmeldingen.strftime('%Y-%m-%d')
        # print('begin_aanmeldingen: %s' % comp_datum1)
        post_datum_bad = self.comp_18.eerste_wedstrijd.strftime('%Y-%m-%d')
        # print('eerste_wedstrijd: %s' % comp_datum2)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-instellingen.dtl', 'plein/site_layout.dtl'))

        # all params missing
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        # all params present
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'teams': 'ja',
                                          'team_alloc': 'vast',
                                          'team_punten': 'F1',
                                          'einde_teams_aanmaken': post_datum_ok})
        self.assert_is_redirect_not_plein(resp)

        # late date
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'teams': 'ja',
                                          'einde_teams_aanmaken': post_datum_bad})
        self.assert404(resp, 'Datum buiten toegestane reeks')

        # late date - not checked when teams=nee
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'teams': 'nee',
                                          'einde_teams_aanmaken': post_datum_bad})
        self.assert_is_redirect_not_plein(resp)
        # teamcompetitie staat nu op Nee
        # zet teamcompetitie weer op Ja
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'teams': 'ja',
                                          'team_alloc': 'vast'})
        self.assert_is_redirect_not_plein(resp)

        # bad date
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'teams': 'ja',
                                          'einde_teams_aanmaken': 'xxx'})
        self.assert404(resp, 'Datum fout formaat')

        # fase B en C

        # tot en met fase C mogen de team punten en datum aanmaken teams aangepast worden
        oude_punten = 'F1'

        for fase in ('B', 'C'):
            zet_competitie_fase(self.comp_18, fase)

            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)  # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('complaagregio/rcl-instellingen.dtl', 'plein/site_layout.dtl'))

            deelcomp_pre = DeelCompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
            self.assertTrue(deelcomp_pre.regio_organiseert_teamcompetitie)
            self.assertTrue(deelcomp_pre.regio_heeft_vaste_teams)
            self.assertEqual(deelcomp_pre.regio_team_punten_model, oude_punten)
            if oude_punten == 'F1':
                nieuwe_punten = '2P'
            else:
                nieuwe_punten = 'SS'

            # all params present
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'teams': 'nee',
                                              'team_alloc': 'vsg',
                                              'team_punten': nieuwe_punten,
                                              'einde_teams_aanmaken': post_datum_ok})
            self.assert_is_redirect_not_plein(resp)

            deelcomp_post = DeelCompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
            self.assertTrue(deelcomp_post.regio_organiseert_teamcompetitie)
            self.assertTrue(deelcomp_post.regio_heeft_vaste_teams)
            self.assertEqual(deelcomp_post.regio_team_punten_model, nieuwe_punten)
            oude_punten = nieuwe_punten

        # fase D

        zet_competitie_fase(self.comp_18, 'E')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-instellingen.dtl', 'plein/site_layout.dtl'))

    def test_regio_instellingen_bad(self):
        # bad cases
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        url = self.url_regio_instellingen % (self.comp_18.pk, 112)

        # na fase F zijn de instellingen niet meer in te zien
        zet_competitie_fase(self.comp_18, 'K')      # fase G is niet te zetten

        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie fase')
        resp = self.client.post(url)
        self.assert404(resp, 'Verkeerde competitie fase')

        # niet bestaande regio
        url = self.url_regio_instellingen % (self.comp_18.pk, 100)
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')
        resp = self.client.post(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # niet de regio van de RCL
        url = self.url_regio_instellingen % (self.comp_18.pk, 110)
        resp = self.client.get(url)
        self.assert403(resp)
        resp = self.client.post(url)
        self.assert403(resp)

        # logout

        url = self.url_regio_instellingen % (self.comp_18.pk, 112)
        self.client.logout()
        resp = self.client.get(url)
        self.assert403(resp)

    def test_regio_globaal(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        self.deelcomp_regio101_18.inschrijf_methode = INSCHRIJF_METHODE_1
        self.deelcomp_regio101_18.regio_organiseert_teamcompetitie = False
        self.deelcomp_regio101_18.save(update_fields=['inschrijf_methode', 'regio_organiseert_teamcompetitie'])

        self.deelcomp_regio101_25.inschrijf_methode = INSCHRIJF_METHODE_1
        self.deelcomp_regio101_25.save(update_fields=['inschrijf_methode'])

        self.deelcomp_regio112_18.inschrijf_methode = INSCHRIJF_METHODE_3
        self.deelcomp_regio112_18.regio_heeft_vaste_teams = False
        self.deelcomp_regio112_18.save(update_fields=['inschrijf_methode', 'regio_heeft_vaste_teams'])

        url = self.url_regio_globaal % self.comp_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-instellingen-globaal.dtl', 'plein/site_layout.dtl'))

        # als RKO
        self.e2e_wissel_naar_functie(self.functie_rko1_18)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-instellingen-globaal.dtl', 'plein/site_layout.dtl'))

        # niet bestaande competitie
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_regio_globaal % 99999)
        self.assert404(resp, 'Competitie niet gevonden')


# end of file
