# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .models import maak_functie, Functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestFunctieKoppelen(E2EHelpers, TestCase):
    """ unit tests voor de Functie applicatie, functionaliteit Koppel bestuurders """

    test_after = ('Account', 'Functie.test_2fa')

    def setUp(self):
        """ initialisatie van de test case """

        # deze test is afhankelijk van de standaard globale functies
        # zoals opgezet door de migratie m0002_functies-2019:
        #   comp_type: 18/25
        #       rol: BKO, RKO (4x), RCL (16x)

        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.nhb', 'Normaal')
        self.account_beh1 = self.e2e_create_account('testbeheerder1', 'beh1@test.nhb', 'Beheerder1', accepteer_vhpg=True)
        self.account_beh2 = self.e2e_create_account('testbeheerder2', 'beh2@test.nhb', 'Beheerder2', accepteer_vhpg=True)
        self.account_ander = self.e2e_create_account('anderlid', 'anderlid@test.nhb', 'Ander')

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

        lid = NhbLid()
        lid.nhb_nr = 100042
        lid.geslacht = "M"
        lid.voornaam = "Beh"
        lid.achternaam = "eerder"
        lid.email = "beh2@test.com"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.account_beh2
        lid.save()

        self.functie_cwz = maak_functie("CWZ test", "CWZ")
        self.functie_cwz.nhb_ver = ver
        self.functie_cwz.save()

        # maak nog een test vereniging
        ver2 = NhbVereniging()
        ver2.naam = "Extra Club"
        ver2.nhb_nr = "1900"
        ver2.regio = NhbRegio.objects.get(regio_nr=112)
        # secretaris kan nog niet ingevuld worden
        ver2.save()

        self.functie_cwz2 = maak_functie("CWZ test 2", "CWZ")
        self.functie_cwz2.nhb_ver = ver2
        self.functie_cwz2.save()

        lid2 = NhbLid()
        lid2.nhb_nr = 100024
        lid2.geslacht = "V"
        lid2.voornaam = "Ander"
        lid2.achternaam = "Lid"
        lid2.email = "anderlid@test.com"
        lid2.geboorte_datum = datetime.date(year=1972, month=3, day=5)
        lid2.sinds_datum = datetime.date(year=2010, month=11, day=11)
        lid2.bij_vereniging = ver2
        lid2.account = self.account_ander
        lid2.save()

        self.url_overzicht = '/functie/overzicht/'
        self.url_wijzig = '/functie/wijzig/'
        self.url_activeer_functie = '/functie/activeer-functie/%s/'
        self.url_activeer_rol = '/functie/activeer-rol/%s/'

    def test_anon(self):
        self.e2e_logout()

        # geen rechten om dit overzicht in te zien
        resp = self.client.get(self.url_overzicht)
        self.assert_is_redirect(resp, '/plein/')

        # geen rechten om beheerders te kiezen
        resp = self.client.get(self.url_wijzig + '123/')
        self.assert_is_redirect(resp, '/plein/')

    def test_overzicht_view_normaal(self):
        # geen rechten om dit overzicht in te zien
        # zelf niet na acceptatie VHPG en OTP controle
        self.e2e_login_and_pass_otp(self.account_normaal)

        resp = self.client.get(self.url_overzicht)
        self.assert_is_redirect(resp, '/plein/')

        resp = self.client.get(self.url_overzicht + 'vereniging/')
        self.assert_is_redirect(resp, '/plein/')

    def test_overzicht_view_admin(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # neem de BB rol aan
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')
        resp = self.client.get('/plein/')
        self.assert_html_ok(resp)
        self.assertContains(resp, "Manager competitiezaken")

        # controleer de Wijzig knoppen op de functie-overzicht pagina
        resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht.dtl', 'plein/site_layout.dtl'))
        urls = [url for url in self.extract_all_urls(resp) if url.startswith('/functie/wijzig/')]
        self.assertEqual(len(urls), 2)      # BKO 18m en 25m

        # controleer de Wijzig knoppen op de functie-overzicht pagina voor verschillende rollen

        # neem de BKO 18m rol aan
        self.e2e_wissel_naar_functie(self.functie_bko)
        self.e2e_check_rol('BKO')
        resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "BKO Indoor")
        urls = [url for url in self.extract_all_urls(resp) if url.startswith(self.url_wijzig)]
        self.assertEqual(len(urls), 4)      # 4x RKO

        # neem de RKO Rayon 3 Indoor rol aan
        self.e2e_wissel_naar_functie(self.functie_rko3)
        self.e2e_check_rol('RKO')
        resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "RKO Rayon 3 Indoor")
        urls = [url for url in self.extract_all_urls(resp) if url.startswith(self.url_wijzig)]
        self.assertEqual(len(urls), 4)      # 4x RCL

        # neem de RCL Rayon 111 Indoor aan
        self.e2e_wissel_naar_functie(self.functie_rcl111)
        self.e2e_check_rol('RCL')

        # controleer de Wijzig knoppen op de functie-overzicht pagina
        resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "RCL Regio 111 Indoor")
        urls = [url for url in self.extract_all_urls(resp) if url.startswith(self.url_wijzig)]
        self.assertEqual(len(urls), 0)      # geen wijzig knoppen voor de RCL

        self.e2e_assert_other_http_commands_not_supported(self.url_overzicht)

    def test_overzicht_view_cwz(self):
        # de CWZ krijgt niet het hele overzicht te zien
        # alleen de RCL, RKO, BKO worden getoond die aan de regio gerelateerd zijn
        self.functie_cwz.accounts.add(self.account_beh1)
        self.e2e_login_and_pass_otp(self.account_beh1)

        self.e2e_wissel_naar_functie(self.functie_cwz)
        self.e2e_check_rol('CWZ')

        # vraag het overzicht van competitie-bestuurders op
        resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "CWZ")
        urls = [url for url in self.extract_all_urls(resp) if url.startswith(self.url_wijzig)]
        self.assertEqual(len(urls), 0)      # geen wijzig knoppen voor de CWZ

        # controleer inhoudelijk op 2xRCL, 2xRKO en 2xBKO (18m en 25m)
        self.assertContains(resp, "BKO", count=2)
        self.assertContains(resp, "RKO", count=2)
        self.assertContains(resp, "RCL", count=2)

        # haal het overzicht van verenigingsbestuurders op
        resp = self.client.get(self.url_overzicht + 'vereniging/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_overzicht + 'vereniging/')

    def test_wijzig_view(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # neem de BB rol aan
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # probeer een niet-bestaande functie
        resp = self.client.get(self.url_wijzig + '999999/')
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        # haal het wijzig scherm op voor de BKO
        url = '/functie/wijzig/%s/' % self.functie_bko.pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wijzig.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Manager competitiezaken")

        # probeer de zoek functie
        resp = self.client.get(url + '?zoekterm=testbeheerder')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wijzig.dtl', 'plein/site_layout.dtl'))

        # controleer aanwezigheid van toevoeg knoppen
        self.assertContains(resp, 'Maak beheerder', count=2)
        # controleer afwezigheid van verwijder knoppen
        self.assertNotContains(resp, 'Verwijder beheerder')

        # koppel de twee beheerders
        self.functie_bko.accounts.add(self.account_beh1)
        self.functie_bko.accounts.add(self.account_beh2)

        # haal het wijzig scherm op voor de BKO weer op
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wijzig.dtl', 'plein/site_layout.dtl'))

        # controleer aanwezigheid van verwijder knoppen
        self.assertContains(resp, 'Verwijder beheerder', count=2)

        self.e2e_assert_other_http_commands_not_supported(url)

    def test_wijzig_view_cwz(self):
        # de CWZ vindt alleen leden van eigen vereniging
        self.functie_cwz.accounts.add(self.account_beh1)
        self.e2e_login_and_pass_otp(self.account_beh1)

        resp = self.client.post(self.url_activeer_functie % self.functie_cwz.pk, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "CWZ")

        # probeer de zoek functie: er vindt 'beheerder' en 'ander'
        url = '/functie/wijzig/%s/' % self.functie_cwz.pk
        resp = self.client.get(url + '?zoekterm=er', follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wijzig.dtl', 'plein/site_layout.dtl'))

        # controleer aanwezigheid van toevoeg knoppen
        self.assertContains(resp, 'Maak beheerder', count=1)         # maar 1 lid van vereniging
        # controleer afwezigheid van verwijder knoppen
        self.assertContains(resp, 'Verwijder beheerder', count=1)    # kan zichzelf verwijderen

    def test_koppel_ontkoppel_bb(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # neem de BB rol aan
        resp = self.client.post(self.url_activeer_rol % 'BB', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Manager competitiezaken")

        # juiste URL om BKO te koppelen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_bko.pk

        # koppel beheerder1
        self.assertEqual(self.functie_bko.accounts.count(), 0)
        resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wijzig.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(self.functie_bko.accounts.count(), 1)

        # koppel beheerder2
        resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_bko.accounts.count(), 2)

        # ontkoppel beheerder1
        resp = self.client.post(url, {'drop': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_bko.accounts.count(), 1)

        # poog lager dan een BKO te koppelen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rko3.pk
        self.assertEqual(self.functie_rko3.accounts.count(), 0)
        resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed
        self.assertEqual(self.functie_rko3.accounts.count(), 0)

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
        self.e2e_login_and_pass_otp(self.account_admin)

        # neem de BKO rol aan
        resp = self.client.post('/functie/activeer-functie/%s/' % self.functie_bko.pk, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "BKO ")

        # koppel de RKO
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rko3.pk
        self.assertEqual(self.functie_rko3.accounts.count(), 0)
        resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_rko3.accounts.count(), 1)

        # check dat de BKO geen RCL kan koppelen
        # juiste URL om RCL te koppelen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rcl111.pk
        self.assertEqual(self.functie_rcl111.accounts.count(), 0)
        resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=False)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed
        self.assertEqual(self.functie_rcl111.accounts.count(), 0)

        # probeer als bezoeker (corner case coverage)
        # (admin kan geen schutter worden)
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rko3.pk
        resp = self.client.post(self.url_activeer_rol % 'geen', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=False)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

    def test_koppel_rko(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # neem de RKO rol aan
        resp = self.client.post(self.url_activeer_functie % self.functie_rko3.pk, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "RKO ")

        # koppel een RCL van het juiste rayon
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rcl111.pk
        self.assertEqual(self.functie_rcl111.accounts.count(), 0)
        resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_rcl111.accounts.count(), 1)

        # koppel een RCL van het verkeerde rayon
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rcl101.pk
        resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed
        self.assertEqual(self.functie_rcl111.accounts.count(), 1)

        # poog een andere rol te koppelen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rko3.pk
        self.assertEqual(self.functie_rko3.accounts.count(), 0)
        resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed
        self.assertEqual(self.functie_rko3.accounts.count(), 0)

    def test_koppel_rcl(self):
        # RCL mag niets

        self.e2e_login_and_pass_otp(self.account_admin)

        # neem de RCL rol aan
        resp = self.client.post(self.url_activeer_functie % self.functie_rcl111.pk, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "RCL ")

        # poog een andere rol te koppelen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rcl101.pk
        self.assertEqual(self.functie_rcl101.accounts.count(), 0)
        resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed
        self.assertEqual(self.functie_rcl101.accounts.count(), 0)

    def test_koppel_cwz(self):
        # CWZ mag zijn eigen leden koppelen: beh2
        self.functie_cwz.accounts.add(self.account_beh1)
        self.e2e_login_and_pass_otp(self.account_beh1)

        self.e2e_wissel_naar_functie(self.functie_cwz)
        self.e2e_check_rol('CWZ')
        resp = self.client.get('/plein/')
        self.assertContains(resp, "CWZ test")

        # haal het overzicht voor bestuurders op
        resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'relevante functies en de beheerders')    # reduced list for CWZ

        # haal het overzicht van verenigingsbestuurders op
        resp = self.client.get('/functie/overzicht/vereniging/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

        # koppel een CWZ uit de eigen gelederen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_cwz.pk
        self.assertEqual(self.functie_cwz.accounts.count(), 1)
        resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_cwz.accounts.count(), 2)

        # controleer dat de naam getoond wordt
        resp = self.client.get('/functie/overzicht/vereniging/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, self.account_beh2.volledige_naam())

        # poog een NHB lid te koppelen dat niet lid is van de vereniging
        resp = self.client.post(url, {'add': self.account_ander.pk}, follow=True)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed
        self.assertEqual(self.functie_cwz.accounts.count(), 2)

        # poog een niet-NHB lid account te koppelen
        resp = self.client.post(url, {'add': self.account_admin.pk}, follow=True)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed
        self.assertEqual(self.functie_cwz.accounts.count(), 2)

        # probeer een verkeerde vereniging te wijzigen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_cwz2.pk
        resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=True)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

# end of file
