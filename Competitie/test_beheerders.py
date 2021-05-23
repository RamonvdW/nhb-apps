# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
from Competitie.models import RegioCompetitieSchutterBoog
from Competitie.test_fase import zet_competitie_fase
from .models import (Competitie, DeelCompetitie,
                     INSCHRIJF_METHODE_3, LAAG_REGIO, LAAG_RK, LAAG_BK)
from .operations import competities_aanmaken
import datetime


class TestCompetitieBeheerders(E2EHelpers, TestCase):

    """ unit tests voor de Competitie applicatie, Koppel Beheerders functie """

    test_after = ('Functie',)

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
        ver.ver_nr = "1000"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self._ver = ver

        # maak HWL functie aan voor deze vereniging
        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
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

        self.url_kies = '/bondscompetities/'
        self.url_overzicht = '/bondscompetities/%s/'                                        # comp_pk
        self.url_wijzigdatums = '/bondscompetities/%s/wijzig-datums/'                       # comp_pk
        self.url_aangemeld_alles = '/bondscompetities/%s/lijst-regiocompetitie/alles/'      # comp_pk
        self.url_aangemeld_rayon = '/bondscompetities/%s/lijst-regiocompetitie/rayon-%s/'   # comp_pk, rayon_pk
        self.url_aangemeld_regio = '/bondscompetities/%s/lijst-regiocompetitie/regio-%s/'   # comp_pk, regio_pk
        self.url_behoefte = '/bondscompetities/%s/lijst-regiocompetitie/regio-%s/dagdeel-behoefte/'  # comp_pk, regio_pk
        self.url_behoefte_bestand = '/bondscompetities/%s/lijst-regiocompetitie/regio-%s/dagdeel-behoefte-als-bestand/'  # comp_pk, regio_pk

    def _doe_inschrijven(self, comp):

        url_inschrijven = '/vereniging/leden-aanmelden/competitie/%s/' % comp.pk

        # meld een bak leden aan voor de competitie
        self.e2e_wisselnaarrol_bb()

        # klassegrenzen vaststellen
        url_klassegrenzen = '/bondscompetities/%s/klassegrenzen/vaststellen/'
        with self.assert_max_queries(86):
            resp = self.client.post(url_klassegrenzen % self.comp_18.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        with self.assert_max_queries(86):
            resp = self.client.post(url_klassegrenzen % self.comp_25.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        # nu in fase A2

        # zet de inschrijfmethode van regio 101 op 'methode 3', oftewel met dagdeel voorkeur
        dagdelen = ['GN', 'ZAT', 'ZON']   # uit: DAGDEEL_AFKORTINGEN
        deelcomp = DeelCompetitie.objects.filter(laag='Regio', nhb_regio=self.regio_101, competitie=comp)[0]
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_3
        deelcomp.toegestane_dagdelen = ",".join(dagdelen)
        deelcomp.save()

        # zet de datum voor inschrijven op vandaag
        for comp in Competitie.objects.filter(is_afgesloten=False):
            zet_competitie_fase(comp, 'B')
        # for

        nhb_nr = 110000
        recurve_boog_pk = BoogType.objects.get(afkorting='R').pk
        compound_boog_pk = BoogType.objects.get(afkorting='C').pk
        barebow_boog_pk = BoogType.objects.get(afkorting='BB').pk

        # doorloop de 2 verenigingen in deze regio
        for nhb_ver in NhbVereniging.objects.filter(regio=self.regio_101):
            # wordt HWL om voorkeuren aan te kunnen passen en in te kunnen schrijven
            functie_hwl = nhb_ver.functie_set.filter(rol='HWL').all()[0]
            self.e2e_wissel_naar_functie(functie_hwl)

            post_params = dict()

            # maak net zoveel leden aan als er dagdeel afkortingen zijn
            for lp in range(len(dagdelen)):
                nhb_nr += 1
                lid = NhbLid()
                lid.nhb_nr = nhb_nr
                lid.voornaam = "Lid %s" % nhb_nr
                lid.achternaam = "de Tester"
                lid.bij_vereniging = nhb_ver
                lid.is_actief_lid = True
                if barebow_boog_pk:
                    lid.geboorte_datum = datetime.date(2019-12, 1, 1)   # aspirant
                else:
                    lid.geboorte_datum = datetime.date(2000, 1, 1)      # senior
                lid.sinds_datum = datetime.date(2010, 1, 1)
                lid.geslacht = 'M'
                lid.save()

                # haal de schutter voorkeuren op, zodat de schutterboog records aangemaakt worden
                url_voorkeuren = '/sporter/voorkeuren/%s/' % nhb_nr
                with self.assert_max_queries(20):
                    resp = self.client.get(url_voorkeuren)
                self.assertEqual(resp.status_code, 200)     # 200 = OK

                # zet de recurve boog aan
                if lp == 1:
                    # zet de DT voorkeur aan voor een paar schutters
                    with self.assert_max_queries(20):
                        resp = self.client.post(url_voorkeuren, {'nhblid_pk': nhb_nr,
                                                                 'schiet_R': 'on',
                                                                 'voorkeur_dt': 'on'})
                    # onthoud deze schutterboog om straks in bulk aan te melden
                    # 'lid_NNNNNN_boogtype_MM'
                    post_params['lid_%s_boogtype_%s' % (nhb_nr, recurve_boog_pk)] = 'on'
                elif lp == 2:
                    with self.assert_max_queries(20):
                        resp = self.client.post(url_voorkeuren, {'nhblid_pk': nhb_nr,
                                                                 'schiet_C': 'on'})
                    post_params['lid_%s_boogtype_%s' % (nhb_nr, compound_boog_pk)] = 'on'
                elif barebow_boog_pk:
                    with self.assert_max_queries(20):
                        resp = self.client.post(url_voorkeuren, {'nhblid_pk': nhb_nr,
                                                                 'schiet_BB': 'on'})
                    post_params['lid_%s_boogtype_%s' % (nhb_nr, barebow_boog_pk)] = 'on'
                    barebow_boog_pk = None
                else:
                    with self.assert_max_queries(20):
                        resp = self.client.post(url_voorkeuren, {'nhblid_pk': nhb_nr,
                                                                 'schiet_R': 'on'})
                    post_params['lid_%s_boogtype_%s' % (nhb_nr, recurve_boog_pk)] = 'on'

                self.assert_is_redirect_not_plein(resp)         # check for success
            # for

            # schrijf in voor de competitie
            post_params['dagdeel'] = dagdelen.pop(-1)
            with self.assert_max_queries(23):
                resp = self.client.post(url_inschrijven, post_params)
            self.assert_is_redirect_not_plein(resp)         # check for success
        # for

    def test_overzicht_anon(self):
        url = self.url_kies
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/kies.dtl', 'plein/site_layout.dtl'))
        self.e2e_assert_other_http_commands_not_supported(url)

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

    def test_overzicht_it(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_it()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % self.comp_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht.dtl', 'plein/site_layout.dtl'))

    def test_overzicht_bb(self):
        self.e2e_login_and_pass_otp(self.account_bb)

        comp = Competitie.objects.all()[0]
        self._doe_inschrijven(comp)         # wisselt naar HWL rol
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht-beheerder.dtl', 'plein/site_layout.dtl'))

        # landelijk
        url = self.url_aangemeld_alles % comp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # rayon 2
        url = self.url_aangemeld_rayon % (comp.pk, self.rayon_1.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # regio 101
        url = self.url_aangemeld_regio % (comp.pk, self.regio_101.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # verkeerde fase
        zet_competitie_fase(comp, 'Z')
        url = self.url_aangemeld_alles % comp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found/allowed

        url = self.url_aangemeld_rayon % (comp.pk, self.rayon_1.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found/allowed

        url = self.url_aangemeld_regio % (comp.pk, self.regio_101.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found/allowed

        # regio 100: niet bestaand als deelcompetitie
        url = self.url_aangemeld_regio % (comp.pk, 100)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)  # 404 = Not found

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

        self.e2e_login_and_pass_otp(self.account_bb)
        self._doe_inschrijven(comp)         # wisselt naar HWL rol
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(functie_bko)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht-beheerder.dtl', 'plein/site_layout.dtl'))

        # landelijk
        url = self.url_aangemeld_alles % comp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # rayon 2
        url = self.url_aangemeld_rayon % (comp.pk, self.rayon_2.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # regio 101
        url = self.url_aangemeld_regio % (comp.pk, self.regio_101.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

    def test_overzicht_rko(self):
        comp = Competitie.objects.get(afstand='25')
        functie_rko = DeelCompetitie.objects.get(competitie=comp, laag=LAAG_RK, nhb_rayon=self.rayon_2).functie

        self.e2e_login_and_pass_otp(self.account_bb)
        self._doe_inschrijven(comp)         # wisselt naar HWL rol
        self.e2e_login_and_pass_otp(self.account_rko)
        self.e2e_wissel_naar_functie(functie_rko)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht-beheerder.dtl', 'plein/site_layout.dtl'))

        # landelijk
        url = self.url_aangemeld_alles % comp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # rayon 2
        url = self.url_aangemeld_rayon % (comp.pk, self.rayon_2.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # regio 101
        url = self.url_aangemeld_regio % (comp.pk, self.regio_101.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

    def test_overzicht_rcl(self):
        comp = Competitie.objects.get(afstand='18')
        functie_rcl = DeelCompetitie.objects.get(competitie=comp, laag=LAAG_REGIO, nhb_regio=self.regio_101).functie

        self.e2e_login_and_pass_otp(self.account_bb)
        self._doe_inschrijven(comp)         # wisselt naar HWL rol
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(functie_rcl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht-beheerder.dtl', 'plein/site_layout.dtl'))

        # landelijk
        url = self.url_aangemeld_alles % comp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # rayon 2
        url = self.url_aangemeld_rayon % (comp.pk, self.rayon_2.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

        # regio 101
        url = self.url_aangemeld_regio % (comp.pk, self.regio_101.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

    def test_overzicht_hwl(self):
        comp = Competitie.objects.get(afstand='18')

        self.e2e_login_and_pass_otp(self.account_bb)
        self._doe_inschrijven(comp)                       # wisselt naar HWL rol
        # self.e2e_login_and_pass_otp(self.account_bb)        # geen account_hwl
        # self.e2e_wissel_naar_functie(self.functie_hwl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht-hwl.dtl', 'plein/site_layout.dtl'))

    # TODO: add WL

    def test_wijzig_datums_not_bb(self):
        comp = Competitie.objects.all()[0]
        url = self.url_wijzigdatums % comp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

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
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/bb-wijzig-datums.dtl', 'plein/site_layout.dtl'))

        # post
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum1': '2019-08-09',
                                          'datum2': '2019-09-10',
                                          'datum3': '2019-10-11',
                                          'datum4': '2019-11-12',
                                          'datum5': '2019-11-12',
                                          'datum6': '2020-02-01',
                                          'datum7': '2019-02-12',
                                          'datum8': '2020-05-01',
                                          'datum9': '2020-05-12',
                                          })
        self.assert_is_redirect(resp, self.url_overzicht % comp.pk)

        # controleer dat de nieuwe datums opgeslagen zijn
        comp = Competitie.objects.get(pk=comp.pk)
        self.assertEqual(datetime.date(year=2019, month=8, day=9), comp.begin_aanmeldingen)
        self.assertEqual(datetime.date(year=2019, month=9, day=10), comp.einde_aanmeldingen)
        self.assertEqual(datetime.date(year=2019, month=10, day=11), comp.einde_teamvorming)
        self.assertEqual(datetime.date(year=2019, month=11, day=12), comp.eerste_wedstrijd)

        # check corner cases

        # alle datums verplicht
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum1': '2019-08-09'})
        self.assert404(resp)     # 404 = Not found

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum1': 'null',
                                          'datum2': 'hallo',
                                          'datum3': '0',
                                          'datum4': '2019-13-42'})
        self.assert404(resp)     # 404 = Not found

        # foute comp_pk bij get
        url = self.url_wijzigdatums % 999999
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        # foute comp_pk bij post
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp)     # 404 = Not found

    def test_behoefte_18(self):
        comp = Competitie.objects.get(afstand='18')
        functie_rcl = DeelCompetitie.objects.get(competitie=comp,
                                                 laag=LAAG_REGIO,
                                                 nhb_regio=self.regio_101).functie

        self.e2e_login_and_pass_otp(self.account_bb)        # geen account_hwl
        self.e2e_wisselnaarrol_bb()

        self._doe_inschrijven(comp)     # wisselt naar HWL functies
        self.e2e_wissel_naar_functie(functie_rcl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/inschrijfmethode3-behoefte.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte_bestand % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        # self.e2e_dump_resp(resp)
        csv_file = 'ver_nr,Naam,Geen voorkeur,Zaterdag,Zondag,Totaal\r\n1000,Grote Club,0,0,3,3\r\n1100,Kleine Club,0,2,0,2\r\n-,Totalen,0,2,3,5\r\n-,-,-,-,-,-\r\n-,Blazoen type,Geen voorkeur,Zaterdag,Zondag,Totaal\r\n-,40cm,0,1,0,1\r\n-,DT Compound,0,0,1,1\r\n-,DT Recurve (wens),0,1,1,2\r\n-,60cm,0,0,1,1\r\n'
        self.assertContains(resp, csv_file, msg_prefix="(was: %s)" % resp.content)

        # creëer een beetje puinhoop
        self._ver2.regio = NhbRegio.objects.get(pk=102)
        self._ver2.save()

        obj = RegioCompetitieSchutterBoog.objects.filter(bij_vereniging=self._ver).all()[0]
        obj.inschrijf_voorkeur_dagdeel = 'XX'
        obj.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/inschrijfmethode3-behoefte.dtl', 'plein/site_layout.dtl'))

    def test_behoefte_25(self):
        comp = Competitie.objects.filter(afstand='25').all()[0]
        functie_rcl = DeelCompetitie.objects.get(competitie=comp, laag=LAAG_REGIO, nhb_regio=self.regio_101).functie

        self.e2e_login_and_pass_otp(self.account_bb)        # geen account_hwl
        self.e2e_wisselnaarrol_bb()

        self._doe_inschrijven(comp)     # wisselt naar HWL functies
        self.e2e_wissel_naar_functie(functie_rcl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/inschrijfmethode3-behoefte.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte_bestand % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        # self.e2e_dump_resp(resp)
        csv_file = 'ver_nr,Naam,Geen voorkeur,Zaterdag,Zondag,Totaal\r\n1000,Grote Club,0,0,3,3\r\n1100,Kleine Club,0,2,0,2\r\n-,Totalen,0,2,3,5\r\n-,-,-,-,-,-\r\n-,Blazoen type,Geen voorkeur,Zaterdag,Zondag,Totaal\r\n-,60cm,0,2,2,4\r\n-,60cm Compound,0,0,1,1\r\n'
        self.assertContains(resp, csv_file)

        # creëer een beetje puinhoop
        self._ver2.regio = NhbRegio.objects.get(pk=102)
        self._ver2.save()

        obj = RegioCompetitieSchutterBoog.objects.filter(bij_vereniging=self._ver).all()[0]
        obj.inschrijf_voorkeur_dagdeel = 'XX'
        obj.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/inschrijfmethode3-behoefte.dtl', 'plein/site_layout.dtl'))

        # landelijk
        url = self.url_aangemeld_alles % comp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

    def test_bad_hwl(self):
        comp = Competitie.objects.get(afstand=18)       # let op: 25 werkt niet

        self.e2e_login_and_pass_otp(self.account_bb)        # geen account_hwl
        self.e2e_wisselnaarrol_bb()
        self._doe_inschrijven(comp)     # wisselt naar HWL functie

        self.e2e_wissel_naar_functie(self.functie_hwl)

        # landelijk
        zet_competitie_fase(comp, 'C')
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'C')

        # als HWL is deze pagina niet beschikbaar
        url = self.url_behoefte % (999999, 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

    def test_bad_rcl(self):
        comp = Competitie.objects.get(afstand='25')
        functie_rcl = DeelCompetitie.objects.get(competitie=comp,
                                                 laag=LAAG_REGIO,
                                                 nhb_regio=self.regio_101).functie

        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(functie_rcl)

        # bad keys
        url = self.url_aangemeld_alles % 999999
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        url = self.url_aangemeld_rayon % (999999, 999999)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        url = self.url_aangemeld_rayon % (comp.pk, 999999)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        url = self.url_aangemeld_regio % (999999, 999999)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        url = self.url_aangemeld_regio % (comp.pk, 999999)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        # competitie bestaat niet
        url = self.url_behoefte % (999999, 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        url = self.url_behoefte_bestand % (999999, 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        # regio bestaat niet
        url = self.url_behoefte % (comp.pk, 999999)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        url = self.url_behoefte_bestand % (comp.pk, 999999)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        # deelcomp bestaat niet
        url = self.url_behoefte % (comp.pk, 100)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        url = self.url_behoefte_bestand % (comp.pk, 100)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        # correct, maar niet inschrijfmethode 3
        url = self.url_behoefte % (comp.pk, 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        url = self.url_behoefte_bestand % (comp.pk, 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

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
        # verander 1 schutterboog naar een andere verenigingen
        # en laat zien dat de oude vereniging blijft staan in de inschrijven
        self.e2e_login_and_pass_otp(self.account_bb)

        comp = Competitie.objects.get(afstand='18')
        self._doe_inschrijven(comp)         # wisselt naar HWL rol

        # wissel naar RCL rol
        functie_rcl = DeelCompetitie.objects.get(competitie=comp,
                                                 laag=LAAG_REGIO,
                                                 nhb_regio=self.regio_101).functie
        self.e2e_wissel_naar_functie(functie_rcl)

        inschrijving = RegioCompetitieSchutterBoog.objects.filter(bij_vereniging=self._ver).all()[0]
        naam_str = "[" + str(inschrijving.schutterboog.nhblid.nhb_nr) + "] " + inschrijving.schutterboog.nhblid.volledige_naam()
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
        lid = inschrijving.schutterboog.nhblid
        lid.bij_vereniging = self._ver2
        lid.save()

        # controleer dat de schutter nog steeds bij dezelfde vereniging staat
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        regel = self._vind_tabel_regel_met(resp, naam_str)
        self.assertTrue(ver_str in regel)


# end of file
