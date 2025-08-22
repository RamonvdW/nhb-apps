# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.definities import GESLACHT_MAN
from Mailer.models import MailQueue
from Registreer.definities import (REGISTRATIE_FASE_EMAIL, REGISTRATIE_FASE_PASS, REGISTRATIE_FASE_CLUB,
                                   REGISTRATIE_FASE_LAND, REGISTRATIE_FASE_AGE, REGISTRATIE_FASE_TEL,
                                   REGISTRATIE_FASE_WA_ID, REGISTRATIE_FASE_GENDER,
                                   REGISTRATIE_FASE_CONFIRM, REGISTRATIE_FASE_COMPLEET)
from Registreer.models import GastRegistratie, GastRegistratieRateTracker, GastLidNummer
from Sporter.models import Sporter
from TijdelijkeCodes.models import TijdelijkeCode
from TestHelpers.e2ehelpers import E2EHelpers
import time


class TestRegistreerGast(E2EHelpers, TestCase):

    """ tests voor de Registreer applicatie; voor gast-accounts """

    test_after = ('Account',)

    url_registreer_gast = '/account/registreer/gast/'
    url_meer_vragen = '/account/registreer/gast/meer-vragen/'
    url_volgende_vraag = '/account/registreer/gast/volgende-vraag/'

    url_tijdelijk = '/tijdelijke-codes/%s/'
    url_sporter_profiel = '/sporter/'
    url_plein = '/plein/'

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
        self.assert_template_used(resp, ('registreer/registreer-gast-01-bevestig-email.dtl', 'plein/site_layout.dtl'))

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
        self.assert_email_html_ok(mail, 'email_registreer/gast-bevestig-toegang-email.dtl')
        self.assert_consistent_email_html_text(mail)

        # admin beschrijving
        self.assertTrue(str(gast) != '')

        # volg de link om de email te bevestigen
        obj = TijdelijkeCode.objects.first()
        self.assertTrue(str(obj) != '')         # coverage of __str__
        self.assertEqual(obj.hoort_bij_gast_reg.pk, gast.pk)
        url = self.url_tijdelijk % obj.url_code

        # haal de pagina op - deze bevat een POST url
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        urls = self.extract_all_urls(resp, skip_menu=True)
        post_url = urls[0]

        # gebruik de POST
        with self.assert_max_queries(39):
            resp = self.client.post(post_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-02-email-bevestigd.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(0, TijdelijkeCode.objects.count())
        self.assertEqual(1, GastRegistratie.objects.count())
        self.assertEqual(2, MailQueue.objects.count())

        mail = MailQueue.objects.exclude(pk=mail.pk).first()
        self.assert_email_html_ok(mail, 'email_registreer/gast-tijdelijk-bondsnummer.dtl')
        self.assert_consistent_email_html_text(mail)

        # herhaal het verzoek --> deze wordt afgewezen
        self.client.logout()
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

    def test_kill_switch(self):
        # controleer gedrag van de kill-switch
        volgende = GastLidNummer.objects.first()
        volgende.kan_aanmaken = False
        volgende.save(update_fields=['kan_aanmaken'])

        self.assertEqual(0, GastRegistratie.objects.count())
        self.assertEqual(0, MailQueue.objects.count())
        self.assertEqual(0, TijdelijkeCode.objects.count())

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_registreer_gast)

        self.assertContains(resp,
                            'Registratie van gast-accounts is op dit moment niet mogelijk. Probeer het later nog eens.')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'achternaam': self.test_achternaam,
                                     'voornaam': self.test_voornaam,
                                     'email': self.test_email},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))

        self.assertContains(resp,
                            'Registratie van gast-accounts is op dit moment niet mogelijk. Probeer het later nog eens.')

        self.assertEqual(0, GastRegistratie.objects.count())

    def test_begin_bad(self):
        # onvolledige verzoeken

        # achternaam ontbreek
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'voornaam': 'test', 'email': 'test@test'},     # geen achternaam
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout: de gegevens worden niet geaccepteerd')

        # voornaam ontbreek
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'achternaam': 'test', 'email': 'test@test'},   # geen voornaam
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout: de gegevens worden niet geaccepteerd')

        # email ontbreek
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'achternaam': 'test', 'voornaam': 'test'},     # geen email
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout: de gegevens worden niet geaccepteerd')

        # achternaam leeg
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'achternaam': '', 'voornaam': 'test', 'email': 'test@test'},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout: de gegevens worden niet geaccepteerd')

        # voornaam leeg
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'achternaam': 'test', 'voornaam': '', 'email': 'test@test'},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout: de gegevens worden niet geaccepteerd')

        # email leeg
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_gast,
                                    {'achternaam': 'test', 'voornaam': 'test', 'email': ''},
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
        self.assertContains(resp, 'Fout: de gegevens worden niet geaccepteerd')

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
        self.assertEqual(obj.hoort_bij_gast_reg.pk, gast.pk)
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
        self.assert_template_used(resp, ('registreer/registreer-gast-01-bevestig-email.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(1, GastRegistratie.objects.count())
        self.assertEqual(1, GastRegistratieRateTracker.objects.count())
        self.assertEqual(1, MailQueue.objects.count())

        # herhaal verzoek met te veel verzoeken in de afgelopen minuut
        tracker = GastRegistratieRateTracker.objects.first()
        tracker.teller_minuut = 3 + 1
        tracker.teller_uur = 3
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
        tracker.teller_uur = 10 + 1
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
        self.assert_template_used(resp, ('registreer/registreer-gast-01-bevestig-email.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(1, GastRegistratie.objects.count())
        gast = GastRegistratie.objects.first()
        self.assertEqual(gast.voornaam, self.test_voornaam)
        self.assertEqual(gast.achternaam, self.test_achternaam)
        self.assertEqual(gast.email, self.test_email)
        self.assertFalse(gast.email_is_bevestigd)
        self.assertEqual(gast.fase, REGISTRATIE_FASE_EMAIL)

        # volg de link om de email te bevestigen
        self.assertEqual(1, TijdelijkeCode.objects.count())
        obj = TijdelijkeCode.objects.first()
        url = self.url_tijdelijk % obj.url_code

        # haal de pagina op - deze bevat een POST url
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        post_url = self.extract_all_urls(resp, skip_menu=True)[0]

        # gebruik de POST
        resp = self.client.post(post_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-02-email-bevestigd.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(urls, [self.url_volgende_vraag])

        gast = GastRegistratie.objects.first()
        self.assertTrue(gast.email_is_bevestigd)
        self.assertEqual(gast.fase, REGISTRATIE_FASE_PASS)

        # gebruiker is nu ingelogd

        # haal de "meer-vragen" pagina op waar verschillende delen van de site heen kunnen verwijzen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_meer_vragen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-03-vervolg.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(urls, [self.url_volgende_vraag])

        # vraag: wachtwoord
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_volgende_vraag)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-04-kies-wachtwoord.dtl', 'plein/site_layout.dtl'))

        # POST een verkeerd antwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-04-kies-wachtwoord.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout:')

        # POST een goed antwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag, {'pass': E2EHelpers.WACHTWOORD})
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        gast = GastRegistratie.objects.first()
        self.assertEqual(gast.fase, REGISTRATIE_FASE_CLUB)

        # bovenstaande maakt een nieuwe sessie aan, waardoor de eerstvolgende GET de sessie aanpast en schrijft
        # with self.assert_max_queries(20):     # geeft concurrency melding door aanmaken sessie tijdens GET
        resp = self.client.get(self.url_volgende_vraag)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-05-club.dtl', 'plein/site_layout.dtl'))

        # POST een verkeerd antwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-05-club.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout:')

        # POST een goed antwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag, {'club': 'Pijlclub', 'plaats': 'Boogstad'})
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        gast = GastRegistratie.objects.first()
        self.assertEqual(gast.club, 'Pijlclub')
        self.assertEqual(gast.club_plaats, 'Boogstad')
        self.assertEqual(gast.fase, REGISTRATIE_FASE_LAND)

        # ga naar Het Plein - deze redirect meteen naar de meer-vragen pagina
        resp = self.client.get(self.url_plein)
        self.assert_is_redirect(resp, self.url_meer_vragen)

        # ga naar Mijn Pagina - deze redirect meteen naar de meer-vragen pagina
        resp = self.client.get(self.url_sporter_profiel)
        self.assert_is_redirect(resp, self.url_meer_vragen)

        # vraag: land, bond, lidnummer
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_volgende_vraag)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-06-land-bond-nr.dtl', 'plein/site_layout.dtl'))

        # POST een verkeerd antwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-06-land-bond-nr.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout:')

        # POST een goed antwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag, {'land': 'Boogland', 'bond': 'Boogbond', 'lid_nr': '666'})
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        gast = GastRegistratie.objects.first()
        self.assertEqual(gast.eigen_sportbond_naam, 'Boogbond')
        self.assertEqual(gast.eigen_lid_nummer, '666')
        self.assertEqual(gast.land, 'Boogland')
        self.assertEqual(gast.fase, REGISTRATIE_FASE_AGE)

        # vraag: geboortedatum
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_volgende_vraag)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-07-age.dtl', 'plein/site_layout.dtl'))

        # POST een verkeerd antwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-07-age.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout:')

        # POST een verkeerd antwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag, {'jaar': '2000', 'maand': '13', 'dag': '01'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-07-age.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout:')

        # POST een verkeerd antwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag, {'jaar': '9999', 'maand': '12', 'dag': '1'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-07-age.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout:')

        # POST een verkeerd antwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag, {'jaar': '0x1234', 'maand': '1-2', 'dag': '#'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-07-age.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout:')

        # POST een goed antwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag, {'jaar': '2000', 'maand': '12', 'dag': '31'})
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        gast = GastRegistratie.objects.first()
        self.assertEqual(gast.geboorte_datum.year, 2000)
        self.assertEqual(gast.geboorte_datum.month, 12)
        self.assertEqual(gast.geboorte_datum.day, 31)
        self.assertEqual(gast.fase, REGISTRATIE_FASE_TEL)

        # vraag: telefoonnummer
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_volgende_vraag)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-08-tel.dtl', 'plein/site_layout.dtl'))

        # POST een verkeerd antwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-08-tel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout:')

        # POST een goed antwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag, {'tel': '+004642140440'})
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        gast = GastRegistratie.objects.first()
        self.assertEqual(gast.telefoon, '+004642140440')
        self.assertEqual(gast.fase, REGISTRATIE_FASE_WA_ID)

        # vraag: WA id
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_volgende_vraag)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-09-wa-id.dtl', 'plein/site_layout.dtl'))

        # POST een antwoord (altijd goed)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag, {'wa_id': '12345'})
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        gast = GastRegistratie.objects.first()
        self.assertEqual(gast.wa_id, '12345')
        self.assertEqual(gast.fase, REGISTRATIE_FASE_GENDER)

        # vraag: Gender
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_volgende_vraag)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-10-gender.dtl', 'plein/site_layout.dtl'))

        # POST een verkeerd antwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-10-gender.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout:')

        # POST een goed antwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag, {'gender': 'M'})
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        gast = GastRegistratie.objects.first()
        self.assertEqual(gast.geslacht, 'M')
        self.assertEqual(gast.fase, REGISTRATIE_FASE_CONFIRM)

        # confirm pagina
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_volgende_vraag)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-25-confirm.dtl', 'plein/site_layout.dtl'))

        # POST een verkeerd antwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag)
        self.assert_is_redirect(resp, self.url_volgende_vraag)

        # POST een negatief goed antwoord (nog een rondje wijzigen)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag, {'bevestigd': 'Nee'})
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        gast = GastRegistratie.objects.first()
        self.assertEqual(gast.fase, REGISTRATIE_FASE_CLUB)

        # vraag: geboortedatum (met al ingevulde niet-default datum)
        gast = GastRegistratie.objects.first()
        gast.fase = REGISTRATIE_FASE_AGE
        gast.save(update_fields=['fase'])
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_volgende_vraag)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-07-age.dtl', 'plein/site_layout.dtl'))

        gast.fase = REGISTRATIE_FASE_CONFIRM
        gast.save(update_fields=['fase'])

        # POST een positief goed antwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag, {'bevestigd': 'Ja'})
        self.assert_is_redirect(resp, self.url_sporter_profiel)
        gast = GastRegistratie.objects.first()
        self.assertEqual(gast.fase, REGISTRATIE_FASE_COMPLEET)

        sporter = gast.sporter
        self.assertEqual(sporter.voornaam, self.test_voornaam)

        # nog een keer, dan bestaat het Sporter record al
        gast.fase = REGISTRATIE_FASE_CONFIRM
        gast.save(update_fields=['fase'])

        sporter_count = Sporter.objects.count()

        # POST een goed antwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag, {'bevestigd': 'Ja'})
        self.assert_is_redirect(resp, self.url_sporter_profiel)
        gast = GastRegistratie.objects.first()
        self.assertEqual(gast.fase, REGISTRATIE_FASE_COMPLEET)

        self.assertEqual(sporter_count, Sporter.objects.count())

        # registratie done
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_meer_vragen)
        self.assert_is_redirect(resp, '/plein/')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_volgende_vraag)
        self.assert_is_redirect(resp, '/plein/')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag)
        self.assert_is_redirect(resp, '/plein/')

        # ga naar Het Plein - deze redirect niet meer naar de meer-vragen pagina
        resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('plein/plein-sporter.dtl', 'plein/site_layout.dtl'))

        # ga naar Mijn Pagina - deze redirect niet meer naar de meer-vragen pagina
        resp = self.client.get(self.url_sporter_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))

        # niet bestaande fase
        gast.fase = 666
        gast.save(update_fields=['fase'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_volgende_vraag)
        self.assert404(resp, 'Verkeerde fase')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_volgende_vraag)
        self.assert404(resp, 'Verkeerde fase')

    def test_bad_meer_vragen(self):
        # meer vragen zonder inlog
        self.client.logout()
        resp = self.client.get(self.url_meer_vragen)
        self.assert_is_redirect(resp, '/plein/')
        resp = self.client.get(self.url_volgende_vraag)
        self.assert_is_redirect(resp, '/plein/')

        # ingelogd als een niet-gast
        self.e2e_login(self.account_normaal)
        resp = self.client.get(self.url_meer_vragen)
        self.assert_is_redirect(resp, '/plein/')
        resp = self.client.get(self.url_volgende_vraag)
        self.assert_is_redirect(resp, '/plein/')

    def test_bekend_als_lid(self):
        # emailadres is in gebruikt voor een sporter
        now = timezone.now()
        Sporter.objects.create(
                            lid_nr=150001,
                            voornaam='Test',
                            achternaam='Test',
                            email=self.test_email,
                            geboorte_datum='2000-01-01',
                            geslacht=GESLACHT_MAN,
                            sinds_datum='2020-01-01',
                            lid_tot_einde_jaar=now.year)

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
        self.assert_template_used(resp, ('registreer/registreer-gast-01-bevestig-email.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(1, GastRegistratie.objects.count())
        gast = GastRegistratie.objects.first()
        self.assertEqual(gast.voornaam, self.test_voornaam)
        self.assertEqual(gast.achternaam, self.test_achternaam)
        self.assertEqual(gast.email, self.test_email)
        self.assertFalse(gast.email_is_bevestigd)
        self.assertEqual(gast.fase, REGISTRATIE_FASE_EMAIL)

        # volg de link om de email te bevestigen
        self.assertEqual(1, TijdelijkeCode.objects.count())
        obj = TijdelijkeCode.objects.first()
        url = self.url_tijdelijk % obj.url_code

        # haal de pagina op - deze bevat een POST url
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        post_url = self.extract_all_urls(resp, skip_menu=True)[0]

        # gebruik de POST
        resp = self.client.post(post_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-98-bekend-als-lid.dtl', 'plein/site_layout.dtl'))
        # self.e2e_open_in_browser(resp)

    def test_bekend_voor_leden(self):
        # e-mailadres is in gebruikt voor meerdere sporters
        # emailadres is in gebruikt voor een sporter
        now = timezone.now()
        Sporter.objects.create(
                            lid_nr=150001,
                            voornaam='Test1',
                            achternaam='Test',
                            email=self.test_email,
                            geboorte_datum='2000-01-01',
                            geslacht=GESLACHT_MAN,
                            sinds_datum='2020-01-01',
                            lid_tot_einde_jaar=now.year)
        Sporter.objects.create(
                            lid_nr=150002,
                            voornaam='Test2',
                            achternaam='Test',
                            email=self.test_email,
                            geboorte_datum='2000-01-01',
                            geslacht=GESLACHT_MAN,
                            sinds_datum='2020-01-01',
                            lid_tot_einde_jaar=now.year)

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
        self.assert_template_used(resp, ('registreer/registreer-gast-01-bevestig-email.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(1, GastRegistratie.objects.count())
        gast = GastRegistratie.objects.first()
        self.assertEqual(gast.voornaam, self.test_voornaam)
        self.assertEqual(gast.achternaam, self.test_achternaam)
        self.assertEqual(gast.email, self.test_email)
        self.assertFalse(gast.email_is_bevestigd)
        self.assertEqual(gast.fase, REGISTRATIE_FASE_EMAIL)

        # volg de link om de email te bevestigen
        self.assertEqual(1, TijdelijkeCode.objects.count())
        obj = TijdelijkeCode.objects.first()
        url = self.url_tijdelijk % obj.url_code

        # haal de pagina op - deze bevat een POST url
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        post_url = self.extract_all_urls(resp, skip_menu=True)[0]

        # gebruik de POST
        resp = self.client.post(post_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-98-bekend-als-lid.dtl', 'plein/site_layout.dtl'))
        # self.e2e_open_in_browser(resp)


# end of file
