# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.models import Competitie, DeelCompetitie, RegioCompetitieSchutterBoog, LAAG_REGIO, LAAG_RK, LAAG_BK
from Competitie.operations import competities_aanmaken
from Competitie.test_fase import zet_competitie_fase
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestCompInschrijvenAangemeld(E2EHelpers, TestCase):

    """ tests voor de CompInfra applicatie, Aangemeld functie """

    test_after = ('Functie',)

    url_wijzigdatums = '/bondscompetities/%s/wijzig-datums/'  # comp_pk
    url_aangemeld_alles = '/bondscompetities/deelnemen/%s/lijst-regiocompetitie/alles/'  # comp_pk
    url_aangemeld_rayon = '/bondscompetities/deelnemen/%s/lijst-regiocompetitie/rayon-%s/'  # comp_pk, rayon_pk
    url_aangemeld_regio = '/bondscompetities/deelnemen/%s/lijst-regiocompetitie/regio-%s/'  # comp_pk, regio_pk

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
        sporter.bij_vereniging = self._ver
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

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self._ver = ver

        # maak HWL functie aan voor deze vereniging
        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_bko = self._prep_beheerder_lid('BKO')
        self.account_rko = self._prep_beheerder_lid('RKO')
        self.account_rcl = self._prep_beheerder_lid('RCL')
        self.account_schutter = self._prep_beheerder_lid('Schutter')

        # creëer een competitie met deelcompetities
        competities_aanmaken(jaar=2019)
        # nu in fase A

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        for deelcomp in DeelCompetitie.objects.filter(laag=LAAG_BK).all():
            deelcomp.functie.accounts.add(self.account_bko)
        # for

        for deelcomp in DeelCompetitie.objects.filter(laag=LAAG_RK, nhb_rayon=self.rayon_2).all():
            deelcomp.functie.accounts.add(self.account_rko)
        # for

        for deelcomp in DeelCompetitie.objects.filter(laag=LAAG_REGIO, nhb_regio=self.regio_101).all():
            deelcomp.functie.accounts.add(self.account_rcl)
        # for

        # maak nog een test vereniging, zonder HWL functie
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.ver_nr = "1100"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self._ver2 = ver

        # maak HWL functie aan voor deze vereniging
        hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        hwl.nhb_ver = ver
        hwl.save()

    def _doe_inschrijven(self, comp):

        url_inschrijven = '/bondscompetities/deelnemen/leden-aanmelden/%s/' % comp.pk

        # meld een bak leden aan voor de competitie
        self.e2e_wisselnaarrol_bb()

        # klassengrenzen vaststellen
        url_klassengrenzen = '/bondscompetities/%s/klassengrenzen/vaststellen/'
        with self.assert_max_queries(97):
            resp = self.client.post(url_klassengrenzen % self.comp_18.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        with self.assert_max_queries(97):
            resp = self.client.post(url_klassengrenzen % self.comp_25.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        # nu in fase A2

        # zet de datum voor inschrijven op vandaag
        for comp in Competitie.objects.filter(is_afgesloten=False):
            zet_competitie_fase(comp, 'B')
        # for

        lid_nr = 110000
        recurve_boog_pk = BoogType.objects.get(afkorting='R').pk
        compound_boog_pk = BoogType.objects.get(afkorting='C').pk
        barebow_boog_pk = BoogType.objects.get(afkorting='BB').pk

        # doorloop de 2 verenigingen in deze regio
        for nhb_ver in NhbVereniging.objects.filter(regio=self.regio_101):
            # wordt HWL om voorkeuren aan te kunnen passen en in te kunnen schrijven
            functie_hwl = nhb_ver.functie_set.filter(rol='HWL').all()[0]
            self.e2e_wissel_naar_functie(functie_hwl)

            post_params = dict()

            # maak 3 leden aan
            for lp in range(3):
                lid_nr += 1
                sporter = Sporter()
                sporter.lid_nr = lid_nr
                sporter.voornaam = "Lid %s" % lid_nr
                sporter.achternaam = "de Tester"
                sporter.bij_vereniging = nhb_ver
                sporter.is_actief_lid = True
                if barebow_boog_pk:
                    sporter.geboorte_datum = datetime.date(2019-12, 1, 1)   # aspirant
                else:
                    sporter.geboorte_datum = datetime.date(2000, 1, 1)      # senior
                sporter.sinds_datum = datetime.date(2010, 1, 1)
                sporter.geslacht = 'M'
                sporter.save()

                # haal de sporter voorkeuren op, zodat de sporterboog records aangemaakt worden
                url_voorkeuren = '/sporter/voorkeuren/%s/' % lid_nr
                with self.assert_max_queries(20):
                    resp = self.client.get(url_voorkeuren)
                self.assertEqual(resp.status_code, 200)     # 200 = OK

                # zet de recurve boog aan
                if lp == 1:
                    # zet de DT voorkeur aan voor een paar sporters
                    with self.assert_max_queries(25):
                        resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_R': 'on',
                                                                 'voorkeur_eigen_blazoen': 'on'})
                    # onthoud deze sporterboog om straks in bulk aan te melden
                    # 'lid_NNNNNN_boogtype_MM'
                    post_params['lid_%s_boogtype_%s' % (lid_nr, recurve_boog_pk)] = 'on'
                elif lp == 2:
                    with self.assert_max_queries(25):
                        resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_C': 'on'})
                    post_params['lid_%s_boogtype_%s' % (lid_nr, compound_boog_pk)] = 'on'
                elif barebow_boog_pk:
                    with self.assert_max_queries(25):
                        resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_BB': 'on'})
                    post_params['lid_%s_boogtype_%s' % (lid_nr, barebow_boog_pk)] = 'on'
                    barebow_boog_pk = None
                else:
                    with self.assert_max_queries(25):
                        resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_R': 'on'})
                    post_params['lid_%s_boogtype_%s' % (lid_nr, recurve_boog_pk)] = 'on'

                self.assert_is_redirect_not_plein(resp)         # check for success
            # for

            # schrijf in voor de competitie
            with self.assert_max_queries(22):
                resp = self.client.post(url_inschrijven, post_params)
            self.assert_is_redirect_not_plein(resp)         # check for success
        # for

    def test_overzicht_anon(self):
        comp = Competitie.objects.all()[0]

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aangemeld_alles % comp.pk)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aangemeld_rayon % (comp.pk, self.rayon_2.pk))
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aangemeld_regio % (comp.pk, self.regio_101.pk))
        self.assert403(resp)

    def test_overzicht_bb(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)

        comp = Competitie.objects.all()[0]
        self._doe_inschrijven(comp)         # wisselt naar HWL rol
        self.e2e_wisselnaarrol_bb()

        # landelijk
        url = self.url_aangemeld_alles % comp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # rayon 2
        url = self.url_aangemeld_rayon % (comp.pk, self.rayon_1.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # regio 101
        url = self.url_aangemeld_regio % (comp.pk, self.regio_101.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # verkeerde fase
        zet_competitie_fase(comp, 'Z')
        url = self.url_aangemeld_alles % comp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie fase')

        url = self.url_aangemeld_rayon % (comp.pk, self.rayon_1.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie fase')

        url = self.url_aangemeld_regio % (comp.pk, self.regio_101.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie fase')

        # regio 100: niet bestaand als deelcompetitie
        url = self.url_aangemeld_regio % (comp.pk, 100)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie fase')

        # coverage voor models __str__
        obj = RegioCompetitieSchutterBoog.objects.filter(deelcompetitie__laag=LAAG_REGIO).all()[0]
        self.assertTrue(str(obj) != '')

        deelcomp = obj.deelcompetitie
        deelcomp.laag = LAAG_RK
        deelcomp.nhb_regio = None
        deelcomp.nhb_rayon = self.rayon_1
        deelcomp.save()
        obj = RegioCompetitieSchutterBoog.objects.filter(deelcompetitie__laag=LAAG_RK).all()[0]
        self.assertTrue(str(obj) != '')

        deelcomp = obj.deelcompetitie
        deelcomp.laag = LAAG_BK
        deelcomp.nhb_rayon = None
        deelcomp.save()
        obj = RegioCompetitieSchutterBoog.objects.filter(deelcompetitie__laag=LAAG_BK).all()[0]
        self.assertTrue(str(obj) != '')

    def test_overzicht_bko(self):
        comp = Competitie.objects.get(afstand='18')
        functie_bko = DeelCompetitie.objects.get(competitie=comp, laag=LAAG_BK).functie

        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self._doe_inschrijven(comp)         # wisselt naar HWL rol
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(functie_bko)

        # landelijk
        url = self.url_aangemeld_alles % comp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # rayon 2
        url = self.url_aangemeld_rayon % (comp.pk, self.rayon_2.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # regio 101
        url = self.url_aangemeld_regio % (comp.pk, self.regio_101.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

    def test_overzicht_rko(self):
        comp = Competitie.objects.get(afstand='25')
        functie_rko = DeelCompetitie.objects.get(competitie=comp, laag=LAAG_RK, nhb_rayon=self.rayon_2).functie

        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self._doe_inschrijven(comp)         # wisselt naar HWL rol
        self.e2e_login_and_pass_otp(self.account_rko)
        self.e2e_wissel_naar_functie(functie_rko)

        # landelijk
        url = self.url_aangemeld_alles % comp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # rayon 2
        url = self.url_aangemeld_rayon % (comp.pk, self.rayon_2.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # regio 101
        url = self.url_aangemeld_regio % (comp.pk, self.regio_101.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

    def test_overzicht_rcl(self):
        comp = Competitie.objects.get(afstand='18')
        functie_rcl = DeelCompetitie.objects.get(competitie=comp, laag=LAAG_REGIO, nhb_regio=self.regio_101).functie

        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self._doe_inschrijven(comp)         # wisselt naar HWL rol
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(functie_rcl)

        # landelijk
        url = self.url_aangemeld_alles % comp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # rayon 2
        url = self.url_aangemeld_rayon % (comp.pk, self.rayon_2.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # regio 101
        url = self.url_aangemeld_regio % (comp.pk, self.regio_101.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

    def test_bad_rcl(self):
        comp = Competitie.objects.get(afstand='25')
        functie_rcl = DeelCompetitie.objects.get(competitie=comp,
                                                 laag=LAAG_REGIO,
                                                 nhb_regio=self.regio_101).functie

        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(functie_rcl)

        # bad keys
        url = self.url_aangemeld_alles % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_aangemeld_rayon % (999999, 999999)
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_aangemeld_rayon % (comp.pk, 999999)
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie fase')

        url = self.url_aangemeld_regio % (999999, 999999)
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_aangemeld_regio % (comp.pk, 999999)
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie fase')

    @staticmethod
    def _vind_tabel_regel_met(resp, zoekterm):
        regel = None
        content = str(resp.content)

        pos = content.find(zoekterm)
        if pos >= 0:
            content = content[pos-200:pos+200]

            pos = content.find('<tr>')
            while pos >= 0:
                content = content[pos:]
                pos = content.find('</tr>')
                regel = content[:pos]
                if zoekterm in regel:
                    pos = -1        # exits while loop
                else:
                    content = content[pos:]
                    pos = content.find('<tr>')
            # while

        return regel

    def test_verander_vereniging(self):
        # verander 1 sporterboog naar een andere verenigingen
        # en laat zien dat de oude vereniging blijft staan in de inschrijven
        self.e2e_login_and_pass_otp(self.testdata.account_bb)

        comp = Competitie.objects.get(afstand='18')
        self._doe_inschrijven(comp)         # wisselt naar HWL rol

        # wissel naar RCL rol
        functie_rcl = DeelCompetitie.objects.get(competitie=comp,
                                                 laag=LAAG_REGIO,
                                                 nhb_regio=self.regio_101).functie
        self.e2e_wissel_naar_functie(functie_rcl)

        inschrijving = RegioCompetitieSchutterBoog.objects.filter(bij_vereniging=self._ver).all()[0]
        naam_str = "[" + str(inschrijving.sporterboog.sporter.lid_nr) + "] " + inschrijving.sporterboog.sporter.volledige_naam()
        ver_str = str(self._ver)            # [ver_nr] Vereniging

        # controleer dat de schutter bij de juiste vereniging staat
        url = self.url_aangemeld_alles % inschrijving.deelcompetitie.competitie.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        regel = self._vind_tabel_regel_met(resp, naam_str)
        self.assertTrue(ver_str in regel)

        self.assertEqual(None, self._vind_tabel_regel_met(resp, 'dit staat er for sure niet in'))

        # schrijf de schutter over naar een andere vereniging
        sporter = inschrijving.sporterboog.sporter
        sporter.bij_vereniging = self._ver2
        sporter.save()

        # controleer dat de schutter nog steeds bij dezelfde vereniging staat
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        regel = self._vind_tabel_regel_met(resp, naam_str)
        self.assertTrue(ver_str in regel)


# end of file
