# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.http import HttpResponseRedirect
from django.urls import reverse
from Account.plugin_manager import account_add_plugin_login_gate
from Mailer.models import MailQueue
from TijdelijkeCodes.models import TijdelijkeCode
from TestHelpers.e2ehelpers import E2EHelpers


class TestAccountWachtwoord(E2EHelpers, TestCase):

    """ tests voor de Account applicatie; module Login/Logout """

    url_vergeten = '/account/wachtwoord-vergeten/'
    url_wijzig = '/account/nieuw-wachtwoord/'
    url_tijdelijk = '/tijdelijke-codes/%s/'       # code

    def _login_gate_blocks(self, request, from_ip, account):
        if self.block_login:
            return HttpResponseRedirect(reverse('Account:logout'))
        return None

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.block_login = False
        account_add_plugin_login_gate(11, self._login_gate_blocks, False)

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
        self.assert_template_used(resp, ('account/wachtwoord-wijzigen.dtl', 'design/site_layout.dtl'))

        # controleer dat we nu ingelogd zijn!
        self.e2e_assert_logged_in()

        nieuw_ww = 'nieuwWwoord'    # noqa

        # foutief huidige wachtwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig, {'huidige': nieuw_ww, 'nieuwe': nieuw_ww})
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-wijzigen.dtl', 'design/site_layout.dtl'))
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
        self.assert_template_used(resp, ('account/wachtwoord-wijzigen.dtl', 'design/site_layout.dtl'))
        self.assertContains(resp, 'wachtwoord is te kort')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig, {'nieuwe': '123412341234'})
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-wijzigen.dtl', 'design/site_layout.dtl'))
        self.assertContains(resp, 'wachtwoord bevat te veel gelijke tekens')

    def test_vergeten_uitgelogd(self):
        self.client.logout()

        # test ophalen van het wachtwoord-vergeten formulier
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_vergeten)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'design/site_layout.dtl'))

        self.assertEqual(MailQueue.objects.count(), 0)
        self.assertEqual(TijdelijkeCode.objects.count(), 0)

        # gebruiker moet valide e-mailadres invoeren via POST
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_vergeten, {'lid_nr': 'normaal',
                                                        'email': 'normaal@test.com'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten-email.dtl', 'design/site_layout.dtl'))

        # er moet nu een mail in de MailQueue staan met een single-use url
        self.assertEqual(MailQueue.objects.count(), 1)
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_account/wachtwoord-vergeten.dtl')
        self.assert_consistent_email_html_text(mail)

        self.assertEqual(TijdelijkeCode.objects.count(), 1)
        obj = TijdelijkeCode.objects.first()

        self.assertEqual(obj.hoort_bij_account.bevestigde_email, 'normaal@test.com')
        url = self.url_tijdelijk % obj.url_code
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        post_url = urls[0]
        with self.assert_max_queries(22):
            resp = self.client.post(post_url)
        self.assert_is_redirect(resp, self.url_wijzig)

        # haal de wachtwoord-vergeten pagina op
        # en controleer dat we het oude wachtwoord niet in hoeven te voeren
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-wijzigen.dtl', 'design/site_layout.dtl'))
        self.assertContains(resp, 'Nieuwe wachtwoord:')
        self.assertNotContains(resp, 'Huidige wachtwoord:')

        # controleer dat we nu ingelogd zijn
        self.e2e_assert_logged_in()

        # wijzig door alleen het nieuwe wachtwoord op te geven
        nieuw_ww = 'nieuwWwoord'        # noqa
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig, {'nieuwe': nieuw_ww})
        self.assert_is_redirect(resp, '/plein/')

        # controleer dat het nieuwe wachtwoord gebruikt kan worden
        self.client.logout()
        self.e2e_login(self.account_normaal, wachtwoord=nieuw_ww)

    def test_vergeten_gewijzigd(self):
        self.client.logout()

        # test ophalen van het wachtwoord-vergeten formulier
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_vergeten)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'design/site_layout.dtl'))

        self.assertEqual(MailQueue.objects.count(), 0)
        self.assertEqual(TijdelijkeCode.objects.count(), 0)

        self.account_normaal.nieuwe_email = 'nieuwe@test.com'
        self.account_normaal.save(update_fields=['nieuwe_email'])

        # gebruiker moet valide e-mailadres invoeren via POST
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_vergeten, {'lid_nr': 'normaal',
                                                        'email': 'nieuwe@test.com'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten-email.dtl', 'design/site_layout.dtl'))

        # er moet nu een mail in de MailQueue staan met een single-use url
        self.assertEqual(MailQueue.objects.count(), 1)
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_account/wachtwoord-vergeten.dtl')
        self.assert_consistent_email_html_text(mail)

        self.assertEqual(TijdelijkeCode.objects.count(), 1)
        obj = TijdelijkeCode.objects.first()

        self.assertEqual(obj.hoort_bij_account.nieuwe_email, 'nieuwe@test.com')

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
        self.assert_template_used(resp, ('account/wachtwoord-vergeten-email.dtl', 'design/site_layout.dtl'))

    def test_vergeten_geblokkeerd(self):
        # raak het pad in receive_wachtwoord_vergeten waarbij plugin blokkeert

        # zet de blokkade
        self.block_login = True

        # vraag om de tijdelijke code
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_vergeten, {'lid_nr': 'normaal',
                                                        'email': 'normaal@test.com'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten-email.dtl', 'design/site_layout.dtl'))

        self.assertEqual(TijdelijkeCode.objects.count(), 1)
        obj = TijdelijkeCode.objects.first()
        url = self.url_tijdelijk % obj.url_code
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, '/account/logout/')

        self.block_login = False

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
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'design/site_layout.dtl'))

        self.assertEqual(MailQueue.objects.count(), 0)
        self.assertEqual(TijdelijkeCode.objects.count(), 0)

        # gebruiker moet valide e-mailadres invoeren via POST
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_vergeten, {'lid_nr': 'normaal',
                                                        'email': 'normaal@test.com'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten-email.dtl', 'design/site_layout.dtl'))

        # er moet nu een mail in de MailQueue staan met een single-use url
        self.assertEqual(MailQueue.objects.count(), 1)
        self.assertEqual(TijdelijkeCode.objects.count(), 1)
        obj = TijdelijkeCode.objects.first()

        self.assertEqual(obj.hoort_bij_account.bevestigde_email, 'normaal@test.com')
        url = self.url_tijdelijk % obj.url_code
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        post_url = urls[0]
        with self.assert_max_queries(22):
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
        self.assert_template_used(resp, ('account/wachtwoord-wijzigen.dtl', 'design/site_layout.dtl'))
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
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'design/site_layout.dtl'))

        # geen email parameter
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_vergeten)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'design/site_layout.dtl'))
        self.assertContains(resp, 'Voer een valide e-mailadres in van een bestaand account')

        # niet valide e-mailadres
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_vergeten, {'email': 'not a valid email adres'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'design/site_layout.dtl'))
        self.assertContains(resp, 'Voer een valide e-mailadres in van een bestaand account')

        # niet bestaand valide e-mailadres
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_vergeten, {'lid_nr': 'normaal',
                                                        'email': 'als.het.maar@test.org'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'design/site_layout.dtl'))
        self.assertContains(resp, 'Voer het e-mailadres en bondsnummer in van een bestaand account')

        # niet bestaand account
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_vergeten, {'lid_nr': '123456',
                                                        'email': 'normaal@test.org'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-vergeten.dtl', 'design/site_layout.dtl'))
        self.assertContains(resp, 'Voer het e-mailadres en bondsnummer in van een bestaand account')


# FUTURE: controleer dat andere sessies van deze gebruiker verdwijnen bij wijzigen wachtwoord?

# end of file
