# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from Functie.models import Functie
from Geo.models import Regio
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Webwinkel.models import WebwinkelProduct, WebwinkelFoto
from PIL import Image
import tempfile
import os


class TestWebwinkelCli(E2EHelpers, TestCase):
    """ unittests voor de Webwinkel applicatie, management commando's """

    def setUp(self):
        """ initialisatie van de test case """
        self.lid_nr = 123456

        self.account_normaal = self.e2e_create_account(self.lid_nr, 'winkel@test.not', 'Mgr', accepteer_vhpg=True)

        self.ver1 = Vereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=Regio.objects.get(regio_nr=112))
        self.ver1.save()

        sporter1 = Sporter(
                    lid_nr=self.lid_nr,
                    geslacht='M',
                    voornaam='Mgr',
                    achternaam='Winkel',
                    geboorte_datum='1977-07-07',
                    sinds_datum='2020-07-07',
                    adres_code='1234AB56',
                    account=self.account_normaal,
                    bij_vereniging=self.ver1)
        sporter1.save()
        self.sporter1 = sporter1

        self.functie_mww = Functie.objects.get(rol='MWW')
        self.functie_mww.accounts.add(self.account_normaal)

        foto = WebwinkelFoto()
        foto.save()
        self.foto = foto

        foto2 = WebwinkelFoto(
                        locatie='test_1.jpg',
                        locatie_thumb='test_1_thumb.jpg')
        foto2.save()
        self.foto2 = foto2

        self.tmp_dir = tempfile.TemporaryDirectory()
        self.foto_dir = self.tmp_dir.name
        if os.path.isdir(self.foto_dir):            # pragma: no branch
            # create a few placeholder fotos
            for fname in (foto2.locatie, foto2.locatie_thumb):
                fpath = os.path.join(self.foto_dir, fname)
                with open(fpath, "wb") as fhandle:
                    fhandle.write(b'hello')
            # for

        product = WebwinkelProduct(
                        omslag_titel='Test titel 1',
                        onbeperkte_voorraad=True,
                        omslag_foto=foto,
                        bestel_begrenzing='')
        product.save()
        self.product = product

        product2 = WebwinkelProduct(
                        omslag_titel='Test titel 2',
                        onbeperkte_voorraad=False,
                        aantal_op_voorraad=10,
                        eenheid='doos,dozen',
                        bestel_begrenzing='1-20')
        product2.save()
        self.product2 = product2

        product3 = WebwinkelProduct(
                        omslag_titel='Test titel 3',
                        sectie='x',
                        onbeperkte_voorraad=False,
                        aantal_op_voorraad=0)           # uitverkocht
        product3.save()
        self.product3 = product3
        self.product3.fotos.add(foto2)

        ongebruikte_foto = WebwinkelFoto(volgorde=66)
        ongebruikte_foto.save()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_check_fotos(self):
        # 1 product heeft een omslagfoto met lege locatie en locatie_thumb
        # 3 product heeft bestaande foto's
        with override_settings(WEBWINKEL_FOTOS_DIR=self.foto_dir):
            with self.assert_max_queries(20):
                f1, f2 = self.run_management_command('check_fotos', report_exit_code=False)
            # print("\nf1:\n%s\nf2:\n%s" % (f1.getvalue(), f2.getvalue()))
            self.assertTrue(" heeft een lege locatie" in f1.getvalue())
            self.assertTrue("Test titel 2) heeft geen omslagfoto" in f2.getvalue())
            self.assertTrue("Test titel 3) heeft geen omslagfoto" in f2.getvalue())
            self.assertTrue("wordt niet (meer) gebruikt" in f2.getvalue())
            self.assertTrue("[INFO] 2 foto's OK" in f2.getvalue())
            self.assertTrue("[ERROR] 4 foto's NOK" in f1.getvalue())

            self.foto.locatie = 'non-existing.jpg'
            self.foto.save()

            # 1 product heeft een niet bestaande foto
            with self.assert_max_queries(20):
                f1, f2 = self.run_management_command('check_fotos', report_exit_code=False)
            # print("\nf1:\n%s\nf2:\n%s" % (f1.getvalue(), f2.getvalue()))
            self.assertTrue('[ERROR] ' in f1.getvalue())
            self.assertTrue(' locatie bestand niet gevonden: ' in f1.getvalue())
            self.assertTrue(self.foto.locatie in f1.getvalue())
            self.assertTrue("[INFO] 2 foto's OK" in f2.getvalue())
            self.assertTrue("[ERROR] 4 foto's NOK" in f1.getvalue())

            # verwijder het probleemgeval
            # de ERROR verandert in een WARNING: product 1 heeft nu ook geen omslagfoto
            self.foto.delete()

            # dubbel gebruik van een foto
            self.product2.fotos.add(self.foto2)

            with self.assert_max_queries(20):
                f1, f2 = self.run_management_command('check_fotos', report_exit_code=False)
            # print("\nf1:\n%s\nf2:\n%s" % (f1.getvalue(), f2.getvalue()))
            self.assertTrue("[INFO] 4 foto's OK" in f2.getvalue())
            self.assertTrue("[ERROR] 4 foto's NOK" in f1.getvalue())
            self.assertTrue("wordt ook gebruikt door product pk=" in f1.getvalue())

            # verwijder alles, dan zijn er geen fouten meer
            WebwinkelProduct.objects.all().delete()
            WebwinkelFoto.objects.all().delete()
            with self.assert_max_queries(20):
                f1, f2 = self.run_management_command('check_fotos', report_exit_code=False)
            _ = (f1 == f2)
            # print("\nf1:\n%s\nf2:\n%s" % (f1.getvalue(), f2.getvalue()))
            self.assertTrue("[INFO] 0 foto's OK; no problems found" in f2.getvalue())

    def test_koppel_fotos(self):
        self.product3.fotos.clear()

        with override_settings(WEBWINKEL_FOTOS_DIR=self.foto_dir):
            # fotobestand niet gevonden
            with self.assert_max_queries(20):
                f1, f2 = self.run_management_command('koppel_fotos', 'Test titel 9999', 'foto1.jpg',
                                                     report_exit_code=False)
            # print("\nf1:\n%s\nf2:\n%s" % (f1.getvalue(), f2.getvalue()))
            self.assertTrue("[ERROR] Kan foto niet vinden: " in f1.getvalue())
            self.assertTrue("foto1.jpg" in f1.getvalue())

            # product niet gevonden
            with self.assert_max_queries(20):
                f1, f2 = self.run_management_command('koppel_fotos', 'Test titel 9999', self.foto2.locatie,
                                                     report_exit_code=False)
            # print("\nf1:\n%s\nf2:\n%s" % (f1.getvalue(), f2.getvalue()))
            self.assertTrue("[ERROR] Product niet gevonden" in f1.getvalue())
            self.assertTrue("[INFO] Zoek product met omslag_titel 'Test titel 9999'" in f2.getvalue())

            # meerdere producten matchen
            with self.assert_max_queries(20):
                f1, f2 = self.run_management_command('koppel_fotos', 'Test titel', self.foto2.locatie,
                                                     report_exit_code=False)
            # print("\nf1:\n%s\nf2:\n%s" % (f1.getvalue(), f2.getvalue()))
            self.assertTrue("[ERROR] Meerdere producten gevonden:" in f1.getvalue())

            # koppel omslagfoto aan product
            with self.assert_max_queries(20):
                f1, f2 = self.run_management_command('koppel_fotos', 'Test titel 1', self.foto2.locatie,
                                                     report_exit_code=False)
            # print("\nf1:\n%s\nf2:\n%s" % (f1.getvalue(), f2.getvalue()))
            self.assertTrue("[INFO] Zoek product met omslag_titel 'Test titel 1'" in f2.getvalue())
            self.assertTrue("[INFO] Gevonden product: 'Test titel 1'" in f2.getvalue())
            self.assertTrue("[INFO] Foto 'test_1.jpg' gekoppeld als omslagfoto" in f2.getvalue())

            # koppel meerdere foto's aan product + maak thumbnail (van garbage)
            with self.assert_max_queries(20):
                f1, f2 = self.run_management_command('koppel_fotos', 'Test titel 1', self.foto2.locatie,
                                                     self.foto2.locatie, report_exit_code=False)
            # print("\nf1:\n%s\nf2:\n%s" % (f1.getvalue(), f2.getvalue()))
            self.assertTrue("[INFO] Zoek product met omslag_titel 'Test titel 1'" in f2.getvalue())
            self.assertTrue("[INFO] Gevonden product: 'Test titel 1'" in f2.getvalue())
            self.assertTrue("[INFO] Foto 'test_1.jpg' was al gekoppeld als omslagfoto" in f2.getvalue())

            # maak een goede foto aan
            fpath = os.path.join(self.foto_dir, self.foto2.locatie)
            im = Image.new('RGB', (100, 100))
            im.save(fpath, "jpeg")

            # koppel meerdere foto's aan product + maak thumbnail
            with self.assert_max_queries(20):
                f1, f2 = self.run_management_command('koppel_fotos', 'Test titel 1', self.foto2.locatie,
                                                     self.foto2.locatie, report_exit_code=False)
            # print("\nf1:\n%s\nf2:\n%s" % (f1.getvalue(), f2.getvalue()))
            self.assertTrue("[INFO] Zoek product met omslag_titel 'Test titel 1'" in f2.getvalue())
            self.assertTrue("[INFO] Gevonden product: 'Test titel 1'" in f2.getvalue())
            self.assertTrue("[INFO] Foto 'test_1.jpg' was al gekoppeld als omslagfoto" in f2.getvalue())
            self.assertTrue("[INFO] Maak thumbnail 'test_1_thumb.jpg'" in f2.getvalue())
            self.assertTrue("[INFO] Foto 'test_1.jpg' + thumb gekoppeld aan product" in f2.getvalue())

            # corner case: thumb pad is aangepast
            self.foto2 = WebwinkelFoto.objects.get(pk=self.foto2.pk)
            self.foto2.locatie_thumb = 'xxx'
            self.foto2.save()
            with self.assert_max_queries(20):
                f1, f2 = self.run_management_command('koppel_fotos', 'Test titel 1', self.foto2.locatie,
                                                     self.foto2.locatie, report_exit_code=False)
            # print("\nf1:\n%s\nf2:\n%s" % (f1.getvalue(), f2.getvalue()))
            self.assertTrue("[INFO] Gevonden product: 'Test titel 1'" in f2.getvalue())
            self.assertTrue("[INFO] Foto 'test_1.jpg' was al gekoppeld als omslagfoto" in f2.getvalue())
            self.assertTrue("[INFO] Maak thumbnail 'test_1_thumb.jpg'" in f2.getvalue())
            self.assertTrue("[INFO] Foto 'test_1.jpg' was al gekoppeld aan product" in f2.getvalue())

            # verwijder een foto
            with self.assert_max_queries(20):
                f1, f2 = self.run_management_command('koppel_fotos', 'Test titel 1', self.foto2.locatie,
                                                     report_exit_code=False)
            # print("\nf1:\n%s\nf2:\n%s" % (f1.getvalue(), f2.getvalue()))
            self.assertTrue("[INFO] Foto 'test_1.jpg' was al gekoppeld als omslagfoto" in f2.getvalue())
            self.assertFalse("[INFO] Foto 'test_1.jpg' was al gekoppeld aan product" in f2.getvalue())
            self.assertTrue("[INFO] De volgende foto's worden losgekoppeld: [" in f2.getvalue())

    def test_maak_kleding(self):
        f1, f2 = self.run_management_command('maak_kleding', 'bestand', report_exit_code=False)
        self.assertTrue("[ERROR] Kan bestand 'bestand' niet laden:" in f1.getvalue())

        fname = 'Webwinkel/test-files/test-maak-kleding.txt'
        f1, f2 = self.run_management_command('maak_kleding', fname, report_exit_code=False)
        # print('f1: %s' % f1.getvalue())
        # print('f2: %s' % f2.getvalue())
        self.assertTrue('[INFO] Maak product 1: Test-shirt (YXS)' in f2.getvalue())
        self.assertTrue('[INFO] Maak product 2: Test-shirt (XXS)' in f2.getvalue())
        self.assertTrue('[INFO] Maak product 3: Test-shirt (XS)' in f2.getvalue())
        self.assertTrue('[ERROR] Kan foto niet vinden:' in f2.getvalue())
        self.assertTrue("[ERROR] Onbekend keyword='Onbekend'" in f2.getvalue())

# end of file
