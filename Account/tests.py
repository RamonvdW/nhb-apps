# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import TestCase
from .rol import Rollen, rol_zet_sessionvars_na_login, rol_mag_wisselen,\
                         rol_get_limiet, rol_get_huidige, rol_activate
from .leeftijdsklassen import leeftijdsklassen_zet_sessionvars_na_login,\
                              get_leeftijdsklassen
from .models import Account
from .views import obfuscate_email
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Plein.tests import assert_html_ok, assert_template_used
import datetime


def get_url(resp, pre=b'\x00', post=b''):
    html = resp.content
    pos = html.find(pre)
    if pos >= 0:
        # print("pre pos=%s" % pos)
        html = html[pos + len(pre):]
        # print("pre html=%s" % repr(html))
        pos = html.find(post)
        if pos >= 0:
            # print("post pos=%s" % pos)
            html = html[:pos]
            # print("post html=%s" % repr(html))
            url = html.decode()     # convert to string
            return url
    return None


class AccountTest(TestCase):

    def setUp(self):
        """ initializatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        self.account_admin = Account.objects.get(username='admin')
        self.account_normaal = Account.objects.get(username='normaal')

        # maak de standard rayon/regio structuur aan
        maak_rayons_2018(NhbRayon)
        maak_regios_2018(NhbRayon, NhbRegio)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = NhbRegio.objects.get(pk=111)
        # secretaris kan nog niet ingevuld worden
        ver.save()

        # maak een test lid aan
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.email = "rdetester@gmail.not"
        lid.postcode = "1234PC"
        lid.huisnummer = "42bis"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()
        self.nhblid1 = lid

        # maak een test lid aan
        lid = NhbLid()
        lid.nhb_nr = 100002
        lid.geslacht = "V"
        lid.voornaam = "Ramona"
        lid.achternaam = "de Testerin"
        lid.email = ""
        lid.postcode = "1234PC"
        lid.huisnummer = "1"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()

    def test_inlog_form_get(self):
        # test ophalen van het inlog formulier
        resp = self.client.get('/account/login/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/login.dtl', 'plein/site_layout.dtl'))

    def test_inlog_form_post(self):
        # test inlog via het inlog formulier
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord': 'wachtwoord'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        # redirect is naar het plein
        assert_template_used(self, resp, ('plein/plein.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Uitloggen')

    def test_inlog_form_post_bad_login_naam(self):
        # test inlog via het inlog formulier, met onbekende login naam
        resp = self.client.post('/account/login/', {'login_naam': 'onbekend', 'wachtwoord': 'wachtwoord'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/login.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'De combinatie van inlog naam en wachtwoord worden niet herkend. Probeer het nog eens.')

    def test_inlog_form_post_bad_wachtwoord(self):
        # test inlog via het inlog formulier, met verkeerd wachtwoord
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord': 'huh'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/login.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'De combinatie van inlog naam en wachtwoord worden niet herkend. Probeer het nog eens.')

    def test_inlog_partialfields(self):
        # test inlog via het inlog formulier, met verkeerd wachtwoord
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord': ''})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/login.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Niet alle velden zijn ingevuld')

    def test_logout(self):
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord': 'wachtwoord'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Uitloggen')

        resp = self.client.get('/account/logout/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/uitloggen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Uitloggen')

        # do the actual logout
        resp = self.client.post('/account/logout/', {}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Uitloggen')

    def test_rol(self):
        # unit-tests voor de 'rol' module

        # simuleer de normale inputs
        account = lambda: None
        request = lambda: None
        request.session = dict()

        # no session vars / not logged in
        self.assertEqual(rol_get_limiet(request), Rollen.ROL_UNKNOWN)
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_UNKNOWN)
        self.assertFalse(rol_mag_wisselen(request))
        rol_activate(request, 'bestaat niet')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_UNKNOWN)
        rol_activate(request, 'schutter')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_UNKNOWN)

        # niet aan nhblid gekoppeld schutter account
        account.is_staff = False
        account.is_BKO = False
        account.nhblid = None
        request.session = dict()
        rol_zet_sessionvars_na_login(account, request)
        self.assertFalse(rol_mag_wisselen(request))
        self.assertEqual(rol_get_limiet(request), Rollen.ROL_SCHUTTER)
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activate(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activate(request, 'BKO')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activate(request, 'schutter')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)

        # schutter
        account.is_staff = False
        account.is_BKO = False
        account.nhblid = 1
        request.session = dict()
        rol_zet_sessionvars_na_login(account, request)
        self.assertFalse(rol_mag_wisselen(request))
        self.assertEqual(rol_get_limiet(request), Rollen.ROL_SCHUTTER)
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activate(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activate(request, 'BKO')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activate(request, 'schutter')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)

        # bko
        account.is_staff = False
        account.is_BKO = True
        account.nhblid = 1
        request.session = dict()
        rol_zet_sessionvars_na_login(account, request)
        self.assertTrue(rol_mag_wisselen(request))
        self.assertEqual(rol_get_limiet(request), Rollen.ROL_BKO)
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_BKO)
        rol_activate(request, 'schutter')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activate(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activate(request, 'BKO')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_BKO)
        rol_activate(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_BKO)

        # beheerder
        account.is_staff = True
        account.is_BKO = False
        account.nhblid = None
        request.session = dict()
        rol_zet_sessionvars_na_login(account, request)
        self.assertTrue(rol_mag_wisselen(request))
        self.assertEqual(rol_get_limiet(request), Rollen.ROL_IT)
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_IT)
        rol_activate(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_IT)
        rol_activate(request, 'BKO')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_BKO)
        rol_activate(request, 'schutter')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activate(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_IT)

    def test_registreer_get(self):
        # test registratie via het formulier
        resp = self.client.get('/account/registreer/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))

    def test_registreer_partialfields(self):
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': ''})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Niet alle velden zijn ingevuld')

    def test_registreer_invalidfields(self):
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100678',
                                 'email': 'is geen email',
                                 'nieuw_wachtwoord': 'jaja'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'De gegevens worden niet geaccepteerd')

    def test_registreer_nhb_bad_nr(self):
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': 'hallo!',
                                 'email': 'test@test.not',
                                 'nieuw_wachtwoord': 'x'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Onbekend NHB nummer')

    def test_registreer_nhb_nonexisting_nr(self):
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '999999',
                                 'email': 'test@test.not',
                                 'nieuw_wachtwoord': 'x'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Onbekend NHB nummer')

    def test_registreer_nhb_geen_email(self):
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100002',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'jaja'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Account heeft geen email adres. Neem contact op met de secretaris van je vereniging.')

    def test_registreer_nhb_verkeerde_email(self):
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.yes',
                                 'nieuw_wachtwoord': 'jaja'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'De combinatie van NHB nummer en email worden niet herkend. Probeer het nog eens.')

    def test_registreer_nhb(self):
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'jaja'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/aangemaakt.dtl', 'plein/site_layout.dtl'))

        # controleer dat het email adres obfuscated is
        self.assertNotContains(resp, 'rdetester@gmail.not')
        self.assertContains(resp, 'r@gmail.not')     # iets van r######r@gmail.not

        # volg de link om de email te bevestigen
        url = get_url(resp, pre=b'Klik voorlopig even op <a href="', post=b'">deze link</a>')
        resp = self.client.get(url, follow=True)    # temporary url redirects
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/bevestigd.dtl', 'plein/site_layout.dtl'))

    def test_registreer_nhb_bestaat_al(self):
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'jaja'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/aangemaakt.dtl', 'plein/site_layout.dtl'))

        # tweede poging
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'neenee'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Account bestaat al')

    def test_direct_aangemaakt(self):
        # test rechtstreeks de 'aangemaakt' pagina ophalen, zonder registratie stappen
        resp = self.client.get('/account/aangemaakt/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect
        self.assertEqual(resp.url, '/plein/')

        # zorg even voor 100% coverage van deze file
        url = get_url(resp)

    def test_obfuscate_email(self):
        self.assertEqual(obfuscate_email(''), '')
        self.assertEqual(obfuscate_email('x'), 'x')
        self.assertEqual(obfuscate_email('x@test.nhb'), 'x@test.nhb')
        self.assertEqual(obfuscate_email('do@test.nhb'), 'd#@test.nhb')
        self.assertEqual(obfuscate_email('tre@test.nhb'), 't#e@test.nhb')
        self.assertEqual(obfuscate_email('vier@test.nhb'), 'v##r@test.nhb')
        self.assertEqual(obfuscate_email('zeven@test.nhb'), 'ze##n@test.nhb')
        self.assertEqual(obfuscate_email('hele.lange@maaktnietuit.nl'), 'he#######e@maaktnietuit.nl')

    def test_leeftijdsklassen(self):
        # unit-tests voor de 'leeftijdsklassen' module

        # simuleer de normale inputs
        account = lambda: None
        request = lambda: None
        nhblid = lambda: None
        nhblid.geboorte_datum = lambda: None
        nhblid.geboorte_datum.year = 0
        request.session = dict()

        # session vars niet gezet
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_leeftijdsklassen(request)
        self.assertIsNone(huidige_jaar)
        self.assertIsNone(leeftijd)
        self.assertFalse(is_jong)
        self.assertIsNone(wlst)
        self.assertIsNone(clst)

        # geen nhblid
        account.nhblid = None
        leeftijdsklassen_zet_sessionvars_na_login(account, request)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_leeftijdsklassen(request)
        self.assertIsNone(huidige_jaar)
        self.assertIsNone(leeftijd)
        self.assertFalse(is_jong)
        self.assertIsNone(wlst)
        self.assertIsNone(clst)

        # test met verschillende leeftijdsklassen van een nhblid
        # noteer: afhankelijk van BasisTypen: init_leeftijdsklasse_2018
        account.nhblid = nhblid
        now_jaar = timezone.now().year  # TODO: should stub, for more reliable test

        # nhblid, aspirant (<= 13)
        nhb_leeftijd = 11
        nhblid.geboorte_datum.year = now_jaar - nhb_leeftijd
        leeftijdsklassen_zet_sessionvars_na_login(account, request)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_leeftijdsklassen(request)
        self.assertEquals(huidige_jaar, now_jaar)
        self.assertEqual(leeftijd, nhb_leeftijd)
        self.assertTrue(is_jong)        # onder 30 == jong
        self.assertEqual(wlst, ('Aspirant', 'Aspirant', 'Aspirant', 'Aspirant', 'Cadet'))
        #                        -1=10       0=11        +1=12       +2=13       +3=14
        self.assertEqual(clst, ('Aspirant', 'Aspirant', 'Aspirant', 'Cadet', 'Cadet'))

        # nhblid, cadet (14, 15, 16, 17)
        nhb_leeftijd = 14
        nhblid.geboorte_datum.year = now_jaar - nhb_leeftijd
        leeftijdsklassen_zet_sessionvars_na_login(account, request)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_leeftijdsklassen(request)
        self.assertEquals(huidige_jaar, now_jaar)
        self.assertEqual(leeftijd, nhb_leeftijd)
        self.assertTrue(is_jong)        # onder 30 == jong
        self.assertEqual(wlst, ('Aspirant', 'Cadet', 'Cadet', 'Cadet', 'Cadet'))
        #                        -1=13       0=14     +1=15    +2=16    +3=17
        self.assertEqual(clst, ('Cadet', 'Cadet', 'Cadet', 'Cadet', 'Junior'))

        # nhblid, junior (18, 19, 20)
        nhb_leeftijd = 18
        nhblid.geboorte_datum.year = now_jaar - nhb_leeftijd
        leeftijdsklassen_zet_sessionvars_na_login(account, request)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_leeftijdsklassen(request)
        self.assertEquals(huidige_jaar, now_jaar)
        self.assertEqual(leeftijd, nhb_leeftijd)
        self.assertTrue(is_jong)        # onder 30 == jong
        self.assertEqual(wlst, ('Cadet', 'Junior', 'Junior', 'Junior', 'Senior'))
        #                        -1=17    0=18     +1=19      +2=20     +3=21
        self.assertEqual(clst, ('Junior', 'Junior', 'Junior', 'Senior', 'Senior'))

        # nhblid, senior (>= 21)
        nhb_leeftijd = 30
        nhblid.geboorte_datum.year = now_jaar - nhb_leeftijd
        leeftijdsklassen_zet_sessionvars_na_login(account, request)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_leeftijdsklassen(request)
        self.assertEquals(huidige_jaar, now_jaar)
        self.assertEqual(leeftijd, nhb_leeftijd)
        self.assertFalse(is_jong)        # onder 30 == jong
        self.assertEqual(wlst, ('Senior', 'Senior', 'Senior', 'Senior', 'Senior'))
        self.assertEqual(clst, wlst)

        # nhblid, master (zelfde als senior, for now)
        nhb_leeftijd = 50
        nhblid.geboorte_datum.year = now_jaar - nhb_leeftijd
        leeftijdsklassen_zet_sessionvars_na_login(account, request)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_leeftijdsklassen(request)
        self.assertEquals(huidige_jaar, now_jaar)
        self.assertEqual(leeftijd, nhb_leeftijd)
        self.assertFalse(is_jong)        # onder 30 == jong
        self.assertEqual(wlst, ('Senior', 'Senior', 'Senior', 'Senior', 'Senior'))
        self.assertEqual(clst, wlst)

    def test_get_names(self):
        account = self.account_normaal

        # account.username
        account.nhblid = None
        self.assertEqual(account.get_first_name(), 'normaal')
        self.assertEqual(account.get_account_full_name(), 'normaal')

        # account.first_name
        account.nhblid = None
        account.first_name = 'Normaal'
        self.assertEqual(account.get_first_name(), 'Normaal')
        self.assertEqual(account.get_account_full_name(), 'normaal')

        # nhblid.voornaam
        account.nhblid = self.nhblid1
        self.assertEqual(account.get_first_name(), 'Ramon')
        self.assertEqual(account.get_account_full_name(), 'Ramon de Tester (normaal)')


# end of file
