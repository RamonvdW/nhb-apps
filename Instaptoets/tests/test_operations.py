# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Geo.models import Regio
from Instaptoets.models import Categorie, Instaptoets, Vraag
from Instaptoets import operations
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestInstaptoetsOperations(E2EHelpers, TestCase):

    """ tests voor de Instaptoets applicatie, module operations """

    test_after = ('Sporter.tests.test_login',)

    def setUp(self):
        """ initialisatie van de test case """

        self.account_100000 = self.e2e_create_account('100000', 'normaal@test.not', 'Normaal')

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

        sporter = Sporter(
                        lid_nr=100000,
                        voornaam='Jan',
                        achternaam='van de Toets',
                        geboorte_datum='1977-07-07',
                        sinds_datum='2024-02-02',
                        account=self.account_100000,
                        bij_vereniging=ver,
                        adres_code='1234XX')
        sporter.save()
        self.sporter_100000 = sporter

        self._maak_vragen()

    @staticmethod
    def _maak_vragen():
        cat = Categorie(beschrijving="Test categorie")
        cat.save()

        Vraag(
            categorie=cat,
            vraag_tekst='Vraag nummer 1',
            antwoord_a='Morgen',
            antwoord_b='Overmorgen',
            antwoord_c='Gisteren',
            antwoord_d='Volgende week',
            juiste_antwoord='A').save()

        Vraag(
            # categorie=cat,            # bewust niet gezet voor meer coverage
            vraag_tekst='Vraag nummer 2',
            antwoord_a='Geel',
            antwoord_b='Rood',
            antwoord_c='Blauw',
            antwoord_d='Wit',
            juiste_antwoord='B').save()

        Vraag(
            categorie=cat,
            is_actief=False,        # mag niet getoond worden
            gebruik_voor_toets=True,
            gebruik_voor_quiz=True,
            vraag_tekst='Inactief mag niet getoond worden',
            antwoord_a='Ja',
            antwoord_b='Nee',
            antwoord_c='Nja',
            antwoord_d='',
            juiste_antwoord='B').save()

        bulk = [Vraag(
                    categorie=cat,
                    vraag_tekst='Vraag nummer %s' % (3 + nr),
                    antwoord_a='Geel',
                    antwoord_b='Rood',
                    antwoord_c='Blauw',
                    antwoord_d='Wit',
                    juiste_antwoord='A')
                for nr in range(20)]
        Vraag.objects.bulk_create(bulk)

    def test_instaptoets_beschikbaar(self):
        Vraag().save()
        self.assertTrue(operations.instaptoets_is_beschikbaar())

        Vraag.objects.all().delete()
        self.assertFalse(operations.instaptoets_is_beschikbaar())

    def test_toets_geldig(self):
        toets = Instaptoets(
                    afgerond=timezone.now().date(),
                    sporter=self.sporter_100000,
                    geslaagd=True)
        self.assertEqual(operations.toets_geldig(toets), (True, 365))

        toets = Instaptoets(
                    afgerond=timezone.now().date() - datetime.timedelta(days=365),
                    sporter=self.sporter_100000,
                    geslaagd=True)
        self.assertEqual(operations.toets_geldig(toets), (True, 1))

        toets = Instaptoets(
                    afgerond=timezone.now().date() - datetime.timedelta(days=366),
                    sporter=self.sporter_100000,
                    geslaagd=True)
        self.assertEqual(operations.toets_geldig(toets), (False, 0))

    def test_vind_toets(self):
        Instaptoets.objects.all().delete()

        # 1 toets, niet gehaald
        Instaptoets(
                afgerond=timezone.now() - datetime.timedelta(days=100),
                sporter=self.sporter_100000,
                aantal_vragen=10,
                aantal_antwoorden=10,
                is_afgerond=True,
                aantal_goed=1,
                geslaagd=False).save()

        # 1 toets, niet af
        toets = Instaptoets(
                    afgerond=timezone.now() - datetime.timedelta(days=10),
                    sporter=self.sporter_100000,
                    aantal_vragen=10,
                    aantal_antwoorden=5,
                    is_afgerond=False,
                    aantal_goed=0,
                    geslaagd=False)
        toets.save()

        gevonden_toets = operations.vind_toets(self.sporter_100000)
        self.assertEqual(gevonden_toets.pk, toets.pk)

        gevonden_toets = operations.vind_toets_prioriteer_geslaagd(self.sporter_100000)
        self.assertEqual(gevonden_toets.pk, toets.pk)

    def test_vind_toets_prioriteer_gehaald(self):
        Instaptoets.objects.all().delete()

        # 1 toets, gehaald
        Instaptoets(
                afgerond=timezone.now() - datetime.timedelta(days=100),
                sporter=self.sporter_100000,
                aantal_vragen=10,
                aantal_antwoorden=10,
                is_afgerond=True,
                aantal_goed=9,
                geslaagd=True).save()

        # 1 toets, niet gehaald
        Instaptoets(
                afgerond=timezone.now() - datetime.timedelta(days=10),
                sporter=self.sporter_100000,
                aantal_vragen=10,
                aantal_antwoorden=10,
                is_afgerond=True,
                aantal_goed=0,
                geslaagd=False).save()

        gevonden_toets = operations.vind_toets_prioriteer_geslaagd(self.sporter_100000)
        self.assertTrue(gevonden_toets.geslaagd)


# end of file
