# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.test import TestCase
from django.conf import settings
from Overig.e2ehelpers import E2EHelpers
from .models import Account
from .forms import LoginForm
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

        self.url_login = '/account/login/'
        
    def test_inlog_form_get(self):
        # test ophalen van het inlog formulier
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_login)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login.dtl', 'plein/site_layout.dtl'))

    def test_inlog_form_post(self):
        # test inlog via het inlog formulier
        self.account_normaal.verkeerd_wachtwoord_teller = 3
        self.account_normaal.save()
        with self.assert_max_queries(23):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal',
                                                     'wachtwoord':  E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.account_normaal = Account.objects.get(username='normaal')
        self.assertEqual(self.account_normaal.verkeerd_wachtwoord_teller, 0)

        self.e2e_assert_other_http_commands_not_supported(self.url_login, post=False)

    def test_inlog_form_post_bad_login_naam(self):
        # test inlog via het inlog formulier, met onbekende login naam
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'login_naam': 'onbekend',
                                                     'wachtwoord':  E2EHelpers.WACHTWOORD})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'De combinatie van inlog naam en wachtwoord worden niet herkend. Probeer het nog eens.')

    def test_inlog_form_niet_compleet(self):
        # test inlog via het inlog formulier, met niet complete parameters
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'wachtwoord': 'ja'})
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
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal', 'wachtwoord': 'huh'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'De combinatie van inlog naam en wachtwoord worden niet herkend. Probeer het nog eens.')
        self.account_normaal = Account.objects.get(username='normaal')
        self.assertEqual(self.account_normaal.verkeerd_wachtwoord_teller, 1)

    def test_inlog_is_geblokkeerd(self):
        self.account_normaal.is_geblokkeerd_tot = timezone.now() + datetime.timedelta(hours=1)
        self.account_normaal.save()
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal', 'wachtwoord': 'huh'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/geblokkeerd.dtl', 'plein/site_layout.dtl'))

    def test_inlog_was_geblokkeerd(self):
        self.account_normaal.is_geblokkeerd_tot = timezone.now() + datetime.timedelta(hours=-1)
        self.account_normaal.save()
        with self.assert_max_queries(22):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal',
                                                     'wachtwoord':  E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        # redirect is naar het plein
        self.assert_template_used(resp, ('functie/otp-controle.dtl', 'plein/site_layout.dtl'))

    def test_inlog_wordt_geblokkeerd(self):
        # te vaak een verkeerd wachtwoord
        self.account_normaal.verkeerd_wachtwoord_teller = settings.AUTH_BAD_PASSWORD_LIMIT - 1
        self.account_normaal.save()
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal', 'wachtwoord': 'huh'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/geblokkeerd.dtl', 'plein/site_layout.dtl'))
        self.account_normaal = Account.objects.get(username='normaal')
        should_block_until = timezone.now() + datetime.timedelta(minutes=settings.AUTH_BAD_PASSWORD_LOCKOUT_MINS-1)
        self.assertTrue(self.account_normaal.is_geblokkeerd_tot > should_block_until)
        self.assertEqual(self.account_normaal.verkeerd_wachtwoord_teller, 0)

    def test_inlog_email_nog_niet_bevestigd(self):
        # verander de status van de bevestiging van het e-mailadres
        self.email_normaal.email_is_bevestigd = False
        self.email_normaal.save()

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal',
                                                     'wachtwoord':  E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/bevestig-email.dtl', 'plein/site_layout.dtl'))

    def test_inlog_partial_fields(self):
        # test inlog via het inlog formulier, met verkeerd wachtwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal', 'wachtwoord': ''})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Niet alle velden zijn ingevuld')

    def test_inlog_form_post_next_good(self):
        # controleer dat de next parameter gebruikt wordt
        with self.assert_max_queries(22):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal',
                                                     'wachtwoord':  E2EHelpers.WACHTWOORD,
                                                     'next': '/account/logout/'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/uitloggen.dtl', 'plein/site_layout.dtl'))

    def test_inlog_form_post_next_bad(self):
        # controleer dat een slechte next parameter naar het Plein gaat
        with self.assert_max_queries(22):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal',
                                                     'wachtwoord':  E2EHelpers.WACHTWOORD,
                                                     'next': '/bla/bla/'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/otp-controle.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal',
                                                     'wachtwoord':  E2EHelpers.WACHTWOORD,
                                                     'next': 'www.handboogsport.nl'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/otp-controle.dtl', 'plein/site_layout.dtl'))

    def test_logout(self):
        # controleer wat er gebeurd indien niet ingelogd
        with self.assert_max_queries(20):
            resp = self.client.get('/account/logout/')
        self.assert_is_redirect(resp, '/plein/')

        # log in
        with self.assert_max_queries(22):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal',
                                                     'wachtwoord': E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-controle.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get('/account/logout/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('account/uitloggen.dtl', 'plein/site_layout.dtl'))

        # do the actual logout
        with self.assert_max_queries(20):
            resp = self.client.post('/account/logout/', {}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported('/account/logout/', post=False)

    def test_get_names(self):
        account = self.account_normaal
        self.assertEqual(account.get_first_name(), 'Normaal')
        self.assertEqual(account.volledige_naam(), 'Normaal')
        self.assertEqual(account.get_account_full_name(), 'Normaal (normaal)')

    def test_login_met_email(self):
        # test inlog via het inlog formulier, met een email adres
        with self.assert_max_queries(22):
            resp = self.client.post(self.url_login, {'login_naam': 'metmail@test.com',
                                                     'wachtwoord': E2EHelpers.WACHTWOORD})
        self.assert_is_redirect(resp, '/functie/otp-controle/')

        # check aanwezigheid van Uitloggen optie in menu als teken van inlog succes
        with self.assert_max_queries(20):
            resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # check of het niet aanzetten van het 'aangemeld blijven' vinkje werkt
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_login_met_email_case_insensitive(self):
        # test inlog via het inlog formulier, met een email adres
        with self.assert_max_queries(22):
            resp = self.client.post(self.url_login, {'login_naam': 'MetMail@test.com',
                                                     'wachtwoord': E2EHelpers.WACHTWOORD})
        self.assert_is_redirect(resp, '/functie/otp-controle/')

    def test_login_aangemeld_blijven(self):
        # test inlog via het inlog formulier, met het 'aangemeld blijven' vinkje gezet
        with self.assert_max_queries(22):
            resp = self.client.post(self.url_login, {'login_naam': 'metmail@test.com',
                                                     'wachtwoord': E2EHelpers.WACHTWOORD,
                                                     'aangemeld_blijven': True})
        self.assert_is_redirect(resp, '/functie/otp-controle/')

        # als het vinkje gezet is, dan verloopt deze sessie niet als de browser afgesloten wordt
        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_login_dubbele_email(self):
        # test inlog via het inlog formulier, met een email adres dat niet eenduidig is

        # geef een tweede account dezelfde email
        self.email_normaal.bevestigde_email = self.email_metmail.bevestigde_email
        self.email_normaal.save()

        # probeer in te loggen met email
        # check de foutmelding
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'login_naam': 'metmail@test.com',
                                                     'wachtwoord': E2EHelpers.WACHTWOORD})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Inloggen met e-mail is niet mogelijk. Probeer het nog eens.')

    def test_login_nieuwe_email(self):
        # zet het nieuwe email klaar
        self.email_metmail.nieuwe_email = 'zometmail@test.com'
        self.email_metmail.save()

        # test inlog via het inlog formulier, met een email adres
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'login_naam': 'metmail@test.com',
                                                     'wachtwoord': E2EHelpers.WACHTWOORD}, follow=True)
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
        with self.assert_max_queries(24):
            resp = self.client.post(self.url_login, {'login_naam': 'metmail@test.com',
                                                     'wachtwoord': E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        # redirect is naar het plein, want er is geen nieuw email adres
        self.assert_template_used(resp, ('functie/otp-controle.dtl', 'plein/site_layout.dtl'))

    def test_login_next(self):
        # test een login met een 'next' parameter die na de login gevolgd wordt
        with self.assert_max_queries(24):
            resp = self.client.post(self.url_login, {'login_naam': 'metmail@test.com', 'wachtwoord': E2EHelpers.WACHTWOORD, 'next': '/account/logout'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        # redirect is naar de 'next' pagina
        self.assert_template_used(resp, ('account/uitloggen.dtl', 'plein/site_layout.dtl'))

    def test_login_next_bad_al_ingelogd(self):
        self.e2e_login(self.account_admin)

        # test een login met een 'next' parameter die na de login gevolgd wordt
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_login, {'next': '/account/bestaat-helemaal-zeker-weten-niet'}, follow=False)
        self.assert_is_redirect(resp, '/plein/')

    def test_login_al_ingelogd(self):
        self.e2e_login(self.account_admin)

        # simuleer een redirect naar het login scherm met een 'next' parameter
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_login, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        # redirect is naar het plein
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_login_next_al_ingelogd(self):
        self.e2e_login(self.account_admin)

        # simuleer een redirect naar het login scherm met een 'next' parameter
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_login, {'next': '/account/logout/'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        # redirect is naar het plein
        self.assert_template_used(resp, ('account/uitloggen.dtl', 'plein/site_layout.dtl'))


# end of file
