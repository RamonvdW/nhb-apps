# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .models import maak_functie, Functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from Logboek.models import LogboekRegel
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestFunctieKoppelen(E2EHelpers, TestCase):
    """ unit tests voor de Functie applicatie, functionaliteit Koppel bestuurders """

    test_after = ('Account', 'Functie.test_2fa', 'Functie.test_overzicht')

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
        ver.ver_nr = "1000"
        ver.regio = NhbRegio.objects.get(regio_nr=111)
        # secretaris kan nog niet ingevuld worden
        ver.save()

        lid = NhbLid()
        lid.nhb_nr = 100042
        lid.geslacht = "M"
        lid.voornaam = "Beh"
        lid.achternaam = "eerder"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.account_beh2
        lid.email = lid.account.email
        lid.save()
        self.nhblid1 = lid

        lid.pk = None
        lid.nhb_nr = 10043
        lid.account = self.account_normaal
        lid.save()
        self.nhblid3 = lid

        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.nhb_ver = ver
        self.functie_sec.save()

        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.nhb_ver = ver
        self.functie_wl.save()

        self.regio_112 = NhbRegio.objects.get(regio_nr=112)

        # maak nog een test vereniging
        ver2 = NhbVereniging()
        ver2.naam = "Extra Club"
        ver2.ver_nr = "1900"
        ver2.regio = self.regio_112
        # secretaris kan nog niet ingevuld worden
        ver2.save()

        self.functie_sec2 = maak_functie("SEC test 2", "SEC")
        self.functie_sec2.nhb_ver = ver2
        self.functie_sec2.save()

        self.functie_hwl2 = maak_functie("HWL test 2", "HWL")
        self.functie_hwl2.nhb_ver = ver2
        self.functie_hwl2.save()

        lid = NhbLid()
        lid.nhb_nr = 100024
        lid.geslacht = "V"
        lid.voornaam = "Ander"
        lid.achternaam = "Lid"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=5)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=11)
        lid.bij_vereniging = ver2
        lid.account = self.account_ander
        lid.email = lid.account.email
        lid.save()
        self.nhblid2 = lid

        self.url_overzicht = '/functie/overzicht/'
        self.url_overzicht_vereniging = '/functie/overzicht/vereniging/'
        self.url_wijzig = '/functie/wijzig/%s/'     # functie_pk
        self.url_activeer_functie = '/functie/activeer-functie/%s/'
        self.url_activeer_rol = '/functie/activeer-rol/%s/'

    def test_wijzig_view(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # neem de BB rol aan
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        self.nhblid1.voornaam = "Test1"
        self.nhblid1.achternaam = "Beheerder"
        self.nhblid1.save()

        self.nhblid2.voornaam = "Test2"
        self.nhblid2.achternaam = "Beheerder"
        self.nhblid2.account = self.account_beh2
        self.nhblid2.save()

        # probeer een niet-bestaande functie
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig % '999999')
        self.assert404(resp)     # 404 = Not allowed

        # haal het wijzig scherm op voor de BKO
        url = '/functie/wijzig/%s/' % self.functie_bko.pk
        with self.assert_max_queries(4):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wijzig.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Manager competitiezaken")

        # probeer de zoek functie
        with self.assert_max_queries(20):
            resp = self.client.get(url + '?zoekterm=beheerder')
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
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wijzig.dtl', 'plein/site_layout.dtl'))

        # controleer aanwezigheid van verwijder knoppen
        self.assertContains(resp, 'Verwijder beheerder', count=2)

        self.e2e_assert_other_http_commands_not_supported(url)

    def test_wijzig_view_hwl(self):
        # de HWL vindt alleen leden van eigen vereniging
        self.account_beh1.functie_set.clear()
        self.account_beh2.functie_set.clear()

        self.functie_hwl.accounts.add(self.account_beh1)
        self.e2e_login_and_pass_otp(self.account_beh1)

        with self.assert_max_queries(21):
            resp = self.client.post(self.url_activeer_functie % self.functie_hwl.pk, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "HWL")

        # probeer de zoek functie: zoek 'er' --> vind 'beheerder' en 'ander'
        url = '/functie/wijzig/%s/' % self.functie_hwl.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url + '?zoekterm=er', follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wijzig.dtl', 'plein/site_layout.dtl'))

        # controleer aanwezigheid van toevoeg knoppen
        self.assertContains(resp, 'Maak beheerder', count=2)         # 2 leden van de vereniging
        # controleer afwezigheid van verwijder knoppen
        self.assertContains(resp, 'Verwijder beheerder', count=1)    # kan zichzelf verwijderen

    def test_koppel_ontkoppel_bb(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # neem de BB rol aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_activeer_rol % 'BB', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Manager competitiezaken")

        # juiste URL om BKO te koppelen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_bko.pk

        # koppel beheerder1
        self.assertEqual(self.functie_bko.accounts.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wijzig.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(self.functie_bko.accounts.count(), 1)

        # koppel beheerder2
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_bko.accounts.count(), 2)

        # ontkoppel beheerder1
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'drop': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_bko.accounts.count(), 1)

        # poog lager dan een BKO te koppelen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rko3.pk
        self.assertEqual(self.functie_rko3.accounts.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assert403(resp)
        self.assertEqual(self.functie_rko3.accounts.count(), 0)

        # probeer een GET
        with self.assert_max_queries(20):
            resp = self.client.get('/functie/wijzig/123/ontvang/')
        self.assert404(resp)  # 404 = Not allowed

        # probeer een niet-bestaande functie
        with self.assert_max_queries(20):
            resp = self.client.post('/functie/wijzig/123/ontvang/')
        self.assert404(resp)  # 404 = Not allowed

        # foute form parameter
        url = '/functie/wijzig/%s/ontvang/' % self.functie_bko.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'what': 1})
        self.assert404(resp)  # 404 = Not allowed

        # fout account nummer
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': '999999'})
        self.assert404(resp)  # 404 = Not allowed

    def test_koppel_bko(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # neem de BKO rol aan
        with self.assert_max_queries(25):
            resp = self.client.post('/functie/activeer-functie/%s/' % self.functie_bko.pk, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "BKO ")

        LogboekRegel.objects.all().delete()

        # koppel de RKO
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rko3.pk
        self.assertEqual(self.functie_rko3.accounts.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_rko3.accounts.count(), 1)

        # controleer correctheid toevoeging in het logboek
        regel = LogboekRegel.objects.all()[0]
        self.assertEqual(regel.gebruikte_functie, 'Rollen')
        self.assertEqual(regel.activiteit, 'NHB lid 100042 (Beh eerder) is beheerder gemaakt voor functie RKO Rayon 3 Indoor')

        # check dat de BKO geen RCL kan koppelen
        # juiste URL om RCL te koppelen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rcl111.pk
        self.assertEqual(self.functie_rcl111.accounts.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=False)
        self.assert403(resp)
        self.assertEqual(self.functie_rcl111.accounts.count(), 0)

        # probeer als bezoeker (corner case coverage)
        # (admin kan geen schutter worden)
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rko3.pk
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_activeer_rol % 'geen', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=False)
        self.assert403(resp)

    def test_koppel_rko(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # neem de RKO rol aan
        with self.assert_max_queries(25):
            resp = self.client.post(self.url_activeer_functie % self.functie_rko3.pk, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "RKO ")

        LogboekRegel.objects.all().delete()

        # koppel een RCL van het juiste rayon
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rcl111.pk
        self.assertEqual(self.functie_rcl111.accounts.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_rcl111.accounts.count(), 1)

        # controleer correctheid toevoeging in het logboek
        regel = LogboekRegel.objects.all()[0]
        self.assertEqual(regel.gebruikte_functie, 'Rollen')
        # beh1 is geen nhb lid
        self.assertEqual(regel.activiteit, 'Account Beheerder1 (testbeheerder1) is beheerder gemaakt voor functie RCL Regio 111 Indoor')

        # koppel een RCL van het verkeerde rayon
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rcl101.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assert403(resp)
        self.assertEqual(self.functie_rcl111.accounts.count(), 1)

        # poog een andere rol te koppelen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rko3.pk
        self.assertEqual(self.functie_rko3.accounts.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assert403(resp)
        self.assertEqual(self.functie_rko3.accounts.count(), 0)

    def test_koppel_rcl(self):
        # RCL mag HWL en WL koppelen
        self.e2e_login_and_pass_otp(self.account_admin)

        # neem de RCL rol aan
        with self.assert_max_queries(25):
            resp = self.client.post(self.url_activeer_functie % self.functie_rcl111.pk, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "RCL ")

        # controleer dat de RCL de WL mag koppelen
        url = '/functie/wijzig/%s/' % self.functie_wl.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # RCL koppelt WL, lid van de juiste vereniging
        url = '/functie/wijzig/%s/ontvang/' % self.functie_wl.pk
        self.assertEqual(self.functie_wl.accounts.count(), 0)
        with self.assert_max_queries(25):
            resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_wl.accounts.count(), 1)

        # controleer dat de RCL de HWL mag koppelen
        url = '/functie/wijzig/%s/' % self.functie_hwl.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # RCL koppelt HWL, lid van de juiste vereniging
        url = '/functie/wijzig/%s/ontvang/' % self.functie_hwl.pk
        self.assertEqual(self.functie_hwl.accounts.count(), 0)
        with self.assert_max_queries(25):
            resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_hwl.accounts.count(), 1)

        # poog een andere rol te koppelen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_rcl101.pk
        self.assertEqual(self.functie_rcl101.accounts.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assert403(resp)
        self.assertEqual(self.functie_rcl101.accounts.count(), 0)

    def test_koppel_hwl(self):
        # HWL mag zijn eigen leden koppelen: beh2
        self.account_beh1.functie_set.clear()
        self.account_beh2.functie_set.clear()

        self.functie_hwl.accounts.add(self.account_beh1)
        self.e2e_login_and_pass_otp(self.account_beh1)

        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')
        with self.assert_max_queries(20):
            resp = self.client.get('/plein/')
        self.assertContains(resp, "HWL test")

        # haal het overzicht voor bestuurders op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'relevante functies en de beheerders')    # reduced list for HWL
        # TODO: check urls

        # haal het overzicht van verenigingsbestuurders op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht_vereniging)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

        # HWL koppelt een lid uit de eigen gelederen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_hwl.pk
        self.assertEqual(self.functie_hwl.accounts.count(), 1)
        with self.assert_max_queries(25):
            resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_hwl.accounts.count(), 2)

        # controleer dat de naam getoond wordt
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht_vereniging)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, self.account_beh2.volledige_naam())

        # poog een NHB lid te koppelen dat niet lid is van de vereniging
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_ander.pk})
        self.assert403(resp)
        self.assertEqual(self.functie_hwl.accounts.count(), 2)

        # poog een niet-NHB lid account te koppelen
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_admin.pk})
        self.assert403(resp)
        self.assertEqual(self.functie_hwl.accounts.count(), 2)

        # probeer een verkeerde vereniging te wijzigen
        url = '/functie/wijzig/%s/ontvang/' % self.functie_hwl2.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh2.pk})
        self.assert403(resp)

        url = '/functie/wijzig/%s/' % self.functie_sec.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # poog sec SEC rol te koppelen (mag niet)
        url = '/functie/wijzig/%s/ontvang/' % self.functie_sec.pk
        self.assertEqual(self.functie_sec.accounts.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh2.pk})
        self.assert403(resp)
        self.assertEqual(self.functie_sec.accounts.count(), 0)

        url = '/functie/wijzig/%s/' % self.functie_wl.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        url = '/functie/wijzig/%s/' % self.functie_hwl.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_koppel_sec(self):
        # SEC mag zijn eigen leden koppelen: account_normaal
        self.account_beh1.functie_set.clear()

        self.functie_sec.accounts.add(self.account_beh1)
        self.e2e_login_and_pass_otp(self.account_beh1)

        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        # haal het overzicht van verenigingsbestuurders op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht_vereniging)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        # verwachting: 2x koppelen beheerders, 1x wijzig email, 1x 'terug'
        # print('SEC urls: %s' % repr(urls))
        self.assertEqual(len(urls), 4)

        # poog een lid te koppelen aan de rol SEC
        url = '/functie/wijzig/%s/' % self.functie_sec.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # koppel een verenigingslid aan de rol SEC
        self.assertEqual(self.functie_sec.accounts.count(), 1)
        url = '/functie/wijzig/%s/ontvang/' % self.functie_sec.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_normaal.pk})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(self.functie_sec.accounts.count(), 2)

        # koppel SEC voor een andere vereniging
        url = '/functie/wijzig/%s/ontvang/' % self.functie_sec2.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_ander.pk})    # silently ignored
        self.assert403(resp)
        self.assertEqual(self.functie_sec.accounts.count(), 2)

        # koppel een niet-verenigingslid aan de rol SEC
        url = '/functie/wijzig/%s/ontvang/' % self.functie_sec.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_ander.pk})
        self.assert403(resp)
        self.assertEqual(self.functie_sec.accounts.count(), 2)

        # koppel een verenigingslid aan de rol HWL
        self.assertEqual(self.functie_hwl.accounts.count(), 0)
        url = '/functie/wijzig/%s/ontvang/' % self.functie_hwl.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_normaal.pk})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(self.functie_hwl.accounts.count(), 1)

        # koppel een verenigingslid aan de rol WL (dit mag de SEC niet)
        self.assertEqual(self.functie_wl.accounts.count(), 0)
        url = '/functie/wijzig/%s/ontvang/' % self.functie_wl.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_normaal.pk})
        self.assert403(resp)
        self.assertEqual(self.functie_wl.accounts.count(), 0)

    def test_administratieve_regio(self):
        # neem de BB rol aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # maak regio 112 administratief
        self.regio_112.is_administratief = True
        self.regio_112.save()

        url = '/functie/wijzig/%s/' % self.functie_bko.pk

        # haal de pagina op - het gevonden lid heeft geen regio vermelding
        with self.assert_max_queries(20):
            resp = self.client.get(url + '?zoekterm=100')       # matcht alle nhb nummers
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'regio 112')

        # voeg het lid van de vereniging in regio 112 toe als beheerder
        self.functie_bko.accounts.add(self.account_ander)

        # haal de pagina opnieuw op - de gekoppelde beheerder heeft geen regio
        url = '/functie/wijzig/%s/' % self.functie_bko.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'regio 112')

    def test_rcl_bad_buiten_regio(self):
        # probeer een HWL te koppelen van een vereniging buiten de regio
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_rcl101)

        url = self.url_wijzig % self.functie_hwl.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

# end of file
