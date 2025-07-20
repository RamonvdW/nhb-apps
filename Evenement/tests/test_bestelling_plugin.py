# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from django.core.management.base import OutputWrapper
from Bestelling.definities import BESTELLING_REGEL_CODE_EVENEMENT
from Bestelling.models import BestellingRegel, BestellingMandje
from Evenement.plugin_bestelling import EvenementBestelPlugin
from Evenement.definities import (EVENEMENT_STATUS_GEACCEPTEERD,
                                  EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                  EVENEMENT_INSCHRIJVING_STATUS_BESTELD,
                                  EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF,
                                  EVENEMENT_INSCHRIJVING_STATUS_AFGEMELD,
                                  EVENEMENT_AFMELDING_STATUS_AFGEMELD,
                                  EVENEMENT_AFMELDING_STATUS_GEANNULEERD)
from Evenement.models import Evenement, EvenementInschrijving, EvenementAfgemeld
from Geo.models import Regio
from Locatie.models import EvenementLocatie
from Mailer.models import MailQueue
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from decimal import Decimal
import datetime
import io


class TestEvenementBestellingPlugin(E2EHelpers, TestCase):

    """ tests voor de Evenement applicatie, module Bestelling Plugin """

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

        locatie = EvenementLocatie(
                    naam='Arnhemhal',
                    vereniging=ver,
                    adres='Papendallaan 9\n6816VD Arnhem',
                    plaats='Arnhem')
        locatie.save()

        now_date = timezone.now().date()
        soon_date = now_date + datetime.timedelta(days=60)

        evenement1 = Evenement(
                        titel='Test evenement 1',
                        status=EVENEMENT_STATUS_GEACCEPTEERD,
                        organiserende_vereniging=ver,
                        datum=soon_date,
                        aanvang='09:30',
                        inschrijven_tot=1,
                        locatie=locatie,
                        contact_naam='Dhr. Organisator',
                        contact_email='info@test.not',
                        contact_website='www.test.not',
                        contact_telefoon='023-1234567',
                        beschrijving='Test beschrijving',
                        prijs_euro_normaal="15",
                        prijs_euro_onder18="15")
        evenement1.save()
        evenement1.refresh_from_db()        # geeft opgeslagen datum/tijd formaat
        self.evenement1 = evenement1

        evenement2 = Evenement(
                        titel='Test evenement 2',
                        status=EVENEMENT_STATUS_GEACCEPTEERD,
                        organiserende_vereniging=ver,
                        datum=soon_date,
                        aanvang='12:30',
                        inschrijven_tot=1,
                        locatie=locatie,
                        contact_naam='Dhr. Organisator',
                        contact_email='info@test.not',
                        contact_website='www.test.not',
                        contact_telefoon='023-1234567',
                        beschrijving='Test beschrijving',
                        prijs_euro_normaal="15",
                        prijs_euro_onder18="15")
        evenement2.save()
        evenement2.refresh_from_db()        # geeft opgeslagen datum/tijd formaat
        self.evenement2 = evenement2

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
        plugin = EvenementBestelPlugin()
        plugin.zet_stdout(stdout)

        verval = timezone.now() - datetime.timedelta(days=3)

        regel1 = BestellingRegel(
                    korte_beschrijving='evenement 1',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_EVENEMENT)
        regel1.save()

        inschrijving1 = EvenementInschrijving(
                            wanneer=verval - datetime.timedelta(days=1),
                            nummer=1,
                            status=EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                            evenement=self.evenement1,
                            sporter=self.sporter_100000,
                            bestelling=regel1,
                            koper=self.account_100000)
        inschrijving1.save()

        regel2 = BestellingRegel(
                    korte_beschrijving='evenement 2',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_EVENEMENT)
        regel2.save()

        inschrijving2 = EvenementInschrijving(
                            wanneer=verval - datetime.timedelta(days=1),
                            nummer=2,
                            status=EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                            evenement=self.evenement2,
                            sporter=self.sporter_100000,
                            bestelling=regel2,
                            koper=self.account_100000)
        inschrijving2.save()

        self.mandje.regels.add(regel1)
        self.mandje.regels.add(regel2)

        mandje_pks = plugin.mandje_opschonen(verval)
        self.assertEqual(len(mandje_pks), 1)
        self.assertEqual(mandje_pks, [self.mandje.pk])

        self.assertTrue('[INFO] Vervallen: BestellingRegel pk=' in stdout.getvalue())
        self.assertTrue('[INFO] BestellingRegel met pk=' in stdout.getvalue())
        self.assertTrue('wordt verwijderd' in stdout.getvalue())

    def test_reserveer(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = EvenementBestelPlugin()
        plugin.zet_stdout(stdout)

        inschrijving = EvenementInschrijving(
                            wanneer=timezone.now(),
                            nummer=1,
                            status='??',
                            evenement=self.evenement1,
                            sporter=self.sporter_100000,
                            bestelling=None,
                            koper=self.account_100000)
        inschrijving.save()

        regel = plugin.reserveer(inschrijving.pk, 'Mandje test')
        self.assertEqual(regel.korte_beschrijving, 'Evenement "Test evenement 1"||voor [100000] Nor Maal')

        inschrijving.refresh_from_db()
        self.assertEqual(inschrijving.bestelling, regel)
        self.assertEqual(inschrijving.status, EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE)

    def test_afmelden(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = EvenementBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='evenement',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_EVENEMENT)
        regel.save()

        inschrijving = EvenementInschrijving(
                            wanneer=timezone.now(),
                            nummer=1,
                            status=EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                            evenement=self.evenement1,
                            sporter=self.sporter_100000,
                            bestelling=regel,
                            koper=self.account_100000)
        inschrijving.save()
        inschrijving.refresh_from_db()

        plugin.afmelden(inschrijving.pk)

        inschrijving.refresh_from_db()
        self.assertEqual(inschrijving.status, EVENEMENT_INSCHRIJVING_STATUS_AFGEMELD)

        afmelding = EvenementAfgemeld.objects.filter(nummer=inschrijving.nummer).first()

        self.assertEqual(afmelding.wanneer_inschrijving, inschrijving.wanneer)
        self.assertEqual(afmelding.evenement, inschrijving.evenement)
        self.assertEqual(afmelding.sporter, inschrijving.sporter)
        self.assertEqual(afmelding.koper, inschrijving.koper)
        self.assertEqual(afmelding.bedrag_ontvangen, inschrijving.bedrag_ontvangen)

    def test_annuleer_mandje(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = EvenementBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='evenement',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_EVENEMENT)
        regel.save()

        # inschrijving bestaat niet
        plugin.annuleer(regel)
        self.assertTrue("[ERROR] Kan EvenementInschrijving voor regel met pk=" in stdout.getvalue())

        inschrijving = EvenementInschrijving(
                            wanneer=timezone.now(),
                            nummer=1,
                            status=EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                            evenement=self.evenement1,
                            sporter=self.sporter_100000,
                            bestelling=regel,
                            koper=self.account_100000)
        inschrijving.save()
        inschrijving.refresh_from_db()

        self.assertEqual(EvenementAfgemeld.objects.count(), 0)

        plugin.annuleer(regel)

        # inschrijving is verwijderd
        self.assertEqual(EvenementInschrijving.objects.filter(pk=inschrijving.pk).count(), 0)
        self.assertEqual(EvenementAfgemeld.objects.count(), 0)

    def test_annuleer_besteld(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = EvenementBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='evenement',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_EVENEMENT)
        regel.save()

        inschrijving = EvenementInschrijving(
                            wanneer=timezone.now(),
                            nummer=1,
                            status=EVENEMENT_INSCHRIJVING_STATUS_BESTELD,
                            evenement=self.evenement1,
                            sporter=self.sporter_100000,
                            bestelling=regel,
                            koper=self.account_100000)
        inschrijving.save()
        inschrijving.refresh_from_db()

        self.assertEqual(EvenementAfgemeld.objects.count(), 0)

        plugin.annuleer(regel)

        # inschrijving is verwijderd
        self.assertEqual(EvenementInschrijving.objects.filter(pk=inschrijving.pk).count(), 0)
        self.assertEqual(EvenementAfgemeld.objects.count(), 1)

        afmelding = EvenementAfgemeld.objects.first()

        self.assertEqual(afmelding.wanneer_inschrijving, inschrijving.wanneer)
        self.assertEqual(afmelding.nummer, inschrijving.nummer)
        self.assertEqual(afmelding.evenement, inschrijving.evenement)
        self.assertEqual(afmelding.sporter, inschrijving.sporter)
        self.assertEqual(afmelding.koper, inschrijving.koper)
        self.assertEqual(afmelding.bedrag_ontvangen, inschrijving.bedrag_ontvangen)
        self.assertEqual(afmelding.status, EVENEMENT_AFMELDING_STATUS_GEANNULEERD)

    def test_annuleer_definitief(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = EvenementBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='evenement',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_EVENEMENT)
        regel.save()

        inschrijving = EvenementInschrijving(
                            wanneer=timezone.now(),
                            nummer=1,
                            status=EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF,
                            evenement=self.evenement1,
                            sporter=self.sporter_100000,
                            bestelling=regel,
                            koper=self.account_100000)
        inschrijving.save()
        inschrijving.refresh_from_db()

        self.assertEqual(EvenementAfgemeld.objects.count(), 0)

        plugin.annuleer(regel)

        # inschrijving is verwijderd
        self.assertEqual(EvenementInschrijving.objects.filter(pk=inschrijving.pk).count(), 0)

        self.assertEqual(EvenementAfgemeld.objects.count(), 1)
        afmelding = EvenementAfgemeld.objects.first()

        self.assertEqual(afmelding.wanneer_inschrijving, inschrijving.wanneer)
        self.assertEqual(afmelding.nummer, inschrijving.nummer)
        self.assertEqual(afmelding.evenement, inschrijving.evenement)
        self.assertEqual(afmelding.sporter, inschrijving.sporter)
        self.assertEqual(afmelding.koper, inschrijving.koper)
        self.assertEqual(afmelding.bedrag_ontvangen, inschrijving.bedrag_ontvangen)
        self.assertEqual(afmelding.status, EVENEMENT_AFMELDING_STATUS_AFGEMELD)

    def test_is_besteld(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = EvenementBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='evenement',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_EVENEMENT)
        regel.save()

        plugin.is_besteld(regel)
        self.assertTrue("[ERROR] Kan EvenementInschrijving voor regel met pk=" in stdout.getvalue())

        inschrijving = EvenementInschrijving(
                            wanneer=timezone.now(),
                            nummer=1,
                            status=EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                            evenement=self.evenement1,
                            sporter=self.sporter_100000,
                            bestelling=regel,
                            koper=self.account_100000)
        inschrijving.save()

        plugin.is_besteld(regel)

        inschrijving.refresh_from_db()
        self.assertEqual(inschrijving.status, EVENEMENT_INSCHRIJVING_STATUS_BESTELD)
        self.assertTrue("Omgezet in een bestelling" in inschrijving.log)

    def test_is_betaald_zelf(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = EvenementBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='evenement',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_EVENEMENT)
        regel.save()

        bedrag_ontvangen = Decimal(10.22)

        plugin.is_betaald(regel, bedrag_ontvangen)
        self.assertTrue("[ERROR] Kan EvenementInschrijving voor regel met pk=" in stdout.getvalue())

        inschrijving = EvenementInschrijving(
                            wanneer=timezone.now(),
                            nummer=1,
                            status=EVENEMENT_INSCHRIJVING_STATUS_BESTELD,
                            evenement=self.evenement1,
                            sporter=self.sporter_100000,
                            bestelling=regel,
                            koper=self.account_100000)
        inschrijving.save()

        stdout = OutputWrapper(io.StringIO())       # weer leeg
        plugin.zet_stdout(stdout)

        plugin.is_betaald(regel, bedrag_ontvangen)

        inschrijving.refresh_from_db()
        self.assertEqual(inschrijving.status, EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF)
        self.assertEqual(round(inschrijving.bedrag_ontvangen, 2), round(bedrag_ontvangen, 2))
        self.assertTrue("Betaling ontvangen" in inschrijving.log)
        self.assertFalse("] Informatieve e-mail is gestuurd naar sporter" in inschrijving.log)

        # betaling was voor "zelf", dus er wordt geen extra mail gestuurd
        self.assertEqual(MailQueue.objects.count(), 0)

    def test_is_betaald_koper(self):
        # koop evenement deelname voor iemand anders
        stdout = OutputWrapper(io.StringIO())
        plugin = EvenementBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='evenement',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_EVENEMENT)
        regel.save()

        inschrijving = EvenementInschrijving(
                            wanneer=timezone.now(),
                            nummer=1,
                            status=EVENEMENT_INSCHRIJVING_STATUS_BESTELD,
                            evenement=self.evenement1,
                            sporter=self.sporter_100001,        # niet gelijk aan koper
                            bestelling=regel,
                            koper=self.account_100000)
        inschrijving.save()

        stdout = OutputWrapper(io.StringIO())       # weer leeg
        plugin.zet_stdout(stdout)

        bedrag_ontvangen = Decimal(10.22)
        plugin.is_betaald(regel, bedrag_ontvangen)

        inschrijving.refresh_from_db()
        self.assertEqual(inschrijving.status, EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF)
        self.assertEqual(round(inschrijving.bedrag_ontvangen, 2), round(bedrag_ontvangen, 2))
        self.assertTrue("] Betaling ontvangen" in inschrijving.log)
        self.assertTrue("] Informatieve e-mail is gestuurd naar sporter" in inschrijving.log)

        self.assertEqual(MailQueue.objects.count(), 1)
        mail = MailQueue.objects.first()
        self.assert_consistent_email_html_text(mail)
        self.assert_email_html_ok(mail, 'email_evenement/info-inschrijving-evenement.dtl')

        # nog een keer, nu heeft de sporter geen valide e-mail
        self.sporter_100001.email = ''
        self.sporter_100001.save(update_fields=['email'])
        MailQueue.objects.all().delete()
        plugin.is_betaald(regel, bedrag_ontvangen)
        self.assertEqual(MailQueue.objects.count(), 0)

        # nog een keer, nu heeft de sporter een account
        account_100001 = self.e2e_create_account('100001', 'sporter1000001@test.not', 'Sporter')
        self.sporter_100001.account = account_100001
        self.sporter_100001.save(update_fields=['account'])
        plugin.is_betaald(regel, bedrag_ontvangen)
        self.assertEqual(MailQueue.objects.count(), 1)

        mail = MailQueue.objects.first()
        self.assert_consistent_email_html_text(mail)
        self.assert_email_html_ok(mail, 'email_evenement/info-inschrijving-evenement.dtl')
        # print(mail.mail_text)

    def test_get_verkoper_ver_nr(self):
        plugin = EvenementBestelPlugin()
        stdout = OutputWrapper(io.StringIO())
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='evenement',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_EVENEMENT)
        regel.save()

        ver_nr = plugin.get_verkoper_ver_nr(regel)
        self.assertEqual(ver_nr, -1)
        self.assertTrue('[ERROR] Kan EvenementInschrijving voor regel met pk=' in stdout.getvalue())

        inschrijving = EvenementInschrijving(
                            wanneer=timezone.now(),
                            nummer=1,
                            status=EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF,
                            evenement=self.evenement1,
                            sporter=self.sporter_100000,
                            bestelling=regel,
                            koper=self.account_100000)
        inschrijving.save()

        ver_nr = plugin.get_verkoper_ver_nr(regel)
        self.assertEqual(ver_nr, self.ver.ver_nr)


# end of file
