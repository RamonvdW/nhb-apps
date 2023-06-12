# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.models import Account
from Functie.models import Functie
from Mailer.models import MailQueue
from NhbStructuur.models import NhbRegio, NhbVereniging
from Registreer.definities import REGISTRATIE_FASE_EMAIL
from Registreer.models import GastRegistratie, GastRegistratieRateTracker
from Sporter.models import Sporter
from TijdelijkeCodes.models import TijdelijkeCode
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Secretaris
import datetime


class TestRegistreerGast(E2EHelpers, TestCase):

    """ tests voor de Registreer applicatie; voor gast-accounts """

    test_after = ('Account',)

    url_registreer_gast = '/account/registreer/gast/'
    url_tijdelijk = '/tijdelijke-codes/%s/'

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        # # maak een test vereniging
        # ver = NhbVereniging(
        #             naam="Grote Club",
        #             ver_nr="1000",
        #             regio=NhbRegio.objects.get(pk=111))
        # ver.save()
        #
        # # maak een test lid aan
        # sporter = Sporter(
        #             lid_nr=100001,
        #             geslacht="M",
        #             voornaam="Ramon",
        #             achternaam="de Tester",
        #             email="normaal@test.com",
        #             geboorte_datum=datetime.date(year=1972, month=3, day=4),
        #             sinds_datum=datetime.date(year=2010, month=11, day=12),
        #             bij_vereniging=ver,
        #             account=self.account_normaal)
        # sporter.save()
        # self.sporter = sporter

    def test_get(self):
        # haal het formulier op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_registreer_gast)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Fout:')

    def test_fase_begin(self):
        # ontvang naam en e-mailadres + stuur e-mail voor bevestigen
        test_voornaam = 'Bågskytt'
        test_achternaam = 'från Utlandet'
        test_email = 'skytt46@test.se'

        self.assertEqual(0, GastRegistratie.objects.count())
        self.assertEqual(0, MailQueue.objects.count())
        self.assertEqual(0, TijdelijkeCode.objects.count())

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
        gast = GastRegistratie.objects.first()
        # print(gast)
        self.assertEqual(gast.voornaam, test_voornaam)
        self.assertEqual(gast.achternaam, test_achternaam)
        self.assertEqual(gast.email, test_email)
        self.assertFalse(gast.email_is_bevestigd)
        self.assertEqual(gast.fase, REGISTRATIE_FASE_EMAIL)

        self.assertEqual(1, MailQueue.objects.count())
        self.assertEqual(1, TijdelijkeCode.objects.count())

        # TODO: check e-mail inhoud

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
        with self.assert_max_queries(20):
            resp = self.client.post(post_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-gast-2-email-bevestigd.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(0, TijdelijkeCode.objects.count())
        self.assertEqual(1, GastRegistratie.objects.count())
        self.assertEqual(2, MailQueue.objects.count())

        # TODO: check e-mail inhoud

        # voorkom ingreep door de rate limiter
        GastRegistratieRateTracker.objects.all().delete()

        # herhaal het verzoek --> deze wordt afgewezen
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

    def test_rate_limiter(self):
        # controleer dat we snelle POSTs blokkeren
        test_voornaam = 'voornaam'
        test_achternaam = 'achternaam'
        test_email = 'voorachter@test.not'

        self.assertEqual(0, GastRegistratie.objects.count())
        self.assertEqual(0, MailQueue.objects.count())

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

        # herhaal verzoek --> deze wordt afgewezen
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


# end of file
