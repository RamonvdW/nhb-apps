# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
import datetime
import os


class TestBondspasMaakPdf(E2EHelpers, TestCase):

    """ tests voor de Bondspas applicatie, maak pdf """

    def setUp(self):

        self.lid_nr = 123456

        now = datetime.datetime.now()

        self.sporter = sporter = Sporter(
                                    lid_nr=self.lid_nr,
                                    voornaam='Tester',
                                    achternaam='De tester',
                                    unaccented_naam='test',
                                    email='tester@mail.not',
                                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                                    geslacht='M',
                                    # bij_vereniging
                                    lid_tot_einde_jaar=now.year)
        self.account = self.e2e_create_account(self.lid_nr, sporter.email, sporter.voornaam)
        sporter.account = self.account
        sporter.save()

    def test_maak_pdf(self):
        # maak een bondspas pdf aan
        f1, f2 = self.run_management_command('maak_bondspas_pdf', self.lid_nr)
        # print('f1=%s\nf2=%s' % (f1.getvalue(), f2.getvalue()))
        fname = 'bondspas_123456.pdf'
        self.assertTrue('[ERROR]' not in f1.getvalue())
        self.assertTrue('[INFO] Gemaakt: %s' % fname in f2.getvalue())
        os.remove(fname)

# end of file
