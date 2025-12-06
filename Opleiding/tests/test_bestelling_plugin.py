# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from django.core.management.base import OutputWrapper
from Bestelling.definities import BESTELLING_REGEL_CODE_OPLEIDING
from Bestelling.models import BestellingRegel, BestellingMandje
from Geo.models import Regio
from Opleiding.definities import (OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                  OPLEIDING_INSCHRIJVING_STATUS_AFGEMELD,
                                  OPLEIDING_INSCHRIJVING_STATUS_BESTELD,
                                  OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF,
                                  OPLEIDING_AFMELDING_STATUS_GEANNULEERD,
                                  OPLEIDING_AFMELDING_STATUS_AFGEMELD)
from Opleiding.models import Opleiding, OpleidingInschrijving, OpleidingAfgemeld
from Opleiding.plugin_bestelling import OpleidingBestelPlugin
from Sporter.models import Sporter
from Taken.models import Taak
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from decimal import Decimal
import datetime
import io


class TestOpleidingBestellingPlugin(E2EHelpers, TestCase):

    """ tests voor de Opleiding applicatie, module Bestelling Plugin """

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

        opleiding = Opleiding(
                        titel='Test opleiding',
                        kosten_euro=Decimal(111.0))
        opleiding.save()
        self.opleiding = opleiding

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
        plugin = OpleidingBestelPlugin()
        plugin.zet_stdout(stdout)

        verval = timezone.now() - datetime.timedelta(days=3)

        regel1 = BestellingRegel(
                    korte_beschrijving='opleiding 1',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_OPLEIDING)
        regel1.save()

        inschrijving1 = OpleidingInschrijving(
                            status=OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                            opleiding=self.opleiding,
                            sporter=self.sporter_100001,
                            nummer=1,
                            koper=self.account_100000,
                            bestelling=regel1)
        inschrijving1.save()

        regel2 = BestellingRegel(
                    korte_beschrijving='opleiding 2',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_OPLEIDING)
        regel2.save()

        inschrijving2 = OpleidingInschrijving(
                            status=OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                            opleiding=self.opleiding,
                            sporter=self.sporter_100001,
                            nummer=2,
                            koper=self.account_100000,
                            bestelling=regel2)
        inschrijving2.save()

        self.mandje.regels.add(regel1)
        self.mandje.regels.add(regel2)

        inschrijving1.wanneer_aangemeld = verval - datetime.timedelta(days=1)
        inschrijving1.save(update_fields=['wanneer_aangemeld'])

        inschrijving2.wanneer_aangemeld = verval - datetime.timedelta(days=1)
        inschrijving2.save(update_fields=['wanneer_aangemeld'])

        mandje_pks = plugin.mandje_opschonen(verval)
        self.assertEqual(len(mandje_pks), 1)
        self.assertEqual(mandje_pks, [self.mandje.pk])

        self.assertTrue('[INFO] Vervallen: BestellingRegel pk=' in stdout.getvalue())
        self.assertTrue('[INFO] BestellingRegel met pk=' in stdout.getvalue())
        self.assertTrue('wordt verwijderd' in stdout.getvalue())

    def test_reserveer(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = OpleidingBestelPlugin()
        plugin.zet_stdout(stdout)

        inschrijving = OpleidingInschrijving(
                            nummer=1,
                            status='??',
                            opleiding=self.opleiding,
                            sporter=self.sporter_100000,
                            bestelling=None,
                            koper=self.account_100000)
        inschrijving.save()

        regel = plugin.reserveer(inschrijving.pk, 'Mandje test')
        self.assertEqual(regel.korte_beschrijving, 'Opleiding "Test opleiding"||voor [100000] Nor Maal')

        inschrijving.refresh_from_db()
        self.assertEqual(inschrijving.bestelling, regel)
        self.assertEqual(inschrijving.status, OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE)

    def test_afmelden(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = OpleidingBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='opleiding',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_OPLEIDING)
        regel.save()

        inschrijving = OpleidingInschrijving(
                            nummer=1,
                            status='??',
                            opleiding=self.opleiding,
                            sporter=self.sporter_100000,
                            bestelling=regel,
                            koper=self.account_100000,
                            bedrag_ontvangen=Decimal(42.0))
        inschrijving.save()
        inschrijving.refresh_from_db()
        inschrijving.wanneer_aangemeld -= datetime.timedelta(days=1)
        inschrijving.save(update_fields=['wanneer_aangemeld'])
        inschrijving.refresh_from_db()

        plugin.afmelden(inschrijving.pk)

        count = OpleidingInschrijving.objects.filter(pk=inschrijving.pk).count()
        self.assertEqual(count, 0)

        afmelding = OpleidingAfgemeld.objects.filter(nummer=inschrijving.nummer).first()

        self.assertEqual(afmelding.wanneer_aangemeld, inschrijving.wanneer_aangemeld)
        self.assertEqual(afmelding.opleiding, inschrijving.opleiding)
        self.assertEqual(afmelding.sporter, inschrijving.sporter)
        self.assertEqual(afmelding.koper, inschrijving.koper)
        self.assertEqual(afmelding.bedrag_ontvangen, inschrijving.bedrag_ontvangen)

        self.assertTrue(str(afmelding) != '')
        self.assertTrue(afmelding.korte_beschrijving() != '')

    def test_annuleer_mandje(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = OpleidingBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='opleiding',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_OPLEIDING)
        regel.save()

        # inschrijving bestaat niet
        plugin.annuleer(regel)
        self.assertTrue("[ERROR] Kan OpleidingInschrijving voor regel met pk=" in stdout.getvalue())

        stdout = OutputWrapper(io.StringIO())       # weer leeg
        plugin.zet_stdout(stdout)

        inschrijving = OpleidingInschrijving(
                            nummer=1,
                            status=OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                            opleiding=self.opleiding,
                            sporter=self.sporter_100000,
                            bestelling=regel,
                            koper=self.account_100000)
        inschrijving.save()

        self.assertEqual(OpleidingAfgemeld.objects.count(), 0)

        plugin.annuleer(regel)

        # inschrijving is verwijderd
        self.assertEqual(OpleidingInschrijving.objects.filter(pk=inschrijving.pk).count(), 0)
        self.assertEqual(OpleidingAfgemeld.objects.count(), 0)

    def test_annuleer_besteld(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = OpleidingBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='opleiding',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_OPLEIDING)
        regel.save()

        inschrijving = OpleidingInschrijving(
                            nummer=1,
                            status=OPLEIDING_INSCHRIJVING_STATUS_BESTELD,
                            opleiding=self.opleiding,
                            sporter=self.sporter_100000,
                            bestelling=regel,
                            koper=self.account_100000)
        inschrijving.save()

        self.assertEqual(OpleidingAfgemeld.objects.count(), 0)

        plugin.annuleer(regel)

        # inschrijving is verwijderd
        self.assertEqual(OpleidingInschrijving.objects.filter(pk=inschrijving.pk).count(), 0)
        self.assertEqual(OpleidingAfgemeld.objects.count(), 1)

        afmelding = OpleidingAfgemeld.objects.first()

        self.assertEqual(afmelding.wanneer_aangemeld, inschrijving.wanneer_aangemeld)
        self.assertEqual(afmelding.nummer, inschrijving.nummer)
        self.assertEqual(afmelding.opleiding, inschrijving.opleiding)
        self.assertEqual(afmelding.sporter, inschrijving.sporter)
        self.assertEqual(afmelding.koper, inschrijving.koper)
        self.assertEqual(afmelding.bedrag_ontvangen, inschrijving.bedrag_ontvangen)
        self.assertEqual(afmelding.status, OPLEIDING_AFMELDING_STATUS_GEANNULEERD)

    def test_annuleer_definitief(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = OpleidingBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='opleiding',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_OPLEIDING)
        regel.save()

        inschrijving = OpleidingInschrijving(
                            nummer=1,
                            status=OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF,
                            opleiding=self.opleiding,
                            sporter=self.sporter_100000,
                            bestelling=regel,
                            koper=self.account_100000)
        inschrijving.save()

        self.assertEqual(OpleidingAfgemeld.objects.count(), 0)

        plugin.annuleer(regel)

        # inschrijving is verwijderd
        self.assertEqual(OpleidingInschrijving.objects.filter(pk=inschrijving.pk).count(), 0)
        self.assertEqual(OpleidingAfgemeld.objects.count(), 1)

        afmelding = OpleidingAfgemeld.objects.first()

        self.assertEqual(afmelding.wanneer_aangemeld, inschrijving.wanneer_aangemeld)
        self.assertEqual(afmelding.nummer, inschrijving.nummer)
        self.assertEqual(afmelding.opleiding, inschrijving.opleiding)
        self.assertEqual(afmelding.sporter, inschrijving.sporter)
        self.assertEqual(afmelding.koper, inschrijving.koper)
        self.assertEqual(afmelding.bedrag_ontvangen, inschrijving.bedrag_ontvangen)
        self.assertEqual(afmelding.status, OPLEIDING_AFMELDING_STATUS_AFGEMELD)

    def test_is_besteld(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = OpleidingBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='opleiding',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_OPLEIDING)
        regel.save()

        plugin.is_besteld(regel)
        self.assertTrue("[ERROR] Kan OpleidingInschrijving voor regel met pk=" in stdout.getvalue())

        inschrijving = OpleidingInschrijving(
                            nummer=1,
                            status=OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                            opleiding=self.opleiding,
                            sporter=self.sporter_100000,
                            bestelling=regel,
                            koper=self.account_100000)
        inschrijving.save()

        plugin.is_besteld(regel)

        inschrijving.refresh_from_db()
        self.assertEqual(inschrijving.status, OPLEIDING_INSCHRIJVING_STATUS_BESTELD)
        self.assertTrue("Omgezet in een bestelling" in inschrijving.log)

    def test_is_betaald(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = OpleidingBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='opleiding',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_OPLEIDING)
        regel.save()

        bedrag_ontvangen = Decimal(10.22)

        plugin.is_betaald(regel, bedrag_ontvangen)
        self.assertTrue("[ERROR] Kan OpleidingInschrijving voor regel met pk=" in stdout.getvalue())

        inschrijving = OpleidingInschrijving(
                            nummer=1,
                            status=OPLEIDING_INSCHRIJVING_STATUS_BESTELD,
                            opleiding=self.opleiding,
                            sporter=self.sporter_100000,
                            bestelling=regel,
                            koper=self.account_100000)
        inschrijving.save()

        self.assertEqual(Taak.objects.count(), 0)

        plugin.is_betaald(regel, bedrag_ontvangen)

        inschrijving.refresh_from_db()
        self.assertEqual(inschrijving.status, OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF)
        self.assertEqual(round(inschrijving.bedrag_ontvangen, 2), round(bedrag_ontvangen, 2))
        self.assertTrue("Betaling ontvangen" in inschrijving.log)

        self.assertEqual(Taak.objects.count(), 1)

        # nog een keer - er moet geen 2e taak komen
        plugin.is_betaald(regel, bedrag_ontvangen)
        self.assertEqual(Taak.objects.count(), 1)

    def test_get_verkoper_ver_nr(self):
        plugin = OpleidingBestelPlugin()
        stdout = OutputWrapper(io.StringIO())
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='opleiding',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_OPLEIDING)
        regel.save()

        ver_nr = plugin.get_verkoper_ver_nr(regel)
        self.assertEqual(ver_nr, settings.WEBWINKEL_VERKOPER_VER_NR)


# end of file
