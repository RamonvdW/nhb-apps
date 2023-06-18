# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Mailer.models import MailQueue
from Registreer.definities import (REGISTRATIE_FASE_EMAIL, REGISTRATIE_FASE_PASSWORD,
                                   REGISTRATIE_FASE_DONE)
from Registreer.models import GastRegistratie, GastRegistratieRateTracker, GastLidNummer
from TijdelijkeCodes.models import TijdelijkeCode
from TestHelpers.e2ehelpers import E2EHelpers
import time


class TestRegistreerGast(E2EHelpers, TestCase):

    """ tests voor de Registreer applicatie; voor gast-accounts """

    test_after = ('Account',)

    url_registreer_gast = '/account/registreer/gast/'
    url_meer_vragen = '/account/registreer/gast/meer-vragen/'
    url_tijdelijk = '/tijdelijke-codes/%s/'

    test_voornaam = 'Bågskytt'
    test_achternaam = 'från Utlandet'
    test_email = 'skytt46@test.se'

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

    def test_get(self):
        # haal het formulier op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_registreer_gast)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Fout:')

        # admin beschrijving
        obj = GastLidNummer.objects.first()
        self.assertTrue(str(obj) != '')

    def test_fase_begin(self):
        # ontvang naam en e-mailadres + stuur e-mail voor bevestigen
        self.assertEqual(0, GastRegistratie.objects.count())
        self.assertEqual(0, MailQueue.objects.count())
        self.assertEqual(0, TijdelijkeCode.objects.count())

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'achternaam': self.test_achternaam,
                                     'voornaam': self.test_voornaam,
                                     'email': self.test_email},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-1-bevestig-email.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(1, GastRegistratie.objects.count())
        gast = GastRegistratie.objects.first()

        # print(gast)
        self.assertEqual(gast.voornaam, self.test_voornaam)
        self.assertEqual(gast.achternaam, self.test_achternaam)
        self.assertEqual(gast.email, self.test_email)
        self.assertFalse(gast.email_is_bevestigd)
        self.assertEqual(gast.fase, REGISTRATIE_FASE_EMAIL)

        self.assertEqual(1, MailQueue.objects.count())
        self.assertEqual(1, TijdelijkeCode.objects.count())

        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail)
        self.assert_consistent_email_html_text(mail)

        # admin beschrijving
        self.assertTrue(str(gast) != '')

        # volg de link om de email te bevestigen
        obj = TijdelijkeCode.objects.first()
        self.assertEqual(obj.hoortbij_gast.pk, gast.pk)
        url = self.url_tijdelijk % obj.url_code

        # haal de pagina op - deze bevat een POST url
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        urls = self.extract_all_urls(resp, skip_menu=True)
        post_url = urls[0]

        # gebruik de POST
        with self.assert_max_queries(37):
            resp = self.client.post(post_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-2-email-bevestigd.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(0, TijdelijkeCode.objects.count())
        self.assertEqual(1, GastRegistratie.objects.count())
        self.assertEqual(2, MailQueue.objects.count())

        mail = MailQueue.objects.exclude(pk=mail.pk).first()
        self.assert_email_html_ok(mail)
        self.assert_consistent_email_html_text(mail)

        # herhaal het verzoek --> deze wordt afgewezen
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'achternaam': self.test_achternaam,
                                     'voornaam': self.test_voornaam,
                                     'email': self.test_email},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout: dubbel verzoek')

        self.assertEqual(1, GastRegistratie.objects.count())
        self.assertEqual(2, MailQueue.objects.count())

    def test_begin_bad(self):
        # onvolledige verzoeken

        # achternaam ontbreek
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {
                                     # 'achternaam': 'test',
                                     'voornaam': 'test',
                                     'email': 'test@test'},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout: de gegevens worden niet geaccepteerd')

        # voornaam ontbreek
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'achternaam': 'test',
                                     #  'voornaam': 'test',
                                     'email': 'test@test'},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout: de gegevens worden niet geaccepteerd')

        # email ontbreek
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'achternaam': 'test',
                                     'voornaam': 'test',
                                     # 'email': 'test@test'
                                    },
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout: de gegevens worden niet geaccepteerd')

        # achternaam leeg
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'achternaam': '',
                                     'voornaam': 'test',
                                     'email': 'test@test'},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout: de gegevens worden niet geaccepteerd')

        # voornaam leeg
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'achternaam': 'test',
                                     'voornaam': '',
                                     'email': 'test@test'},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout: de gegevens worden niet geaccepteerd')

        # email leeg
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'achternaam': 'test',
                                     'voornaam': 'test',
                                     'email': ''},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout: de gegevens worden niet geaccepteerd')

        # slechte email
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'achternaam': 'test',
                                     'voornaam': 'test',
                                     'email': 'test@localhost'},        # @localhost passes EmailValidator checking
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout: voer een valide e-mailadres in')

    def test_bad_create(self):
        # trigger een AccountCreateError met een slechte e-mail

        test_voornaam = 'Bågskytt'
        test_achternaam = 'från Utlandet'
        test_email = 'skytt46@test.se'

        self.assertEqual(0, GastRegistratie.objects.count())
        self.assertEqual(0, MailQueue.objects.count())
        self.assertEqual(0, TijdelijkeCode.objects.count())

        self.client.post(self.url_registreer_gast,
                         {'achternaam': test_achternaam,
                          'voornaam': test_voornaam,
                          'email': test_email},
                         follow=True)

        self.assertEqual(1, GastRegistratie.objects.count())
        self.assertEqual(1, TijdelijkeCode.objects.count())

        gast = GastRegistratie.objects.first()
        self.assertEqual(gast.fase, REGISTRATIE_FASE_EMAIL)

        # volg de link om de email te bevestigen
        obj = TijdelijkeCode.objects.first()
        self.assertEqual(obj.hoortbij_gast.pk, gast.pk)
        url = self.url_tijdelijk % obj.url_code

        # haal de pagina op - deze bevat een POST url
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        urls = self.extract_all_urls(resp, skip_menu=True)
        post_url = urls[0]

        # verpruts het e-mailadres
        gast.email = 'bla!'
        gast.save(update_fields=['email'])

        # gebruik de POST en controleer de foutmelding
        resp = self.client.post(post_url)
        self.assert404(resp, 'Account aanmaken is onverwacht mislukt')

    def test_rate_limiter(self):
        # controleer dat we snelle POSTs blokkeren
        test_voornaam = 'voornaam'
        test_achternaam = 'achternaam'
        test_email = 'voorachter@test.not'

        self.assertEqual(0, GastRegistratie.objects.count())
        self.assertEqual(0, MailQueue.objects.count())

        # voorkom problemen met deze test op het punt van overstappen op een nieuwe minuut
        now = timezone.now()
        if now.second > 55:                         # pragma: no cover
            sleep_seconds = 61 - now.second
            print('Sleeping %s seconds' % sleep_seconds)
            time.sleep(sleep_seconds)

        # basis verzoek
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'achternaam': test_achternaam,
                                     'voornaam': test_voornaam,
                                     'email': test_email},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-1-bevestig-email.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(1, GastRegistratie.objects.count())
        self.assertEqual(1, GastRegistratieRateTracker.objects.count())
        self.assertEqual(1, MailQueue.objects.count())

        # herhaal verzoek met te veel verzoeken in de afgelopen minuut
        tracker = GastRegistratieRateTracker.objects.first()
        tracker.teller_minuut = 50
        tracker.save(update_fields=['teller_minuut'])

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'achternaam': test_achternaam,
                                     'voornaam': test_voornaam,
                                     'email': test_email},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout: te snel')

        self.assertEqual(1, GastRegistratie.objects.count())
        self.assertEqual(1, GastRegistratieRateTracker.objects.count())
        self.assertEqual(1, MailQueue.objects.count())

        # herhaal met veel verzoeker in het afgelopen uur
        tracker = GastRegistratieRateTracker.objects.first()
        tracker.teller_minuut = 1
        tracker.teller_uur = 100
        tracker.save(update_fields=['teller_minuut', 'teller_uur'])

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'achternaam': test_achternaam,
                                     'voornaam': test_voornaam,
                                     'email': test_email},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout: te snel')

        self.assertEqual(1, GastRegistratie.objects.count())
        self.assertEqual(1, GastRegistratieRateTracker.objects.count())
        self.assertEqual(1, MailQueue.objects.count())

        # pas het opgeslagen e-mailadres aan en probeer opnieuw
        tracker = GastRegistratieRateTracker.objects.first()
        tracker.from_ip = 'test'
        tracker.save(update_fields=['from_ip'])

        # admin beschrijving
        self.assertTrue(str(tracker) != '')

        # herhaal verzoek --> deze wordt afgewezen als dubbel verzoek (zelfde naam/email, vanaf een andere IP)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'achternaam': test_achternaam,
                                     'voornaam': test_voornaam,
                                     'email': test_email},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout: dubbel verzoek')

        self.assertEqual(1, GastRegistratie.objects.count())
        self.assertEqual(2, GastRegistratieRateTracker.objects.count())
        self.assertEqual(1, MailQueue.objects.count())

    def test_meer_vragen(self):
        # ontvang naam en e-mailadres + stuur e-mail voor bevestigen
        self.assertEqual(0, GastRegistratie.objects.count())
        self.assertEqual(0, MailQueue.objects.count())
        self.assertEqual(0, TijdelijkeCode.objects.count())

        resp = self.client.post(self.url_registreer_gast,
                                {'achternaam': self.test_achternaam,
                                 'voornaam': self.test_voornaam,
                                 'email': self.test_email},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('registreer/registreer-gast-1-bevestig-email.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(1, GastRegistratie.objects.count())
        gast = GastRegistratie.objects.first()
        self.assertEqual(gast.fase, REGISTRATIE_FASE_EMAIL)

        # volg de link om de email te bevestigen
        self.assertEqual(1, TijdelijkeCode.objects.count())
        obj = TijdelijkeCode.objects.first()
        self.assertEqual(obj.hoortbij_gast.pk, gast.pk)
        url = self.url_tijdelijk % obj.url_code

        # haal de pagina op - deze bevat een POST url
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        urls = self.extract_all_urls(resp, skip_menu=True)
        post_url = urls[0]

        # gebruik de POST
        resp = self.client.post(post_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-2-email-bevestigd.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(urls, [self.url_meer_vragen])

        gast = GastRegistratie.objects.first()
        self.assertEqual(gast.fase, REGISTRATIE_FASE_PASSWORD)

        # gebruiker is nu ingelogd

        # haal de meer-vragen pagina op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_meer_vragen)
        self.e2e_dump_resp(resp)

        # TODO: meer tests

        # registratie done
        gast.fase = REGISTRATIE_FASE_DONE
        gast.save(update_fields=['fase'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_meer_vragen)
        self.assert_is_redirect(resp, '/plein/')

    def test_bad_meer_vragen(self):
        # meer vragen zonder inlog
        self.client.logout()
        resp = self.client.get(self.url_meer_vragen)
        self.assert_is_redirect(resp, '/plein/')

        # ingelogd als een niet-gast
        self.e2e_login(self.account_normaal)
        resp = self.client.get(self.url_meer_vragen)
        self.assert_is_redirect(resp, '/plein/')

# end of file
