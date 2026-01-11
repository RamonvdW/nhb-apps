# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.utils.timezone import make_aware
from BasisTypen.definities import GESLACHT_ANDERS
from Bondspas.models import BondspasJaar
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Opleiding.models import OpleidingDiploma
from Sporter.models import Sporter, SporterVoorkeuren, Speelsterkte
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from unittest.mock import patch
import datetime


class TestBondspasOnline(E2EHelpers, TestCase):

    """ tests voor de Bondspas applicatie, ophalen van de bondspas """

    url_toon_sporter = '/bondspas/toon/'
    url_toon_van = '/bondspas/toon/van-lid/%s/'         # lid_nr
    url_ver_van = '/bondspas/vereniging/van-lid/%s/'    # lid_nr
    url_ophalen = '/bondspas/dynamic/ophalen/'
    url_download = '/bondspas/dynamic/download/'

    bondspas_jaar1 = 2025       # files/achtergrond_bondspas-2025.jpg moet aanwezig zijn
    bondspas_jaar2 = 2026       # files/achtergrond_bondspas-2026.jpg moet aanwezig zijn

    def setUp(self):

        self.lid_nr = 123456

        BondspasJaar.objects.create(jaar=self.bondspas_jaar1, zichtbaar=True)
        BondspasJaar.objects.create(jaar=self.bondspas_jaar2, zichtbaar=False)

        now = datetime.datetime.now()

        # maak een test vereniging
        self.ver1 = Vereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=Regio.objects.get(regio_nr=112))
        self.ver1.save()

        self.sporter = sporter = Sporter(
                                    lid_nr=self.lid_nr,
                                    voornaam='Tester',
                                    achternaam='De tester',
                                    unaccented_naam='test',
                                    email='tester@mail.not',
                                    geboorte_datum=datetime.date(year=now.year - 55, month=3, day=4),
                                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                                    geslacht='M',
                                    bij_vereniging=self.ver1,
                                    lid_tot_einde_jaar=now.year)
        self.account = self.e2e_create_account(self.lid_nr, sporter.email, sporter.voornaam)
        sporter.account = self.account
        sporter.save()

        self.voorkeuren, _ = SporterVoorkeuren.objects.get_or_create(sporter=self.sporter)

        self.account_admin = self.e2e_create_account_admin()

        self.functie_sec = maak_functie('SEC test', 'SEC')
        self.functie_sec.vereniging = self.ver1
        self.functie_sec.save()
        self.functie_sec.accounts.add(self.account_admin)

        self.functie_la = maak_functie('LA test', 'LA')
        self.functie_la.vereniging = self.ver1
        self.functie_la.save()
        self.functie_la.accounts.add(self.account_admin)

    def test_toon(self):
        # anon
        resp = self.client.get(self.url_toon_sporter)
        self.assert_is_redirect_login(resp, self.url_toon_sporter)

        resp = self.client.get(self.url_ophalen)
        self.assert_is_redirect_login(resp, self.url_toon_sporter)

        resp = self.client.post(self.url_ophalen)
        self.assert_is_redirect_login(resp, self.url_toon_sporter)

        url = self.url_toon_van % 99999
        resp = self.client.get(url)
        self.assert_is_redirect_login(resp, self.url_toon_sporter)

        # sporter
        self.e2e_login(self.account)

        # in januari van het oude jaar
        with patch('django.utils.timezone.now') as mock_timezone:
            dt = make_aware(datetime.datetime(year=self.bondspas_jaar1, month=1, day=31, hour=19))
            mock_timezone.return_value = dt

            with self.assert_max_queries(20):
                resp = self.client.get(self.url_toon_sporter)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('bondspas/toon-bondspas-sporter.dtl', 'design/site_layout.dtl'))

        # in juli
        with patch('django.utils.timezone.now') as mock_timezone:
            dt = make_aware(datetime.datetime(year=self.bondspas_jaar1, month=7, day=1, hour=19))
            mock_timezone.return_value = dt

            with self.assert_max_queries(20):
                resp = self.client.get(self.url_toon_sporter)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('bondspas/toon-bondspas-sporter.dtl', 'design/site_layout.dtl'))

        # in januari van het nieuwe jaar
        with patch('django.utils.timezone.now') as mock_timezone:
            dt = make_aware(datetime.datetime(year=self.bondspas_jaar2, month=1, day=7, hour=19))
            mock_timezone.return_value = dt

            with self.assert_max_queries(20):
                resp = self.client.get(self.url_toon_sporter)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('bondspas/toon-bondspas-sporter.dtl', 'design/site_layout.dtl'))

        # gast-account
        self.sporter.is_gast = True
        self.sporter.save(update_fields=['is_gast'])
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_toon_sporter)
        self.assert404(resp, 'Geen bondspas voor gast-accounts')

        resp = self.client.get(self.url_toon_van % 99999)
        self.assert403(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_toon_sporter)
        self.e2e_assert_other_http_commands_not_supported(self.url_toon_van % 999999)
        self.e2e_assert_other_http_commands_not_supported(self.url_ver_van % 999999, post=False)
        self.e2e_assert_other_http_commands_not_supported(self.url_ophalen, post=False)

    def _check_bondspas_resp(self, resp):
        # check het antwoord
        data = self.assert200_json(resp)
        keys = list(data.keys())
        self.assertEqual(keys, ['bondspas_base64'])

        base64_len = len(data['bondspas_base64'])
        self.assertTrue(base64_len > 100000)        # minimaal 100kB image
        self.assertTrue(base64_len < 2000000)       # maximaal 2MB image

    def _check_bondspas_pdf(self, resp):
        # check het antwoord
        self.assert_bestand(resp, 'application/pdf')
        # print(repr(resp.content))
        header = resp.content[:5]
        self.assertEqual(header, b'%PDF-')

    def test_ophalen(self):
        # sporter
        self.e2e_login(self.account)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_ophalen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self._check_bondspas_resp(resp)

        now = datetime.datetime.now()

        # speciaal geval: jarig op 1 januari
        # speciaal geval: geslacht X
        # speciaal geval: geen vereniging
        # speciaal: KHSN leeftijdsklassen die anders is dan WA: 60
        # speciaal: para classificatie
        self.sporter.geboorte_datum = '%4d-01-01' % (now.year - 60)
        self.sporter.geslacht = GESLACHT_ANDERS
        self.sporter.bij_vereniging = None
        self.sporter.wa_id = '99999'
        self.sporter.para_classificatie = 'ST'
        self.sporter.save(update_fields=['geboorte_datum', 'geslacht', 'bij_vereniging', 'wa_id', 'para_classificatie'])

        self.voorkeuren.wedstrijd_geslacht_gekozen = False
        self.voorkeuren.save(update_fields=['wedstrijd_geslacht_gekozen'])

        test_opleiding_codes = [
            ('041', 'Pas ja', 'Test code 41', ()),
            ('042', 'Pas ja', 'Test code 42', ('041',))
        ]

        OpleidingDiploma(
                    sporter=self.sporter,
                    code='042',
                    beschrijving='n/a',
                    toon_op_pas=True).save()

        OpleidingDiploma(
                    sporter=self.sporter,
                    code='041',
                    beschrijving='n/a',
                    toon_op_pas=True).save()

        OpleidingDiploma(
                    sporter=self.sporter,
                    code='TBD',
                    beschrijving='n/a',
                    toon_op_pas=True).save()

        Speelsterkte(
                sporter=self.sporter,
                datum='2000-01-01',
                beschrijving='test',
                discipline='test',
                category='test',
                pas_code='TST',
                volgorde=100).save()

        Speelsterkte(
                sporter=self.sporter,
                datum='2000-01-01',
                beschrijving='test',
                discipline='test',      # zelfde als hierboven
                category='test',
                pas_code='TST',
                volgorde=101).save()

        with override_settings(OPLEIDING_CODES=test_opleiding_codes):
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_ophalen)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self._check_bondspas_resp(resp)

        # download de pdf
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_download)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self._check_bondspas_pdf(resp)

        # gast-account
        self.sporter.is_gast = True
        self.sporter.save(update_fields=['is_gast'])
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_ophalen)
        self.assert404(resp, 'Geen bondspas voor gast-accounts')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_download)
        self.assert404(resp, 'Geen bondspas voor gast-accounts')

    def test_beheerder_van(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        self.sporter.is_erelid = True
        self.sporter.save(update_fields=['is_erelid'])

        url = self.url_toon_van % self.sporter.lid_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bondspas/toon-bondspas-van.dtl', 'design/site_layout.dtl'))

        # download de pdf
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self._check_bondspas_pdf(resp)

        # gast-account
        self.sporter.is_gast = True
        self.sporter.save(update_fields=['is_gast'])
        resp = self.client.get(url)
        self.assert404(resp, 'Geen bondspas voor gast-accounts')
        resp = self.client.post(url)
        self.assert404(resp, 'Geen bondspas voor gast-accounts')

        url = self.url_toon_van % 99999
        resp = self.client.get(url)
        self.assert404(resp, 'Geen valide parameter')
        resp = self.client.post(url)
        self.assert404(resp, 'Geen valide parameter')

    def test_ver_van(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        url = self.url_ver_van % self.sporter.lid_nr

        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bondspas/toon-bondspas-van.dtl', 'design/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [url])

        # download de pdf
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self._check_bondspas_pdf(resp)

        self.e2e_wissel_naar_functie(self.functie_la)
        self.e2e_check_rol('LA')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bondspas/toon-bondspas-van.dtl', 'design/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [url])

        # download de pdf
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self._check_bondspas_pdf(resp)

        # gast-account
        self.sporter.is_gast = True
        self.sporter.save(update_fields=['is_gast'])
        resp = self.client.get(url)
        self.assert404(resp, 'Geen bondspas voor gast-accounts')
        resp = self.client.post(url)
        self.assert404(resp, 'Geen bondspas voor gast-accounts')
        self.sporter.is_gast = False
        self.sporter.bij_vereniging = None
        self.sporter.save(update_fields=['is_gast', 'bij_vereniging'])

        # corner cases
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde vereniging')
        resp = self.client.post(url)
        self.assert404(resp, 'Verkeerde vereniging')

        resp = self.client.get(self.url_ver_van % 99999)
        resp = self.client.post(self.url_ver_van % 99999)
        self.assert404(resp, 'Geen valide parameter')

    def test_speelsterkte(self):
        for lp in range(15):
            Speelsterkte(
                sporter=self.sporter,
                datum='2000-01-01',
                beschrijving='test',
                discipline='uniek %s' % lp,
                category='test',
                pas_code='CodeLang',
                volgorde=600 + lp).save()
        # for

        # sporter
        self.e2e_login(self.account)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_ophalen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self._check_bondspas_resp(resp)

    def test_begin_nieuwe_jaar(self):
        # sporter
        self.e2e_login(self.account)

        # self.bondspas_jaar2 heeft zichtbaar=False
        with patch('django.utils.timezone.now') as mock_timezone:
            dt = make_aware(datetime.datetime(year=self.bondspas_jaar2, month=1, day=1, hour=19))
            mock_timezone.return_value = dt

            with self.assert_max_queries(20):
                resp = self.client.post(self.url_ophalen)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self._check_bondspas_resp(resp)

    def test_corner_cases(self):
        # sporter
        self.e2e_login(self.account)

        # geen bondspas record
        BondspasJaar.objects.all().update(zichtbaar=False)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_toon_sporter)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bondspas/toon-bondspas-sporter.dtl', 'design/site_layout.dtl'))

        # admin interface
        bondspas = BondspasJaar(jaar=1999, zichtbaar=False)
        self.assertTrue(str(bondspas) != '')
        bondspas.zichtbaar = True
        self.assertTrue(str(bondspas) != '')

        # inactief lid
        self.sporter.is_actief_lid = False
        self.sporter.save(update_fields=['is_actief_lid'])

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_ophalen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert404(resp, 'Geen bondspas voor inactieve leden')

        # geen sporter account
        self.sporter.delete()

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_ophalen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert404(resp, 'Geen bondspas voor dit account')

# end of file
