# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from BasisTypen.definities import SCHEIDS_BOND
from Locatie.models import Locatie, Reistijd
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers.mgmt_cmds_helper import TEST_GMAPS_API_URL


class TestLocatieCliReistijd(E2EHelpers, TestCase):

    """ tests voor de Locatie applicatie, management commando's """

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

    def _reistijd_bijwerken(self):
        with override_settings(GMAPS_API_URL=TEST_GMAPS_API_URL):
            f1, f2 = self.run_management_command('reistijd_bijwerken')
        return f1, f2

    def test_basic(self):
        # niets te doen
        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertEqual(f1.getvalue(), '')

        with override_settings(GMAPS_API_URL=TEST_GMAPS_API_URL, GMAPS_KEY='garbage'):
            f1, f2 = self.run_management_command('reistijd_bijwerken')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue('[ERROR] Fout tijdens gmaps init: Invalid API key provided' in f1.getvalue())

    def test_geocode_crm(self):
        # normaal
        locatie = Locatie(
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
        locatie = Locatie(
                        naam='Test2',
                        adres='Peeslaan 42, 123ERR Boogdorp',       # 123ERR = geef foutmelding
                        plaats='Boogdorp',
                        adres_uit_crm=True)
        locatie.save()

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue('[ERROR] Fout van gmaps geocode: UNKNOWN_ERROR' in f1.getvalue())
        self.assertTrue('[WARNING] Geen lat/lon voor locatie pk=' in f1.getvalue())

        locatie.refresh_from_db()
        # print('lat/lon=%s/%s' % (repr(locatie.adres_lat), repr(locatie.adres_lon)))
        self.assertEqual(locatie.adres_lat, '?')
        self.assertEqual(locatie.adres_lon, '?')

        # geen resultaat
        locatie = Locatie(
                        naam='Test2',
                        adres='Peeslaan 42, 0000XX Boogdorp',       # 0000XX = geen resultaat geven
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
        locatie = Locatie(
                        naam='Test2',
                        adres='Peeslaan 42, 42GEEN Boogdorp',       # 42GEEN = geen resultaat geven
                        plaats='Boogdorp',
                        adres_uit_crm=True)
        locatie.save()

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue('[WARNING] Kan geen lat/lng halen uit geocode results ' in f1.getvalue())
        self.assertTrue('[WARNING] Geen lat/lon voor locatie pk=' in f1.getvalue())

        locatie.refresh_from_db()
        # print('lat/lon=%s/%s' % (repr(locatie.adres_lat), repr(locatie.adres_lon)))
        self.assertEqual(locatie.adres_lat, '?')
        self.assertEqual(locatie.adres_lon, '?')

    def test_geocode_overig(self):
        # incompleet resultaat
        locatie = Locatie(
                        naam='Test2',
                        adres='Peeslaan 42, 1234AB Boogdorp',       # 42GEEN = geen resultaat geven
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
        locatie = Locatie(
                        naam='Test2',
                        adres='Peeslaan 42, 42GEEN Boogdorp',       # 42GEEN = geen resultaat geven
                        plaats='Boogdorp',
                        adres_uit_crm=False)
        locatie.save()

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue('[WARNING] Kan geen lat/lng halen uit geocode results ' in f1.getvalue())
        self.assertTrue('[WARNING] Geen lat/lon voor locatie pk=' in f1.getvalue())

        locatie.refresh_from_db()
        # print('lat/lon=%s/%s' % (repr(locatie.adres_lat), repr(locatie.adres_lon)))
        self.assertEqual(locatie.adres_lat, '?')
        self.assertEqual(locatie.adres_lon, '?')

        # adres "diverse"
        locatie = Locatie(
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
        self.assertTrue('[WARNING] Geen lat/lon voor sporter 123456 met adres' in f1.getvalue())

        sporter.refresh_from_db()
        # print('lat/lon=%s/%s' % (repr(sporter.adres_lat), repr(sporter.adres_lon)))
        self.assertEqual(sporter.adres_lat, '?')
        self.assertEqual(sporter.adres_lon, '?')

    def test_reistijd(self):
        self.scheids.save()

        # maak een reistijd verzoek
        reistijd = Reistijd(vanaf_lat='sr3_lat',
                            vanaf_lon='sr3_lon',
                            naar_lat='zelf_lat',
                            naar_lon='zelf_lon',
                            reistijd_min=0)         # 0 = nog niet uitgerekend
        reistijd.save()

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue("[INFO] Reistijd '17 mins' is 1030 seconden; is 17 minuten" in f2.getvalue())

        scheids = Sporter.objects.get(lid_nr=self.scheids.lid_nr)
        self.assertEqual(scheids.adres_lat, '42.000000')
        self.assertEqual(scheids.adres_lon, '5.123000')

        reistijd.refresh_from_db()
        self.assertEqual(reistijd.reistijd_min, 17)

        # incompleet verzoek
        reistijd = Reistijd(vanaf_lat='sr3_lat',
                            vanaf_lon='sr3_lon',
                            naar_lat='incompleet',
                            naar_lon='zelf_lon',
                            reistijd_min=0)         # 0 = nog niet uitgerekend
        reistijd.save()

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[ERROR] Onvolledig directions antwoord: " in f1.getvalue())

        scheids = Sporter.objects.get(lid_nr=self.scheids.lid_nr)
        self.assertEqual(scheids.adres_lat, '42.000000')
        self.assertEqual(scheids.adres_lon, '5.123000')

        reistijd.refresh_from_db()
        self.assertEqual(reistijd.reistijd_min, 17 * 60)

        # fout
        reistijd = Reistijd(vanaf_lat='sr3_lat',
                            vanaf_lon='sr3_lon',
                            naar_lat='geef fout',
                            naar_lon='zelf_lon',
                            reistijd_min=0)         # 0 = nog niet uitgerekend
        reistijd.save()

        f1, f2 = self._reistijd_bijwerken()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[ERROR] Fout van gmaps directions route van" in f1.getvalue())

# end of file
