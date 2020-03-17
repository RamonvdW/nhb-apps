# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import maak_functie, Functie
from .rol import rol_zet_sessionvars_na_otp_controle
from Account.models import Account,\
                    account_zet_sessionvars_na_otp_controle,\
                    account_vhpg_is_geaccepteerd
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging
from Plein.tests import assert_html_ok, assert_template_used, assert_other_http_commands_not_supported
from Plein.test_helpers import extract_all_href_urls


class TestFunctieKoppelen(TestCase):
    """ unit tests voor de Functie applicatie, functionaliteit Koppelen van bestuurders """

    def setUp(self):
        """ initialisatie van de test case """

        # deze test is afhankelijk van de standaard globale functies
        # zoals opgezet door de migratie m0002_functies-2019:
        #   comp_type: 18/25
        #       rol: BKO, RKO (4x), RCL (16x)

        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        self.account_normaal = Account.objects.get(username='normaal')
        account_vhpg_is_geaccepteerd(self.account_normaal)

        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        self.account_admin = Account.objects.get(username='admin')
        account_vhpg_is_geaccepteerd(self.account_admin)

        usermodel.objects.create_user('testbeheerder1', 'beh1@test.com', 'wachtwoord')
        self.account_beh1 = Account.objects.get(username='testbeheerder1')
        account_vhpg_is_geaccepteerd(self.account_beh1)

        usermodel.objects.create_user('testbeheerder2', 'beh2@test.com', 'wachtwoord')
        self.account_beh2 = Account.objects.get(username='testbeheerder2')
        account_vhpg_is_geaccepteerd(self.account_beh2)

        self.functie_bko = Functie.objects.get(comp_type='18', rol='BKO')
        self.functie_rko3 = Functie.objects.get(comp_type='18', rol='RKO', nhb_rayon=NhbRayon.objects.get(rayon_nr=3))
        self.functie_rcl111 = Functie.objects.get(comp_type='18', rol='RCL', nhb_regio=NhbRegio.objects.get(regio_nr=111))
        self.functie_rcl101 = Functie.objects.get(comp_type='18', rol='RCL', nhb_regio=NhbRegio.objects.get(regio_nr=101))

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = NhbRegio.objects.get(regio_nr=111)
        # secretaris kan nog niet ingevuld worden
        ver.save()

        self.functie_cwz = maak_functie("CWZ test", "CWZ")
        self.functie_cwz.nhb_ver = ver
        self.functie_cwz.save()

    def test_anon(self):
        self.client.logout()

        # geen rechten om dit overzicht in te zien
        resp = self.client.get('/functie/overzicht/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

        # geen rechten om beheerders te kiezen
        resp = self.client.get('/functie/wijzig/123/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_overzicht_view_normaal(self):
        # geen rechten om dit overzicht in te zien
        # zelf niet na acceptatie VHPG en OTP controle
        account = self.account_normaal
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()

        resp = self.client.get('/functie/overzicht/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

    def test_overzicht_view_admin(self):
        # neem de BB rol aan
        account = self.account_admin
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()
        resp = self.client.get('/functie/wissel-van-rol/BB/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: Manager competitiezaken")

        # controleer de Wijzig knoppen op de functie-overzicht pagina
        resp = self.client.get('/functie/overzicht/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('functie/overzicht.dtl', 'plein/site_layout.dtl'))
        urls = [url for url in extract_all_href_urls(resp) if url.startswith('/functie/wijzig/')]
        self.assertEqual(len(urls), 2)      # BKO 18m en 25m

        # neem de BKO 18m rol aan
        resp = self.client.get('/functie/wissel-van-rol/functie/%s' % self.functie_bko.pk, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: BKO Indoor")

        # controleer de Wijzig knoppen op de functie-overzicht pagina
        resp = self.client.get('/functie/overzicht/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('functie/overzicht.dtl', 'plein/site_layout.dtl'))
        urls = [url for url in extract_all_href_urls(resp) if url.startswith('/functie/wijzig/')]
        self.assertEqual(len(urls), 4)      # 4x RKO

        # neem de RKO Rayon 3 Indoor rol aan
        resp = self.client.get('/functie/wissel-van-rol/functie/%s' % self.functie_rko3.pk, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: RKO Rayon 3 Indoor")

        # controleer de Wijzig knoppen op de functie-overzicht pagina
        resp = self.client.get('/functie/overzicht/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('functie/overzicht.dtl', 'plein/site_layout.dtl'))
        urls = [url for url in extract_all_href_urls(resp) if url.startswith('/functie/wijzig/')]
        self.assertEqual(len(urls), 4)      # 4x RCL

        # neem de RCL Rayon 111 Indoor aan
        resp = self.client.get('/functie/wissel-van-rol/functie/%s' % self.functie_rcl111.pk, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: RCL Regio 111 Indoor")

        # controleer de Wijzig knoppen op de functie-overzicht pagina
        resp = self.client.get('/functie/overzicht/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('functie/overzicht.dtl', 'plein/site_layout.dtl'))
        urls = [url for url in extract_all_href_urls(resp) if url.startswith('/functie/wijzig/')]
        self.assertEqual(len(urls), 0)      # geen wijzig knoppen voor de RCL

        assert_other_http_commands_not_supported(self, '/functie/overzicht/')

    def test_wijzig_view(self):
        # neem de BB rol aan
        account = self.account_admin
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()
        resp = self.client.get('/functie/wissel-van-rol/BB/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: Manager competitiezaken")

        # probeer een niet-bestaande functie
        resp = self.client.get('/functie/wijzig/999999/', follow=False)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        # haal het wijzig scherm op voor de BKO
        url = '/functie/wijzig/%s/' % self.functie_bko.pk
        resp = self.client.get(url, follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('functie/wijzig.dtl', 'plein/site_layout.dtl'))

        # probeer de zoek functie
        resp = self.client.get(url + '?zoekterm=testbeheerder', follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('functie/wijzig.dtl', 'plein/site_layout.dtl'))

        # controleer aanwezigheid van toevoeg knoppen
        self.assertContains(resp, 'Maak beheerder', count=2)
        # controleer afwezigheid van verwijder knoppen
        self.assertNotContains(resp, 'Verwijder beheerder')

        # koppel de twee beheerders
        self.account_beh1.functies.add(self.functie_bko)
        self.account_beh2.functies.add(self.functie_bko)

        # haal het wijzig scherm op voor de BKO weer op
        resp = self.client.get(url, follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('functie/wijzig.dtl', 'plein/site_layout.dtl'))

        # controleer aanwezigheid van verwijder knoppen
        self.assertContains(resp, 'Verwijder beheerder', count=2)

        assert_other_http_commands_not_supported(self, url)

    def test_koppel_ontkoppel_bb(self):
        # neem de BB rol aan
        account = self.account_admin
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()
        resp = self.client.get('/functie/wissel-van-rol/BB/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: Manager competitiezaken")

        # juiste URL om BKO te koppelen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_bko.pk

        # koppel beheerder1
        self.assertEqual(len(self.functie_bko.account_set.all()), 0)
        resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('functie/wijzig.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(len(self.functie_bko.account_set.all()), 1)

        # koppel beheerder2
        resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(len(self.functie_bko.account_set.all()), 2)

        # ontkoppel beheerder1
        resp = self.client.post(url, {'drop': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(len(self.functie_bko.account_set.all()), 1)

        # poog lager dan een BKO te koppelen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rko3.pk
        self.assertEqual(len(self.functie_rko3.account_set.all()), 0)
        resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed
        self.assertEqual(len(self.functie_rko3.account_set.all()), 0)

        # probeer een GET
        resp = self.client.get('/functie/wijzig/123/ontvang/')
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # probeer een niet-bestaande functie
        resp = self.client.post('/functie/wijzig/123/ontvang/')
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # foute form parameter
        url = '/functie/wijzig/%s/ontvang/' % self.functie_bko.pk
        resp = self.client.post(url, {'what': 1})
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # fout account nummer
        resp = self.client.post(url, {'add': '999999'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

    def test_koppel_bko(self):
        # neem de BKO rol aan
        account = self.account_admin
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()
        resp = self.client.get('/functie/wissel-van-rol/functie/%s/' % self.functie_bko.pk, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: BKO ")

        # koppel de RKO
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rko3.pk
        self.assertEqual(len(self.functie_rko3.account_set.all()), 0)
        resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(len(self.functie_rko3.account_set.all()), 1)

        # check dat de BKO geen RCL kan koppelen
        # juiste URL om RCL te koppelen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rcl111.pk
        self.assertEqual(len(self.functie_rcl111.account_set.all()), 0)
        resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=False)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed
        self.assertEqual(len(self.functie_rcl111.account_set.all()), 0)

        # probeer als bezoeker (corner case coverage)
        # (admin kan geen schutter worden)
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rko3.pk
        resp = self.client.get('/functie/wissel-van-rol/geen/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=False)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

    def test_koppel_rko(self):
        # neem de RKO rol aan
        account = self.account_admin
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()
        resp = self.client.get('/functie/wissel-van-rol/functie/%s/' % self.functie_rko3.pk, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: RKO ")

        # koppel een RCL van het juiste rayon
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rcl111.pk
        self.assertEqual(len(self.functie_rcl111.account_set.all()), 0)
        resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(len(self.functie_rcl111.account_set.all()), 1)

        # koppel een RCL van het verkeerde rayon
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rcl101.pk
        resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed
        self.assertEqual(len(self.functie_rcl111.account_set.all()), 1)

        # poog een andere rol te koppelen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rko3.pk
        self.assertEqual(len(self.functie_rko3.account_set.all()), 0)
        resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed
        self.assertEqual(len(self.functie_rko3.account_set.all()), 0)

    def test_koppel_rcl(self):
        # RCL mag niets

        # neem de RCL rol aan
        account = self.account_admin
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()
        resp = self.client.get('/functie/wissel-van-rol/functie/%s/' % self.functie_rcl111.pk, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: RCL ")

        # poog een andere rol te koppelen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rcl101.pk
        self.assertEqual(len(self.functie_rcl101.account_set.all()), 0)
        resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed
        self.assertEqual(len(self.functie_rcl101.account_set.all()), 0)

# end of file
