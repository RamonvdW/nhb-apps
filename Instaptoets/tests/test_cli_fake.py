# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Geo.models import Regio
from Instaptoets.models import Instaptoets
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestInstaptoetsCliFake(E2EHelpers, TestCase):
    """ unittests voor de Instaptoets applicatie, management command fake_instaptoets_gehaald """

    def setUp(self):
        """ initialisatie van de test case """
        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(regio_nr=102),
                    bank_iban='IBAN123456789',
                    bank_bic='BIC2BIC',
                    kvk_nummer='KvK1234',
                    website='www.bb.not',
                    contact_email='info@bb.not',
                    telefoonnummer='12345678')
        ver.save()

        self.lid_nr = 100000
        sporter = Sporter(
                        lid_nr=self.lid_nr,
                        voornaam='Jan',
                        achternaam='van de Toets',
                        geboorte_datum='1977-07-07',
                        sinds_datum='2024-02-02',
                        account=None,
                        bij_vereniging=ver,
                        adres_code='1234XX')
        sporter.save()
        self.sporter_100000 = sporter

    def test_fake(self):
        f1, f2 = self.run_management_command('fake_instaptoets_gehaald', 'NaN', '2000-01-01',
                                             report_exit_code=False)
        # print('\nf1:', f1.getvalue())
        self.assertTrue(' raised CommandError("Error: argument bondsnummer: invalid int value' in f1.getvalue())

        f1, f2 = self.run_management_command('fake_instaptoets_gehaald', 1234, '1234')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[ERROR] '1234' is geen valide datum. Moet voldoen aan YYYY-MM-DD" in f1.getvalue())
        self.assertTrue("[ERROR] Sporter met bondsnummer 1234 niet gevonden" in f1.getvalue())

        # foute datum
        f1, f2 = self.run_management_command('fake_instaptoets_gehaald', self.lid_nr, '2000-01-01')
        self.assertTrue("[ERROR] Datum moet in de afgelopen 365 dagen liggen" in f1.getvalue())

        self.assertEqual(Instaptoets.objects.count(), 0)
        datum_str = (timezone.now() - datetime.timedelta(days=40)).date().strftime("%Y-%m-%d")
        self.run_management_command('fake_instaptoets_gehaald', self.lid_nr, datum_str)
        self.assertEqual(Instaptoets.objects.count(), 1)
        toets = Instaptoets.objects.first()
        self.assertTrue(toets.is_afgerond)
        self.assertTrue(toets.geslaagd)

# end of file
