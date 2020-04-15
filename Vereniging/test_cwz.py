# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestVerenigingCWZ(E2EHelpers, TestCase):

    """ Tests voor de Vereniging applicatie, functies voor de CWZ """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie', 'Schutter', 'Competitie')

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        regio_111 = NhbRegio.objects.get(regio_nr=111)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = regio_111
        # secretaris kan nog niet ingevuld worden
        ver.save()

        # maak de CWZ functie
        self.functie_cwz = maak_functie("CWZ test", "CWZ")
        self.functie_cwz.nhb_ver = ver
        self.functie_cwz.save()

        # maak het lid aan dat CWZ wordt
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.email = "rdetester@gmail.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()

        self.account_cwz = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam, accepteer_vhpg=True)
        self.functie_cwz.accounts.add(self.account_cwz)

        lid.account = self.account_cwz
        lid.save()
        self.nhblid1 = lid

        # maak een jeugdlid aan
        lid = NhbLid()
        lid.nhb_nr = 100002
        lid.geslacht = "V"
        lid.voornaam = "Ramona"
        lid.achternaam = "de Jeugdschutter"
        lid.email = ""
        lid.geboorte_datum = datetime.date(year=2010, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()

        # maak een senior lid aan, om inactief te maken
        lid = NhbLid()
        lid.nhb_nr = 100003
        lid.geslacht = "V"
        lid.voornaam = "Ramona"
        lid.achternaam = "de Testerin"
        lid.email = ""
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()
        self.nhblid2 = lid

        self.url_overzicht = '/vereniging/'
        self.url_ledenlijst = '/vereniging/leden-lijst/'
        self.url_voorkeuren = '/vereniging/leden-voorkeuren/'
        self.url_aanmelden = '/vereniging/leden-aanmelden/'

    def _zet_schutter_voorkeuren(self, nhb_nr):
        # deze functie kan alleen gebruikt worden als CWZ
        url_schutter_voorkeuren = '/schutter/voorkeuren/'

        # haal als CWZ de voorkeuren pagina op van een lid van de vereniging
        # dit maakt ook de SchutterBoog records aan
        resp = self.client.get(url_schutter_voorkeuren + '%s/' % nhb_nr)
        self.assertEqual(resp.status_code, 200)

        # post een wijziging
        resp = self.client.post(url_schutter_voorkeuren, {'nhblid_pk': nhb_nr, 'schiet_R': 'on', 'info_C': 'on'})
        self.assert_is_redirect(resp, '/vereniging/leden-voorkeuren/')

    def test_overzicht(self):
        # anon
        self.e2e_logout()
        resp = self.client.get(self.url_overzicht)
        self.assert_is_redirect(resp, '/plein/')

        # login als CWZ
        self.e2e_login_and_pass_otp(self.account_cwz)
        self.e2e_wissel_naar_functie(self.functie_cwz)
        self.e2e_check_rol('CWZ')

        resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/overzicht.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_overzicht)

    def test_ledenlijst(self):
        # anon
        self.e2e_logout()
        resp = self.client.get(self.url_ledenlijst)
        self.assert_is_redirect(resp, '/plein/')

        # login als CWZ
        self.e2e_login_and_pass_otp(self.account_cwz)
        self.e2e_wissel_naar_functie(self.functie_cwz)
        self.e2e_check_rol('CWZ')

        resp = self.client.get(self.url_ledenlijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/ledenlijst.dtl', 'plein/site_layout.dtl'))

        self.assertContains(resp, 'Jeugd')
        self.assertContains(resp, 'Senioren')
        self.assertNotContains(resp, 'Inactieve leden')

        # maak een lid inactief
        self.nhblid2.is_actief_lid = False
        self.nhblid2.save()

        # stel ook een paar bogen in
        self._zet_schutter_voorkeuren(100002)

        resp = self.client.get(self.url_ledenlijst)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        self.assertContains(resp, 'Jeugd')
        self.assertContains(resp, 'Senioren')
        self.assertContains(resp, 'Inactieve leden')

        self.e2e_assert_other_http_commands_not_supported(self.url_ledenlijst)

    def test_voorkeuren(self):
        # login als CWZ
        self.e2e_login_and_pass_otp(self.account_cwz)
        self.e2e_wissel_naar_functie(self.functie_cwz)
        self.e2e_check_rol('CWZ')

        resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/leden-voorkeuren.dtl', 'plein/site_layout.dtl'))
        # inhoudelijk is de pagina gelijk aan ledenlijst

    def test_aanmelden(self):
        # anon
        self.e2e_logout()
        resp = self.client.get(self.url_aanmelden)
        self.assert_is_redirect(resp, '/plein/')

        # login als CWZ
        self.e2e_login_and_pass_otp(self.account_cwz)
        self.e2e_wissel_naar_functie(self.functie_cwz)
        self.e2e_check_rol('CWZ')

        # stel een paar bogen in
        self._zet_schutter_voorkeuren(100002)

        resp = self.client.get(self.url_aanmelden)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/leden-aanmelden.dtl', 'plein/site_layout.dtl'))

# end of file
