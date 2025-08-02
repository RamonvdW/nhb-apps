# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.core.management.base import OutputWrapper
from BasisTypen.definities import SCHEIDS_BOND
from Locatie.models import WedstrijdLocatie, Reistijd
from Locatie.operations import ReistijdBepaler
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
import io


class TestLocatieCliReistijd(E2EHelpers, TestCase):

    """ tests voor de Locatie applicatie, management commando's """

    SR3_LAT = 1.0
    SR3_LON = 1.1
    ZELF_LAT = 2.0
    ZELF_LON = 2.1

    def setUp(self):
        scheids = Sporter(
                        lid_nr=123456,
                        voornaam='Scheids',
                        achternaam='den Urste',
                        unaccented_naam='Scheids den Urste',
                        email='scheids@test.not',
                        geboorte_datum='2000-01-01',
                        geslacht='M',
                        sinds_datum='2000-01-01',
                        postadres_1='Spanboog 5',
                        postadres_2='1234AB Pijlstad',
                        postadres_3='',
                        adres_code='1234AB',
                        scheids=SCHEIDS_BOND)
        # scheids.save()
        self.scheids = scheids

    @staticmethod
    def _reistijd_bijwerken():
        # gebruik een verse instantie met "schone" stdout/stderr
        stdout = OutputWrapper(io.StringIO())
        stderr = OutputWrapper(io.StringIO())

        bepaler = ReistijdBepaler(stdout, stderr, 25)
        bepaler.run()

        return stderr, stdout

    def test_basic(self):
        # niets te doen
        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertEqual(f1.getvalue(), '')

        # trigger hergebruik gmaps instantie
        stdout = OutputWrapper(io.StringIO())
        stderr = OutputWrapper(io.StringIO())

        bepaler = ReistijdBepaler(stdout, stderr, 25)
        bepaler.run()
        bepaler.run()  # triggers gmap connection already done

    def test_bad_key(self):
        stdout = OutputWrapper(io.StringIO())
        stderr = OutputWrapper(io.StringIO())

        with override_settings(GOOGLEMAPS_API_KEY='garbage'):
            bepaler = ReistijdBepaler(stdout, stderr, 25)
            bepaler.run()
        # print('\nf1: %s\nf2: %s' % (stdout.getvalue(), stderr.getvalue()))
        self.assertTrue('[ERROR] Fout tijdens gmaps init: Invalid API key provided' in stderr.getvalue())

    def test_geocode_crm(self):
        # normaal
        locatie = WedstrijdLocatie(
                        naam='Test1',
                        adres='Peeslaan 42, 1234AB Boogdorp',
                        plaats='Boogdorp',
                        adres_uit_crm=True)
        locatie.save()

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertEqual(f1.getvalue(), '')

        locatie.refresh_from_db()
        # print('lat/lon=%s/%s' % (repr(locatie.adres_lat), repr(locatie.adres_lon)))
        self.assertTrue('42.00' in locatie.adres_lat)
        self.assertTrue('5.123' in locatie.adres_lon)

        # trigger foutmelding van de server
        locatie = WedstrijdLocatie(
                        naam='Test2',
                        adres='Peeslaan 42, 123ERR Boogdorp',       # 123ERR = geef foutmelding
                        plaats='Boogdorp',
                        adres_uit_crm=True)
        locatie.save()

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue('[ERROR] Fout van gmaps geocode: UNKNOWN_ERROR' in f1.getvalue())
        # self.assertTrue('[WARNING] Geen lat/lon voor locatie pk=' in f1.getvalue())

        locatie.refresh_from_db()
        # print('lat/lon=%s/%s' % (repr(locatie.adres_lat), repr(locatie.adres_lon)))
        self.assertEqual(locatie.adres_lat, '')
        self.assertEqual(locatie.adres_lon, '')

        # geen resultaat
        locatie = WedstrijdLocatie(
                        naam='Test2',
                        adres='Peeslaan 42, 0000XX Boogdorp',       # 0000XX = leeg resultaat
                        plaats='Boogdorp',
                        adres_uit_crm=True)
        locatie.save()

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue('[WARNING] Geen geocode resultaten voor adres=' in f1.getvalue())
        self.assertTrue('[WARNING] Geen lat/lon voor locatie pk=' in f1.getvalue())

        locatie.refresh_from_db()
        # print('lat/lon=%s/%s' % (repr(locatie.adres_lat), repr(locatie.adres_lon)))
        self.assertEqual(locatie.adres_lat, '?')
        self.assertEqual(locatie.adres_lon, '?')

        # incompleet resultaat
        locatie = WedstrijdLocatie(
                        naam='Test2',
                        adres='Peeslaan 42, 42GEEN Boogdorp',       # 42GEEN = geen resultaat geven
                        plaats='Boogdorp',
                        adres_uit_crm=True)
        locatie.save()

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue('[WARNING] Kan geen lat/lng halen uit geocode results ' in f1.getvalue())
        # self.assertTrue('[WARNING] Geen lat/lon voor locatie pk=' in f1.getvalue())

        locatie.refresh_from_db()
        # print('lat/lon=%s/%s' % (repr(locatie.adres_lat), repr(locatie.adres_lon)))
        self.assertEqual(locatie.adres_lat, '')
        self.assertEqual(locatie.adres_lon, '')

    def test_geocode_overig(self):
        # normaal resultaat
        locatie = WedstrijdLocatie(
                        naam='Test2',
                        adres='Peeslaan 42, 1234AB Boogdorp',
                        plaats='Boogdorp',
                        adres_uit_crm=False)
        locatie.save()

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        # self.assertTrue('[WARNING] No lat/lon for locatie pk=' in f1.getvalue())
        self.assertEqual(f1.getvalue(), '')

        locatie.refresh_from_db()
        # print('lat/lon=%s/%s' % (repr(locatie.adres_lat), repr(locatie.adres_lon)))
        self.assertTrue('42.00' in locatie.adres_lat)
        self.assertTrue('5.123' in locatie.adres_lon)

        # incompleet resultaat
        locatie = WedstrijdLocatie(
                        naam='Test2',
                        adres='Peeslaan 42, 42GEEN Boogdorp',       # 42GEEN = geen resultaat geven
                        plaats='Boogdorp',
                        adres_uit_crm=False)
        locatie.save()

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue('[WARNING] Kan geen lat/lng halen uit geocode results ' in f1.getvalue())
        # self.assertTrue('[WARNING] Geen lat/lon voor locatie pk=' in f1.getvalue())

        locatie.refresh_from_db()
        # print('lat/lon=%s/%s' % (repr(locatie.adres_lat), repr(locatie.adres_lon)))
        self.assertEqual(locatie.adres_lat, '')
        self.assertEqual(locatie.adres_lon, '')

        # adres "diverse"
        locatie = WedstrijdLocatie(
                        naam='Test3',
                        adres='(diverse)',     # speciale betekenis
                        plaats='(diverse)',
                        adres_uit_crm=False)
        locatie.save()

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        locatie.refresh_from_db()
        # print('lat/lon=%s/%s' % (repr(locatie.adres_lat), repr(locatie.adres_lon)))
        self.assertEqual(locatie.adres_lat, '')
        self.assertEqual(locatie.adres_lon, '')

    def test_geocode_scheids(self):
        self.scheids.save()
        sporter = Sporter(
                    lid_nr='123456',
                    voornaam='S',
                    achternaam='Porter',
                    unaccented_naam='S Porter',
                    email='sporter@khsn.not',
                    geboorte_datum='1990-02-03',
                    geslacht='M',
                    sinds_datum='2000-01-01',
                    postadres_1='Whatever',
                    postadres_2='',
                    postadres_3='',
                    scheids=SCHEIDS_BOND)
        sporter.save()

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertEqual(f1.getvalue(), '')

        sporter.refresh_from_db()
        # print('lat/lon=%s/%s' % (repr(sporter.adres_lat), repr(sporter.adres_lon)))
        self.assertTrue('42.00' in sporter.adres_lat)
        self.assertTrue('5.123' in sporter.adres_lon)

        # foutsituatie
        sporter.postadres_2 = '42GEEN Boogstad'     # 42GEEN = Geen resultaat geven
        sporter.postadres_3 = 'Nederland'
        sporter.adres_lat = ''
        sporter.adres_lon = ''
        sporter.save(update_fields=['postadres_2', 'postadres_3', 'adres_lat', 'adres_lon'])

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue('[WARNING] Kan geen lat/lng halen uit geocode results' in f1.getvalue())

        sporter.refresh_from_db()
        # print('lat/lon=%s/%s' % (repr(sporter.adres_lat), repr(sporter.adres_lon)))
        self.assertEqual(sporter.adres_lat, '')
        self.assertEqual(sporter.adres_lon, '')

        # foutsituatie
        sporter.postadres_2 = '0000XX Boogstad'  # 0000XX = Leeg resultaat
        sporter.postadres_3 = 'Nederland'
        sporter.adres_lat = ''
        sporter.adres_lon = ''
        sporter.save(update_fields=['postadres_2', 'postadres_3', 'adres_lat', 'adres_lon'])

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[WARNING] Geen geocode resultaten voor adres='Whatever, 0000XX" in f1.getvalue())
        self.assertTrue("[WARNING] Geen lat/lon voor sporter 123456 met adres 'Whatever, 0000XX" in f1.getvalue())

        sporter.refresh_from_db()
        # print('lat/lon=%s/%s' % (repr(sporter.adres_lat), repr(sporter.adres_lon)))
        self.assertEqual(sporter.adres_lat, '?')
        self.assertEqual(sporter.adres_lon, '?')

    def test_geocode_fallback(self):
        # incompleet resultaat
        locatie = WedstrijdLocatie(
                        naam='Test2',
                        adres='Peeslaan 41, 0000XX Boogdorp',
                        plaats='Boogdorp',
                        adres_uit_crm=False)
        locatie.save()

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue('[WARNING] Geen geocode resultaten voor adres=' in f1.getvalue())
        self.assertTrue('[WARNING] Geen lat/lon voor locatie pk=' in f1.getvalue())

        locatie.refresh_from_db()
        # print('lat/lon=%s/%s' % (repr(locatie.adres_lat), repr(locatie.adres_lon)))
        self.assertEqual(locatie.adres_lat, '?')
        self.assertEqual(locatie.adres_lon, '?')

        # fallback laten gebruiken
        fallback = {'PEESLAAN 41, 0000XX BOOGDORP': (1.23, 4.56)}
        with override_settings(GEOCODE_FALLBACK=fallback):
            f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        self.assertFalse('[WARNING] Geen fallback voor locatie pk=' in f2.getvalue())

    def test_reistijd(self):
        self.scheids.save()

        # maak een reistijd verzoek
        reistijd = Reistijd(vanaf_lat=self.SR3_LAT,
                            vanaf_lon=self.SR3_LON,
                            naar_lat=self.ZELF_LAT,
                            naar_lon=self.ZELF_LON,
                            reistijd_min=0)         # 0 = nog niet uitgerekend
        reistijd.save()

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue("[INFO] Aantal verzoeken naar Routes API: 1" in f2.getvalue())

        scheids = Sporter.objects.get(lid_nr=self.scheids.lid_nr)
        self.assertEqual(scheids.adres_lat, '42.000000')
        self.assertEqual(scheids.adres_lon, '5.123000')

        reistijd.refresh_from_db()
        self.assertEqual(reistijd.reistijd_min, 17)
        self.assertTrue(str(reistijd) != '')

        # input wordt niet geaccepteerd
        Reistijd.objects.all().delete()
        reistijd = Reistijd(vanaf_lat=self.SR3_LAT,
                            vanaf_lon=self.SR3_LON,
                            naar_lat='BAD',
                            naar_lon=self.ZELF_LON,
                            reistijd_min=0)         # 0 = nog niet uitgerekend
        reistijd.save()

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[WARNING] Fout in lat/lon (geen float?) voor reistijd pk=" in f2.getvalue())

        reistijd.refresh_from_db()
        self.assertEqual(reistijd.reistijd_min, 0)      # niet bijgewerkt

        # speciaal verzoek: simulator geeft een leeg antwoord
        Reistijd.objects.all().delete()
        reistijd = Reistijd(vanaf_lat=self.SR3_LAT,
                            vanaf_lon=self.SR3_LON,
                            naar_lat=420.0,
                            naar_lon=self.ZELF_LON,
                            reistijd_min=0)         # 0 = nog niet uitgerekend
        reistijd.save()

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[ERROR] Onvolledig routes antwoord:" in f1.getvalue())

        reistijd.refresh_from_db()
        self.assertGreater(reistijd.reistijd_min, 5 * 60)       # speciaal getal (16 of 17 uur)

        reistijd = Reistijd(vanaf_lat='')
        self.assertFalse(reistijd.is_compleet())

        reistijd = Reistijd(naar_lat='', vanaf_lat='x', vanaf_lon='y')
        self.assertFalse(reistijd.is_compleet())

# end of file
