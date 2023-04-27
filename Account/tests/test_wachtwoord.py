# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Overig.models import SiteTijdelijkeUrl
from Mailer.models import MailQueue
from TestHelpers.e2ehelpers import E2EHelpers


class TestAccountWachtwoord(E2EHelpers, TestCase):

    """ tests voor de Account applicatie; module Login/Logout """

    url_vergeten = '/account/wachtwoord-vergeten/'
    url_wijzig = '/account/nieuw-wachtwoord/'
    url_tijdelijk = '/overig/url/%s/'       # url_code

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

    def test_wijzig_anon(self):
        # niet ingelogd
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig, {'param': 'yeah'})
        self.assert403(resp)

    def test_wijzig(self):
        # log in
        self.e2e_login(self.account_normaal)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/nieuw-wachtwoord.dtl', 'plein/site_layout.dtl'))

        # controleer dat we nu ingelogd zijn!
        self.e2e_assert_logged_in()

        nieuw_ww = 'nieuwWwoord'

        # foutief huidige wachtwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig, {'huidige': nieuw_ww, 'nieuwe': nieuw_ww})
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/nieuw-wachtwoord.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Huidige wachtwoord komt niet overeen')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig, {'huidige': self.WACHTWOORD, 'nieuwe': nieuw_ww})
        self.assert_is_redirect(resp, '/plein/')

        # controleer dat we nog steeds ingelogd zijn
        self.e2e_assert_logged_in()

        # controleer dat het nieuwe wachtwoord gebruikt kan worden
        self.client.logout()
        self.e2e_login(self.account_normaal, wachtwoord=nieuw_ww)

        # wijzig met een slecht wachtwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/nieuw-wachtwoord.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Wachtwoord moet minimaal 9 tekens lang zijn')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig, {'nieuwe': '123412341234'})
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/nieuw-wachtwoord.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Wachtwoord bevat te veel gelijke tekens')

    def test_vergeten_uitgelogd(self):
        self.client.logout()

        # test ophalen van het wachtwoord-vergeten formulier
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_vergeten)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(MailQueue.objects.count(), 0)
        self.assertEqual(SiteTijdelijkeUrl.objects.count(), 0)

        # gebruiker moet valide e-mailadres invoeren via POST
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_vergeten, {'lid_nr': 'normaal',
                                                        'email': 'normaal@test.com'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/email_wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))

        # er moet nu een mail in de MailQueue staan met een single-use url
        self.assertEqual(MailQueue.objects.count(), 1)
        mail = MailQueue.objects.all()[0]
        self.assert_email_html_ok(mail)
        self.assert_consistent_email_html_text(mail)

        self.assertEqual(SiteTijdelijkeUrl.objects.count(), 1)
        obj = SiteTijdelijkeUrl.objects.all()[0]

        self.assertEqual(obj.hoortbij_account.bevestigde_email, 'normaal@test.com')
        url = self.url_tijdelijk % obj.url_code
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        post_url = urls[0]
        with self.assert_max_queries(27):
            resp = self.client.post(post_url)
        self.assert_is_redirect(resp, self.url_wijzig)

        # haal de wachtwoord-vergeten pagina op
        # en controleer dat we het oude wachtwoord niet in hoeven te voeren
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/nieuw-wachtwoord.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Nieuwe wachtwoord:')
        self.assertNotContains(resp, 'Huidige wachtwoord:')

        # controleer dat we nu ingelogd zijn
        self.e2e_assert_logged_in()

        # wijzig door alleen het nieuwe wachtwoord op te geven
        nieuw_ww = 'nieuwWwoord'
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig, {'nieuwe': nieuw_ww})
        self.assert_is_redirect(resp, '/plein/')

        # controleer dat het nieuwe wachtwoord gebruikt kan worden
        self.client.logout()
        self.e2e_login(self.account_normaal, wachtwoord=nieuw_ww)

    def test_dupe_email(self):
        # maak nog een account aan met hetzelfde e-mailadres
        # door ook het de inlog naam op te geven lukt het toch om het wachtwoord te resetten
        account_twee = self.e2e_create_account('twee', 'normaal@test.com', 'Twee')  # dupe email
        self.assertTrue(str(account_twee) != '')    # coverage for __str__
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_vergeten, {'lid_nr': 'twee',
                                                        'email': 'normaal@test.com'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/email_wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))

    def test_vergeten_geblokkeerd(self):
        # raak het pad in receive_wachtwoord_vergeten waarbij plugin blokkeert

        # zet de blokkade
        self.account_normaal.email_is_bevestigd = False
        self.account_normaal.save(update_fields=['email_is_bevestigd'])

        # gebruiker moet valide e-mailadres invoeren via POST
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_vergeten, {'lid_nr': 'normaal',
                                                        'email': 'normaal@test.com'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/email_wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(SiteTijdelijkeUrl.objects.count(), 1)
        obj = SiteTijdelijkeUrl.objects.all()[0]
        url = self.url_tijdelijk % obj.url_code
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('account/bevestig-email.dtl', 'plein/site_layout.dtl'))

    def test_vergeten_ingelogd(self):
        # log in als admin
        self.account_admin = self.e2e_create_account_admin()
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # test ophalen van het wachtwoord-vergeten formulier
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_vergeten)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(MailQueue.objects.count(), 0)
        self.assertEqual(SiteTijdelijkeUrl.objects.count(), 0)

        # gebruiker moet valide e-mailadres invoeren via POST
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_vergeten, {'lid_nr': 'normaal',
                                                        'email': 'normaal@test.com'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/email_wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))

        # er moet nu een mail in de MailQueue staan met een single-use url
        self.assertEqual(MailQueue.objects.count(), 1)
        self.assertEqual(SiteTijdelijkeUrl.objects.count(), 1)
        obj = SiteTijdelijkeUrl.objects.all()[0]

        self.assertEqual(obj.hoortbij_account.bevestigde_email, 'normaal@test.com')
        url = self.url_tijdelijk % obj.url_code
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        post_url = urls[0]
        with self.assert_max_queries(27):
            resp = self.client.post(post_url)
        self.assert_is_redirect(resp, self.url_wijzig)
        session = self.client.session
        self.assertTrue('moet_oude_ww_weten' in session)
        self.assertFalse(session['moet_oude_ww_weten'])

        # haal de wachtwoord-vergeten pagina op
        # en controleer dat we het oude wachtwoord niet in hoeven te voeren
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/nieuw-wachtwoord.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Nieuwe wachtwoord:')
        self.assertNotContains(resp, 'Huidige wachtwoord:')

        # controleer dat we nu ingelogd zijn!
        self.e2e_assert_logged_in()

        # check dat we geen BB meer zijn
        self.assertContains(resp, 'Normaal')

    def test_vergeten_bad(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_vergeten)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))

        # geen email parameter
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_vergeten)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Voer een valide e-mailadres in van een bestaand account')

        # niet valide e-mailadres
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_vergeten, {'email': 'not a valid email adres'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Voer een valide e-mailadres in van een bestaand account')

        # niet bestaand valide e-mailadres
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_vergeten, {'lid_nr': '123456',
                                                        'email': 'als.het.maar@test.org'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Voer het e-mailadres en NHB nummer in van een bestaand account')


# FUTURE: controleer dat andere sessies van deze gebruiker verdwijnen bij wijzigen wachtwoord?

# end of file
