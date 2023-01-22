# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from django.utils import timezone
from BasisTypen.models import BoogType
from Competitie.models import (Competitie, CompetitieIndivKlasse, DeelCompetitie, DeelKampioenschap, DEEL_RK, DEEL_BK,
                               RegioCompetitieSporterBoog, KampioenschapSporterBoog)
from Competitie.operations import competities_aanmaken
from Competitie.tests.test_helpers import zet_competitie_fase
from Functie.operations import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging
from Sporter.models import Sporter, SporterBoog
from Wedstrijden.models import WedstrijdLocatie
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime
import io


class TestCompetitiePlanningBond(E2EHelpers, TestCase):

    """ tests voor de CompBeheer applicatie, module BKO """

    test_after = ('Competitie.tests.test_fase', 'Competitie.tests.test_beheerders')

    url_competitie_overzicht = '/bondscompetities/%s/'                                          # comp_pk
    url_doorzetten_rk = '/bondscompetities/beheer/%s/doorzetten-rk/'                            # comp_pk
    url_doorzetten_bk = '/bondscompetities/beheer/%s/doorzetten-bk/'                            # comp_pk
    url_doorzetten_voorbij_bk = '/bondscompetities/beheer/%s/doorzetten-voorbij-bk/'            # comp_pk
    url_klassengrenzen_vaststellen = '/bondscompetities/beheer/%s/klassengrenzen-vaststellen/'  # comp_pk
    url_teams_klassengrenzen_vaststellen = '/bondscompetities/beheer/%s/rk-bk-teams-klassengrenzen/vaststellen/'  # comp_pk

    regio_nr = 101
    ver_nr = 0      # wordt in setupTestData ingevuld

    testdata = None

    @classmethod
    def setUpTestData(cls):
        s1 = timezone.now()
        print('CompBeheer.test_bko: populating testdata start')
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()
        cls.testdata.maak_clubs_en_sporters()
        cls.ver_nr = cls.testdata.regio_ver_nrs[cls.regio_nr][2]
        cls.testdata.maak_bondscompetities()
        s2 = timezone.now()
        d = s2 - s1
        print('CompBeheer.test_bko: populating testdata took %s seconds' % d.seconds)

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

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        # klassengrenzen vaststellen om de competitie voorbij fase A te krijgen
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        url_klassengrenzen_vaststellen_18 = self.url_klassengrenzen_vaststellen % self.comp_18.pk
        resp = self.client.post(url_klassengrenzen_vaststellen_18)
        self.assert_is_redirect_not_plein(resp)  # check for success

        self.deelkamp_bk_18 = DeelKampioenschap.objects.filter(competitie=self.comp_18,
                                                               deel=DEEL_BK)[0]
        self.deelkamp_rayon1_18 = DeelKampioenschap.objects.filter(competitie=self.comp_18,
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

        self.functie_rko1_18 = self.deelkamp_rayon1_18.functie
        self.functie_rko1_18.accounts.add(self.account_rko1_18)

        # maak nog een test vereniging, zonder HWL functie
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.ver_nr = "1100"
        ver.regio = self.regio_101
        ver.save()

    def _regioschutters_inschrijven(self):

        boog_c = BoogType.objects.get(afkorting='C')

        klasse_r = CompetitieIndivKlasse.objects.filter(boogtype__afkorting='R',
                                                        is_onbekend=False,
                                                        is_voor_rk_bk=True)[0]

        klasse_c = CompetitieIndivKlasse.objects.filter(boogtype__afkorting='C',
                                                        is_onbekend=False,
                                                        is_voor_rk_bk=True)[0]

        # recurve, lid 1
        RegioCompetitieSporterBoog(deelcompetitie=self.deelcomp_regio_101,
                                   sporterboog=self.sporterboog,
                                   bij_vereniging=self.sporterboog.sporter.bij_vereniging,
                                   indiv_klasse=klasse_r,
                                   aantal_scores=7).save()

        # compound, lid 1
        sporterboog = SporterBoog(sporter=self.lid_sporter_1,
                                  boogtype=boog_c,
                                  voor_wedstrijd=True)
        sporterboog.save()

        RegioCompetitieSporterBoog(deelcompetitie=self.deelcomp_regio_101,
                                   sporterboog=sporterboog,
                                   bij_vereniging=sporterboog.sporter.bij_vereniging,
                                   indiv_klasse=klasse_c,
                                   aantal_scores=6).save()

        # compound, lid2
        sporterboog = SporterBoog(sporter=self.lid_sporter_2,
                                  boogtype=boog_c,
                                  voor_wedstrijd=True)
        sporterboog.save()

        RegioCompetitieSporterBoog(deelcompetitie=self.deelcomp_regio_101,
                                   sporterboog=sporterboog,
                                   bij_vereniging=sporterboog.sporter.bij_vereniging,
                                   indiv_klasse=klasse_c,
                                   aantal_scores=6).save()

    def test_doorzetten_naar_rk(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        url = self.url_doorzetten_rk % self.comp_18.pk

        # fase F: pagina zonder knop 'doorzetten'
        zet_competitie_fase(self.comp_18, 'F')
        self.comp_18.bepaal_fase()
        self.assertEqual(self.comp_18.fase, 'F')

        # zet een deelcompetitie die geen team competitie organiseert
        self.deelcomp_regio_101.regio_organiseert_teamcompetitie = False
        self.deelcomp_regio_101.save(update_fields=['regio_organiseert_teamcompetitie'])

        # zet een deelcompetitie team ronde > 7
        self.deelcomp_regio_105.huidige_team_ronde = 8
        self.deelcomp_regio_105.save(update_fields=['huidige_team_ronde'])

        # status ophalen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bko-doorzetten-naar-rk.dtl', 'plein/site_layout.dtl'))

        # sluit alle deelcompetitie regio
        for obj in DeelCompetitie.objects.filter(competitie=self.comp_18,
                                                 is_afgesloten=False):
            obj.is_afgesloten = True
            obj.save()
        # for

        # fase G: pagina met knop 'doorzetten'
        zet_competitie_fase(self.comp_18, 'G')
        self.comp_18.bepaal_fase()
        self.assertEqual(self.comp_18.fase, 'G')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bko-doorzetten-naar-rk.dtl', 'plein/site_layout.dtl'))

        # nu echt doorzetten
        self._regioschutters_inschrijven()

        self.assertEqual(3, RegioCompetitieSporterBoog.objects.count())
        self.assertEqual(0, KampioenschapSporterBoog.objects.count())

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, '/bondscompetities/')       # redirect = Success

        # laat de mutatie verwerken
        management.call_command('regiocomp_mutaties', '1', '--quick', stderr=io.StringIO(), stdout=io.StringIO())

        self.assertEqual(3, KampioenschapSporterBoog.objects.count())

        # verkeerde competitie/BKO
        resp = self.client.get(self.url_doorzetten_rk % self.comp_25.pk)
        self.assert404(resp, 'Verkeerde competitie')

    def test_doorzetten_rk_geen_lid(self):
        # variant van doorzetten_rk met een lid dat niet meer bij een vereniging aangesloten is
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        # fase F: pagina zonder knop 'doorzetten'
        zet_competitie_fase(self.comp_18, 'F')

        # sluit alle deelcompetitie regio
        for obj in DeelCompetitie.objects.filter(competitie=self.comp_18,
                                                 is_afgesloten=False):
            obj.is_afgesloten = True
            obj.save()
        # for

        # fase G: pagina met knop 'doorzetten'
        zet_competitie_fase(self.comp_18, 'G')

        # nu echt doorzetten
        self._regioschutters_inschrijven()

        self.assertEqual(3, RegioCompetitieSporterBoog.objects.count())
        self.assertEqual(0, KampioenschapSporterBoog.objects.count())

        self.lid_sporter_2.bij_vereniging = None
        self.lid_sporter_2.save()

        url = self.url_doorzetten_rk % self.comp_18.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, '/bondscompetities/')       # redirect = Success

        # laat de mutatie verwerken
        management.call_command('regiocomp_mutaties', '1', '--quick', stderr=io.StringIO(), stdout=io.StringIO())

        # het lid zonder vereniging komt NIET in de RK selectie
        self.assertEqual(2, KampioenschapSporterBoog.objects.count())

        # verdere tests in test_planning_rayon.test_geen_vereniging check

    def test_doorzetten_naar_bk(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        url = self.url_doorzetten_bk % self.comp_18.pk

        # fase M: pagina zonder knop 'doorzetten'
        zet_competitie_fase(self.comp_18, 'M')
        self.comp_18.bepaal_fase()
        self.assertEqual(self.comp_18.fase, 'M')

        # zet een rayon met status 'afgesloten'
        self.deelkamp_rayon1_18.is_afgesloten = True
        self.deelkamp_rayon1_18.save(update_fields=['is_afgesloten'])

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bko-doorzetten-naar-bk.dtl', 'plein/site_layout.dtl'))

        # alle rayonkampioenschappen afsluiten
        for obj in DeelKampioenschap.objects.filter(competitie=self.comp_18,
                                                    is_afgesloten=False,
                                                    deel=DEEL_RK):
            obj.is_afgesloten = True
            obj.save()
        # for

        # fase N: pagina met knop 'doorzetten'
        zet_competitie_fase(self.comp_18, 'N')
        self.comp_18.bepaal_fase()
        self.assertEqual(self.comp_18.fase, 'N')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bko-doorzetten-naar-bk.dtl', 'plein/site_layout.dtl'))

        # nu echt doorzetten
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, '/bondscompetities/')       # redirect = Success

        self.assertTrue(str(self.deelkamp_bk_18) != '')

        deelkamp_bk_18 = DeelKampioenschap.objects.get(competitie=self.comp_18,
                                                       deel=DEEL_BK)
        objs = KampioenschapSporterBoog.objects.filter(kampioenschap=deelkamp_bk_18)
        self.assertEqual(objs.count(), 0)       # worden nog niet gemaakt, dus 0

    def test_bad(self):
        # moet BKO zijn
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        resp = self.client.get(self.url_doorzetten_rk % 999999)
        self.assert403(resp)

        resp = self.client.get(self.url_doorzetten_bk % 999999)
        self.assert403(resp)

        # niet bestaande comp_pk
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        resp = self.client.get(self.url_doorzetten_rk % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.post(self.url_doorzetten_rk % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.get(self.url_doorzetten_bk % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.post(self.url_doorzetten_bk % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.get(self.url_doorzetten_voorbij_bk % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.post(self.url_doorzetten_voorbij_bk % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        # juiste comp_pk maar verkeerde fase
        zet_competitie_fase(self.comp_18, 'C')
        resp = self.client.get(self.url_doorzetten_rk % self.comp_18.pk)
        self.assert404(resp, 'Verkeerde competitie fase')

        resp = self.client.post(self.url_doorzetten_rk % self.comp_18.pk)
        self.assert404(resp, 'Verkeerde competitie fase')

        resp = self.client.get(self.url_doorzetten_bk % self.comp_18.pk)
        self.assert404(resp, 'Verkeerde competitie fase')

        resp = self.client.post(self.url_doorzetten_bk % self.comp_18.pk)
        self.assert404(resp, 'Verkeerde competitie fase')

        resp = self.client.get(self.url_doorzetten_voorbij_bk % self.comp_18.pk)
        self.assert404(resp, 'Verkeerde competitie fase')

        resp = self.client.post(self.url_doorzetten_voorbij_bk % self.comp_18.pk)
        self.assert404(resp, 'Verkeerde competitie fase')

    def test_doorzetten_voorbij_bk(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        zet_competitie_fase(self.comp_18, 'R')
        self.comp_18.bepaal_fase()
        self.assertEqual(self.comp_18.fase, 'R')

        url = self.url_doorzetten_voorbij_bk % self.comp_18.pk

        # pagina ophalen
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bko-doorzetten-voorbij-bk.dtl', 'plein/site_layout.dtl'))

        # verkeerde BKO
        self.e2e_wissel_naar_functie(self.functie_bko_25)
        resp = self.client.get(url)
        self.assert403(resp)
        resp = self.client.post(url)
        self.assert403(resp)

        # echt doorzetten
        self.e2e_wissel_naar_functie(self.functie_bko_18)
        resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_competitie_overzicht % self.comp_18.pk)

    def test_rk_bk_klassengrenzen(self):
        # maak een paar teams aan
        self.testdata.maak_voorinschrijvingen_rk_teamcompetitie(25, self.nhbver_101.ver_nr, ook_incomplete_teams=False)
        self.testdata.geef_rk_team_tijdelijke_sporters_genoeg_scores(25, self.nhbver_101.ver_nr)

        # als BKO doorzetten naar RK fase (G --> J) en bepaal de klassengrenzen (fase J --> K)
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_bko)
        zet_competitie_fase(self.testdata.comp25, 'G')

        url = self.url_teams_klassengrenzen_vaststellen % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')
        resp = self.client.post(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_teams_klassengrenzen_vaststellen % self.testdata.comp25.pk
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet in de juiste fase')
        resp = self.client.post(url)
        self.assert404(resp, 'Competitie niet in de juiste fase')

        url = self.url_doorzetten_rk % self.testdata.comp25.pk
        resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)
        self.verwerk_regiocomp_mutaties()

        comp = Competitie.objects.get(pk=self.testdata.comp25.pk)
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'J')

        url = self.url_teams_klassengrenzen_vaststellen % self.testdata.comp25.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp,
                                  ('compbeheer/bko-klassengrenzen-vaststellen-rk-bk-teams.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        url = self.url_teams_klassengrenzen_vaststellen % self.testdata.comp25.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        resp = self.client.get(url)
        self.assert404(resp, 'De klassengrenzen zijn al vastgesteld')
        resp = self.client.post(url)
        self.assert404(resp, 'De klassengrenzen zijn al vastgesteld')


# end of file
