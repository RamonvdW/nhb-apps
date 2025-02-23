# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import Functie
from Functie.tests.helpers import maak_functie
from Geo.models import Rayon, Regio
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestFunctieBeheerders(E2EHelpers, TestCase):

    """ tests voor de Functie applicatie, functionaliteit Koppel bestuurders """

    test_after = ('Account.tests.test_otp_controle',)

    url_beheerders = '/functie/beheerders/'
    url_email_sec_hwl = '/functie/beheerders/email/sec-hwl/'
    url_email_competitie = '/functie/beheerders/email/competitie/'
    url_wijzig = '/functie/wijzig/'

    def setUp(self):
        """ initialisatie van de test case """

        # deze test is afhankelijk van de standaard globale functies
        # zoals opgezet door de migratie m0002_functies-2019:
        #   comp_type: 18/25
        #       rol: BKO, RKO (4x), RCL (16x)

        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.nhb', 'Normaal')
        self.account_beh1 = self.e2e_create_account('testbeheerder1', 'beh1@test.nhb', 'Beheerder1',
                                                    accepteer_vhpg=True)
        self.account_beh2 = self.e2e_create_account('testbeheerder2', 'beh2@test.nhb', 'Beheerder2',
                                                    accepteer_vhpg=True)
        self.account_ander = self.e2e_create_account('anderlid', 'anderlid@test.nhb', 'Ander')

        self.functie_mwz = Functie.objects.get(rol='MWZ')
        self.functie_bko_18 = Functie.objects.get(comp_type='18', rol='BKO')
        self.functie_bko_25 = Functie.objects.get(comp_type='25', rol='BKO')
        self.functie_rko3_18 = Functie.objects.get(comp_type='18', rol='RKO', rayon=Rayon.objects.get(rayon_nr=3))
        self.functie_rko2_25 = Functie.objects.get(comp_type='25', rol='RKO', rayon=Rayon.objects.get(rayon_nr=2))
        self.functie_rcl111_18 = Functie.objects.get(comp_type='18', rol='RCL', regio=Regio.objects.get(regio_nr=111))
        self.functie_rcl111_25 = Functie.objects.get(comp_type='25', rol='RCL', regio=Regio.objects.get(regio_nr=111))
        self.functie_rcl101_18 = Functie.objects.get(comp_type='18', rol='RCL', regio=Regio.objects.get(regio_nr=101))

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(pk=111))
        ver.save()

        sporter = Sporter(
                    lid_nr=100042,
                    geslacht="M",
                    voornaam="Beh",
                    achternaam="eerder",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver,
                    account=self.account_beh2,
                    email=self.account_beh2.email)
        sporter.save()
        self.sporter_100042 = sporter

        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.vereniging = ver
        self.functie_sec.save()

        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()

        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.vereniging = ver
        self.functie_wl.save()

        # maak nog een test vereniging
        ver2 = Vereniging(
                    naam="Extra Club",
                    ver_nr=1900,
                    regio=Regio.objects.get(regio_nr=112))
        ver2.save()

        self.functie_hwl2 = maak_functie("HWL test 2", "HWL")
        self.functie_hwl2.vereniging = ver2
        self.functie_hwl2.save()

        sporter = Sporter(
                    lid_nr=100024,
                    geslacht="V",
                    voornaam="Ander",
                    achternaam="Lid",
                    geboorte_datum=datetime.date(year=1972, month=3, day=5),
                    sinds_datum=datetime.date(year=2010, month=11, day=11),
                    bij_vereniging=ver2,
                    account=self.account_ander,
                    email=self.account_ander.email)
        sporter.save()
        self.sporter_100024 = sporter

    def test_anon(self):
        self.e2e_logout()

        # geen rechten om dit overzicht in te zien
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beheerders)
        self.assert403(resp)

        # geen rechten om beheerders te kiezen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig + '123/')
        self.assert403(resp)

    def test_sporter(self):
        # geen rechten om dit overzicht in te zien
        # zelf niet na acceptatie VHPG en OTP controle
        self.e2e_login_and_pass_otp(self.account_normaal)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beheerders)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beheerders + 'vereniging/')
        self.assert403(resp)

    def test_bb(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # neem de BB rol aan
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')
        with self.assert_max_queries(20):
            resp = self.client.get('/plein/')
        self.assert_html_ok(resp)
        self.assertContains(resp, "Manager MH")

        # meerdere accounts met rol IT en BB, voor coverage in de template (for-loop over accounts)
        self.account_beh1.is_BB = True
        self.account_beh1.save(update_fields=['is_BB'])
        self.account_beh2.is_staff = True
        self.account_beh2.is_BB = True
        self.account_beh2.save(update_fields=['is_staff', 'is_BB'])

        self.functie_mwz.accounts.add(self.account_beh1)
        self.functie_mwz.accounts.add(self.account_beh2)

        self.functie_mwz.bevestigde_email = 'mwz@khsn.not'
        self.functie_mwz.save(update_fields=['bevestigde_email'])

        # controleer de Wijzig knoppen op de functie-overzicht pagina
        with self.assert_max_queries(6):
            resp = self.client.get(self.url_beheerders)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/lijst-beheerders.dtl', 'plein/site_layout.dtl'))
        urls = [url for url in self.extract_all_urls(resp) if url.startswith('/functie/wijzig/')]
        self.assertEqual(len(urls), 8)      # MWZ, MWW, MLA, MO, CS, SUP, BKO 18m, BKO 25m

        # controleer de Wijzig knoppen op de functie-overzicht pagina voor verschillende rollen

        # neem de BKO 18m rol aan
        self.e2e_wissel_naar_functie(self.functie_bko_18)
        self.e2e_check_rol('BKO')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beheerders)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/lijst-beheerders.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "BKO Indoor")
        urls = [url for url in self.extract_all_urls(resp) if url.startswith(self.url_wijzig)]
        self.assertEqual(len(urls), 4)      # 4x RKO

        # neem de RKO Rayon 3 Indoor rol aan
        self.e2e_wissel_naar_functie(self.functie_rko3_18)
        self.e2e_check_rol('RKO')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beheerders)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/lijst-beheerders.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "RKO Rayon 3 Indoor")
        urls = [url for url in self.extract_all_urls(resp) if url.startswith(self.url_wijzig)]
        self.assertEqual(len(urls), 4)      # 4x RCL

        # neem de RCL Rayon 111 Indoor aan
        self.e2e_wissel_naar_functie(self.functie_rcl111_18)
        self.e2e_check_rol('RCL')

        # controleer de Wijzig knoppen op de functie-overzicht pagina
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beheerders)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/lijst-beheerders.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "RCL Regio 111 Indoor")
        urls = [url for url in self.extract_all_urls(resp) if url.startswith(self.url_wijzig)]
        self.assertEqual(len(urls), 0)      # geen wijzig knoppen voor de RCL

        self.e2e_assert_other_http_commands_not_supported(self.url_beheerders)

    def test_hwl(self):
        # de HWL krijgt niet het hele overzicht te zien
        # alleen de RCL, RKO, BKO worden getoond die aan de regio gerelateerd zijn
        self.functie_hwl.accounts.add(self.account_beh1)
        self.e2e_login_and_pass_otp(self.account_beh1)

        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # vraag het overzicht van competitie-bestuurders op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beheerders)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/lijst-beheerders.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "HWL")
        urls = [url for url in self.extract_all_urls(resp) if url.startswith(self.url_wijzig)]
        self.assertEqual(len(urls), 0)      # geen wijzig knoppen voor de HWL

        # controleer inhoudelijk op 2xRCL, 2xRKO en 2xBKO (18m en 25m)
        # self.e2e_dump_resp(resp)
        self.assertContains(resp, "BKO", count=4)   # 2 functions, but double entries due to responsive entries
        self.assertContains(resp, "RKO", count=4)
        self.assertContains(resp, "RCL", count=4)

        # haal het overzicht van verenigingsbestuurders op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beheerders + 'vereniging/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/lijst-beheerders-vereniging.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_beheerders + 'vereniging/')

    def test_wl(self):
        # de WL krijgt niet het hele overzicht te zien
        # alleen de RCL, RKO, BKO worden getoond die aan de regio gerelateerd zijn
        self.functie_wl.accounts.add(self.account_beh1)
        self.e2e_login_and_pass_otp(self.account_beh1)

        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')

        # vraag het overzicht van competitie-bestuurders op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beheerders)
        urls = [url for url in self.extract_all_urls(resp) if url.startswith(self.url_wijzig)]
        self.assertEqual(len(urls), 0)      # geen wijzig knoppen voor de WL

        # haal het overzicht van verenigingsbestuurders op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beheerders + 'vereniging/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/lijst-beheerders-vereniging.dtl', 'plein/site_layout.dtl'))

    def test_sec(self):
        # de SEC krijgt niet het hele overzicht te zien
        # alleen de RCL, RKO, BKO worden getoond die aan de regio gerelateerd zijn
        self.functie_sec.accounts.add(self.account_beh1)
        self.e2e_login_and_pass_otp(self.account_beh1)

        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        # vraag het overzicht van competitie-bestuurders op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beheerders)
        urls = [url for url in self.extract_all_urls(resp) if url.startswith(self.url_wijzig)]
        self.assertEqual(len(urls), 0)      # geen wijzig knoppen voor de WL

        # haal het overzicht van verenigingsbestuurders op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beheerders + 'vereniging/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/lijst-beheerders-vereniging.dtl', 'plein/site_layout.dtl'))

    def test_emails_sec_hwl(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_email_sec_hwl)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/emails-sec-hwl.dtl', 'plein/site_layout.dtl'))

        self.e2e_wissel_naar_functie(self.functie_rko3_18)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_email_sec_hwl)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/emails-sec-hwl.dtl', 'plein/site_layout.dtl'))

        self.e2e_wissel_naar_functie(self.functie_rcl111_18)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_email_sec_hwl)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/emails-sec-hwl.dtl', 'plein/site_layout.dtl'))

    def test_emails_beheerders(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        # BB
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_email_competitie)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/emails-beheerders.dtl', 'plein/site_layout.dtl'))

        # MWZ
        self.e2e_wissel_naar_functie(self.functie_mwz)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_email_competitie)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/emails-beheerders.dtl', 'plein/site_layout.dtl'))

        # BKO Indoor
        self.e2e_wissel_naar_functie(self.functie_bko_18)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_email_competitie)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/emails-beheerders.dtl', 'plein/site_layout.dtl'))

        # BKO 25m1pijl
        self.e2e_wissel_naar_functie(self.functie_bko_25)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_email_competitie)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/emails-beheerders.dtl', 'plein/site_layout.dtl'))

        # RKO Indoor
        self.assertTrue(self.functie_rko3_18.is_indoor())
        self.assertFalse(self.functie_rko3_18.is_25m1pijl())
        self.e2e_wissel_naar_functie(self.functie_rko3_18)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_email_competitie)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/emails-beheerders.dtl', 'plein/site_layout.dtl'))

        # RKO 25m1pijl
        self.assertFalse(self.functie_rko2_25.is_indoor())
        self.assertTrue(self.functie_rko2_25.is_25m1pijl())
        self.e2e_wissel_naar_functie(self.functie_rko2_25)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_email_competitie)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/emails-beheerders.dtl', 'plein/site_layout.dtl'))

        # RCL
        self.e2e_wissel_naar_functie(self.functie_rcl111_18)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_email_competitie)
        self.assert403(resp, 'Geen toegang')


# end of file
