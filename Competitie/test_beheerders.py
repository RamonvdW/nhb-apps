# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Functie.models import maak_functie, Functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
from Competitie.models import RegioCompetitieSchutterBoog
from .models import (Competitie, DeelCompetitie, competitie_aanmaken,
                     INSCHRIJF_METHODE_3, DAGDEEL_AFKORTINGEN, LAAG_REGIO, LAAG_RK, LAAG_BK)
import datetime


class TestCompetitieBeheerders(E2EHelpers, TestCase):

    """ unit tests voor de Competitie applicatie, Koppel Beheerders functie """

    test_after = ('Competitie.test_planning',)

    def _prep_beheerder_lid(self, voornaam):
        nhb_nr = self._next_nhbnr
        self._next_nhbnr += 1

        lid = NhbLid()
        lid.nhb_nr = nhb_nr
        lid.geslacht = "M"
        lid.voornaam = voornaam
        lid.achternaam = "Tester"
        lid.email = voornaam.lower() + "@nhb.test"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = self._ver
        lid.save()

        return self.e2e_create_account(nhb_nr, lid.email, lid.voornaam, accepteer_vhpg=True)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.account_admin = self.e2e_create_account_admin()

        self._next_nhbnr = 100001

        self.rayon_1 = NhbRayon.objects.get(rayon_nr=1)
        self.rayon_2 = NhbRayon.objects.get(rayon_nr=2)
        self.regio_101 = NhbRegio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self._ver = ver

        # maak HWL functie aan voor deze vereniging
        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.nhb_nr, "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        # maak een BB aan (geen NHB lid)
        self.account_bb = self.e2e_create_account('bb', 'bko@nhb.test', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_bko = self._prep_beheerder_lid('BKO')
        self.account_rko = self._prep_beheerder_lid('RKO')
        self.account_rcl = self._prep_beheerder_lid('RCL')
        self.account_schutter = self._prep_beheerder_lid('Schutter')

        # creëer een competitie met deelcompetities
        competitie_aanmaken(jaar=2019)

        self.functie_bko = DeelCompetitie.objects.filter(laag=LAAG_BK)[0].functie
        self.functie_rko = DeelCompetitie.objects.filter(laag=LAAG_RK, nhb_rayon=self.rayon_2)[0].functie
        self.functie_rcl = DeelCompetitie.objects.filter(laag=LAAG_REGIO, nhb_regio=self.regio_101)[0].functie

        self.functie_bko.accounts.add(self.account_bko)
        self.functie_rko.accounts.add(self.account_rko)
        self.functie_rcl.accounts.add(self.account_rcl)

        # maak nog een test vereniging, zonder HWL functie
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.nhb_nr = "1100"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self._ver2 = ver

        # maak HWL functie aan voor deze vereniging
        hwl = maak_functie("HWL Vereniging %s" % ver.nhb_nr, "HWL")
        hwl.nhb_ver = ver
        hwl.save()

        self.url_overzicht = '/competitie/'
        self.url_wijzigdatums = '/competitie/wijzig-datums/%s/'
        self.url_aangemeld_alles = '/competitie/lijst-regiocompetitie/%s/alles/'  # % comp_pk
        self.url_aangemeld_rayon = '/competitie/lijst-regiocompetitie/%s/rayon-%s/'  # % comp_pk, rayon_pk
        self.url_aangemeld_regio = '/competitie/lijst-regiocompetitie/%s/regio-%s/'  # % comp_pk, regio_pk
        self.url_behoefte = '/competitie/lijst-regiocompetitie/%s/regio-%s/dagdeel-behoefte/'  # comp_pk, regio_pk
        self.url_behoefte_bestand = '/competitie/lijst-regiocompetitie/%s/regio-%s/dagdeel-behoefte-als-bestand/'  # comp_pk, regio_pk

    def _doe_inschrijven(self, comp):
        # meld een bak leden aan voor de competitie

        url_inschrijven = '/vereniging/leden-inschrijven/competitie/%s/' % comp.pk

        self.e2e_wisselnaarrol_bb()

        # klassegrenzen vaststellen
        url_klassegrenzen_18 = '/competitie/klassegrenzen/vaststellen/18/'
        url_klassegrenzen_25 = '/competitie/klassegrenzen/vaststellen/25/'
        resp = self.client.post(url_klassegrenzen_18)
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect = succes
        resp = self.client.post(url_klassegrenzen_25)
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect = succes

        # zet de inschrijfmethode van regio 101 op 'methode 3', oftewel met dagdeel voorkeur
        deelcomp = DeelCompetitie.objects.filter(laag='Regio', nhb_regio=self.regio_101, competitie=comp)[0]
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_3
        deelcomp.save()

        dagdelen = list(DAGDEEL_AFKORTINGEN)
        nhb_nr = 110000

        recurve_boog_pk = BoogType.objects.get(afkorting='R').pk

        # doorloop alle verenigingen in deze regio (er zijn er maar 2)
        for nhb_ver in NhbVereniging.objects.filter(regio=self.regio_101).all()[:5]:

            # wordt HWL om voorkeuren aan te kunnen passen en in te kunnen schrijven
            functie_hwl = nhb_ver.functie_set.filter(rol='HWL').all()[0]
            self.e2e_wissel_naar_functie(functie_hwl)

            post_params = dict()

            # maak net zoveel leden aan als er dagdeel afkortingen zijn (5 dus)
            for lp in range(5):
                nhb_nr += 1
                lid = NhbLid()
                lid.nhb_nr = nhb_nr
                lid.voornaam = "Lid %s" % nhb_nr
                lid.achternaam = "de Tester"
                lid.bij_vereniging = nhb_ver
                lid.is_actief_lid = True
                lid.geboorte_datum = datetime.date(2000, 1, 1)
                lid.sinds_datum = datetime.date(2010, 1, 1)
                lid.geslacht = 'M'
                lid.save()

                # haal de schutter voorkeuren op, zodat de schutterboog records aangemaakt worden
                url_voorkeuren = '/schutter/voorkeuren/%s/' % nhb_nr
                resp = self.client.get(url_voorkeuren)
                self.assertEqual(resp.status_code, 200)     # 200 = OK

                # zet de recurve boog aan
                resp = self.client.post(url_voorkeuren, {'nhblid_pk': nhb_nr,
                                                         'schiet_R': 'on'})
                self.assertEqual(resp.status_code, 302)     # 302 = redirect = succes

                # onthoud deze schutterboog om straks in bulk aan te melden
                # 'lid_NNNNNN_boogtype_MM'
                post_params['lid_%s_boogtype_%s' % (nhb_nr, recurve_boog_pk)] = 'on'
            # for

            # schrijf in voor de competitie
            post_params['dagdeel'] = dagdelen.pop(-1)
            resp = self.client.post(url_inschrijven, post_params)
            self.assertEqual(resp.status_code, 302)     # 302 = Redirect = succes
        # for

    def test_overzicht_anon(self):
        resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, '/competitie/beheer-favorieten/')
        self.e2e_assert_other_http_commands_not_supported(self.url_overzicht)

        comp = Competitie.objects.all()[0]

        resp = self.client.get(self.url_aangemeld_alles % comp.pk)
        self.assert_is_redirect(resp, '/plein/')

        resp = self.client.get(self.url_aangemeld_rayon % (comp.pk, self.rayon_2.pk))
        self.assert_is_redirect(resp, '/plein/')

        resp = self.client.get(self.url_aangemeld_regio % (comp.pk, self.regio_101.pk))
        self.assert_is_redirect(resp, '/plein/')

    def test_overzicht_it(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_it()

        resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht-beheerder.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, '/competitie/beheer-favorieten/')

    def test_overzicht_bb(self):
        self.e2e_login_and_pass_otp(self.account_bb)

        comp = Competitie.objects.all()[0]
        self._doe_inschrijven(comp)         # wisselt naar HWL rol
        self.e2e_wisselnaarrol_bb()

        resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht-beheerder.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, '/competitie/beheer-favorieten/')

        # landelijk
        url = self.url_aangemeld_alles % comp.pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # rayon 2
        url = self.url_aangemeld_rayon % (comp.pk, self.rayon_1.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # regio 101
        url = self.url_aangemeld_regio % (comp.pk, self.regio_101.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # regio 100: niet bestaand als deelcompetitie
        url = self.url_aangemeld_regio % (comp.pk, 100)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

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
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_bko)

        resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht-beheerder.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, '/competitie/beheer-favorieten/')

        # landelijk
        comp_pk = Competitie.objects.all()[0].pk
        url = self.url_aangemeld_alles % comp_pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # rayon 2
        url = self.url_aangemeld_rayon % (comp_pk, self.rayon_2.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # regio 101
        url = self.url_aangemeld_regio % (comp_pk, self.regio_101.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

    def test_overzicht_rko(self):
        self.e2e_login_and_pass_otp(self.account_rko)
        self.e2e_wissel_naar_functie(self.functie_rko)

        resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht-beheerder.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, '/competitie/beheer-favorieten/')

        # landelijk
        comp_pk = Competitie.objects.all()[0].pk
        url = self.url_aangemeld_alles % comp_pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # rayon 2
        url = self.url_aangemeld_rayon % (comp_pk, self.rayon_2.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # regio 101
        url = self.url_aangemeld_regio % (comp_pk, self.regio_101.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

    def test_overzicht_rcl(self):
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(self.functie_rcl)

        resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht-beheerder.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, '/competitie/beheer-favorieten/')

        # landelijk
        comp_pk = Competitie.objects.all()[0].pk
        url = self.url_aangemeld_alles % comp_pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # rayon 2
        url = self.url_aangemeld_rayon % (comp_pk, self.rayon_2.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # regio 101
        url = self.url_aangemeld_regio % (comp_pk, self.regio_101.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

    def test_overzicht_hwl(self):
        self.e2e_login_and_pass_otp(self.account_bb)        # geen account_hwl
        self.e2e_wissel_naar_functie(self.functie_hwl)

        resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht-hwl.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, '/competitie/beheer-favorieten/')

        # landelijk
        comp_pk = Competitie.objects.all()[0].pk
        url = self.url_aangemeld_alles % comp_pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # rayon 2
        url = self.url_aangemeld_rayon % (comp_pk, self.rayon_2.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # regio 101
        url = self.url_aangemeld_regio % (comp_pk, self.regio_101.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

    # TODO: add WL

    def test_wijzig_datums_not_bb(self):
        comp = Competitie.objects.all()[0]
        url = self.url_wijzigdatums % comp.pk
        resp = self.client.get(url)
        self.assert_is_redirect(resp, '/plein/')

    def test_wijzig_datums_bb(self):
        comp = Competitie.objects.all()[0]
        url = self.url_wijzigdatums % comp.pk

        self.assertEqual(datetime.date(year=2019, month=12, day=31), comp.begin_aanmeldingen)
        self.assertEqual(datetime.date(year=2019, month=12, day=31), comp.einde_aanmeldingen)
        self.assertEqual(datetime.date(year=2019, month=12, day=31), comp.einde_teamvorming)
        self.assertEqual(datetime.date(year=2019, month=12, day=31), comp.eerste_wedstrijd)

        # wordt BB
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()

        # get
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/wijzig-datums.dtl', 'plein/site_layout.dtl'))

        # post
        resp = self.client.post(url, {'datum1': '2019-08-09',
                                      'datum2': '2019-09-10',
                                      'datum3': '2019-10-11',
                                      'datum4': '2019-11-12'})
        self.assert_is_redirect(resp, self.url_overzicht)

        # controleer dat de nieuwe datums opgeslagen zijn
        comp = Competitie.objects.get(pk=comp.pk)
        self.assertEqual(datetime.date(year=2019, month=8, day=9), comp.begin_aanmeldingen)
        self.assertEqual(datetime.date(year=2019, month=9, day=10), comp.einde_aanmeldingen)
        self.assertEqual(datetime.date(year=2019, month=10, day=11), comp.einde_teamvorming)
        self.assertEqual(datetime.date(year=2019, month=11, day=12), comp.eerste_wedstrijd)

        # check corner cases

        # alle datums verplicht
        resp = self.client.post(url, {'datum1': '2019-08-09'})
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        resp = self.client.post(url, {'datum1': 'null',
                                      'datum2': 'hallo',
                                      'datum3': '0',
                                      'datum4': '2019-13-42'})
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # foute comp_pk bij get
        url = self.url_wijzigdatums % 999999
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # foute comp_pk bij post
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

    def test_behoefte(self):
        self.e2e_login_and_pass_otp(self.account_bb)        # geen account_hwl
        self.e2e_wisselnaarrol_bb()

        comp = Competitie.objects.all()[0]
        self._doe_inschrijven(comp)     # wisselt naar HWL functies
        self.e2e_wissel_naar_functie(self.functie_rcl)

        resp = self.client.get(self.url_behoefte % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/inschrijfmethode3-behoefte.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_behoefte_bestand % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        csv_file = "ver_nr,Naam,Geen voorkeur,'s Avonds,Zaterdag,Zondag,Weekend\r\n1000,Grote Club,0,0,0,0,5\r\n1100,Kleine Club,0,0,0,5,0\r\n"
        self.assertContains(resp, csv_file)

        # creëer een beetje puinhoop
        self._ver2.regio = NhbRegio.objects.get(pk=102)
        self._ver2.save()

        obj = RegioCompetitieSchutterBoog.objects.filter(bij_vereniging=self._ver).all()[0]
        obj.inschrijf_voorkeur_dagdeel = 'XX'
        obj.save()

        resp = self.client.get(self.url_behoefte % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/inschrijfmethode3-behoefte.dtl', 'plein/site_layout.dtl'))

    def test_bad_hwl(self):
        self.e2e_login_and_pass_otp(self.account_bb)        # geen account_hwl
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # landelijk
        comp_pk = Competitie.objects.all()[0].pk

        # bad keys
        url = self.url_aangemeld_alles % 999999
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        url = self.url_aangemeld_rayon % (999999, 999999)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        url = self.url_aangemeld_rayon % (comp_pk, 999999)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        url = self.url_aangemeld_regio % (999999, 999999)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        url = self.url_aangemeld_regio % (comp_pk, 999999)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # als HWL is deze pagina niet beschikbaar
        url = self.url_behoefte % (999999, 101)
        resp = self.client.get(url)
        self.assert_is_redirect(resp, '/plein/')

    def test_bad_rcl(self):
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(self.functie_rcl)

        comp_pk = Competitie.objects.all()[0].pk

        # competitie bestaat niet
        url = self.url_behoefte % (999999, 101)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        url = self.url_behoefte_bestand % (999999, 101)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # regio bestaat niet
        url = self.url_behoefte % (comp_pk, 999999)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        url = self.url_behoefte_bestand % (comp_pk, 999999)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # deelcomp bestaat niet
        url = self.url_behoefte % (comp_pk, 100)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        url = self.url_behoefte_bestand % (comp_pk, 100)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # correct, maar niet inschrijfmethode 3
        url = self.url_behoefte % (comp_pk, 101)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        url = self.url_behoefte_bestand % (comp_pk, 101)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found


# end of file
