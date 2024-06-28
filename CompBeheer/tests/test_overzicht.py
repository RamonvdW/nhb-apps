# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.definities import DEEL_RK, DEEL_BK
from Competitie.models import Competitie, Regiocompetitie, RegiocompetitieSporterBoog, Kampioenschap
from Competitie.operations import competities_aanmaken
from Competitie.test_utils.tijdlijn import zet_competitie_fase_regio_inschrijven
from Functie.tests.helpers import maak_functie
from Geo.models import Rayon, Regio
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime


class TestCompBeheerOverzicht(E2EHelpers, TestCase):

    """ tests voor de CompBeheer applicatie, Overzicht pagina """

    test_after = ('Functie',)

    url_kies = '/bondscompetities/'
    url_overzicht = '/bondscompetities/%s/'                     # comp_pk
    url_tijdlijn = '/bondscompetities/beheer/%s/tijdlijn/'      # comp_pk
    url_overzicht_beheer = '/bondscompetities/beheer/%s/'       # comp_pk
    url_aangemeld_alles = '/bondscompetities/deelnemen/%s/lijst-regiocompetitie/alles/'  # comp_pk

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()

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
                    bij_vereniging=self._ver)
        sporter.save()

        return self.e2e_create_account(lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self._next_lid_nr = 100001

        self.rayon_1 = Rayon.objects.get(rayon_nr=1)
        self.rayon_2 = Rayon.objects.get(rayon_nr=2)
        self.regio_101 = Regio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = Vereniging(
                    ver_nr="1000",
                    naam="Grote Club",
                    regio=self.regio_101)
        ver.save()
        self._ver = ver

        # maak functie HWL aan voor deze vereniging
        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_bko = self._prep_beheerder_lid('BKO')
        self.account_rko = self._prep_beheerder_lid('RKO')
        self.account_rcl = self._prep_beheerder_lid('RCL')
        self.account_schutter = self._prep_beheerder_lid('Schutter')

        # creëer een competitie met regiocompetities
        competities_aanmaken(jaar=2019)
        # nu in fase A

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        for deelkamp in Kampioenschap.objects.filter(deel=DEEL_BK).all():
            deelkamp.functie.accounts.add(self.account_bko)
        # for

        for deelkamp in Kampioenschap.objects.filter(deel=DEEL_RK, rayon=self.rayon_2).all():
            deelkamp.functie.accounts.add(self.account_rko)
        # for

        for deelcomp in Regiocompetitie.objects.filter(regio=self.regio_101).all():
            deelcomp.functie.accounts.add(self.account_rcl)
        # for

        # maak nog een test vereniging, zonder HWL functie
        ver = Vereniging(
                    naam="Kleine Club",
                    ver_nr=1100,
                    regio=self.regio_101)
        ver.save()
        self._ver2 = ver

        # maak functie HWL aan voor deze vereniging
        hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        hwl.vereniging = ver
        hwl.save()

    def _zet_competities_naar_fase_b(self):
        # meld een bak leden aan voor de competitie
        self.e2e_wisselnaarrol_bb()

        # klassengrenzen vaststellen
        url_klassengrenzen = '/bondscompetities/beheer/%s/klassengrenzen-vaststellen/'
        with self.assert_max_queries(97):
            resp = self.client.post(url_klassengrenzen % self.comp_18.pk)
            self.assert_is_redirect_not_plein(resp)  # check for success
        with self.assert_max_queries(97):
            resp = self.client.post(url_klassengrenzen % self.comp_25.pk)
            self.assert_is_redirect_not_plein(resp)  # check for success
        # nu in fase A2

        # zet de datum voor inschrijven op vandaag
        for comp in Competitie.objects.filter(is_afgesloten=False):
            zet_competitie_fase_regio_inschrijven(comp)
        # for

    def _maak_leden_met_voorkeuren(self):
        lid_nr = 110000
        do_barebow = True

        # doorloop de 2 verenigingen in deze regio
        for ver in Vereniging.objects.filter(regio=self.regio_101):
            # wordt HWL om voorkeuren aan te kunnen passen en in te kunnen schrijven
            functie_hwl = ver.functie_set.filter(rol='HWL').first()
            self.e2e_wissel_naar_functie(functie_hwl)

            # maak 3 leden aan
            for lp in range(3):
                lid_nr += 1
                sporter = Sporter(
                            lid_nr=lid_nr,
                            voornaam="Lid %s" % lid_nr,
                            achternaam="de Tester",
                            bij_vereniging=ver,
                            is_actief_lid=True,
                            sinds_datum=datetime.date(2010, 1, 1),
                            geboorte_datum=datetime.date(2000, 1, 1),     # senior
                            geslacht='M')
                if do_barebow:
                    sporter.geboorte_datum = datetime.date(2019 - 12, 1, 1)  # aspirant
                sporter.save()

                url_voorkeuren = '/sporter/voorkeuren/%s/' % lid_nr

                # zet de juiste boog 'aan' voor wedstrijden
                if lp == 1:
                    # zet de voorkeur voor eigen blazoen aan voor een paar sporters
                    resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                             'schiet_R': 'on',
                                                             'voorkeur_eigen_blazoen': 'on'})
                elif lp == 2:
                    resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                             'schiet_C': 'on'})
                elif do_barebow:
                    resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                             'schiet_BB': 'on'})
                    do_barebow = False
                else:
                    resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                             'schiet_R': 'on'})

                self.assert_is_redirect_not_plein(resp)  # check for success
            # for
        # for

    def _doe_inschrijven(self, comp):
        url_inschrijven = '/bondscompetities/deelnemen/leden-aanmelden/%s/' % comp.pk

        lid_nr = 110000
        recurve_boog_pk = BoogType.objects.get(afkorting='R').pk
        compound_boog_pk = BoogType.objects.get(afkorting='C').pk
        barebow_boog_pk = BoogType.objects.get(afkorting='BB').pk

        # doorloop de 2 verenigingen in deze regio
        for ver in Vereniging.objects.filter(regio=self.regio_101):
            # wordt HWL om voorkeuren aan te kunnen passen en in te kunnen schrijven
            functie_hwl = ver.functie_set.filter(rol='HWL').first()
            self.e2e_wissel_naar_functie(functie_hwl)

            post_params = dict()

            # maak 3 leden aan
            for lp in range(3):
                lid_nr += 1

                # zet de recurve boog aan
                if lp == 1:
                    # onthoud deze sporterboog om straks in bulk aan te melden
                    # 'lid_NNNNNN_boogtype_MM'
                    post_params['lid_%s_boogtype_%s' % (lid_nr, recurve_boog_pk)] = 'on'
                elif lp == 2:
                    post_params['lid_%s_boogtype_%s' % (lid_nr, compound_boog_pk)] = 'on'
                elif barebow_boog_pk:
                    post_params['lid_%s_boogtype_%s' % (lid_nr, barebow_boog_pk)] = 'on'
                    barebow_boog_pk = None
                else:
                    post_params['lid_%s_boogtype_%s' % (lid_nr, recurve_boog_pk)] = 'on'
            # for

            # schrijf in voor de competitie
            with self.assert_max_queries(29):
                resp = self.client.post(url_inschrijven, post_params)
            self.assert_is_redirect_not_plein(resp)         # check for success
        # for

    def test_kies_anon(self):
        url = self.url_kies
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/kies.dtl', 'plein/site_layout.dtl'))
        self.e2e_assert_other_http_commands_not_supported(url)

    def test_overzicht(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        comp18 = Competitie.objects.get(afstand='18')
        comp25 = Competitie.objects.get(afstand='25')

        # statistiek voor de BB met 0 deelnemers
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kies)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/kies.dtl', 'plein/site_layout.dtl'))

        self._zet_competities_naar_fase_b()
        self._maak_leden_met_voorkeuren()
        self._doe_inschrijven(comp18)         # wisselt naar HWL rol
        self._doe_inschrijven(comp25)         # wisselt naar HWL rol

        # BB
        self.e2e_wisselnaarrol_bb()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht.dtl', 'plein/site_layout.dtl'))

        self.e2e_wisselnaarrol_bb()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht_beheer % comp18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/overzicht.dtl', 'plein/site_layout.dtl'))

        # bad
        resp = self.client.get(self.url_overzicht_beheer % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        # BKO 18m
        deelkamp = Kampioenschap.objects.get(competitie=comp18, deel=DEEL_BK)
        functie_bko = deelkamp.functie
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(functie_bko)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht_beheer % comp18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/overzicht.dtl', 'plein/site_layout.dtl'))

        # RKO 25m Rayon 2
        deelkamp = Kampioenschap.objects.get(competitie=comp25, deel=DEEL_RK, rayon=self.rayon_2)
        functie_rko = deelkamp.functie
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_login_and_pass_otp(self.account_rko)
        self.e2e_wissel_naar_functie(functie_rko)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht_beheer % comp25.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/overzicht.dtl', 'plein/site_layout.dtl'))

        # RCL
        deelcomp = Regiocompetitie.objects.get(competitie=comp18, regio=self.regio_101)
        functie_rcl = deelcomp.functie
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(functie_rcl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht_beheer % comp18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/overzicht.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_tijdlijn % comp18.pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/tijdlijn.dtl', 'plein/site_layout.dtl'))

        # HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_tijdlijn % comp18.pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/tijdlijn.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_tijdlijn % comp25.pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/tijdlijn.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_tijdlijn % 'x')
        self.assert404(resp, 'Competitie niet gevonden')

        # TODO: add WL

        # coverage voor models __str__
        obj = RegiocompetitieSporterBoog.objects.first()
        self.assertTrue(str(obj) != '')

# end of file
