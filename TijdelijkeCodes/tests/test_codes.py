# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.http import HttpResponseRedirect
from BasisTypen.models import BoogType
from Competitie.models import Competitie, CompetitieIndivKlasse, Kampioenschap, KampioenschapSporterBoog
from Functie.models import Functie
from Geo.models import Rayon
from Sporter.models import SporterBoog, Sporter
from Registreer.models import GastRegistratie
from TijdelijkeCodes.definities import (RECEIVER_BEVESTIG_EMAIL_ACCOUNT, RECEIVER_BEVESTIG_EMAIL_FUNCTIE,
                                        RECEIVER_BEVESTIG_EMAIL_REG_LID, RECEIVER_BEVESTIG_EMAIL_REG_GAST,
                                        RECEIVER_ACCOUNT_WISSEL, RECEIVER_WACHTWOORD_VERGETEN,
                                        RECEIVER_DEELNAME_KAMPIOENSCHAP)
from TijdelijkeCodes.models import TijdelijkeCode, save_tijdelijke_code
from TijdelijkeCodes.operations import (tijdelijke_code_dispatcher, set_tijdelijke_codes_receiver,
                                        maak_tijdelijke_code_bevestig_email_account,
                                        maak_tijdelijke_code_bevestig_email_registreer_lid,
                                        maak_tijdelijke_code_bevestig_email_registreer_gast,
                                        maak_tijdelijke_code_accountwissel,
                                        maak_tijdelijke_code_wachtwoord_vergeten,
                                        maak_tijdelijke_code_bevestig_email_functie,
                                        maak_tijdelijke_code_deelname_kampioenschap)
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from datetime import timedelta


class TestTijdelijkeCodes(E2EHelpers, TestCase):

    """ tests voor de TijdelijkeCodes applicatie """

    testdata = None
    url_code_prefix = '/tijdelijke-codes/'
    url_code = '/tijdelijke-codes/%s/'

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()

    def setUp(self):
        """ initialisatie van de test case """
        tijdelijke_code_dispatcher.test_backup()

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        self.account_normaal.nieuwe_email = "hoi@gmail.not"
        self.account_normaal.save(update_fields=['nieuwe_email'])

    def tearDown(self):
        tijdelijke_code_dispatcher.test_restore()

    def test_code_bestaat_niet(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_code % 'test')
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('tijdelijkecodes/code-fout.dtl', 'design/site_layout.dtl'))

    def test_verlopen(self):
        obj = save_tijdelijke_code('code1', 'iets_anders', geldig_dagen=-1)
        self.assertTrue(str(obj) != '')

        obj = save_tijdelijke_code('code1', 'bevestig_email', geldig_dagen=1)
        self.assertTrue(str(obj) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_code % 'code1')
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('tijdelijkecodes/code-goed.dtl', 'design/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        self.assertEqual(1, len(urls))
        self.assertTrue(self.url_code_prefix in urls[0])
        url = urls[0]

        # pas de datum aan zodat deze verlopen is tijdens de POST
        obj.geldig_tot = obj.aangemaakt_op - timedelta(days=1)
        obj.save()

        # volg de 'ga door' knop
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, '/plein/')

    def test_bad_dispatch_to(self):
        save_tijdelijke_code('code3', 'onbekend', geldig_dagen=1)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_code % 'code3')
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('tijdelijkecodes/code-goed.dtl', 'design/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(1, len(urls))
        self.assertTrue(self.url_code_prefix in urls[0])

        # volg de 'ga door' knop
        url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, '/plein/')

    def test_onbekend_topic(self):
        with self.assertRaises(NotImplementedError):
            tijdelijke_code_dispatcher.get_receiver('bestaat niet')

    def test_setup_dispatcher(self):
        set_tijdelijke_codes_receiver("my topic", "123")
        self.assertEqual(tijdelijke_code_dispatcher.get_receiver("my topic"), "123")

    def _my_receiver_func_email(self, request, hoortbij_account):
        # self.assertEqual(request, "request")
        self.assertEqual(hoortbij_account, self.account_normaal)
        self.callback_count += 1
        url = "/feedback/bedankt/"
        if self.callback_count == 1:
            # return url
            return url
        else:
            # return response
            return HttpResponseRedirect(url)

    def _my_receiver_func_1_arg(self, request, hoortbij):
        # self.assertEqual(request, "request")
        self.callback_count += 1
        url = "/feedback/bedankt/"
        return url

    def test_bevestig_email_account(self):
        set_tijdelijke_codes_receiver(RECEIVER_BEVESTIG_EMAIL_ACCOUNT, self._my_receiver_func_email)

        url = maak_tijdelijke_code_bevestig_email_account(self.account_normaal, test="een")
        self.assertTrue(self.url_code_prefix in url)
        self.callback_count = 1

        # extra coverage
        obj = TijdelijkeCode.objects.first()
        self.assertTrue(str(obj) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('tijdelijkecodes/code-goed.dtl', 'design/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(1, len(urls))
        self.assertTrue(self.url_code_prefix in urls[0])
        self.assertEqual(self.callback_count, 1)

        # volg de 'ga door' knop
        url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.callback_count, 2)
        # _my_receiver_func stuurt door naar de feedback-bedankt pagina
        self.assert_template_used(resp, ('feedback/bedankt.dtl', 'design/site_layout.dtl'))

    def test_account_wissel(self):
        set_tijdelijke_codes_receiver(RECEIVER_ACCOUNT_WISSEL, self._my_receiver_func_email)

        url = maak_tijdelijke_code_accountwissel(self.account_normaal, test="twee")
        self.assertTrue(self.url_code_prefix in url)
        self.callback_count = 0

        # extra coverage
        obj = TijdelijkeCode.objects.first()
        self.assertTrue(str(obj) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('tijdelijkecodes/code-goed.dtl', 'design/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(1, len(urls))
        self.assertTrue(self.url_code_prefix in urls[0])
        self.assertEqual(self.callback_count, 0)

        # volg de 'ga door' knop
        url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.callback_count, 1)
        # _my_receiver_func stuurt door naar de feedback-bedankt pagina
        self.assert_template_used(resp, ('feedback/bedankt.dtl', 'design/site_layout.dtl'))

    def test_wachtwoord_vergeten(self):
        set_tijdelijke_codes_receiver(RECEIVER_WACHTWOORD_VERGETEN, self._my_receiver_func_email)
        url = maak_tijdelijke_code_wachtwoord_vergeten(self.account_normaal, test="drie")
        self.assertTrue(self.url_code_prefix in url)
        self.callback_count = 0

        # extra coverage
        obj = TijdelijkeCode.objects.first()
        self.assertTrue(str(obj) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('tijdelijkecodes/code-goed.dtl', 'design/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(1, len(urls))
        self.assertTrue(self.url_code_prefix in urls[0])
        self.assertEqual(self.callback_count, 0)

        # volg de 'ga door' knop
        url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.callback_count, 1)
        # _my_receiver_func stuurt door naar de feedback-bedankt pagina
        self.assert_template_used(resp, ('feedback/bedankt.dtl', 'design/site_layout.dtl'))

    def test_bevestig_email_functie(self):
        set_tijdelijke_codes_receiver(RECEIVER_BEVESTIG_EMAIL_FUNCTIE, self._my_receiver_func_1_arg)

        functie = Functie.objects.filter(rol='BKO').first()
        url = maak_tijdelijke_code_bevestig_email_functie(functie)
        self.assertTrue(self.url_code_prefix in url)
        self.callback_count = 0

        # extra coverage
        obj = TijdelijkeCode.objects.first()
        self.assertTrue(str(obj) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('tijdelijkecodes/code-goed.dtl', 'design/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(1, len(urls))
        url = urls[0]
        self.assertTrue(self.url_code_prefix in url)
        self.assertEqual(self.callback_count, 0)

        # volg de 'ga door' knop
        with self.assert_max_queries(20):
            resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.callback_count, 1)
        # _my_receiver_func stuurt door naar de feedback-bedankt pagina
        self.assert_template_used(resp, ('feedback/bedankt.dtl', 'design/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_code % '0', post=False)

    def test_registreer_lid(self):
        set_tijdelijke_codes_receiver(RECEIVER_BEVESTIG_EMAIL_REG_LID, self._my_receiver_func_1_arg)

        url = maak_tijdelijke_code_bevestig_email_registreer_lid(self.account_normaal, lid="een")
        self.assertTrue(self.url_code_prefix in url)
        self.callback_count = 0

        # extra coverage
        obj = TijdelijkeCode.objects.first()
        self.assertTrue(str(obj) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('tijdelijkecodes/code-goed.dtl', 'design/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(1, len(urls))
        url = urls[0]
        self.assertTrue(self.url_code_prefix in url)
        self.assertEqual(self.callback_count, 0)

        # volg de 'ga door' knop
        with self.assert_max_queries(20):
            resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.callback_count, 1)
        # _my_receiver_func stuurt door naar de feedback-bedankt pagina
        self.assert_template_used(resp, ('feedback/bedankt.dtl', 'design/site_layout.dtl'))

    def test_registreer_gast(self):
        set_tijdelijke_codes_receiver(RECEIVER_BEVESTIG_EMAIL_REG_GAST, self._my_receiver_func_1_arg)

        gast = GastRegistratie(lid_nr=123456)
        gast.save()
        url = maak_tijdelijke_code_bevestig_email_registreer_gast(gast)
        self.assertTrue(self.url_code_prefix in url)
        self.callback_count = 0

        # extra coverage
        obj = TijdelijkeCode.objects.first()
        self.assertTrue(str(obj) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('tijdelijkecodes/code-goed.dtl', 'design/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(1, len(urls))
        url = urls[0]
        self.assertTrue(self.url_code_prefix in url)
        self.assertEqual(self.callback_count, 0)

        # volg de 'ga door' knop
        with self.assert_max_queries(20):
            resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.callback_count, 1)
        # _my_receiver_func stuurt door naar de feedback-bedankt pagina
        self.assert_template_used(resp, ('feedback/bedankt.dtl', 'design/site_layout.dtl'))

    def test_kampioen(self):
        set_tijdelijke_codes_receiver(RECEIVER_DEELNAME_KAMPIOENSCHAP, self._my_receiver_func_1_arg)

        boog_r = BoogType.objects.get(afkorting='R')

        sporter = Sporter(
                    lid_nr=100000,
                    voornaam='Ad',
                    achternaam='de Admin',
                    geboorte_datum='1966-06-06',
                    sinds_datum='2020-02-02')
        sporter.save()

        sporterboog = SporterBoog(
                            sporter=sporter,
                            boogtype=boog_r,
                            voor_wedstrijd=True)
        sporterboog.save()

        comp = Competitie(afstand=18, begin_jaar=2023)
        comp.save()

        klasse = CompetitieIndivKlasse(
                    competitie=comp,
                    volgorde=1,
                    boogtype=boog_r,
                    min_ag=0)
        klasse.save()

        kamp = Kampioenschap(
                    competitie=comp,
                    deel='RK',
                    rayon=Rayon.objects.first(),
                    functie=Functie.objects.filter(rol='RKO').first())
        kamp.save()

        kamp = KampioenschapSporterBoog(
                    kampioenschap=kamp,
                    sporterboog=sporterboog,
                    indiv_klasse=klasse)
        kamp.save()

        url = maak_tijdelijke_code_deelname_kampioenschap(kamp)
        self.assertTrue(self.url_code_prefix in url)
        self.callback_count = 0

        # extra coverage
        obj = TijdelijkeCode.objects.first()
        self.assertTrue(str(obj) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('tijdelijkecodes/code-goed.dtl', 'design/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(1, len(urls))
        url = urls[0]
        self.assertTrue(self.url_code_prefix in url)
        self.assertEqual(self.callback_count, 0)

        # volg de 'ga door' knop
        with self.assert_max_queries(20):
            resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.callback_count, 1)
        # _my_receiver_func stuurt door naar de feedback-bedankt pagina
        self.assert_template_used(resp, ('feedback/bedankt.dtl', 'design/site_layout.dtl'))


# end of file
