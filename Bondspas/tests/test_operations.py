# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Bondspas.operations import bepaal_jaar_bondspas, maak_bondspas_regels
from Bondspas.models import BondspasJaar
from Geo.models import Regio
from Opleiding.models import OpleidingDiploma
from Sporter.models import Sporter, Speelsterkte
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from unittest.mock import patch
import datetime


class TestBondspasOperations(E2EHelpers, TestCase):

    """ tests voor de Bondspas applicatie, berekenen van de informatie die op de bondspas moet komen """

    bondspas_jaar1 = 2025       # files/achtergrond_bondspas-2025.jpg moet aanwezig zijn
    bondspas_jaar2 = 2026       # files/achtergrond_bondspas-2026.jpg moet aanwezig zijn

    def setUp(self):
        pass

    def test_jaar(self):
        BondspasJaar.objects.create(jaar=self.bondspas_jaar1, zichtbaar=True)
        BondspasJaar.objects.create(jaar=self.bondspas_jaar2, zichtbaar=False)

        with patch('django.utils.timezone.localtime') as mock_timezone:
            mock_timezone.return_value = datetime.datetime(year=self.bondspas_jaar1, month=11, day=12, tzinfo=datetime.timezone.utc)
            jaar_pas = bepaal_jaar_bondspas()
            self.assertEqual(jaar_pas, self.bondspas_jaar1)

            mock_timezone.return_value = datetime.datetime(year=self.bondspas_jaar2, month=1, day=12, tzinfo=datetime.timezone.utc)
            jaar_pas = bepaal_jaar_bondspas()
            self.assertEqual(jaar_pas, self.bondspas_jaar1)

            mock_timezone.return_value = datetime.datetime(year=self.bondspas_jaar2, month=1, day=31, tzinfo=datetime.timezone.utc)
            jaar_pas = bepaal_jaar_bondspas()
            self.assertEqual(jaar_pas, self.bondspas_jaar1)

            BondspasJaar.objects.filter(jaar=self.bondspas_jaar2).update(zichtbaar=True)

            mock_timezone.return_value = datetime.datetime(year=self.bondspas_jaar2, month=1, day=12, tzinfo=datetime.timezone.utc)
            jaar_pas = bepaal_jaar_bondspas()
            self.assertEqual(jaar_pas, self.bondspas_jaar2)

            mock_timezone.return_value = datetime.datetime(year=self.bondspas_jaar2, month=1, day=31, tzinfo=datetime.timezone.utc)
            jaar_pas = bepaal_jaar_bondspas()
            self.assertEqual(jaar_pas, self.bondspas_jaar2)

    def test_regels(self):
        now = datetime.datetime.now()
        year = now.year

        ver = Vereniging(
                        ver_nr=1000,
                        naam="Grote Club",
                        regio=Regio.objects.get(regio_nr=112))
        ver.save()

        sporter = Sporter(
                        lid_nr=123456,
                        voornaam='Tester',
                        achternaam='De tester',
                        unaccented_naam='test',
                        email='tester@mail.not',
                        geboorte_datum=datetime.date(year=now.year - 55, month=3, day=4),
                        sinds_datum=datetime.date(year=2010, month=11, day=12),
                        geslacht='M',
                        bij_vereniging=None,
                        lid_tot_einde_jaar=year,
                        is_erelid=True,
                        para_classificatie='test')

        regels = maak_bondspas_regels(sporter, year)
        # print(regels)

        # andere varianten
        sporter.is_erelid = False
        sporter.para_classificatie = ''
        sporter.bij_vereniging = ver

        regels = maak_bondspas_regels(sporter, year)
        # print(regels)

        sporter.save()

        Speelsterkte(
                sporter=sporter,
                datum=now,
                beschrijving='test',
                discipline='Recurve',
                category='Cadet',
                pas_code='RC1200',
                volgorde=143).save()

        Speelsterkte(
                sporter=sporter,
                datum=now,
                beschrijving='test',
                discipline='Recurve',
                category='Master',
                pas_code='RM1000',
                volgorde=155).save()

        Speelsterkte(
                sporter=sporter,
                datum=now,
                beschrijving='test',
                discipline='Recurve',
                category='Master',
                pas_code='RM1100',
                volgorde=154).save()

        Speelsterkte(
                sporter=sporter,
                datum=now,
                beschrijving='test',
                discipline='Recurve',
                category='Senior',
                pas_code='R1000',
                volgorde=135).save()

        Speelsterkte(
                sporter=sporter,
                datum=now,
                beschrijving='test',
                discipline='KHSN Tussenspeld',
                category='Senior',
                pas_code='TS1150',
                volgorde=201).save()

        Speelsterkte(
                sporter=sporter,
                datum=now,
                beschrijving='Gouden Pijl',
                discipline='Algemeen',
                category='Senior',
                pas_code='GPIJL',
                volgorde=600).save()

        OpleidingDiploma(
                sporter=sporter,
                code='020',
                beschrijving='test',
                toon_op_pas=True,
                datum_begin=now).save()

        OpleidingDiploma(
                sporter=sporter,
                code='Huh?',
                beschrijving='test',
                toon_op_pas=True,
                datum_begin=now).save()

        regels = maak_bondspas_regels(sporter, year)
        # print(regels)

        self.assertTrue(('Speelsterkte', 'R1000, RM1100, TS1150') in regels)


# end of file
