# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.management.base import OutputWrapper
from Bestelling.definities import BESTELLING_REGEL_CODE_WEBWINKEL
from Bestelling.models import BestellingRegel, BestellingMandje
from Geo.models import Regio
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Webwinkel.definities import (VERZENDKOSTEN_PAKKETPOST, VERZENDKOSTEN_BRIEFPOST,
                                  KEUZE_STATUS_RESERVERING_MANDJE, KEUZE_STATUS_BESTELD, KEUZE_STATUS_BACKOFFICE)
from Webwinkel.models import WebwinkelKeuze, WebwinkelProduct
from Webwinkel.plugin_bestelling import WebwinkelBestelPlugin, VerzendkostenBestelPlugin
from decimal import Decimal
import datetime
import io


class TestWebwinkelBestellingPlugin(E2EHelpers, TestCase):

    """ tests voor de Webwinkel applicatie, module Bestelling Plugin """

    def setUp(self):
        """ initialisatie van de test case """

        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(regio_nr=112),
                    bank_iban='IBAN123456789',
                    bank_bic='BIC2BIC',
                    kvk_nummer='KvK1234',
                    website='www.bb.not',
                    contact_email='info@bb.not',
                    telefoonnummer='12345678')
        ver.save()
        self.ver = ver

        product = WebwinkelProduct(
                    omslag_titel='product',
                    prijs_euro=Decimal(10.0),
                    onbeperkte_voorraad=False,
                    aantal_op_voorraad=10,
                    bestel_begrenzing='1-5',
                    gewicht_gram=10,
                    type_verzendkosten=VERZENDKOSTEN_PAKKETPOST)
        product.save()
        self.product = product

        self.account_100000 = self.e2e_create_account('100000', 'normaal@test.not', 'Tester', accepteer_vhpg=True)
        sporter = Sporter(
                        lid_nr=100000,
                        voornaam='Nor',
                        achternaam='Maal',
                        geboorte_datum='1988-08-08',
                        sinds_datum='2020-02-20',
                        account=self.account_100000,
                        bij_vereniging=ver,
                        adres_code='1234XX')
        sporter.save()
        sporter.refresh_from_db()        # geeft opgeslagen datum/tijd formaat
        self.sporter_100000 = sporter

        sporter = Sporter(
                        lid_nr=100001,
                        voornaam='And',
                        achternaam='Ere',
                        geboorte_datum='1988-08-09',
                        sinds_datum='2020-02-21',
                        account=None,
                        email='sporter100001@khsn.not',
                        bij_vereniging=ver,
                        adres_code='1234YY')
        sporter.save()
        sporter.refresh_from_db()        # geeft opgeslagen datum/tijd formaat
        self.sporter_100001 = sporter

        self.mandje = BestellingMandje(
                            account=self.account_100000)
        self.mandje.save()

    def test_opschonen(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = WebwinkelBestelPlugin()
        plugin.zet_stdout(stdout)

        verval = timezone.now() - datetime.timedelta(days=3)
        vervallen = verval - datetime.timedelta(days=1)

        regel1 = BestellingRegel(
                    korte_beschrijving='webwinkel 1',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel1.save()

        keuze1 = WebwinkelKeuze(
                    wanneer=vervallen,
                    status=KEUZE_STATUS_RESERVERING_MANDJE,
                    bestelling=regel1,
                    product=self.product,
                    aantal=1)
        keuze1.save()

        regel2 = BestellingRegel(
                    korte_beschrijving='webwinkel 2',
                    bedrag_euro=Decimal(5.0),
                    code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel2.save()

        keuze2 = WebwinkelKeuze(
                    wanneer=vervallen,
                    status=KEUZE_STATUS_RESERVERING_MANDJE,
                    bestelling=regel2,
                    product=self.product,
                    aantal=1)
        keuze2.save()

        self.mandje.regels.add(regel1)
        self.mandje.regels.add(regel2)

        mandje_pks = plugin.mandje_opschonen(verval)
        self.assertEqual(len(mandje_pks), 1)
        self.assertEqual(mandje_pks, [self.mandje.pk])

        self.assertTrue('[INFO] Vervallen: BestellingRegel pk=' in stdout.getvalue())
        self.assertTrue('[INFO] BestellingRegel met pk=' in stdout.getvalue())
        self.assertTrue('wordt verwijderd' in stdout.getvalue())

        stdout = OutputWrapper(io.StringIO())
        plugin = VerzendkostenBestelPlugin()
        plugin.zet_stdout(stdout)

        verval = timezone.now() - datetime.timedelta(days=3)

        mandje_pks = plugin.mandje_opschonen(verval)
        self.assertEqual(mandje_pks, [])

    def test_reserveer(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = WebwinkelBestelPlugin()
        plugin.zet_stdout(stdout)

        keuze = WebwinkelKeuze(
                    wanneer=timezone.now(),
                    status=KEUZE_STATUS_RESERVERING_MANDJE,
                    bestelling=None,
                    product=self.product,
                    aantal=1)
        keuze.save()

        regel = plugin.reserveer(keuze, 'Mandje test')
        self.assertEqual(regel.korte_beschrijving, '1 x product')
        self.assertEqual(regel.btw_percentage, '21')
        self.assertEqual(round(regel.btw_euro, 2), round(Decimal(1.74), 2))
        self.assertEqual(round(regel.bedrag_euro, 2), round(Decimal(10.00), 2))

        keuze.refresh_from_db()
        self.assertEqual(keuze.bestelling, regel)
        # self.assertEqual(keuze.status, KEUZE_STATUS_RESERVERING_MANDJE)       # wordt niet aangepast

        # extra coverage
        self.product.onbeperkte_voorraad = True
        self.product.save(update_fields=['onbeperkte_voorraad'])
        with override_settings(WEBWINKEL_BTW_PERCENTAGE=21.1):
            regel = plugin.reserveer(keuze, 'Mandje test')

    def test_annuleer(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = WebwinkelBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='webwinkel',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel.save()

        # keuze bestaat niet
        plugin.annuleer(regel)
        self.assertTrue("[ERROR] Kan WebwinkelKeuze voor regel met pk=" in stdout.getvalue())

        stdout = OutputWrapper(io.StringIO())       # weer leeg
        plugin.zet_stdout(stdout)

        keuze = WebwinkelKeuze(
                    wanneer=timezone.now(),
                    status=KEUZE_STATUS_RESERVERING_MANDJE,
                    bestelling=regel,
                    product=self.product,
                    aantal=1)
        keuze.save()

        n = self.product.aantal_op_voorraad

        plugin.annuleer(regel)

        self.product.refresh_from_db()
        self.assertEqual(self.product.aantal_op_voorraad, n+1)

        # extra coverage
        self.product.onbeperkte_voorraad = True
        self.product.save(update_fields=['onbeperkte_voorraad'])

        keuze = WebwinkelKeuze(
                    wanneer=timezone.now(),
                    status=KEUZE_STATUS_RESERVERING_MANDJE,
                    bestelling=regel,
                    product=self.product,
                    aantal=1)
        keuze.save()

        plugin.annuleer(regel)

    def test_is_besteld(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = WebwinkelBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='webwinkel',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel.save()

        # zonder keuze
        plugin.is_besteld(regel)

        keuze = WebwinkelKeuze(
                    wanneer=timezone.now(),
                    status=KEUZE_STATUS_RESERVERING_MANDJE,
                    bestelling=regel,
                    product=self.product,
                    aantal=1)
        keuze.save()

        plugin.is_besteld(regel)

        keuze.refresh_from_db()
        self.assertEqual(keuze.status, KEUZE_STATUS_BESTELD)
        self.assertTrue("] Reservering is omgezet in een bestelling\n" in keuze.log)

        # coverage
        stdout = OutputWrapper(io.StringIO())
        plugin = VerzendkostenBestelPlugin()
        plugin.zet_stdout(stdout)
        plugin.is_besteld(regel)

    def test_is_betaald(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = WebwinkelBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='webwinkel',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel.save()

        bedrag_ontvangen = Decimal(10.22)

        plugin.is_betaald(regel, bedrag_ontvangen)
        self.assertTrue("[ERROR] Kan WebwinkelKeuze voor regel met pk=" in stdout.getvalue())

        keuze = WebwinkelKeuze(
                    wanneer=timezone.now(),
                    status=KEUZE_STATUS_RESERVERING_MANDJE,
                    bestelling=regel,
                    product=self.product,
                    aantal=1)
        keuze.save()

        plugin.is_betaald(regel, bedrag_ontvangen)

        keuze.refresh_from_db()
        self.assertEqual(keuze.status, KEUZE_STATUS_BACKOFFICE)
        self.assertTrue("] Betaling is ontvangen" in keuze.log)

        # coverage
        stdout = OutputWrapper(io.StringIO())
        plugin = VerzendkostenBestelPlugin()
        plugin.zet_stdout(stdout)
        plugin.is_betaald(regel, bedrag_ontvangen)

    def test_get_verkoper_ver_nr(self):
        plugin = WebwinkelBestelPlugin()
        stdout = OutputWrapper(io.StringIO())
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='webwinkel',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel.save()

        ver_nr = plugin.get_verkoper_ver_nr(regel)
        self.assertEqual(ver_nr, settings.WEBWINKEL_VERKOPER_VER_NR)

        plugin = VerzendkostenBestelPlugin()
        stdout = OutputWrapper(io.StringIO())
        plugin.zet_stdout(stdout)

        ver_nr = plugin.get_verkoper_ver_nr(regel)
        self.assertEqual(ver_nr, settings.WEBWINKEL_VERKOPER_VER_NR)

    def test_verzendkosten(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = VerzendkostenBestelPlugin()
        plugin.zet_stdout(stdout)

        # leeg mandje
        kosten, btw_perc, btw_euro = plugin.bereken_verzendkosten(self.mandje)
        self.assertEqual(kosten, 0)

        regel = BestellingRegel(
                    korte_beschrijving='webwinkel 2',
                    bedrag_euro=Decimal(5.0),
                    code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel.save()

        keuze2 = WebwinkelKeuze(
                    wanneer=timezone.now(),
                    status=KEUZE_STATUS_RESERVERING_MANDJE,
                    bestelling=regel,
                    product=self.product,
                    aantal=1)
        keuze2.save()

        # pakketpost
        self.mandje.regels.add(regel)
        kosten, btw_perc, btw_euro = plugin.bereken_verzendkosten(self.mandje)
        self.assertEqual(kosten, Decimal(settings.WEBWINKEL_PAKKET_10KG_VERZENDKOSTEN_EURO))

        # briefpost
        self.product.type_verzendkosten = VERZENDKOSTEN_BRIEFPOST
        self.product.save(update_fields=['type_verzendkosten'])
        kosten, btw_perc, btw_euro = plugin.bereken_verzendkosten(self.mandje)
        self.assertEqual(kosten, Decimal(settings.WEBWINKEL_PAKKET_2KG_VERZENDKOSTEN_EURO))


# end of file
