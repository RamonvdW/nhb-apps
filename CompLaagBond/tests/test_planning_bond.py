# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.models import Competitie, DeelCompetitie, DeelKampioenschap, DEEL_RK, DEEL_BK
from Competitie.operations import competities_aanmaken
from Functie.operations import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging
from Sporter.models import Sporter, SporterBoog
from Wedstrijden.models import WedstrijdLocatie
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestCompetitiePlanningBond(E2EHelpers, TestCase):

    """ tests voor de CompLaagBond applicatie, planning voor het BK """

    test_after = ('Competitie.tests.test_fase', 'Competitie.tests.test_beheerders')

    url_competitie_overzicht = '/bondscompetities/%s/'                                          # comp_pk
    url_planning_bk = '/bondscompetities/bk/planning/%s/'                                       # deelcomp_pk
    url_klassengrenzen_vaststellen = '/bondscompetities/beheer/%s/klassengrenzen-vaststellen/'  # comp.pk

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def _prep_beheerder_lid(self, voornaam):
        lid_nr = self._next_lid_nr
        self._next_lid_nr += 1

        sporter = Sporter(
                    lid_nr=lid_nr,
                    geslacht="M",
                    voornaam=voornaam,
                    achternaam="Tester",
                    email=voornaam.lower() + "@nhb.test",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=self.nhbver_101)
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
        ver.ver_nr = "1111"
        ver.regio = self.regio_112
        ver.save()
        self.nhbver_112 = ver

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
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

        self.boog_r = BoogType.objects.get(afkorting='R')

        self.sporterboog = SporterBoog(sporter=self.lid_sporter_1,
                                       boogtype=self.boog_r,
                                       voor_wedstrijd=True)
        self.sporterboog.save()

        # creëer een competitie met deelcompetities
        competities_aanmaken(jaar=2019)

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        # klassengrenzen vaststellen om de competitie voorbij fase A te krijgen
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        url_klassengrenzen_vaststellen = self.url_klassengrenzen_vaststellen % self.comp_18.pk
        resp = self.client.post(url_klassengrenzen_vaststellen)
        self.assert_is_redirect_not_plein(resp)  # check for success

        self.deelkamp_bk_18 = DeelKampioenschap.objects.filter(competitie=self.comp_18,
                                                               deel=DEEL_BK)[0]
        self.deelcomp_rayon1_18 = DeelKampioenschap.objects.filter(competitie=self.comp_18,
                                                                   deel=DEEL_RK,
                                                                   nhb_rayon=self.rayon_1)[0]
        self.deelcomp_regio_101 = DeelCompetitie.objects.filter(competitie=self.comp_18,
                                                                nhb_regio=self.regio_101)[0]
        self.deelcomp_regio_105 = DeelCompetitie.objects.filter(competitie=self.comp_18,
                                                                nhb_regio=self.regio_105)[0]

        self.functie_bko_18 = self.deelkamp_bk_18.functie
        self.functie_bko_18.accounts.add(self.account_bko_18)

        self.deelkamp_bk_25 = DeelKampioenschap.objects.filter(competitie=self.comp_25,
                                                               deel=DEEL_BK)[0]
        self.functie_bko_25 = self.deelkamp_bk_25.functie
        self.functie_bko_25.accounts.add(self.account_bko_25)

        self.functie_rko1_18 = self.deelcomp_rayon1_18.functie
        self.functie_rko1_18.accounts.add(self.account_rko1_18)

        # maak nog een test vereniging, zonder HWL functie
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.ver_nr = "1100"
        ver.regio = self.regio_101
        ver.save()

    def test_planning_bk(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        # verkeerde BKO
        url = self.url_planning_bk % self.deelkamp_bk_25.pk
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie (2)')

        url = self.url_planning_bk % self.deelkamp_bk_18.pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/planning-landelijk.dtl', 'plein/site_layout.dtl'))

        # probeer als BB
        self.e2e_wisselnaarrol_bb()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/planning-landelijk.dtl', 'plein/site_layout.dtl'))

        # verkeerde deelcomp
        resp = self.client.get(self.url_planning_bk % self.deelcomp_rayon1_18.pk)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        resp = self.client.get(self.url_planning_bk % 999999)
        self.assert404(resp, 'Kampioenschap niet gevonden')


# end of file
