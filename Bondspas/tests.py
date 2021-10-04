# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.core import management
from django.conf import settings
from django.utils import timezone
from Bondspas.models import Bondspas
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
import tempfile
import datetime
import json
import stat
import os
import io


class TestBondspas(E2EHelpers, TestCase):

    """ tests voor de Bondspas applicatie """

    url_check_status = '/sporter/bondspas/check-status/'
    url_toon = '/sporter/bondspas/toon/'

    def setUp(self):

        self.lid_nr = 123456

        now = datetime.datetime.now()

        self.sporter = sporter = Sporter(
                                    lid_nr=self.lid_nr,
                                    voornaam='Tester',
                                    achternaam='De tester',
                                    unaccented_naam='test',
                                    email='tester@mail.not',
                                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                                    geslacht='M',
                                    # bij_vereniging
                                    lid_tot_einde_jaar=now.year)
        self.account = self.e2e_create_account(self.lid_nr, sporter.email, sporter.voornaam)
        sporter.account = self.account
        sporter.save()

    def test_check_status(self):
        # anon
        resp = self.client.post(self.url_check_status, {})
        self.assert403(resp)

        # sporter
        self.e2e_login(self.account)

        # post zonder data
        resp = self.client.post(self.url_check_status, {})
        self.assert404(resp)

        # get is not implemented
        resp = self.client.get(self.url_check_status)
        self.assertEqual(resp.status_code, 405)

        # corrupte json
        data = "hallo daar"
        resp = self.client.post(self.url_check_status, data=data, content_type="application/json")
        self.assert404(resp, 'Geen valide verzoek')

        # ontbrekend veld
        data = '{"daar": "1"}'
        resp = self.client.post(self.url_check_status, data=data, content_type="application/json")
        self.assert404(resp, 'Niet gevonden')

        # geen valide lid_nr
        data = '{"lid_nr": "blablabla"}'
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_check_status, data=data, content_type="application/json")
        self.assert404(resp, 'Niet gevonden')

        # wel valide lid_nr, maar nog geen record in de database
        data = '{"lid_nr": %s}' % self.lid_nr
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_check_status, data=data, content_type="application/json")
        self.assert404(resp, 'Niet gevonden')

        # maak een record aan en check the status
        bondspas = Bondspas(
                        lid_nr=self.lid_nr,
                        status='N')     # nieuw
        bondspas.save()

        for status_code, expected_status in (('N', "onbekend"),     # nieuw
                                             ('O', "bezig"),        # ophalen
                                             ('B', "bezig"),
                                             ('A', "aanwezig"),
                                             ('F', "fail"),
                                             ('V', "onbekend"),     # verwijderd
                                             ('N', "onbekend")):    # nieuw
            bondspas.status = status_code
            bondspas.save(update_fields=['status'])

            with self.assert_max_queries(20):
                resp = self.client.post(self.url_check_status, data=data, content_type="application/json")
            self.assertEqual(resp.status_code, 200)
            reply = json.loads(resp.content)
            self.assertEqual(reply['status'], expected_status)
        # for

        self.e2e_assert_other_http_commands_not_supported(self.url_check_status, post=False)

    def test_toon(self):
        # anon
        resp = self.client.get(self.url_toon)
        self.assert403(resp)

        # sporter
        self.e2e_login(self.account)

        # eerste keer --> ophalen
        self.assertEqual(Bondspas.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bondspas/bondspas-ophalen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Je bondspas wordt opgehaald.")

        self.assertEqual(Bondspas.objects.count(), 1)
        bondspas = Bondspas.objects.get(lid_nr=self.lid_nr)
        self.assertEqual(bondspas.status, 'O')      # ophalen
        self.assertTrue(str(bondspas) != '')

        # verwijderd --> ophalen
        bondspas.status = 'V'
        bondspas.save(update_fields=['status'])
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('bondspas/bondspas-ophalen.dtl', 'plein/site_layout.dtl'))

        bondspas = Bondspas.objects.get(lid_nr=self.lid_nr)
        self.assertEqual(bondspas.status, 'O')      # ophalen

        # fail + nog niet tijd om opnieuw op te halen
        when = timezone.now() + datetime.timedelta(days=1)
        bondspas.status = 'F'
        bondspas.opnieuw_proberen_na = when
        bondspas.save(update_fields=['status', 'opnieuw_proberen_na'])
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bondspas/bondspas-ophalen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Over een paar minuten')
        bondspas = Bondspas.objects.get(lid_nr=self.lid_nr)
        self.assertEqual(bondspas.status, 'F')      # nog steeds Fail

        # fail + opnieuw proberen
        bondspas.opnieuw_proberen_na = timezone.now() - datetime.timedelta(minutes=1)
        bondspas.save(update_fields=['status', 'opnieuw_proberen_na'])
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bondspas/bondspas-ophalen.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Over een paar minuten')
        bondspas = Bondspas.objects.get(lid_nr=self.lid_nr)
        self.assertEqual(bondspas.status, 'O')      # Ophalen

        # aanwezig, maar geen bestand --> fallback naar ophalen
        bondspas.status = 'A'
        bondspas.aanwezig_sinds = timezone.now()
        bondspas.save(update_fields=['status', 'aanwezig_sinds'])
        self.assertTrue(str(bondspas) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bondspas/bondspas-ophalen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Er is een onverwacht probleem opgetreden')
        bondspas = Bondspas.objects.get(lid_nr=self.lid_nr)
        self.assertEqual(bondspas.status, 'O')      # Ophalen
        self.assertEqual(bondspas.aantal_keer_bekeken, 0)

        # create bondspas bestand
        fname = "bondspas_%s.pdf" % self.lid_nr
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_file = os.path.join(tmp_dir, fname)
            with open(tmp_file, 'wb') as w:
                w.write(b'bondspas testje\n')
            # with
            bondspas.status = 'A'
            bondspas.filename = fname
            bondspas.save(update_fields=['status', 'filename'])

            # aanwezig
            with override_settings(BONDSPAS_CACHE_PATH=tmp_dir):
                with self.assert_max_queries(20):
                    resp = self.client.get(self.url_toon)
            self.assertEqual(resp.get('content-type'), 'application/pdf')
            self.assertEqual(resp.get('content-disposition'), 'inline; filename="bondspas_123456.pdf"')
        # with

        bondspas = Bondspas.objects.get(lid_nr=self.lid_nr)
        self.assertEqual(bondspas.status, 'A')      # Ophalen
        self.assertEqual(bondspas.aantal_keer_bekeken, 1)

        # weird status
        bondspas.status = 'X'
        bondspas.save(update_fields=['status'])
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bondspas/bondspas-ophalen.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_toon)

    def test_cli(self):
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        # maak nog een bondspas records aan, om de for-loop bezig te houden
        Bondspas(
                lid_nr=100042,
                status='O',
                opnieuw_proberen_na=timezone.now() + datetime.timedelta(days=5)).save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with override_settings(BONDSPAS_CACHE_PATH='garbage'):
            management.call_command('bondspas_downloader', '1', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('[ERROR] Bondspas cache directory bestaat niet: garbage' in f1.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20, check_duration=False):
            management.call_command('bondspas_downloader', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('[TODO] Implement bondspas cache scrubbing' in f1.getvalue())
        # self.assertEqual(f1.getvalue(), '')
        self.assertTrue('[INFO] Taak loopt tot ' in f2.getvalue())

        # maak een ophaal verzoek aan, maar kan niet verbinden met server
        bondspas = Bondspas(lid_nr=self.lid_nr, status='O')
        bondspas.save()
        f1 = io.StringIO()
        f2 = io.StringIO()
        with override_settings(BONDSPAS_DOWNLOAD_URL='http://localhost:9999/%s'):
            management.call_command('bondspas_downloader', '1', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('[WARNING] Onverwachte fout:' in f2.getvalue())
        bondspas = Bondspas.objects.get(lid_nr=self.lid_nr)
        self.assertEqual(bondspas.status, 'F')
        self.assertIsNotNone(bondspas.opnieuw_proberen_na)
        self.assertTrue('Onverwachte fout (zie logfile)' in bondspas.log)

        # maak een ophaal verzoek aan, maar de server geeft status 500
        bondspas.status = 'O'
        bondspas.opnieuw_proberen_na = None
        bondspas.save(update_fields=['log', 'status', 'opnieuw_proberen_na'])
        with override_settings(BONDSPAS_DOWNLOAD_URL=settings.BONDSPAS_DOWNLOAD_URL + '/werkt-niet-meer'):
            f1 = io.StringIO()
            f2 = io.StringIO()
            management.call_command('bondspas_downloader', '1', '--quick', stderr=f1, stdout=f2)
            self.assertTrue('[WARNING] Onverwachte fout:' in f2.getvalue())
            self.assertTrue('Connection aborted' in f2.getvalue())
            bondspas = Bondspas.objects.get(lid_nr=self.lid_nr)
            self.assertEqual(bondspas.status, 'F')  # failed
            self.assertIsNotNone(bondspas.opnieuw_proberen_na)
        # with

        # maak een ophaal verzoek aan, maar de server geeft status 404
        bondspas.status = 'O'
        bondspas.opnieuw_proberen_na = None
        bondspas.save(update_fields=['status', 'opnieuw_proberen_na'])
        url = settings.BONDSPAS_DOWNLOAD_URL % 404
        url += '/%s'
        with override_settings(BONDSPAS_DOWNLOAD_URL=url):
            f1 = io.StringIO()
            f2 = io.StringIO()
            management.call_command('bondspas_downloader', '1', '--quick', stderr=f1, stdout=f2)
            self.assertTrue('[WARNING] Unexpected status_code: 404' in f2.getvalue())
            bondspas = Bondspas.objects.get(lid_nr=self.lid_nr)
            self.assertEqual(bondspas.status, 'F')  # failed
            self.assertIsNotNone(bondspas.opnieuw_proberen_na)

        # maak een ophaal verzoek aan, maar de server geeft status 500
        bondspas.status = 'O'
        bondspas.opnieuw_proberen_na = None
        bondspas.save(update_fields=['status', 'opnieuw_proberen_na'])
        url = settings.BONDSPAS_DOWNLOAD_URL % 500
        url += '/%s'
        with override_settings(BONDSPAS_DOWNLOAD_URL=url):
            f1 = io.StringIO()
            f2 = io.StringIO()
            management.call_command('bondspas_downloader', '1', '--quick', stderr=f1, stdout=f2)
            self.assertTrue('[WARNING] Unexpected status_code: 500' in f2.getvalue())
            bondspas = Bondspas.objects.get(lid_nr=self.lid_nr)
            self.assertEqual(bondspas.status, 'F')  # failed
            self.assertIsNotNone(bondspas.opnieuw_proberen_na)

        # doe een echte download, maar het bestand is te klein
        bondspas.status = 'O'
        bondspas.opnieuw_proberen_na = None
        bondspas.save(update_fields=['status', 'opnieuw_proberen_na'])
        url = settings.BONDSPAS_DOWNLOAD_URL % 42
        url += '/%s'
        with override_settings(BONDSPAS_DOWNLOAD_URL=url):
            f1 = io.StringIO()
            f2 = io.StringIO()
            management.call_command('bondspas_downloader', '1', '--quick', stderr=f1, stdout=f2)
            self.assertTrue('[WARNING] Unreasonable length (42 bytes)' in f2.getvalue())
            bondspas = Bondspas.objects.get(lid_nr=self.lid_nr)
            self.assertEqual(bondspas.status, 'F')  # failed
            self.assertIsNotNone(bondspas.opnieuw_proberen_na)

        # doe een echte download, maar geen content-length header
        bondspas.status = 'O'
        bondspas.opnieuw_proberen_na = timezone.now() - datetime.timedelta(days=2)   # zet in het verleden
        bondspas.save(update_fields=['status', 'opnieuw_proberen_na'])
        url = settings.BONDSPAS_DOWNLOAD_URL % '43'
        url += '/%s'
        with override_settings(BONDSPAS_DOWNLOAD_URL=url):
            f1 = io.StringIO()
            f2 = io.StringIO()
            management.call_command('bondspas_downloader', '1', '--quick', stderr=f1, stdout=f2)
            self.assertTrue('[WARNING] Missing header: Content-length' in f2.getvalue())
            bondspas = Bondspas.objects.get(lid_nr=self.lid_nr)
            self.assertEqual(bondspas.status, 'F')  # failed
            self.assertIsNotNone(bondspas.opnieuw_proberen_na)

        # ga echt een download down
        bondspas.status = 'O'
        bondspas.opnieuw_proberen_na = None
        bondspas.log = 'regel niet af'  # triggert toevoegen van \n
        bondspas.save(update_fields=['log', 'status', 'opnieuw_proberen_na'])
        with tempfile.TemporaryDirectory() as tmp_dir:
            with override_settings(BONDSPAS_CACHE_PATH=tmp_dir):
                f1 = io.StringIO()
                f2 = io.StringIO()
                with self.assert_max_queries(20):
                    management.call_command('bondspas_downloader', '1', '--quick', stderr=f1, stdout=f2)
                self.assertTrue('[INFO] Bondspas ophalen voor lid 123456' in f2.getvalue())
                bondspas = Bondspas.objects.get(lid_nr=self.lid_nr)
                self.assertEqual(bondspas.status, 'A')      # aanwezig

        # doe nog een download die niet op te slaan is
        tmp_dir = '/tmp/nhb-apps-autotest-bondspas/'
        try:
            os.mkdir(tmp_dir)
        except FileExistsError:     # pragma: no cover
            pass
        os.chmod(tmp_dir, stat.S_IRUSR | stat.S_IXUSR)  # maak directory r-x
        # st = os.stat(tmp_dir)
        # print('mode:', st.st_mode)     # 40500 = IFDIR + R + X
        with override_settings(BONDSPAS_CACHE_PATH=tmp_dir):
            bondspas.status = 'O'
            bondspas.log = 'regel niet af'          # triggert toevoegen van \n
            bondspas.save(update_fields=['log', 'status'])
            f1 = io.StringIO()
            f2 = io.StringIO()
            with self.assert_max_queries(20):
                management.call_command('bondspas_downloader', '1', '--quick', stderr=f1, stdout=f2)
            self.assertTrue('[WARNING] Can bestand niet opslaan: [Errno 13] Permission denied:' in f2.getvalue())
            bondspas = Bondspas.objects.get(lid_nr=self.lid_nr)
            self.assertEqual(bondspas.status, 'F')
            self.assertIsNotNone(bondspas.opnieuw_proberen_na)
        # with
        os.rmdir(tmp_dir)


# end of file
