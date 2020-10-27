# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Overig.e2ehelpers import E2EHelpers
from Overig.models import SiteTijdelijkeUrl
from Mailer.models import MailQueue


class TestAccountWachtwoord(E2EHelpers, TestCase):
    """ unit tests voor de Account applicatie; module Login/Logout """

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        self.url_vergeten = '/account/wachtwoord-vergeten/'
        self.url_wijzig = '/account/nieuw-wachtwoord/'

    def test_wijzig_anon(self):
        # niet ingelogd
        resp = self.client.get(self.url_wijzig)
        self.assert_is_redirect(resp, '/plein/')

        resp = self.client.post(self.url_wijzig, {'param': 'yeah'})
        self.assert_is_redirect(resp, '/plein/')

    def test_wijzig(self):
        # log in
        self.e2e_login(self.account_normaal)
        resp = self.client.get(self.url_wijzig)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/nieuw-wachtwoord.dtl', 'plein/site_layout.dtl'))

        # controleer dat we ingelogd zijn: het menu bevat de optie Uitloggen
        self.assertContains(resp, 'Uitloggen')

        nieuw_ww = 'nieuwWwoord'

        # foutief huidige wachtwoord
        resp = self.client.post(self.url_wijzig, {'huidige': nieuw_ww, 'nieuwe': nieuw_ww})
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/nieuw-wachtwoord.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Huidige wachtwoord komt niet overeen')

        resp = self.client.post(self.url_wijzig, {'huidige': self.WACHTWOORD, 'nieuwe': nieuw_ww})
        self.assert_is_redirect(resp, '/plein/')

        # controleer dat we nog steeds ingelogd zijn
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Uitloggen')

        # controleer dat het nieuwe wachtwoord gebruikt kan worden
        self.client.logout()
        self.e2e_login(self.account_normaal, wachtwoord=nieuw_ww)

        # wijzig met een slecht wachtwoord
        resp = self.client.post(self.url_wijzig)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/nieuw-wachtwoord.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Wachtwoord moet minimaal 9 tekens lang zijn')

        resp = self.client.post(self.url_wijzig, {'nieuwe': '123412341234'})
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/nieuw-wachtwoord.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Wachtwoord bevat te veel gelijke tekens')

    def test_vergeten_uitgelogd(self):
        self.client.logout()

        # test ophalen van het wachtwoord-vergeten formulier
        resp = self.client.get(self.url_vergeten)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(MailQueue.objects.count(), 0)
        self.assertEqual(SiteTijdelijkeUrl.objects.count(), 0)

        # gebruiker moet valide e-mailadres invoeren via POST
        resp = self.client.post(self.url_vergeten, {'email': 'normaal@test.com'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/email_wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))

        # er moet nu een mail in de MailQueue staan met een single-use url
        self.assertEqual(MailQueue.objects.count(), 1)
        self.assertEqual(SiteTijdelijkeUrl.objects.count(), 1)
        obj = SiteTijdelijkeUrl.objects.all()[0]

        self.assertEqual(obj.hoortbij_accountemail.bevestigde_email, 'normaal@test.com')
        url = '/overig/url/' + obj.url_code + '/'
        self.client.logout()
        resp = self.client.get(url)
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        post_url = urls[0]
        resp = self.client.post(post_url)
        self.assert_is_redirect(resp, self.url_wijzig)

        # haal de wachtwoord-vergeten pagina op
        # en controleer dat we het oude wachtwoord niet in hoeven te voeren
        resp = self.client.get(self.url_wijzig)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/nieuw-wachtwoord.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Nieuwe wachtwoord:')
        self.assertNotContains(resp, 'Huidige wachtwoord:')

        # controleer dat we nu ingelogd zijn!
        self.assertContains(resp, 'Uitloggen')

    def test_vergeten_ingelogd(self):
        # log in als admin
        self.account_admin = self.e2e_create_account_admin()
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # test ophalen van het wachtwoord-vergeten formulier
        resp = self.client.get(self.url_vergeten)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(MailQueue.objects.count(), 0)
        self.assertEqual(SiteTijdelijkeUrl.objects.count(), 0)

        # gebruiker moet valide e-mailadres invoeren via POST
        resp = self.client.post(self.url_vergeten, {'email': 'normaal@test.com'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/email_wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))

        # er moet nu een mail in de MailQueue staan met een single-use url
        self.assertEqual(MailQueue.objects.count(), 1)
        self.assertEqual(SiteTijdelijkeUrl.objects.count(), 1)
        obj = SiteTijdelijkeUrl.objects.all()[0]

        self.assertEqual(obj.hoortbij_accountemail.bevestigde_email, 'normaal@test.com')
        url = '/overig/url/' + obj.url_code + '/'
        self.client.logout()
        resp = self.client.get(url)
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        post_url = urls[0]
        resp = self.client.post(post_url)
        self.assert_is_redirect(resp, self.url_wijzig)
        session = self.client.session
        self.assertTrue('moet_oude_ww_weten' in session)
        self.assertFalse(session['moet_oude_ww_weten'])

        # haal de wachtwoord-vergeten pagina op
        # en controleer dat we het oude wachtwoord niet in hoeven te voeren
        resp = self.client.get(self.url_wijzig)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/nieuw-wachtwoord.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Nieuwe wachtwoord:')
        self.assertNotContains(resp, 'Huidige wachtwoord:')

        # controleer dat we nu ingelogd zijn!
        self.assertContains(resp, 'Uitloggen')

        # check dat we geen BB meer zijn
        self.assertContains(resp, 'Normaal')

    def test_vergeten_bad(self):
        resp = self.client.get(self.url_vergeten)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))

        # geen email parameter
        resp = self.client.post(self.url_vergeten)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Voer het e-mailadres in van een bestaand account')

        # niet valide e-mailadres
        resp = self.client.post(self.url_vergeten, {'email': 'not a valid email adres'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Voer het e-mailadres in van een bestaand account')

        # niet bestaand valide e-mailadres
        resp = self.client.post(self.url_vergeten, {'email': 'als.het.maar@test.org'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Voer het e-mailadres in van een bestaand account')

        account_twee = self.e2e_create_account('twee', 'normaal@test.com', 'Twee')  # dupe email
        resp = self.client.post(self.url_vergeten, {'email': 'normaal@test.com'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Er is een probleem met dit e-mailadres. Neem contact op met het bondsburo!')


# TODO: controleer dat andere sessies van deze gebruiker verdwijnen bij wijzigen wachtwoord?

# end of file
