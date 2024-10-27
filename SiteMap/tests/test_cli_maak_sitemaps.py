# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Competitie.models import Competitie
from Evenement.definities import EVENEMENT_STATUS_GEACCEPTEERD
from Evenement.models import Evenement
from Geo.models import Regio
from Locatie.models import EvenementLocatie, WedstrijdLocatie
from Records.models import IndivRecord
from Vereniging.models import Vereniging
from Webwinkel.models import WebwinkelProduct
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD
from Wedstrijden.models import Wedstrijd
from SiteMap.models import SiteMapLastMod
from TestHelpers.e2ehelpers import E2EHelpers
import tempfile
import datetime
import os


class TestSiteMapCliMaakSitemaps(E2EHelpers, TestCase):

    """ tests voor de SiteMap applicatie, management command maak_sitemaps """

    expected_sitemaps = 7 + 1       # +1 for index

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_alles(self):
        self.assertEqual(SiteMapLastMod.objects.count(), 0)

        with tempfile.TemporaryDirectory() as output_dir:
            with self.assert_max_queries(20):
                f1, f2 = self.run_management_command('maak_sitemaps', output_dir)
            # print("f1: %s" % f1.getvalue())
            # print("f2: %s" % f2.getvalue())

            self.assertTrue('[ERROR]' not in f1.getvalue())
            self.assertTrue('[ERROR]' not in f2.getvalue())

            fnames = os.listdir(output_dir)
            self.assertEqual(len(fnames), self.expected_sitemaps)

        self.assertEqual(SiteMapLastMod.objects.count(), self.expected_sitemaps - 1)

        last_mod = SiteMapLastMod.objects.first()
        self.assertTrue(str(last_mod) != '')

        # nog een keer, dan zijn de last_mod records beschikbaar en de digest hetzelfde
        with tempfile.TemporaryDirectory() as output_dir:
            with self.assert_max_queries(20):
                f1, f2 = self.run_management_command('maak_sitemaps', output_dir)

            self.assertTrue('[ERROR]' not in f1.getvalue())
            self.assertTrue('[ERROR]' not in f2.getvalue())

            fnames = os.listdir(output_dir)
            self.assertEqual(len(fnames), self.expected_sitemaps)

        self.assertEqual(SiteMapLastMod.objects.count(), self.expected_sitemaps - 1)

    def test_exception(self):
        fake_dir = '/tmp/does-not-exist/'
        f1, f2 = self.run_management_command('maak_sitemaps', fake_dir, report_exit_code=False)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertTrue('[ERROR]' in f1.getvalue())
        self.assertTrue('Traceback:' in f1.getvalue())

    def test_met_objects(self):
        # voor coverage van de plugins moet er data zijn

        now_date = timezone.now().date()
        yesterday = now_date - datetime.timedelta(days=1)
        back_6_weeks = now_date - datetime.timedelta(days=6*7)
        future_5_weeks = now_date + datetime.timedelta(days=5*7)

        ver = Vereniging(
                    ver_nr=1000,
                    naam='Grote Club',
                    plaats='',
                    regio=Regio.objects.first(),
                    contact_email='')
        ver.save()

        Competitie(
                beschrijving='',
                afstand=25,
                begin_jaar=2000,
                klassengrenzen_vastgesteld=True,
                begin_fase_F=yesterday).save()

        # nog een, niet openbaar
        Competitie(
                beschrijving='',
                afstand=18,
                begin_jaar=2000,
                klassengrenzen_vastgesteld=False).save()

        loc = EvenementLocatie(
                    naam='',
                    vereniging=ver,
                    adres='')
        loc.save()

        Evenement(
            status=EVENEMENT_STATUS_GEACCEPTEERD,
            organiserende_vereniging=ver,
            datum=yesterday,
            locatie=loc).save()

        Evenement(
            status=EVENEMENT_STATUS_GEACCEPTEERD,
            organiserende_vereniging=ver,
            datum=back_6_weeks,
            locatie=loc).save()

        Evenement(
            status=EVENEMENT_STATUS_GEACCEPTEERD,
            organiserende_vereniging=ver,
            datum=future_5_weeks,
            locatie=loc).save()

        IndivRecord(
            volg_nr=1,
            discipline='18',
            soort_record='hoog',
            geslacht='M',
            leeftijdscategorie='L',
            materiaalklasse='M',
            para_klasse='',
            naam='',
            datum='2000-01-01',
            plaats='',
            land='',
            score=1,
            x_count=0,
            max_score=10).save()

        loc = WedstrijdLocatie(
                naam='',
                discipline_25m1pijl=True,
                discipline_indoor=True,
                adres='')
        loc.save()

        Wedstrijd(
            status=WEDSTRIJD_STATUS_GEACCEPTEERD,
            datum_begin=yesterday,
            datum_einde=yesterday,
            organiserende_vereniging=ver,
            locatie=loc).save()

        Wedstrijd(
            status=WEDSTRIJD_STATUS_GEACCEPTEERD,
            datum_begin=future_5_weeks,
            datum_einde=future_5_weeks,
            organiserende_vereniging=ver,
            locatie=loc).save()

        Wedstrijd(
            status=WEDSTRIJD_STATUS_GEACCEPTEERD,
            datum_begin=back_6_weeks,
            datum_einde=back_6_weeks,
            organiserende_vereniging=ver,
            locatie=loc).save()

        WebwinkelProduct(
            omslag_titel='Test titel 1',
            onbeperkte_voorraad=True,
            bestel_begrenzing='').save()

        WebwinkelProduct(
            omslag_titel='Test titel 1',   # zelfde titel als vorige product
            onbeperkte_voorraad=True,
            bestel_begrenzing='').save()

        WebwinkelProduct(
            omslag_titel='Test titel 2',
            beschrijving='https://extern.site',         # link naar externe webshop
            onbeperkte_voorraad=True,
            bestel_begrenzing='').save()

        with tempfile.TemporaryDirectory() as output_dir:
            with self.assert_max_queries(20):
                f1, f2 = self.run_management_command('maak_sitemaps', output_dir)
            # print("f1: %s" % f1.getvalue())
            # print("f2: %s" % f2.getvalue())

# end of file
