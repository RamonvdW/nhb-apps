# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone
from Bestelling.definities import BESTELLING_REGEL_CODE_WEBWINKEL
from Bestelling.models import BestellingRegel, BestellingMandje
from Geo.models import Regio
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers, OutputBuffer
from Vereniging.models import Vereniging
from Webwinkel.definities import (VERZENDKOSTEN_PAKKETPOST, VERZENDKOSTEN_BRIEFPOST,
                                  KEUZE_STATUS_RESERVERING_MANDJE, KEUZE_STATUS_BESTELD, KEUZE_STATUS_BACKOFFICE)
from Webwinkel.models import WebwinkelKeuze, WebwinkelProduct
from Bestelling.plugins.plugin_bestelling_verzendkosten import VerzendkostenBestelPlugin
from decimal import Decimal
import datetime


class TestBestellingVerzendkosten(E2EHelpers, TestCase):

    """ tests voor de Bestelling applicatie, module Verzendkosten plugin """

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

    def test_verzendkosten(self):
        stdout = OutputBuffer()
        plugin = VerzendkostenBestelPlugin()
        plugin.zet_stdout(stdout)

        # leeg mandje
        kosten, btw_perc, btw_euro = plugin.bereken_verzendkosten(self.mandje)
        self.assertEqual(kosten, 0)

        # TODO: prestatiespeld

        regel = BestellingRegel(
                    korte_beschrijving='webwinkel 2',
                    bedrag_euro=Decimal(5.0),
                    code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel.save()

        keuze2 = WebwinkelKeuze(
                    wanneer=timezone.now(),
                    status=KEUZE_STATUS_RESERVERING_MANDJE,
                    bestelling_regel=regel,
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

        # coverage
        plugin.is_besteld(regel)

        bedrag_ontvangen = Decimal(10.22)
        plugin.is_betaald(regel, bedrag_ontvangen)

        verval = timezone.now() - datetime.timedelta(days=3)
        mandje_pks = plugin.mandje_opschonen(verval)
        self.assertEqual(mandje_pks, [])

        ver_nr = plugin.get_verkoper_ver_nr(regel)
        self.assertEqual(ver_nr, settings.WEBWINKEL_VERKOPER_VER_NR)

# end of file
