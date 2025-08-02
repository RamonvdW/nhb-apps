# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.models import Account
from Functie.models import Functie
from Geo.models import Regio
from Mailer.models import MailQueue
from TijdelijkeCodes.models import TijdelijkeCode
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Sporter.models import Sporter
from Vereniging.models import Vereniging, Secretaris
import datetime


class TestRegistreerLid(E2EHelpers, TestCase):

    """ tests voor de Registreer applicatie; voor leden """

    test_after = ('Account',)

    url_tijdelijk = '/tijdelijke-codes/%s/'
    url_registreer_khsn = '/account/registreer/lid/'

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(pk=111))
        ver.save()
        self.ver1 = ver

        # maak de SEC functie aan
        self.functie_sec = Functie(rol='SEC',
                                   vereniging=ver,
                                   beschrijving='SEC vereniging 1000',
                                   bevestigde_email='sec@ver1.not')
        self.functie_sec.save()

        # maak een test lid aan
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    email="normaal@test.com",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver,
                    account=self.account_normaal)
        sporter.save()
        self.sporter_100001 = sporter

        # maak een test lid aan
        sporter = Sporter(
                    lid_nr=100002,
                    geslacht="V",
                    voornaam="Ramona",
                    achternaam="de Testerin",
                    email="",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver)
        sporter.save()
        self.sporter_100002 = sporter

    def test_get(self):
        # test registratie via het formulier
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_registreer_khsn)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid.dtl', 'plein/site_layout.dtl'))

    def test_post(self):
        # partial fields
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': ''})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp.context['form'], None, 'niet alle velden zijn ingevuld')

        # invalid fields
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': '100678',
                                     'email': 'is geen email',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp.context['form'], None, 'de gegevens worden niet geaccepteerd')

        # bad fields
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': 'hallo!',
                                     'email': 'test@test.not',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp.context['form'], None, 'onbekend bondsnummer')

        # niet bestaand nummer
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': '999999',
                                     'email': 'test@test.not',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp.context['form'], None, 'onbekend bondsnummer')

        # verkeerde email
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': '100001',
                                     'email': 'rdetester@gmail.yes',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp.context['form'], None,
                             'de combinatie van bondsnummer en e-mailadres wordt niet herkend. Probeer het nog eens.')

        # zwak wachtwoord: te kort
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': 'te kort'},
                                    follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "wachtwoord is te kort")

        # zwak wachtwoord: verboden reeks
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': 'handboogsport'},
                                    follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "wachtwoord is niet sterk genoeg")

        # zwak wachtwoord: bondsnummer in wachtwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': 'yoho100001jaha'},  # noqa
                                    follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "wachtwoord bevat een verboden reeks")

        # zwak wachtwoord: te weinig verschillende tekens
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': 'jaJAjaJAjaJA'},
                                    follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "wachtwoord bevat te veel gelijke tekens")

    def test_geen_email(self):
        # geen secretaris bekend
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': '100002',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid-fout-geen-email.dtl', 'plein/site_layout.dtl'))

        # vul de SEC in voor deze vereniging
        self.functie_sec.accounts.add(self.sporter_100001.account)      # voor het e-mailadres

        sec = Secretaris(vereniging=self.ver1)
        sec.save()
        sec.sporters.add(self.sporter_100001)       # voor de naam

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': '100002',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid-fout-geen-email.dtl', 'plein/site_layout.dtl'))

    def test_geen_email_geen_sec(self):
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': '100002',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid-fout-geen-email.dtl', 'plein/site_layout.dtl'))

    def test_geen_email_geen_ver(self):
        self.sporter_100002.bij_vereniging = None
        self.sporter_100002.save(update_fields=['bij_vereniging'])
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': '100002',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid-fout-geen-email.dtl', 'plein/site_layout.dtl'))

    def test_registreer(self):
        # maak een andere sporter secretaris van de vereniging
        sec = Secretaris(vereniging=self.ver1)
        sec.save()
        sec.sporters.add(self.sporter_100002)

        # doorloop de registratie
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': '100001',
                                     'email': 'norMAAl@test.com',    # dekt case-insensitive e-mailadres
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid-01-bevestig-email.dtl', 'plein/site_layout.dtl'))

        # controleer dat het email adres obfuscated is
        self.assertNotContains(resp, 'normaal@test.com')
        self.assertContains(resp, 'l@test.com')     # iets van n####l@test.com

        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_registreer/lid-bevestig-toegang-email.dtl')
        self.assert_consistent_email_html_text(mail)

        # controleer dat de volledige naam meteen al overgenomen is
        account = Account.objects.get(username='100001')
        self.assertEqual(account.volledige_naam(), 'Ramon de Tester')

        # verander de naam, om te testen dat de volledige naam later uit het Sporter overgenomen wordt
        account.first_name = '100001'
        account.last_name = ''
        account.save()
        self.assertEqual(account.volledige_naam(), '100001')

        sporter = Sporter.objects.get(lid_nr=self.sporter_100001.lid_nr)
        self.assertEqual(sporter.account, account)

        # volg de link om de email te bevestigen
        # (dit test een stukje functionaliteit aangeboden door Account)
        objs = TijdelijkeCode.objects.all().order_by('-aangemaakt_op')       # nieuwste eerst
        self.assertTrue(len(objs) > 0)
        obj = objs.first()
        self.assertEqual(obj.hoort_bij_account.nieuwe_email, 'normaal@test.com')
        self.assertFalse(obj.hoort_bij_account.email_is_bevestigd)
        url = self.url_tijdelijk % obj.url_code
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        post_url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(post_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid-02-email-bevestigd.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "inloggen")
        self.assertNotContains(resp, "Sluiten")

        account = Account.objects.get(username='100001')
        self.assertTrue(account.email_is_bevestigd)
        self.assertEqual(account.bevestigde_email, 'normaal@test.com')

        # tijdens inlog wordt de volledige naam weer overgenomen (deze hadden we aangepast)
        self.e2e_login(account)
        account = Account.objects.get(username='100001')
        self.assertEqual(account.volledige_naam(), 'Ramon de Tester')

    def test_registreer_al_ingelogd(self):
        # variant van test_registreer waarbij sporter al ingelogd is bij volgen tijdelijke link
        sec = Secretaris(vereniging=self.ver1)
        sec.save()
        sec.sporters.add(self.sporter_100002)

        # doorloop de registratie
        resp = self.client.post(self.url_registreer_khsn,
                                {'lid_nr': '100001',
                                 'email': 'normaal@test.com',
                                 'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid-01-bevestig-email.dtl', 'plein/site_layout.dtl'))

        # volg de link om de email te bevestigen
        objs = TijdelijkeCode.objects.order_by('-aangemaakt_op')       # nieuwste eerst
        obj = objs.first()
        self.assertEqual(obj.hoort_bij_account.nieuwe_email, 'normaal@test.com')
        url = self.url_tijdelijk % obj.url_code
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        post_url = urls[0]

        # log in
        self.e2e_login(self.account_normaal)

        # volg de tijdelijke url --> het scherm heeft nu een knop "sluiten" in plaats van "inloggen"
        with self.assert_max_queries(20):
            resp = self.client.post(post_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid-02-email-bevestigd.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Sluiten")
        self.assertNotContains(resp, "inloggen")

    def test_bestaat_al(self):
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': '100001',
                                     'email': 'normaal@test.com',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid-01-bevestig-email.dtl', 'plein/site_layout.dtl'))

        # tweede poging
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': '100001',
                                     'email': 'normaal@test.com',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp.context['form'], None, 'Account bestaat al')

    def test_inactief(self):
        self.sporter_100001.is_actief_lid = False
        self.sporter_100001.save()

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': '100001',
                                     'email': self.sporter_100001.email,
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp.context['form'], None,
                             'Gebruik van KHSN diensten is geblokkeerd.' +
                             ' Neem contact op met de secretaris van je vereniging.')

    def test_sec(self):
        # lid dat zich registreert, is secretaris van een vereniging
        # en wordt meteen gekoppeld aan de SEC rol

        sec = Secretaris(vereniging=self.ver1)
        sec.save()
        sec.sporters.add(self.sporter_100001)

        functie = Functie.objects.get(rol='SEC', vereniging=self.ver1)
        self.assertEqual(functie.accounts.count(), 0)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': '100001',
                                     'email': 'normaal@test.com',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid-01-bevestig-email.dtl', 'plein/site_layout.dtl'))

        self.sporter_100001 = Sporter.objects.get(pk=self.sporter_100001.pk)   # refresh

        # sporter is nog niet gekoppeld aan de functie
        # dat wordt gedaan door de CRM import
        self.assertEqual(functie.accounts.count(), 0)

        # sporter is wel gekoppeld aan Secretaris
        self.assertEqual(sec.sporters.count(), 1)
        self.assertEqual(sec.sporters.first(), self.sporter_100001)

    def test_geen_ver(self):
        self.sporter_100001.bij_vereniging = None
        self.sporter_100001.save()

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_registreer_khsn,
                                    {'lid_nr': '100001',
                                     'email': self.sporter_100001.email,
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/registreer-lid.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp.context['form'], None,
                             'Gebruik van KHSN diensten is geblokkeerd.' +
                             ' Neem contact op met de secretaris van je vereniging.')


# end of file
