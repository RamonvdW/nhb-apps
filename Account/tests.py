# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from django.test import TestCase
from django.conf import settings
from django.core import management
from .rol import Rollen, rol_zet_sessionvars_na_login, rol_zet_sessionvars_na_otp_controle,\
                         rol_mag_wisselen, rol_is_bestuurder,\
                         rol_get_huidige, rol_activeer_rol, rol_activeer_functie
from .leeftijdsklassen import leeftijdsklassen_zet_sessionvars_na_login,\
                              get_leeftijdsklassen
from .models import Account, AccountEmail,\
                    account_zet_sessionvars_na_login, account_zet_sessionvars_na_otp_controle,\
                    is_email_valide,\
                    HanterenPersoonsgegevens, account_needs_vhpg, account_vhpg_is_geaccepteerd
from .views import obfuscate_email
from .forms import LoginForm
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Plein.tests import assert_html_ok, assert_template_used, assert_other_http_commands_not_supported
from Overig.models import SiteTijdelijkeUrl
import datetime
import pyotp
import io
from types import SimpleNamespace


def get_otp_code(account):
    otp = pyotp.TOTP(account.otp_code)
    return otp.now()


class TestAccount(TestCase):
    """ unit tests voor de Account applicatie """

    def setUp(self):
        """ initializatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        self.account_admin = Account.objects.get(username='admin')
        self.account_normaal = Account.objects.get(username='normaal')

        self.group_bko, _ = Group.objects.get_or_create(name="BKO test")
        self.group_rko, _ = Group.objects.get_or_create(name="RKO test")
        self.group_rcl, _ = Group.objects.get_or_create(name="RCL test")
        self.group_cwz, _ = Group.objects.get_or_create(name="CWZ test")

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
        self.account_normaal.verkeerd_wachtwoord_teller = 3
        self.account_normaal.save()
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord': 'wachtwoord'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        # redirect is naar het plein
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Uitloggen')
        self.account_normaal = Account.objects.get(username='normaal')
        self.assertEqual(self.account_normaal.verkeerd_wachtwoord_teller, 0)

    def test_inlog_form_post_bad_login_naam(self):
        # test inlog via het inlog formulier, met onbekende login naam
        resp = self.client.post('/account/login/', {'login_naam': 'onbekend', 'wachtwoord': 'wachtwoord'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/login.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'De combinatie van inlog naam en wachtwoord worden niet herkend. Probeer het nog eens.')

    def test_inlog_form_niet_compleet(self):
        # test inlog via het inlog formulier, met niet complete parameters
        resp = self.client.post('/account/login/', {'wachtwoord': 'ja'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/login.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Niet alle velden zijn ingevuld')

    def test_inlog_form_invalid_input(self):
        # coverage voor is_valid functie van het formulier door valid==False
        form = LoginForm()
        self.assertFalse(form.is_valid())

    def test_inlog_form_post_bad_wachtwoord(self):
        # test inlog via het inlog formulier, met verkeerd wachtwoord
        self.assertEqual(self.account_normaal.verkeerd_wachtwoord_teller, 0)
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord': 'huh'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/login.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'De combinatie van inlog naam en wachtwoord worden niet herkend. Probeer het nog eens.')
        self.account_normaal = Account.objects.get(username='normaal')
        self.assertEqual(self.account_normaal.verkeerd_wachtwoord_teller, 1)

    def test_inlog_is_geblokkeerd(self):
        self.account_normaal.is_geblokkeerd_tot = timezone.now() + datetime.timedelta(hours=1)
        self.account_normaal.save()
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord': 'huh'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/geblokkeerd.dtl', 'plein/site_layout.dtl'))

    def test_inlog_was_geblokkeerd(self):
        self.account_normaal.is_geblokkeerd_tot = timezone.now() + datetime.timedelta(hours=-1)
        self.account_normaal.save()
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord': 'wachtwoord'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        # redirect is naar het plein
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Uitloggen')

    def test_inlog_wordt_geblokkeerd(self):
        # te vaak een verkeerd wachtwoord
        self.account_normaal.verkeerd_wachtwoord_teller = settings.AUTH_BAD_PASSWORD_LIMIT - 1
        self.account_normaal.save()
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord': 'huh'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/geblokkeerd.dtl', 'plein/site_layout.dtl'))
        self.account_normaal = Account.objects.get(username='normaal')
        should_block_until = timezone.now() + datetime.timedelta(minutes=settings.AUTH_BAD_PASSWORD_LOCKOUT_MINS-1)
        self.assertTrue(self.account_normaal.is_geblokkeerd_tot > should_block_until)
        self.assertEqual(self.account_normaal.verkeerd_wachtwoord_teller, 0)

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
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Uitloggen')

    def test_rol(self):
        # unit-tests voor de 'rol' module

        # simuleer de normale inputs
        account = self.account_normaal
        request = SimpleNamespace()
        request.session = dict()
        request.user = account

        # no session vars / not logged in
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        self.assertFalse(rol_mag_wisselen(request))
        rol_activeer_rol(request, 'bestaat niet')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        rol_activeer_rol(request, 'schutter')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        self.assertFalse(rol_is_bestuurder(request))

        # niet aan nhblid gekoppeld schutter account
        account.is_staff = False
        account.is_BKO = False
        account.nhblid = None
        request.session = dict()
        rol_zet_sessionvars_na_login(account, request)
        self.assertFalse(rol_mag_wisselen(request))
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        self.assertFalse(rol_is_bestuurder(request))
        rol_activeer_rol(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        rol_activeer_rol(request, 'BKO')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        rol_activeer_rol(request, 'schutter')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        rol_activeer_rol(request, 'geen')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)

        # schutter
        account.is_staff = False
        account.is_BKO = False
        account.nhblid = self.nhblid1
        request.session = dict()
        account_zet_sessionvars_na_login(request)
        rol_zet_sessionvars_na_login(account, request)
        self.assertFalse(rol_mag_wisselen(request))
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        self.assertFalse(rol_is_bestuurder(request))
        rol_activeer_rol(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activeer_rol(request, 'BKO')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activeer_rol(request, 'geen')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        rol_activeer_rol(request, 'schutter')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)

        # bb
        account.is_staff = False
        account.is_BKO = True
        account.nhblid = self.nhblid1
        request.session = dict()
        account_zet_sessionvars_na_otp_controle(request)
        rol_zet_sessionvars_na_otp_controle(account, request)
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        self.assertTrue(rol_mag_wisselen(request))
        self.assertFalse(rol_is_bestuurder(request))        # ivm VHPG niet geaccepteerd

        account_vhpg_is_geaccepteerd(account)
        account_zet_sessionvars_na_otp_controle(request)
        rol_zet_sessionvars_na_otp_controle(account, request)
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        self.assertFalse(rol_is_bestuurder(request))

        rol_activeer_rol(request, 'schutter')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activeer_rol(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activeer_rol(request, 'BB')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_BB)
        self.assertTrue(rol_is_bestuurder(request))
        rol_activeer_rol(request, 'geen')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        rol_activeer_rol(request, 'BB')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_BB)
        rol_activeer_rol(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_BB)
        rol_activeer_rol(request, 'BKO')        # kan niet, moet via functie
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_BB)

        # beheerder
        account = self.account_admin
        request.session = dict()
        account_vhpg_is_geaccepteerd(account)
        account_zet_sessionvars_na_otp_controle(request)
        rol_zet_sessionvars_na_otp_controle(account, request)
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        self.assertTrue(rol_mag_wisselen(request))

        rol_activeer_rol(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_IT)
        rol_activeer_rol(request, 'BB')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_BB)
        rol_activeer_rol(request, 'geen')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        rol_activeer_rol(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_IT)
        rol_activeer_rol(request, 'schutter')
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
        self.assertFormError(resp, 'form', None, 'Geen email adres bekend. Neem contact op met de secretaris van je vereniging.')

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
        objs = SiteTijdelijkeUrl.objects.all().order_by('-aangemaakt_op')       # nieuwste eerst
        self.assertTrue(len(objs) > 0)
        obj = objs[0]
        self.assertEqual(obj.hoortbij_accountemail.nieuwe_email, 'rdetester@gmail.not')
        self.assertFalse(obj.hoortbij_accountemail.email_is_bevestigd)
        url = '/overig/url/' + obj.url_code + '/'
        resp = self.client.get(url, follow=True)    # temporary url redirects
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/bevestigd.dtl', 'plein/site_layout.dtl'))

        account = Account.objects.filter(username='100001')[0]
        accmail = AccountEmail.objects.filter(account=account)[0]
        self.assertTrue(accmail.email_is_bevestigd)

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
        account = SimpleNamespace()
        request = SimpleNamespace()
        nhblid = SimpleNamespace()
        nhblid.geboorte_datum = SimpleNamespace()
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
        self.assertEqual(account.volledige_naam(), 'normaal')

        # account.first_name
        account.nhblid = None
        account.first_name = 'Normaal'
        self.assertEqual(account.get_first_name(), 'Normaal')
        self.assertEqual(account.get_account_full_name(), 'normaal')
        self.assertEqual(account.volledige_naam(), 'normaal')

        # nhblid.voornaam
        account.nhblid = self.nhblid1
        self.assertEqual(account.get_first_name(), 'Ramon')
        self.assertEqual(account.get_account_full_name(), 'Ramon de Tester (normaal)')
        self.assertEqual(account.volledige_naam(), 'Ramon de Tester')

    def test_deblok_account(self):
        # validate precondition
        self.assertIsNone(self.account_normaal.is_geblokkeerd_tot)

        # deblock when not blocked
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('deblok_account', 'normaal', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertEqual(f2.getvalue(), "Account 'normaal' is niet geblokkeerd\n")

        # blokkeren
        self.account_normaal.is_geblokkeerd_tot = timezone.now() + datetime.timedelta(hours=1)
        self.account_normaal.save()

        # deblock
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('deblok_account', 'normaal', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertEqual(f2.getvalue(), "Account 'normaal' is niet meer geblokkeerd\n")
        # validate
        self.account_normaal = Account.objects.get(username='normaal')
        self.assertTrue(self.account_normaal.is_geblokkeerd_tot <= timezone.now())

        # exception case
        management.call_command('deblok_account', 'nietbestaand', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), 'Account matching query does not exist.\n')

    def test_maak_account(self):
        with self.assertRaises(Account.DoesNotExist):
            Account.objects.get(username='nieuwelogin')
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('maak_account', 'Voornaam', 'nieuwelogin', 'nieuwwachtwoord', 'nieuw@nhb.test', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertEqual(f2.getvalue(), "Aanmaken van account 'nieuwelogin' is gelukt\n")
        obj = Account.objects.get(username='nieuwelogin')
        self.assertEqual(obj.username, 'nieuwelogin')
        self.assertEqual(obj.first_name, 'Voornaam')
        self.assertEqual(obj.email, '')
        self.assertTrue(obj.is_active)
        self.assertFalse(obj.is_staff)
        self.assertFalse(obj.is_superuser)

        mail = AccountEmail.objects.get(account=obj)
        self.assertTrue(mail.email_is_bevestigd)
        self.assertEqual(mail.bevestigde_email, 'nieuw@nhb.test')
        self.assertEqual(mail.nieuwe_email, '')

        # coverage voor AccountEmail.__str__()
        self.assertEqual(str(mail), "E-mail voor account 'nieuwelogin' (nieuw@nhb.test)")

        # exception cases
        f1 = io.StringIO()
        management.call_command('maak_account', 'Voornaam', 'nieuwelogin', 'nieuwwachtwoord', 'nieuw@nhb.test', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), 'Account bestaat al\n')

        f1 = io.StringIO()
        management.call_command('maak_account', 'Voornaam', 'nieuwelogin', 'nieuwwachtwoord', 'nieuw.nhb.test', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), 'Dat is geen valide e-mail\n')

    def test_maak_beheerder(self):
        self.assertFalse(self.account_normaal.is_staff)
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('maak_beheerder', 'normaal', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertEqual(f2.getvalue(), "Account 'normaal' is beheerder gemaakt\n")
        self.account_normaal = Account.objects.get(username='normaal')
        self.assertTrue(self.account_normaal.is_staff)

        # exception case
        management.call_command('maak_beheerder', 'nietbestaand', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), 'Account matching query does not exist.\n')

    def test_wisselvanrol_pagina_admin(self):
        # controleer dat de link naar het wisselen van rol op de pagina staat
        self.account_admin.otp_is_actief = False
        self.account_admin.save()
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        resp = self.client.get('/account/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        self.assertNotContains(resp, 'IT beheerder')
        self.assertNotContains(resp, 'Manager competitiezaken')
        self.assertContains(resp, 'Gebruiker')
        self.assertContains(resp, 'Controle met een tweede factor is verplicht voor gebruikers met toegang tot persoonsgegevens')

        self.client.logout()

        # controleer dat de link naar de OTP controle en VHPG op de pagina staan
        self.account_admin.otp_is_actief = True
        self.account_admin.save()
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        resp = self.client.get('/account/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        self.assertNotContains(resp, 'IT beheerder')
        self.assertNotContains(resp, 'Manager competitiezaken')
        self.assertContains(resp, 'Gebruiker')
        self.assertContains(resp, 'Voordat je aan de slag kan moeten we eerst een paar afspraken maken over het omgaan met persoonsgegevens.')
        self.assertContains(resp, 'Een aantal rollen komt beschikbaar nadat de controle van de tweede factor uitgevoerd is.')

        # controleer dat de complete keuzemogelijkheden op de pagina staan
        account_vhpg_is_geaccepteerd(self.account_admin)
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_admin, self.client).save()
        resp = self.client.get('/account/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        self.assertContains(resp, 'IT beheerder')
        self.assertContains(resp, 'Manager competitiezaken')
        self.assertContains(resp, 'Gebruiker')

        assert_template_used(self, resp, ('account/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        assert_other_http_commands_not_supported(self, '/account/wissel-van-rol/')
        self.client.logout()

    def test_wisselvanrol_pagina_normaal(self):
        self.account_normaal.nhblid = self.nhblid1
        self.account_normaal.save()
        self.client.login(username=self.account_normaal.username, password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_normaal, self.client).save()

        # controleer dat de wissel-van-rol pagina niet aanwezig is voor deze normale gebruiker
        resp = self.client.get('/account/wissel-van-rol/')
        self.assertEqual(resp.status_code, 403)     # 403 = Forbidden
        self.client.logout()

    def test_wisselvanrol_pagina_normaal_met_rol(self):
        # voeg de gebruiker toe aan een groep waardoor wissel-van-rol actief wordt
        self.account_normaal.nhblid = self.nhblid1
        self.account_normaal.save()
        self.account_normaal.groups.add(self.group_rcl)
        account_vhpg_is_geaccepteerd(self.account_normaal)

        self.client.login(username=self.account_normaal.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_normaal, self.client).save()

        resp = self.client.get('/account/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        self.assertNotContains(resp, "BKO")
        self.assertNotContains(resp, "RKO")
        self.assertContains(resp, "RCL")     # TODO: RKO moet RCL kunnen helpen
        self.assertNotContains(resp, "CWZ")

    def test_rolwissel(self):
        self.client.login(username=self.account_admin.username, password='wachtwoord')
        account_vhpg_is_geaccepteerd(self.account_admin)
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_admin, self.client).save()

        resp = self.client.get('/account/wissel-van-rol/BB/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: Manager competitiezaken")

        resp = self.client.get('/account/wissel-van-rol/beheerder/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: IT beheerder")

        # controleer dat een niet valide rol wissel geen effect heeft
        # dit raakt een exception in Account.rol:rol_activeer
        resp = self.client.get('/account/wissel-van-rol/huh/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: IT beheerder")

        # controleer dat een rol wissel die met een functie moet geen effect heeft
        resp = self.client.get('/account/wissel-van-rol/BKO/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: IT beheerder")

        resp = self.client.get('/account/wissel-van-rol/geen/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: Gebruiker")

        self.client.logout()

    def test_geen_rolwissel(self):
        # dit raakt de exceptie in Account.rol:rol_mag_wisselen
        self.client.logout()
        resp = self.client.get('/account/wissel-van-rol/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect (to login)

    def test_reset_otp(self):
        # non-existing user
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('reset_otp', 'noujazeg', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), "Account matching query does not exist.\n")
        self.assertEqual(f2.getvalue(), '')

        # OTP is niet actief
        self.account_normaal.otp_is_actief = False
        self.account_normaal.save()
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('reset_otp', 'normaal', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertEqual(f2.getvalue(), "Account 'normaal' heeft OTP niet aan staan\n")

        # OTP resetten
        self.account_normaal.otp_is_actief = True
        self.account_normaal.otp_code = "1234"
        self.account_normaal.save()
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('reset_otp', 'normaal', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertEqual(f2.getvalue(), "Account 'normaal' moet nu opnieuw de OTP koppeling leggen\n")
        self.account_normaal = Account.objects.get(username='normaal')
        self.assertFalse(self.account_normaal.otp_is_actief)
        self.assertEqual(self.account_normaal.otp_code, "1234")

        # OTP resetten + otp_code vergeten
        self.account_normaal.otp_is_actief = True
        self.account_normaal.otp_code = "1234"
        self.account_normaal.save()
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('reset_otp', 'normaal', '--reset_secret', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertEqual(f2.getvalue(), "Account 'normaal' moet nu opnieuw de OTP koppeling leggen\n")
        self.account_normaal = Account.objects.get(username='normaal')
        self.assertFalse(self.account_normaal.otp_is_actief)
        self.assertNotEqual(self.account_normaal.otp_code, "1234")

        # exception case
        management.call_command('deblok_account', 'nietbestaand', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), 'Account matching query does not exist.\n')

    def test_otp_koppelen_niet_ingelogd(self):
        self.client.logout()
        # controleer redirect naar het plein, omdat de gebruiker niet ingelogged is
        resp = self.client.get('/account/otp-koppelen/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

        resp = self.client.post('/account/otp-koppelen/', {'otp_code': '123456'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_otp_koppelen_niet_nodig(self):
        self.client.login(username='normaal', password='wachtwoord')
        # controleer redirect naar het plein, omdat OTP koppeling niet nodig is
        resp = self.client.get('/account/otp-koppelen/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

        resp = self.client.post('/account/otp-koppelen/', {'otp_code': '123456'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

    def test_otp_koppelen_al_gekoppeld(self):
        self.account_admin.otp_is_actief = True
        self.account_admin.save()
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        # controleer redirect naar het plein, omdat OTP koppeling er al is
        resp = self.client.get('/account/otp-koppelen/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

        resp = self.client.post('/account/otp-koppelen/', {'otp_code': '123456'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

    def test_otp_koppelen(self):
        # reset OTP koppeling
        self.account_admin.otp_is_actief = False
        self.account_admin.otp_code = 'xx'
        self.account_admin.save()
        # log in
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        # check mogelijkheid tot koppelen
        resp = self.client.get('/account/otp-koppelen/', follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/otp-koppelen.dtl', 'plein/site_layout.dtl'))
        # check dat het OTP secret aangemaakt is
        self.account_admin = Account.objects.get(username='admin')
        self.assertNotEqual(self.account_admin.otp_code, 'xx')
        # geef foute otp code op
        resp = self.client.post('/account/otp-koppelen/', {'otp_code': '123456'}, follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/otp-koppelen.dtl', 'plein/site_layout.dtl'))
        self.account_admin = Account.objects.get(username='admin')
        self.assertFalse(self.account_admin.otp_is_actief)
        # juiste otp code
        code = get_otp_code(self.account_admin)
        resp = self.client.post('/account/otp-koppelen/', {'otp_code': code}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/otp-koppelen-gelukt.dtl', 'plein/site_layout.dtl'))
        self.account_admin = Account.objects.get(username='admin')
        self.assertTrue(self.account_admin.otp_is_actief)

    def test_otp_controle_niet_ingelogd(self):
        self.client.logout()
        # controleer redirect naar het plein, omdat de gebruiker niet ingelogged is
        resp = self.client.get('/account/otp-controle/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

        resp = self.client.post('/account/otp-controle/', {'otp_code': '123456'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_otp_controle_niet_nodig(self):
        self.client.login(username='normaal', password='wachtwoord')
        # controleer redirect naar het plein, omdat OTP koppeling niet nodig is
        resp = self.client.get('/account/otp-controle/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

        resp = self.client.post('/account/otp-controle/', {'otp_code': '123456'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

    def test_otp_controle(self):
        self.account_admin.otp_is_actief = True
        self.account_admin.otp_code = "ABCDEFGHIJKLMNOP"
        self.account_admin.save()
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        resp = self.client.get('/account/otp-controle/', follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/otp-controle.dtl', 'plein/site_layout.dtl'))
        # geen code
        resp = self.client.post('/account/otp-controle/', {'jaja': 'nee'}, follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "De gegevens worden niet geaccepteerd")
        # lege code
        resp = self.client.post('/account/otp-controle/', {'otp_code': ''}, follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "De gegevens worden niet geaccepteerd")
        # illegale code
        resp = self.client.post('/account/otp-controle/', {'otp_code': 'ABCDEF'}, follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Voer de vereiste code in")
        # fout code
        resp = self.client.post('/account/otp-controle/', {'otp_code': '123456'}, follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Verkeerde code. Probeer het nog eens.")
        # juiste otp code resulteert in redirect naar het plein
        code = get_otp_code(self.account_admin)
        resp = self.client.post('/account/otp-controle/', {'otp_code': code}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/wissel-van-rol.dtl', 'plein/site_layout.dtl'))

    def test_is_email_valide(self):
        self.assertTrue(is_email_valide('test@nhb.nl'))
        self.assertTrue(is_email_valide('jan.de.tester@nhb.nl'))
        self.assertTrue(is_email_valide('jan.de.tester@hb.nl'))
        self.assertTrue(is_email_valide('r@hb.nl'))
        self.assertFalse(is_email_valide('tester@nhb'))
        self.assertFalse(is_email_valide('test er@nhb.nl'))
        self.assertFalse(is_email_valide('test\ter@nhb.nl'))
        self.assertFalse(is_email_valide('test\ner@nhb.nl'))

    def test_vhpg_anon(self):
        self.client.logout()
        resp = self.client.get('/account/vhpg-acceptatie/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

        # doe een post zonder ingelogd te zijn
        resp = self.client.post('/account/vhpg-acceptatie/', {}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_vhpg_niet_nodig(self):
        self.client.login(username='normaal', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_normaal, self.client).save()
        resp = self.client.get('/account/vhpg-acceptatie/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

    def test_vhpg(self):
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        resp = self.client.get('/account/vhpg-acceptatie/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/vhpg-acceptatie.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'verplicht')

        self.assertEqual(len(HanterenPersoonsgegevens.objects.all()), 0)
        needs_vhpg, _ = account_needs_vhpg(self.account_admin)
        self.assertTrue(needs_vhpg)

        # voer de post uit zonder checkbox (dit gebeurt ook als de checkbox niet gezet wordt)
        resp = self.client.post('/account/vhpg-acceptatie/', {}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/vhpg-acceptatie.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'verplicht')

        self.assertEqual(len(HanterenPersoonsgegevens.objects.all()), 0)

        # voer de post uit met checkbox wel gezet (waarde maakt niet uit)
        resp = self.client.post('/account/vhpg-acceptatie/', {'accepteert': 'whatever'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/wissel-van-rol.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(len(HanterenPersoonsgegevens.objects.all()), 1)
        needs_vhpg, _ = account_needs_vhpg(self.account_admin)
        self.assertFalse(needs_vhpg)

        obj = HanterenPersoonsgegevens.objects.all()[0]
        self.assertTrue(str(obj) != "")

    def test_vhpg_afspraken_anon(self):
        self.client.logout()
        resp = self.client.get('/account/vhpg-afspraken/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/login.dtl', 'plein/site_layout.dtl'))

    def test_vhpg_afspraken(self):
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        resp = self.client.get('/account/vhpg-afspraken/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/vhpg-afspraken.dtl', 'plein/site_layout.dtl'))

# end of file
