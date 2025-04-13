# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase, Client
from django.contrib.sessions.backends.db import SessionStore
from Account.models import AccountSessions
from Functie.models import Functie
from Functie.rol.mag_wisselen import SESSIONVAR_ROL_MAG_WISSELEN_BOOL
from Functie.tests.helpers import maak_functie
from Geo.models import Rayon, Regio
from Logboek.models import LogboekRegel
from Mailer.models import MailQueue
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime


class TestFunctieKoppelBeheerder(E2EHelpers, TestCase):

    """ tests voor de Functie applicatie, functionaliteit Koppel bestuurders """

    test_after = ('Account', 'Functie.tests.test_beheerders')

    url_beheerders = '/functie/beheerders/'
    url_beheerders_vereniging = '/functie/beheerders/vereniging/'
    url_wijzig = '/functie/wijzig/%s/'  # functie_pk
    url_wijzig_ontvang = '/functie/wijzig/%s/ontvang/'
    url_activeer_functie = '/functie/activeer-functie/%s/'
    url_activeer_rol = '/functie/activeer-rol/%s/'

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()

    def setUp(self):
        """ initialisatie van de test case """

        # deze test is afhankelijk van de standaard globale functies
        # zoals opgezet door de migratie m0002_functies-2019:
        #   comp_type: 18/25
        #       rol: BKO, RKO (4x), RCL (16x)

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.mh', 'Normaal')
        self.account_beh1 = self.e2e_create_account('testbeheerder1', 'beh1@test.mh', 'Beheerder1',
                                                    accepteer_vhpg=True)
        self.account_beh2 = self.e2e_create_account('testbeheerder2', 'beh2@test.mh', 'Beheerder2',
                                                    accepteer_vhpg=True)
        self.account_ander = self.e2e_create_account('anderlid', 'anderlid@test.nhb', 'Ander')

        self.functie_bko = Functie.objects.get(comp_type='18', rol='BKO')
        self.functie_rko3 = Functie.objects.get(comp_type='18', rol='RKO', rayon=Rayon.objects.get(rayon_nr=3))
        self.functie_rcl111 = Functie.objects.get(comp_type='18', rol='RCL', regio=Regio.objects.get(regio_nr=111))
        self.functie_rcl101 = Functie.objects.get(comp_type='18', rol='RCL', regio=Regio.objects.get(regio_nr=101))

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(pk=111))
        ver.save()
        self.ver1 = ver

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

        sporter = Sporter(
                    lid_nr=100043,
                    geslacht="M",
                    voornaam="Beh",
                    achternaam="eerder",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver,
                    account=self.account_normaal,
                    email=self.account_normaal.email)
        sporter.save()
        self.sporter_100043 = sporter

        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.vereniging = ver
        self.functie_sec.save()

        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.vereniging = ver
        self.functie_hwl.bevestigde_email = 'hwl@khsn.not'
        self.functie_hwl.save()

        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.vereniging = ver
        self.functie_wl.save()

        self.regio_112 = Regio.objects.get(regio_nr=112)

        # maak nog een test vereniging
        ver2 = Vereniging(
                    naam="Extra Club",
                    ver_nr=1900,
                    regio=self.regio_112)
        ver2.save()
        self.ver2 = ver2

        self.functie_sec2 = maak_functie("SEC test 2", "SEC")
        self.functie_sec2.vereniging = ver2
        self.functie_sec2.save()

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

    def test_wijzig_view(self):
        self.e2e_login_and_pass_otp(self.testdata.account_admin)

        # neem de BB rol aan
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        self.sporter_100042.voornaam = "Test1"
        self.sporter_100042.achternaam = "Beheerder"
        self.sporter_100042.save()

        self.sporter_100024.voornaam = "Test2"
        self.sporter_100024.achternaam = "Beheerder"
        self.sporter_100024.account = self.account_beh2
        self.sporter_100024.save()

        # probeer een niet-bestaande functie
        resp = self.client.get(self.url_wijzig % '999999')
        self.assert404(resp, 'Verkeerde functie')

        # haal het wijzigscherm op voor de BKO
        url = self.url_wijzig % self.functie_bko.pk
        with self.assert_max_queries(4):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/koppel-beheerders.dtl', 'plein/site_layout.dtl'))

        # probeer de zoekfunctie
        with self.assert_max_queries(20):
            resp = self.client.get(url + '?zoekterm=beheerder')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/koppel-beheerders.dtl', 'plein/site_layout.dtl'))

        # controleer aanwezigheid van toevoeg-knoppen
        self.assertContains(resp, '</i>Koppel</button>', count=2)
        # controleer afwezigheid van verwijder-knoppen
        self.assertNotContains(resp, 'Verwijder beheerder')

        # koppel de twee beheerders
        self.functie_bko.accounts.add(self.account_beh1)
        self.functie_bko.accounts.add(self.account_beh2)

        # haal het wijzigscherm op voor de BKO weer op
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/koppel-beheerders.dtl', 'plein/site_layout.dtl'))

        # controleer aanwezigheid van verwijder-knoppen
        self.assertContains(resp, '</i>Verwijder</a>', count=2)

        # zoek maar niets gevonden
        with self.assert_max_queries(20):
            resp = self.client.get(url + '?zoekterm=xxxx')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/koppel-beheerders.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Niemand gevonden')

        self.e2e_assert_other_http_commands_not_supported(url)

    def test_wijzig_view_hwl(self):
        # de HWL vindt alleen leden van eigen vereniging
        self.account_beh1.functie_set.clear()
        self.account_beh2.functie_set.clear()

        self.functie_hwl.accounts.add(self.account_beh1)
        self.e2e_login_and_pass_otp(self.account_beh1)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        with self.assert_max_queries(23):
            resp = self.client.post(self.url_activeer_functie % self.functie_hwl.pk, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/overzicht.dtl', 'plein/site_layout.dtl'))

        # probeer de zoek functie: zoek 'er' --> vind 'beheerder' en 'ander'
        url = self.url_wijzig % self.functie_hwl.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url + '?zoekterm=er', follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/koppel-beheerders.dtl', 'plein/site_layout.dtl'))

        # controleer aanwezigheid van toevoeg-knoppen
        self.assertContains(resp, '</i>Koppel</button>', count=2)         # 2 leden van de vereniging
        # controleer afwezigheid van verwijder-knoppen
        self.assertContains(resp, '</i>Verwijder</a>', count=1)      # kan zichzelf verwijderen

    def test_koppel_ontkoppel_bb(self):
        self.e2e_login_and_pass_otp(self.testdata.account_admin)

        # neem de BB rol aan
        resp = self.client.post(self.url_activeer_rol % 'BB', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Manager MH")

        # juiste URL om BKO te koppelen
        url = self.url_wijzig_ontvang % self.functie_bko.pk

        # zet OTP uit voor beheerder 1 zodat de handleiding meegestuurd wordt
        self.account_beh1.otp_is_actief = False
        self.account_beh1.save(update_fields=['otp_is_actief'])

        # koppel beheerder1
        self.assertEqual(self.functie_bko.accounts.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/koppel-beheerders.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(self.functie_bko.accounts.count(), 1)

        # er moet nu een mail in de MailQueue staan met een single-use url
        self.assertEqual(MailQueue.objects.count(), 1)
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_functie/rollen-gewijzigd.dtl')
        self.assertTrue(settings.URL_PDF_HANDLEIDING_BEHEERDERS in mail.mail_html)
        self.assert_consistent_email_html_text(mail)

        # koppel beheerder2
        with self.assert_max_queries(22):
            resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_bko.accounts.count(), 2)

        # ontkoppel beheerder1
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'drop': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_bko.accounts.count(), 1)

        # poog lager dan een BKO te koppelen
        url = self.url_wijzig_ontvang % self.functie_rko3.pk
        self.assertEqual(self.functie_rko3.accounts.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assert403(resp)
        self.assertEqual(self.functie_rko3.accounts.count(), 0)

        # probeer een GET
        with self.assert_max_queries(20):
            resp = self.client.get('/functie/wijzig/123/ontvang/')
        self.assert405(resp)  # 405 = Not implemented

        # probeer een niet-bestaande functie
        with self.assert_max_queries(20):
            resp = self.client.post('/functie/wijzig/123/ontvang/')
        self.assert404(resp, 'Verkeerde functie')

        # foute form parameter
        url = self.url_wijzig_ontvang % self.functie_bko.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'what': 1})
        self.assert404(resp, 'Verkeerd gebruik')

        # fout account nummer
        resp = self.client.post(url, {'add': '999999'})
        self.assert404(resp, 'Account niet gevonden')

    def test_koppel_bko(self):
        self.e2e_login_and_pass_otp(self.testdata.account_admin)

        # neem de BKO rol aan
        resp = self.client.post('/functie/activeer-functie/%s/' % self.functie_bko.pk, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "BKO ")

        # variant: nog geen bevestigde email
        account = self.account_beh2
        account.email_is_bevestigd = False
        account.save(update_fields=['email_is_bevestigd'])

        LogboekRegel.objects.all().delete()

        # koppel de RKO
        url = self.url_wijzig_ontvang % self.functie_rko3.pk
        self.assertEqual(self.functie_rko3.accounts.count(), 0)
        with self.assert_max_queries(24):
            resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_rko3.accounts.count(), 1)

        # controleer correctheid toevoeging in het logboek
        regel = LogboekRegel.objects.first()
        self.assertEqual(regel.gebruikte_functie, 'Rollen')
        self.assertEqual(regel.activiteit,
                         'Sporter 100042 (Beh eerder) is beheerder gemaakt voor functie RKO Rayon 3 Indoor')

        # check dat de BKO geen RCL kan koppelen
        # juiste URL om RCL te koppelen
        url = self.url_wijzig_ontvang % self.functie_rcl111.pk
        self.assertEqual(self.functie_rcl111.accounts.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=False)
        self.assert403(resp)
        self.assertEqual(self.functie_rcl111.accounts.count(), 0)

        # probeer als bezoeker (corner case coverage)
        # (admin kan geen schutter worden)
        url = self.url_wijzig_ontvang % self.functie_rko3.pk
        resp = self.client.post(self.url_activeer_rol % 'geen', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=False)
        self.assert403(resp)

    def test_koppel_rko(self):
        # log in als beh1 zodat er sessie gemaakt wordt
        self.e2e_login(self.account_beh1)

        # manipuleer de sessie zodat deze verlopen is, maar niet verwijderd wordt
        # (normaal worden sessies verwijderd bij logout omdat expiry op 0 staat == at browser close)
        session = self.client.session
        session.set_expiry(-5)      # expiry in -5 seconds
        session.save()

        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wissel_naar_functie(self.functie_rko3)
        self.e2e_check_rol('RKO')

        LogboekRegel.objects.all().delete()

        # koppel een RCL van het juiste rayon
        url = self.url_wijzig_ontvang % self.functie_rcl111.pk
        self.assertEqual(self.functie_rcl111.accounts.count(), 0)
        with self.assert_max_queries(28):
            resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_rcl111.accounts.count(), 1)

        # controleer correctheid toevoeging in het logboek
        regel = LogboekRegel.objects.first()
        self.assertEqual(regel.gebruikte_functie, 'Rollen')
        # beh1 is geen nhb lid
        self.assertEqual(regel.activiteit,
                         'Account Beheerder1 (testbeheerder1) is beheerder gemaakt voor functie RCL Regio 111 Indoor')

        # koppel een RCL van het verkeerde rayon
        url = self.url_wijzig_ontvang % self.functie_rcl101.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assert403(resp)
        self.assertEqual(self.functie_rcl111.accounts.count(), 1)

        # poog een andere rol te koppelen
        url = self.url_wijzig_ontvang % self.functie_rko3.pk
        self.assertEqual(self.functie_rko3.accounts.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assert403(resp)
        self.assertEqual(self.functie_rko3.accounts.count(), 0)

    def test_koppel_rcl(self):
        # RCL mag HWL en WL koppelen
        self.e2e_login_and_pass_otp(self.testdata.account_admin)

        # neem de RCL rol aan
        resp = self.client.post(self.url_activeer_functie % self.functie_rcl111.pk, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "RCL ")

        # controleer dat de RCL de WL mag koppelen
        url = self.url_wijzig % self.functie_wl.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # RCL koppelt WL, lid van de juiste vereniging
        url = self.url_wijzig_ontvang % self.functie_wl.pk
        self.assertEqual(self.functie_wl.accounts.count(), 0)
        with self.assert_max_queries(28):
            resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_wl.accounts.count(), 1)

        # controleer dat de RCL de HWL mag koppelen
        url = self.url_wijzig % self.functie_hwl.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # RCL koppelt HWL, lid van de juiste vereniging
        url = self.url_wijzig_ontvang % self.functie_hwl.pk
        self.assertEqual(self.functie_hwl.accounts.count(), 0)
        with self.assert_max_queries(27):
            resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_hwl.accounts.count(), 1)

        # poog een andere rol te koppelen
        url = self.url_wijzig_ontvang % self.functie_rcl101.pk
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
            resp = self.client.get(self.url_beheerders)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/lijst-beheerders.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'relevante functies en de beheerders')    # reduced list for HWL
        # TODO: check urls

        # haal het overzicht van verenigingsbestuurders op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beheerders_vereniging)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/lijst-beheerders-vereniging.dtl', 'plein/site_layout.dtl'))

        # HWL koppelt een lid uit de eigen gelederen
        url = self.url_wijzig_ontvang % self.functie_hwl.pk
        self.assertEqual(self.functie_hwl.accounts.count(), 1)
        with self.assert_max_queries(28):
            resp = self.client.post(url, {'add': self.account_beh2.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_hwl.accounts.count(), 2)

        # controleer dat de naam getoond wordt
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beheerders_vereniging)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/lijst-beheerders-vereniging.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, self.account_beh2.volledige_naam())

        # poog een lid te koppelen dat niet lid is van de vereniging
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_ander.pk})
        self.assert403(resp)
        self.assertEqual(self.functie_hwl.accounts.count(), 2)

        # poog een niet-NHB lid account te koppelen
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.testdata.account_admin.pk})
        self.assert403(resp)
        self.assertEqual(self.functie_hwl.accounts.count(), 2)

        # probeer een verkeerde vereniging te wijzigen
        url = self.url_wijzig_ontvang % self.functie_hwl2.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh2.pk})
        self.assert403(resp)

        url = self.url_wijzig % self.functie_sec.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # poog sec SEC rol te koppelen (mag niet)
        url = self.url_wijzig_ontvang % self.functie_sec.pk
        self.assertEqual(self.functie_sec.accounts.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_beh2.pk})
        self.assert403(resp)
        self.assertEqual(self.functie_sec.accounts.count(), 0)

        url = self.url_wijzig % self.functie_wl.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        url = self.url_wijzig % self.functie_hwl.pk
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
            resp = self.client.get(self.url_beheerders_vereniging)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/lijst-beheerders-vereniging.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        # verwachting: 2x koppelen beheerders, 1x wijzig email
        # print('SEC urls: %s' % repr(urls))
        self.assertEqual(len(urls), 3)

        # poog een lid te koppelen aan de rol SEC
        url = self.url_wijzig % self.functie_sec.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # koppel een verenigingslid aan de rol SEC
        self.assertEqual(self.functie_sec.accounts.count(), 1)
        url = self.url_wijzig_ontvang % self.functie_sec.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_normaal.pk})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(self.functie_sec.accounts.count(), 2)

        # koppel SEC voor een andere vereniging
        url = self.url_wijzig_ontvang % self.functie_sec2.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_ander.pk})    # silently ignored
        self.assert403(resp)
        self.assertEqual(self.functie_sec.accounts.count(), 2)

        # koppel een niet-verenigingslid aan de rol SEC
        url = self.url_wijzig_ontvang % self.functie_sec.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_ander.pk})
        self.assert403(resp)
        self.assertEqual(self.functie_sec.accounts.count(), 2)

        # koppel een verenigingslid aan de rol HWL
        self.assertEqual(self.functie_hwl.accounts.count(), 0)
        url = self.url_wijzig_ontvang % self.functie_hwl.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_normaal.pk})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(self.functie_hwl.accounts.count(), 1)

        # koppel een verenigingslid aan de rol WL (dit mag de SEC niet)
        self.assertEqual(self.functie_wl.accounts.count(), 0)
        url = self.url_wijzig_ontvang % self.functie_wl.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'add': self.account_normaal.pk})
        self.assert403(resp)
        self.assertEqual(self.functie_wl.accounts.count(), 0)

    def test_administratieve_regio(self):
        # neem de BB rol aan
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # maak regio 112 administratief
        self.regio_112.is_administratief = True
        self.regio_112.save()

        url = self.url_wijzig % self.functie_bko.pk

        # haal de pagina op - het gevonden lid heeft geen regio vermelding
        with self.assert_max_queries(20):
            resp = self.client.get(url + '?zoekterm=100')       # matcht alle bondsnummers
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'regio 112')

        # voeg het lid van de vereniging in regio 112 toe als beheerder
        self.functie_bko.accounts.add(self.account_ander)

        # haal de pagina opnieuw op - de gekoppelde beheerder heeft geen regio
        url = self.url_wijzig % self.functie_bko.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'regio 112')

    def test_rcl_bad_buiten_regio(self):
        # probeer een HWL te koppelen van een vereniging buiten de regio
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wissel_naar_functie(self.functie_rcl101)

        url = self.url_wijzig % self.functie_hwl.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

    def test_verwijder_ex_lid(self):
        # maak een gekoppelde beheerder ex-lid
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wissel_naar_functie(self.functie_rcl111)

        # koppel een HWL
        self.functie_hwl.accounts.add(self.account_beh2)

        # haal de lijst met gekoppelde beheerder op
        url = self.url_wijzig % self.functie_hwl.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assertNotContains(resp, 'LET OP:')

        # maak de HWL een ex-lid
        self.assertEqual(self.sporter_100042.account, self.account_beh2)
        self.sporter_100042.bij_vereniging = None
        self.sporter_100042.save()

        # haal de lijst met gekoppelde beheerder op
        url = self.url_wijzig % self.functie_hwl.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assertContains(resp, 'LET OP: geen lid meer bij een vereniging')

        # maak de HWL lid bij een andere vereniging
        self.assertEqual(self.sporter_100042.account, self.account_beh2)
        self.sporter_100042.bij_vereniging = self.ver2
        self.sporter_100042.save()

        # haal de lijst met gekoppelde beheerder op
        url = self.url_wijzig % self.functie_hwl.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assertContains(resp, 'LET OP: geen lid bij deze vereniging')

    def test_menu(self):
        # Controleer het het Wissel van Rol menu getoond wordt nadat een
        # gebruiker aan een eerste rol gekoppeld is.

        # log in met aparte een aparte test client instantie, zodat de sessie behouden blijft
        client2 = Client()
        resp = client2.post('/account/login/',
                            {'login_naam': self.account_beh1.username,
                             'wachtwoord': self.WACHTWOORD})
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect = success
        session_key_beh1 = AccountSessions.objects.first().session.session_key

        session = SessionStore(session_key_beh1)
        self.assertEqual(session[SESSIONVAR_ROL_MAG_WISSELEN_BOOL], False)

        resp = client2.get('/plein/')
        urls = self.extract_all_urls(resp)
        self.assertNotIn('/functie/wissel-van-rol/', urls)

        session = SessionStore(session_key_beh1)
        self.assertEqual(session[SESSIONVAR_ROL_MAG_WISSELEN_BOOL], False)

        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()

        # koppel beheerder1 aan zijn eerste rol
        self.assertEqual(self.functie_bko.accounts.count(), 0)
        url = self.url_wijzig_ontvang % self.functie_bko.pk
        with self.assert_max_queries(21):
            resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(self.functie_bko.accounts.count(), 1)

        session = SessionStore(session_key_beh1)
        self.assertEqual(session[SESSIONVAR_ROL_MAG_WISSELEN_BOOL], True)

        resp = client2.get('/plein/')
        urls = self.extract_all_urls(resp)
        self.assertIn('/functie/wissel-van-rol/', urls)

        session = SessionStore(session_key_beh1)
        self.assertEqual(session[SESSIONVAR_ROL_MAG_WISSELEN_BOOL], True)

        # coverage: eerste koppeling als de gebruiker al wissel-van-rol heeft
        self.functie_bko.accounts.clear()
        resp = self.client.post(url, {'add': self.account_beh1.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        session = SessionStore(session_key_beh1)
        self.assertEqual(session[SESSIONVAR_ROL_MAG_WISSELEN_BOOL], True)


# end of file
