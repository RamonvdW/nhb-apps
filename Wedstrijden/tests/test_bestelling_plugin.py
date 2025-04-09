# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from django.core.management.base import OutputWrapper
from BasisTypen.definities import ORGANISATIE_IFAA
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestelling.definities import BESTELLING_REGEL_CODE_WEDSTRIJD, BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING
from Bestelling.models import BestellingRegel, BestellingMandje
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import (WEDSTRIJD_STATUS_GEACCEPTEERD,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF)
from Wedstrijden.models import Wedstrijd, WedstrijdInschrijving, WedstrijdSessie
from Wedstrijden.plugin_bestelling import WedstrijdBestelPlugin, WedstrijdKortingBestelPlugin
from decimal import Decimal
import datetime
import io


class TestWedstrijdenBestellingPlugin(E2EHelpers, TestCase):

    """ tests voor de Wedstrijden applicatie, module Bestelling Plugin """

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

        locatie = WedstrijdLocatie(
                        naam='Test locatie',
                        plaats='Boogstad')
        locatie.save()

        date_next_month = timezone.now() + datetime.timedelta(days=31)

        wedstrijd = Wedstrijd(
                        titel='Test wedstrijd',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=date_next_month,
                        datum_einde=date_next_month,
                        organiserende_vereniging=ver,
                        locatie=locatie,
                        verkoopvoorwaarden_status_acceptatie=True,
                        prijs_euro_normaal=Decimal(10.0),
                        prijs_euro_onder18=Decimal(10.0))
        wedstrijd.save()
        self.wedstrijd = wedstrijd

        sessie = WedstrijdSessie(
                        datum=date_next_month,
                        tijd_begin='09:00',
                        tijd_einde='15:00',
                        max_sporters=10)
        sessie.save()
        self.sessie = sessie
        wedstrijd.sessies.add(sessie)

        self.account_100000 = self.e2e_create_account('100000', 'normaal@test.not', 'Tester 1')
        sporter = Sporter(
                        lid_nr=100000,
                        voornaam='Nor',
                        achternaam='Maal',
                        geboorte_datum='1988-08-08',
                        sinds_datum='2020-02-20',
                        account=self.account_100000,
                        email='sporter100000@khsn.not',
                        bij_vereniging=ver,
                        adres_code='1234XX')
        sporter.save()
        sporter.refresh_from_db()        # geeft opgeslagen datum/tijd formaat
        self.sporter_100000 = sporter

        boog_r = BoogType.objects.get(afkorting='R')
        boog_c = BoogType.objects.get(afkorting='C')

        sporterboog = SporterBoog(
                            sporter=sporter,
                            boogtype=boog_r,
                            voor_wedstrijd=True)
        sporterboog.save()
        self.sporterboog_r = sporterboog

        sporterboog = SporterBoog(
                            sporter=sporter,
                            boogtype=boog_c,
                            voor_wedstrijd=True)
        sporterboog.save()
        self.sporterboog_c = sporterboog

        self.account_100001 = self.e2e_create_account('100001', 'andere@test.not', 'Tester 2')
        sporter = Sporter(
                        lid_nr=100001,
                        voornaam='And',
                        achternaam='Ere',
                        geboorte_datum='1988-08-09',
                        sinds_datum='2020-02-21',
                        account=self.account_100001,
                        email='sporter100001@khsn.not',
                        bij_vereniging=ver,
                        adres_code='1234YY')
        sporter.save()
        sporter.refresh_from_db()        # geeft opgeslagen datum/tijd formaat
        self.sporter_100001 = sporter

        self.wedstrijdklasse_r = KalenderWedstrijdklasse.objects.get(volgorde=110)    # R50+ gemengd
        self.wedstrijdklasse_c = KalenderWedstrijdklasse.objects.get(volgorde=210)    # C50+ gemengd

        self.mandje = BestellingMandje(
                            account=self.account_100000)
        self.mandje.save()

    def test_opschonen(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = WedstrijdBestelPlugin()
        plugin.zet_stdout(stdout)

        verval = timezone.now() - datetime.timedelta(days=3)

        regel1 = BestellingRegel(
                    korte_beschrijving='wedstrijd 1',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_WEDSTRIJD)
        regel1.save()

        inschrijving1 = WedstrijdInschrijving(
                                wanneer=timezone.now(),
                                status=WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                wedstrijd=self.wedstrijd,
                                sessie=self.sessie,
                                sporterboog=self.sporterboog_r,
                                wedstrijdklasse=self.wedstrijdklasse_r,
                                bestelling=regel1,
                                koper=self.account_100000)
        inschrijving1.save()

        regel2 = BestellingRegel(
                    korte_beschrijving='wedstrijd 2',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_WEDSTRIJD)
        regel2.save()

        inschrijving2 = WedstrijdInschrijving(
                                wanneer=timezone.now(),
                                status=WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                wedstrijd=self.wedstrijd,
                                sessie=self.sessie,
                                sporterboog=self.sporterboog_c,
                                wedstrijdklasse=self.wedstrijdklasse_c,
                                bestelling=regel2,
                                koper=self.account_100000)
        inschrijving2.save()

        self.sessie.aantal_inschrijvingen += 2
        self.sessie.save(update_fields=['aantal_inschrijvingen'])

        self.mandje.regels.add(regel1)
        self.mandje.regels.add(regel2)

        inschrijving1.wanneer = verval - datetime.timedelta(days=1)
        inschrijving1.save(update_fields=['wanneer'])

        inschrijving2.wanneer = verval - datetime.timedelta(days=1)
        inschrijving2.save(update_fields=['wanneer'])

        mandje_pks = plugin.mandje_opschonen(verval)
        self.assertEqual(len(mandje_pks), 1)
        self.assertEqual(mandje_pks, [self.mandje.pk])

        self.assertTrue('[INFO] Vervallen: BestellingRegel pk=' in stdout.getvalue())
        self.assertTrue('[INFO] BestellingRegel met pk=' in stdout.getvalue())
        self.assertTrue('wordt verwijderd' in stdout.getvalue())

        stdout = OutputWrapper(io.StringIO())
        plugin = WedstrijdKortingBestelPlugin()
        plugin.zet_stdout(stdout)

        # coverage (lege implementatie)
        mandje_pks = plugin.mandje_opschonen(verval)
        self.assertEqual(mandje_pks, [])

    def test_reserveer(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = WedstrijdBestelPlugin()
        plugin.zet_stdout(stdout)

        inschrijving = WedstrijdInschrijving(
                                wanneer=timezone.now(),
                                status=WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                wedstrijd=self.wedstrijd,
                                sessie=self.sessie,
                                sporterboog=self.sporterboog_r,
                                wedstrijdklasse=self.wedstrijdklasse_r,
                                bestelling=None,
                                koper=self.account_100000)
        inschrijving.save()

        regel = plugin.reserveer(inschrijving, 'Mandje test')
        self.assertEqual(regel.korte_beschrijving,
                         'Wedstrijd "Test wedstrijd"||deelname door [100000] Nor Maal||met boog Recurve')

        inschrijving.refresh_from_db()
        self.assertEqual(inschrijving.bestelling, regel)
        self.assertEqual(inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE)
        self.assertTrue("] Toegevoegd aan het mandje van Mandje test" in inschrijving.log)

    def test_afmelden(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = WedstrijdBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='wedstrijd',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_WEDSTRIJD)
        regel.save()

        inschrijving = WedstrijdInschrijving(
                                wanneer=timezone.now(),
                                status=WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD,
                                wedstrijd=self.wedstrijd,
                                sessie=self.sessie,
                                sporterboog=self.sporterboog_r,
                                wedstrijdklasse=self.wedstrijdklasse_r,
                                bestelling=regel,
                                koper=self.account_100000,
                                ontvangen_euro=Decimal(12.34))
        inschrijving.save()

        self.sessie.aantal_inschrijvingen = 1
        self.sessie.save(update_fields=['aantal_inschrijvingen'])

        plugin.afmelden(inschrijving)

        inschrijving.refresh_from_db()
        self.assertEqual(inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD)
        self.assertTrue('] Afgemeld voor de wedstrijd' in inschrijving.log)

        self.sessie.refresh_from_db()
        self.assertEqual(self.sessie.aantal_inschrijvingen, 0)

        # coverage: al afgemeld
        plugin.afmelden(inschrijving)

        self.sessie.refresh_from_db()
        self.assertEqual(self.sessie.aantal_inschrijvingen, 0)

    def test_annuleer(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = WedstrijdBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='opleiding',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_WEDSTRIJD)
        regel.save()

        # inschrijving bestaat niet
        plugin.annuleer(regel)
        self.assertTrue("[ERROR] Kan WedstrijdInschrijving voor regel met pk=" in stdout.getvalue())

        stdout = OutputWrapper(io.StringIO())       # weer leeg
        plugin.zet_stdout(stdout)

        inschrijving = WedstrijdInschrijving(
                                wanneer=timezone.now(),
                                status=WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD,
                                wedstrijd=self.wedstrijd,
                                sessie=self.sessie,
                                sporterboog=self.sporterboog_r,
                                wedstrijdklasse=self.wedstrijdklasse_r,
                                bestelling=regel,
                                koper=self.account_100000,
                                ontvangen_euro=Decimal(12.34))
        inschrijving.save()

        self.sessie.aantal_inschrijvingen = 1
        self.sessie.save(update_fields=['aantal_inschrijvingen'])

        plugin.annuleer(regel)

        # inschrijving is verwijderd
        self.assertEqual(WedstrijdInschrijving.objects.filter(pk=inschrijving.pk).count(), 0)

        # kortingen plugin
        stdout = OutputWrapper(io.StringIO())
        plugin = WedstrijdKortingBestelPlugin()
        plugin.zet_stdout(stdout)

        plugin.annuleer(regel)      # dummy implementatie

    def test_is_besteld(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = WedstrijdBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='wedstrijd',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_WEDSTRIJD)
        regel.save()

        # niet te vinden
        plugin.is_besteld(regel)
        self.assertTrue("[ERROR] Kan WedstrijdInschrijving voor regel met pk=" in stdout.getvalue())

        inschrijving = WedstrijdInschrijving(
                                wanneer=timezone.now(),
                                status=WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD,
                                wedstrijd=self.wedstrijd,
                                sessie=self.sessie,
                                sporterboog=self.sporterboog_r,
                                wedstrijdklasse=self.wedstrijdklasse_r,
                                bestelling=regel,
                                koper=self.account_100000,
                                ontvangen_euro=Decimal(12.34))
        inschrijving.save()

        plugin.is_besteld(regel)

        inschrijving.refresh_from_db()
        self.assertEqual(inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD)
        self.assertTrue("Omgezet in een bestelling" in inschrijving.log)

        # kortingen plugin
        plugin = WedstrijdKortingBestelPlugin()
        plugin.is_besteld(regel)      # dummy implementatie

    def test_is_betaald_zelf(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = WedstrijdBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='wedstrijd',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_WEDSTRIJD)
        regel.save()

        bedrag_ontvangen = Decimal(10.22)

        plugin.is_betaald(regel, bedrag_ontvangen)
        self.assertTrue("[ERROR] Kan WedstrijdInschrijving voor regel met pk=" in stdout.getvalue())

        inschrijving = WedstrijdInschrijving(
                                wanneer=timezone.now(),
                                status=WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD,
                                wedstrijd=self.wedstrijd,
                                sessie=self.sessie,
                                sporterboog=self.sporterboog_r,
                                wedstrijdklasse=self.wedstrijdklasse_r,
                                bestelling=regel,
                                koper=self.account_100000)      # zelf
        inschrijving.save()

        # deelnemer == koper
        plugin.is_betaald(regel, bedrag_ontvangen)

        inschrijving.refresh_from_db()
        self.assertEqual(inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF)
        self.assertEqual(round(inschrijving.ontvangen_euro, 2), round(bedrag_ontvangen, 2))
        self.assertTrue("Betaling ontvangen" in inschrijving.log)

        # kortingen plugin
        plugin = WedstrijdKortingBestelPlugin()
        plugin.is_betaald(regel, bedrag_ontvangen)      # dummy implementatie

    def test_is_betaald_ander(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = WedstrijdBestelPlugin()
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='wedstrijd',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_WEDSTRIJD)
        regel.save()

        bedrag_ontvangen = Decimal(10.22)

        plugin.is_betaald(regel, bedrag_ontvangen)
        self.assertTrue("[ERROR] Kan WedstrijdInschrijving voor regel met pk=" in stdout.getvalue())

        inschrijving = WedstrijdInschrijving(
                                wanneer=timezone.now(),
                                status=WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD,
                                wedstrijd=self.wedstrijd,
                                sessie=self.sessie,
                                sporterboog=self.sporterboog_r,
                                wedstrijdklasse=self.wedstrijdklasse_r,
                                bestelling=regel,
                                koper=self.account_100001)      # ander
        inschrijving.save()

        # deelnemer != koper; sporter heeft account met bevestigde e-mail
        plugin.is_betaald(regel, bedrag_ontvangen)

        inschrijving.refresh_from_db()
        self.assertEqual(inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF)
        self.assertEqual(round(inschrijving.ontvangen_euro, 2), round(bedrag_ontvangen, 2))
        self.assertTrue("Betaling ontvangen" in inschrijving.log)

        self.wedstrijd.organisatie = ORGANISATIE_IFAA
        self.wedstrijd.save(update_fields=['organisatie'])

        # sporter heeft geen account maar wel een e-mail
        self.account_100000.delete()
        plugin.is_betaald(regel, bedrag_ontvangen)

        # sporter heeft geen account en geen e-mail
        self.sporter_100000.email = ''
        self.sporter_100000.save(update_fields=['email'])
        plugin.is_betaald(regel, bedrag_ontvangen)

    def test_get_verkoper_ver_nr(self):
        plugin = WedstrijdBestelPlugin()
        stdout = OutputWrapper(io.StringIO())
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='wedstrijd',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_WEDSTRIJD)
        regel.save()

        ver_nr = plugin.get_verkoper_ver_nr(regel)
        self.assertEqual(ver_nr, -1)
        self.assertTrue('] Kan WedstrijdInschrijving voor regel met pk=' in stdout.getvalue())

        inschrijving = WedstrijdInschrijving(
                                wanneer=timezone.now(),
                                status=WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD,
                                wedstrijd=self.wedstrijd,
                                sessie=self.sessie,
                                sporterboog=self.sporterboog_r,
                                wedstrijdklasse=self.wedstrijdklasse_r,
                                bestelling=regel,
                                koper=self.account_100000,
                                ontvangen_euro=Decimal(12.34))
        inschrijving.save()

        ver_nr = plugin.get_verkoper_ver_nr(regel)
        self.assertEqual(ver_nr, self.wedstrijd.organiserende_vereniging.ver_nr)

        # kortingen plugin
        plugin = WedstrijdKortingBestelPlugin()
        stdout = OutputWrapper(io.StringIO())
        plugin.zet_stdout(stdout)

        regel = BestellingRegel(
                    korte_beschrijving='wedstrijd',
                    bedrag_euro=Decimal(1.0),
                    code=BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING,
                    korting_ver_nr=1234)
        regel.save()

        ver_nr = plugin.get_verkoper_ver_nr(regel)
        self.assertEqual(ver_nr, 1234)

    def test_kwalificatiescores(self):
        stdout = OutputWrapper(io.StringIO())
        plugin = WedstrijdBestelPlugin()
        plugin.zet_stdout(stdout)

        # niet bestaande wedstrijd
        regel = BestellingRegel(code=BESTELLING_REGEL_CODE_WEDSTRIJD)
        regel.save()
        res = plugin.wil_kwalificatiescores(regel)
        self.assertIsNone(res)

        inschrijving = WedstrijdInschrijving(
                                wanneer=timezone.now(),
                                status=WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                wedstrijd=self.wedstrijd,
                                sessie=self.sessie,
                                sporterboog=self.sporterboog_r,
                                wedstrijdklasse=self.wedstrijdklasse_r,
                                bestelling=None,
                                koper=self.account_100000)
        inschrijving.save()

        regel = plugin.reserveer(inschrijving, 'Mandje test')
        self.assertEqual(regel.korte_beschrijving,
                         'Wedstrijd "Test wedstrijd"||deelname door [100000] Nor Maal||met boog Recurve')

        # wedstrijd heeft geen kwalificatie scores nodig
        wedstrijd = plugin.wil_kwalificatiescores(regel)
        self.assertIsNone(res)

        self.wedstrijd.eis_kwalificatie_scores = True
        self.wedstrijd.save(update_fields=['eis_kwalificatie_scores'])

        wedstrijd = plugin.wil_kwalificatiescores(regel)
        self.assertTrue(wedstrijd.datum_str != '')
        self.assertTrue(wedstrijd.plaats_str != '')
        self.assertTrue(wedstrijd.sporter_str != '')
        self.assertTrue(wedstrijd.url_kwalificatie_scores != '')


# end of file
