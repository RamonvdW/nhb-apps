# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.test import TestCase
from django.conf import settings
from .models import Account, AccountEmail,account_is_email_valide
from .views import obfuscate_email
from .forms import LoginForm
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestAccountLogin(E2EHelpers, TestCase):
    """ unit tests voor de Account applicatie; module Login/Logout """

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_metmail = self.e2e_create_account('metmail', 'metmail@test.com', 'MetMail')

        self.email_normaal = self.account_normaal.accountemail_set.all()[0]
        self.email_metmail = self.account_metmail.accountemail_set.all()[0]

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
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login.dtl', 'plein/site_layout.dtl'))

    def test_inlog_form_post(self):
        # test inlog via het inlog formulier
        self.account_normaal.verkeerd_wachtwoord_teller = 3
        self.account_normaal.save()
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord':  E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        # redirect is naar het plein
        self.assert_template_used(resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Uitloggen')
        self.account_normaal = Account.objects.get(username='normaal')
        self.assertEqual(self.account_normaal.verkeerd_wachtwoord_teller, 0)

        self.e2e_assert_other_http_commands_not_supported('/account/login/', post=False)

    def test_inlog_form_post_bad_login_naam(self):
        # test inlog via het inlog formulier, met onbekende login naam
        resp = self.client.post('/account/login/', {'login_naam': 'onbekend', 'wachtwoord':  E2EHelpers.WACHTWOORD})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'De combinatie van inlog naam en wachtwoord worden niet herkend. Probeer het nog eens.')

    def test_inlog_form_niet_compleet(self):
        # test inlog via het inlog formulier, met niet complete parameters
        resp = self.client.post('/account/login/', {'wachtwoord': 'ja'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login.dtl', 'plein/site_layout.dtl'))
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
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'De combinatie van inlog naam en wachtwoord worden niet herkend. Probeer het nog eens.')
        self.account_normaal = Account.objects.get(username='normaal')
        self.assertEqual(self.account_normaal.verkeerd_wachtwoord_teller, 1)

    def test_inlog_is_geblokkeerd(self):
        self.account_normaal.is_geblokkeerd_tot = timezone.now() + datetime.timedelta(hours=1)
        self.account_normaal.save()
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord': 'huh'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/geblokkeerd.dtl', 'plein/site_layout.dtl'))

    def test_inlog_was_geblokkeerd(self):
        self.account_normaal.is_geblokkeerd_tot = timezone.now() + datetime.timedelta(hours=-1)
        self.account_normaal.save()
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord':  E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        # redirect is naar het plein
        self.assert_template_used(resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Uitloggen')

    def test_inlog_wordt_geblokkeerd(self):
        # te vaak een verkeerd wachtwoord
        self.account_normaal.verkeerd_wachtwoord_teller = settings.AUTH_BAD_PASSWORD_LIMIT - 1
        self.account_normaal.save()
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord': 'huh'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/geblokkeerd.dtl', 'plein/site_layout.dtl'))
        self.account_normaal = Account.objects.get(username='normaal')
        should_block_until = timezone.now() + datetime.timedelta(minutes=settings.AUTH_BAD_PASSWORD_LOCKOUT_MINS-1)
        self.assertTrue(self.account_normaal.is_geblokkeerd_tot > should_block_until)
        self.assertEqual(self.account_normaal.verkeerd_wachtwoord_teller, 0)

    def test_inlog_partialfields(self):
        # test inlog via het inlog formulier, met verkeerd wachtwoord
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord': ''})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Niet alle velden zijn ingevuld')

    def test_inlog_form_post_next_good(self):
        # controleer dat de next parameter gebruikt wordt
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord':  E2EHelpers.WACHTWOORD, 'next': '/account/logout/'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/uitloggen.dtl', 'plein/site_layout.dtl'))

    def test_inlog_form_post_next_bad(self):
        # controleer dat een slechte next parameter naar het Plein gaat
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord':  E2EHelpers.WACHTWOORD, 'next': '/bla/bla/'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord':  E2EHelpers.WACHTWOORD, 'next': 'www.handboogsport.nl'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

    def test_logout(self):
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord': E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Uitloggen')

        resp = self.client.get('/account/logout/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('account/uitloggen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Uitloggen')

        # do the actual logout
        resp = self.client.post('/account/logout/', {}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Uitloggen')

        self.e2e_assert_other_http_commands_not_supported('/account/logout/', post=False)

    def test_obfuscate_email(self):
        self.assertEqual(obfuscate_email(''), '')
        self.assertEqual(obfuscate_email('x'), 'x')
        self.assertEqual(obfuscate_email('x@test.nhb'), 'x@test.nhb')
        self.assertEqual(obfuscate_email('do@test.nhb'), 'd#@test.nhb')
        self.assertEqual(obfuscate_email('tre@test.nhb'), 't#e@test.nhb')
        self.assertEqual(obfuscate_email('vier@test.nhb'), 'v##r@test.nhb')
        self.assertEqual(obfuscate_email('zeven@test.nhb'), 'ze##n@test.nhb')
        self.assertEqual(obfuscate_email('hele.lange@maaktnietuit.nl'), 'he#######e@maaktnietuit.nl')

    def test_get_names(self):
        account = self.account_normaal
        self.assertEqual(account.get_first_name(), 'Normaal')
        self.assertEqual(account.volledige_naam(), 'Normaal')
        self.assertEqual(account.get_account_full_name(), 'Normaal (normaal)')

    def test_is_email_valide(self):
        self.assertTrue(account_is_email_valide('test@nhb.nl'))
        self.assertTrue(account_is_email_valide('jan.de.tester@nhb.nl'))
        self.assertTrue(account_is_email_valide('jan.de.tester@hb.nl'))
        self.assertTrue(account_is_email_valide('r@hb.nl'))
        self.assertFalse(account_is_email_valide('tester@nhb'))
        self.assertFalse(account_is_email_valide('test er@nhb.nl'))
        self.assertFalse(account_is_email_valide('test\ter@nhb.nl'))
        self.assertFalse(account_is_email_valide('test\ner@nhb.nl'))

    def test_login_met_email(self):
        # test inlog via het inlog formulier, met een email adres
        resp = self.client.post('/account/login/', {'login_naam': 'metmail@test.com', 'wachtwoord': E2EHelpers.WACHTWOORD})
        self.assert_is_redirect(resp, '/plein/')

        # check aanwezigheid van Uitloggen optie in menu als teken van inlog succes
        resp = self.client.get('/plein/')
        self.assertContains(resp, 'Uitloggen')

        # check of het niet aanzetten van het 'aangemeld blijven' vinkje werkt
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_login_aangemeld_blijven(self):
        # test inlog via het inlog formulier, met het 'aangemeld blijven' vinkje gezet
        resp = self.client.post('/account/login/', {'login_naam': 'metmail@test.com', 'wachtwoord': E2EHelpers.WACHTWOORD, 'aangemeld_blijven': True})
        self.assert_is_redirect(resp, '/plein/')

        # check aanwezigheid van Uitloggen optie in menu als teken van inlog succes
        resp = self.client.get('/plein/')
        self.assertContains(resp, 'Uitloggen')

        # als het vinkje gezet is, dan verloopt deze sessie niet als de browser afgesloten wordt
        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_login_dubbele_email(self):
        # test inlog via het inlog formulier, met een email adres dat niet eenduidig is

        # geef een tweede account dezelfde email
        self.email_normaal.bevestigde_email = self.email_metmail.bevestigde_email
        self.email_normaal.save()

        # probeer in te loggen met email
        # check de foutmelding
        resp = self.client.post('/account/login/', {'login_naam': 'metmail@test.com', 'wachtwoord': E2EHelpers.WACHTWOORD})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Inloggen met e-mail is niet mogelijk. Probeer het nog eens.')

    def test_login_nieuwe_email(self):
        # zet het nieuwe email klaar
        self.email_metmail.nieuwe_email = 'zometmail@test.com'
        self.email_metmail.save()

        # test inlog via het inlog formulier, met een email adres
        resp = self.client.post('/account/login/', {'login_naam': 'metmail@test.com', 'wachtwoord': E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        # redirect is naar de nieuwe-email pagina
        self.assert_template_used(resp, ('account/nieuwe-email.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'zo#')

    def test_login_nieuwe_email_zelfde(self):
        # zet het nieuwe email klaar
        self.email_metmail.nieuwe_email = self.email_metmail.bevestigde_email
        self.email_metmail.save()

        # test inlog via het inlog formulier, met een email adres
        resp = self.client.post('/account/login/', {'login_naam': 'metmail@test.com', 'wachtwoord': E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        # redirect is naar het plein, want er is geen nieuw email adres
        self.assert_template_used(resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

    def test_login_next(self):
        # test een login met een 'next' parameter die na de login gevolgd wordt
        resp = self.client.post('/account/login/', {'login_naam': 'metmail@test.com', 'wachtwoord': E2EHelpers.WACHTWOORD, 'next': '/account/logout'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        # redirect is naar de 'next' pagina
        self.assert_template_used(resp, ('account/uitloggen.dtl', 'plein/site_layout.dtl'))

    def test_login_next_bad_al_ingelogd(self):
        self.e2e_login(self.account_admin)

        # test een login met een 'next' parameter die na de login gevolgd wordt
        resp = self.client.get('/account/login/', {'next': '/account/bestaat-helemaal-zeker-weten-niet'}, follow=False)
        self.assert_is_redirect(resp, '/plein/')

    def test_login_al_ingelogd(self):
        self.e2e_login(self.account_admin)

        # simuleer een redirect naar het login scherm met een 'next' parameter
        resp = self.client.get('/account/login/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        # redirect is naar het plein
        self.assert_template_used(resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Uitloggen')

    def test_login_next_al_ingelogd(self):
        self.e2e_login(self.account_admin)

        # simuleer een redirect naar het login scherm met een 'next' parameter
        resp = self.client.get('/account/login/', {'next': '/account/logout/'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        # redirect is naar het plein
        self.assert_template_used(resp, ('account/uitloggen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Uitloggen')

    def test_nieuwe_email_bad(self):
        # nieuwe-email pagina ophalen zonder inlog
        self.e2e_logout()
        resp = self.client.get('/account/nieuwe-email/')
        self.assert_is_redirect(resp, '/plein/')

        # nieuwe-email pagina ophalen als er geen email is
        AccountEmail.objects.get(account=self.account_normaal).delete()
        self.e2e_login(self.account_normaal)

        resp = self.client.get('/account/nieuwe-email/')
        self.assert_is_redirect(resp, '/plein/')

        self.e2e_assert_other_http_commands_not_supported('/account/nieuwe-email/')


# end of file
