# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.urls import reverse
from django.test import TestCase
from django.conf import settings
from Account.models import Account
from Account.forms import LoginForm
from Mailer.models import MailQueue
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from TijdelijkeCodes.operations import maak_tijdelijke_code_account_email
import datetime


class TestAccountLogin(E2EHelpers, TestCase):

    """ tests voor de Account applicatie; module Login/Logout """

    url_login = '/account/login/'

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_metmail = self.e2e_create_account('metmail', 'metmail@test.com', 'MetMail')

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
        self.account_normaal.save(update_fields=['verkeerd_wachtwoord_teller'])
        with self.assert_max_queries(27):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal',
                                                     'wachtwoord':  E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
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
        self.assertFormError(resp.context['form'], None, 'De combinatie van inlog naam en wachtwoord worden niet herkend. Probeer het nog eens.')

    def test_inlog_form_niet_compleet(self):
        # test inlog via het inlog formulier, met niet complete parameters
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'wachtwoord': 'ja'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp.context['form'], None, 'Niet alle velden zijn ingevuld')

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
        self.assertFormError(resp.context['form'], None, 'De combinatie van inlog naam en wachtwoord worden niet herkend. Probeer het nog eens.')
        self.account_normaal = Account.objects.get(username='normaal')
        self.assertEqual(self.account_normaal.verkeerd_wachtwoord_teller, 1)

    def test_inlog_is_geblokkeerd(self):
        self.account_normaal.is_geblokkeerd_tot = timezone.now() + datetime.timedelta(hours=1)
        self.account_normaal.save(update_fields=['is_geblokkeerd_tot'])
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal', 'wachtwoord': 'huh'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login-geblokkeerd.dtl', 'plein/site_layout.dtl'))
        template_names = [templ.name for templ in resp.templates]
        self.assertFalse('account/login.dtl' in template_names)

    def test_inlog_was_geblokkeerd(self):
        self.account_normaal.is_geblokkeerd_tot = timezone.now() + datetime.timedelta(hours=-1)
        self.account_normaal.save(update_fields=['is_geblokkeerd_tot'])
        with self.assert_max_queries(26):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal',
                                                     'wachtwoord':  E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        # redirect is naar het plein
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_inlog_wordt_geblokkeerd(self):
        # te vaak een verkeerd wachtwoord
        self.account_normaal.verkeerd_wachtwoord_teller = settings.AUTH_BAD_PASSWORD_LIMIT - 1
        self.account_normaal.save(update_fields=['verkeerd_wachtwoord_teller'])
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal', 'wachtwoord': 'huh'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login-geblokkeerd.dtl', 'plein/site_layout.dtl'))
        self.account_normaal = Account.objects.get(username='normaal')
        should_block_until = timezone.now() + datetime.timedelta(minutes=settings.AUTH_BAD_PASSWORD_LOCKOUT_MINS-1)
        self.assertTrue(self.account_normaal.is_geblokkeerd_tot > should_block_until)
        self.assertEqual(self.account_normaal.verkeerd_wachtwoord_teller, 0)

    def test_inlog_email_nog_niet_bevestigd(self):
        # verander de status van de bevestiging van het e-mailadres
        account = self.account_normaal
        account.email_is_bevestigd = False
        account.nieuwe_email = 'normaal@test.com'
        account.save(update_fields=['email_is_bevestigd', 'nieuwe_email'])

        url = maak_tijdelijke_code_account_email(account, test="hallo")
        code = url.split('/')[-2]

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal',
                                                     'wachtwoord':  E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/email-bevestig-huidige.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'no####l@test.com')

        self.e2e_login(self.testdata.account_admin)
        url = reverse('TijdelijkeCodes:tijdelijke-url', kwargs={'code': code})
        resp = self.client.post(url)
        self.assertTrue(resp.status_code, 200)
        self.assert_template_used(resp, ('account/email-bevestigd.dtl', 'plein/site_layout.dtl'))

    def test_inlog_foutieve_email_nog_niet_bevestigd(self):
        # verander de status van de bevestiging van het e-mailadres
        account = self.account_normaal
        account.email_is_bevestigd = False
        account.nieuwe_email = 'normaal@test.com'
        account.save(update_fields=['email_is_bevestigd', 'nieuwe_email'])

        url = maak_tijdelijke_code_account_email(account, test="hallo")
        code = url.split('/')[-2]

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal',
                                                     'wachtwoord':  E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/email-bevestig-huidige.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'no####l@test.com')

        # we komen er niet in
        # simuleer wijziging e-mailadres
        account.nieuwe_email = 'meer_normaal@test.com'
        account.save(update_fields=['nieuwe_email'])

        url = maak_tijdelijke_code_account_email(account, test="hallo")
        code = url.split('/')[-2]

        # probeer opnieuw in te loggen
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal',
                                                     'wachtwoord':  E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/email-bevestig-nieuwe.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'me#########l@test.com')

        # er moet nu een mail in de MailQueue staan met een single-use url
        self.assertEqual(MailQueue.objects.count(), 1)
        mail = MailQueue.objects.all()[0]
        self.assert_email_html_ok(mail)
        self.assert_consistent_email_html_text(mail)

        self.e2e_login(self.testdata.account_admin)
        url = reverse('TijdelijkeCodes:tijdelijke-url', kwargs={'code': code})
        resp = self.client.post(url)
        self.assertTrue(resp.status_code, 200)
        self.assert_template_used(resp, ('account/email-bevestigd.dtl', 'plein/site_layout.dtl'))

    def test_inlog_partial_fields(self):
        # test inlog via het inlog formulier, met verkeerd wachtwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal', 'wachtwoord': ''})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp.context['form'], None, 'Niet alle velden zijn ingevuld')

    def test_inlog_form_post_next_good(self):
        # controleer dat de next parameter gebruikt wordt
        with self.assert_max_queries(26):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal',
                                                     'wachtwoord':  E2EHelpers.WACHTWOORD,
                                                     'next': '/account/logout/'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/uitloggen.dtl', 'plein/site_layout.dtl'))

    def test_inlog_form_post_next_bad(self):
        # controleer dat een slechte next parameter naar het Plein gaat
        with self.assert_max_queries(26):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal',
                                                     'wachtwoord':  E2EHelpers.WACHTWOORD,
                                                     'next': '/bla/bla/'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal',
                                                     'wachtwoord':  E2EHelpers.WACHTWOORD,
                                                     'next': 'www.handboogsport.nl'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_logout(self):
        # controleer wat er gebeurd indien niet ingelogd
        with self.assert_max_queries(20):
            resp = self.client.get('/account/logout/')
        self.assert_is_redirect(resp, '/plein/')

        # log in
        with self.assert_max_queries(26):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal',
                                                     'wachtwoord': E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

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
        with self.assert_max_queries(26):
            resp = self.client.post(self.url_login, {'login_naam': 'metmail@test.com',
                                                     'wachtwoord': E2EHelpers.WACHTWOORD})
        self.assert_is_redirect(resp, '/plein/')

        # check aanwezigheid van Uitloggen optie in menu als teken van inlog succes
        with self.assert_max_queries(20):
            resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # check of het niet aanzetten van het 'aangemeld blijven' vinkje werkt
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_login_met_email_case_insensitive(self):
        # test inlog via het inlog formulier, met een email adres
        with self.assert_max_queries(26):
            resp = self.client.post(self.url_login, {'login_naam': 'MetMail@test.com',
                                                     'wachtwoord': E2EHelpers.WACHTWOORD})
        self.assert_is_redirect(resp, '/plein/')

    def test_login_aangemeld_blijven(self):
        # test inlog via het inlog formulier, met het 'aangemeld blijven' vinkje gezet
        with self.assert_max_queries(26):
            resp = self.client.post(self.url_login, {'login_naam': 'metmail@test.com',
                                                     'wachtwoord': E2EHelpers.WACHTWOORD,
                                                     'aangemeld_blijven': True})
        self.assert_is_redirect(resp, '/plein/')

        # als het vinkje gezet is, dan verloopt deze sessie niet als de browser afgesloten wordt
        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_login_dubbele_email(self):
        # test inlog via het inlog formulier, met een email adres dat niet eenduidig is

        # geef een tweede account dezelfde email
        self.account_normaal.bevestigde_email = self.account_metmail.bevestigde_email
        self.account_normaal.save(update_fields=['bevestigde_email'])

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
        self.account_metmail.nieuwe_email = 'zometmail@test.com'
        self.account_metmail.save(update_fields=['nieuwe_email'])

        # test inlog via het inlog formulier, met een email adres
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_login, {'login_naam': 'metmail@test.com',
                                                     'wachtwoord': E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        # redirect is naar de nieuwe-email pagina
        self.assert_template_used(resp, ('account/email-bevestig-nieuwe.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'zo#')

    def test_login_nieuwe_email_zelfde(self):
        # zet het nieuwe email klaar
        self.account_metmail.nieuwe_email = self.account_metmail.bevestigde_email
        self.account_metmail.save(update_fields=['nieuwe_email'])

        # test inlog via het inlog formulier, met een email adres
        with self.assert_max_queries(28):
            resp = self.client.post(self.url_login, {'login_naam': 'metmail@test.com',
                                                     'wachtwoord': E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        # redirect is naar het wissel-van-rol, want er is geen nieuw email adres
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_login_next(self):
        # test een login met een 'next' parameter die na de login gevolgd wordt
        with self.assert_max_queries(28):
            resp = self.client.post(self.url_login, {'login_naam': 'metmail@test.com', 'wachtwoord': E2EHelpers.WACHTWOORD, 'next': '/account/logout'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        # redirect is naar de 'next' pagina
        self.assert_template_used(resp, ('account/uitloggen.dtl', 'plein/site_layout.dtl'))

    def test_login_next_bad_al_ingelogd(self):
        self.e2e_login(self.testdata.account_admin)

        # test een login met een 'next' parameter die na de login gevolgd wordt
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_login, {'next': '/account/bestaat-helemaal-zeker-weten-niet'}, follow=False)
        self.assert_is_redirect(resp, '/plein/')

    def test_login_al_ingelogd(self):
        self.testdata.account_admin.sporter_set.all().delete()      # corner case
        self.e2e_login(self.testdata.account_admin)

        # simuleer een redirect naar het login scherm met een 'next' parameter
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_login, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        # redirect is naar het plein
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_login_next_al_ingelogd(self):
        self.e2e_login(self.testdata.account_admin)

        # simuleer een redirect naar het login scherm met een 'next' parameter
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_login, {'next': '/account/logout/'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        # redirect is naar het plein
        self.assert_template_used(resp, ('account/uitloggen.dtl', 'plein/site_layout.dtl'))


# end of file
