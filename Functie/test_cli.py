# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from TestHelpers.e2ehelpers import E2EHelpers
from NhbStructuur.models import NhbVereniging, NhbRegio
from Sporter.models import Sporter
from .models import maak_functie
import io


class TestFunctieCli(E2EHelpers, TestCase):

    """ tests voor de Functie command line interface (CLI) applicatie """

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_tst = maak_functie("Test test", "x")

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = 1001
        ver.regio = NhbRegio.objects.get(pk=111)
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver1 = ver

        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        self.functie_sec.nhb_ver = ver
        self.functie_sec.save()

    def test_maak_hwl(self):
        self.assertFalse(self.account_normaal.is_staff)
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_hwl', 'normaal', '1001', stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("Account 'normaal' is HWL gemaakt van vereniging [1001] Grote Club" in f2.getvalue())

        # probeer nog een keer HWL te maken
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_hwl', 'normaal', '1001', stderr=f1, stdout=f2)
        self.assertTrue("[WARNING] Account 'normaal' is al HWL van vereniging [1001] Grote Club" in f2.getvalue())

    def test_bad_account(self):
        # niet bestaand account
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_hwl', 'abnormaal', '1001', stderr=f1, stdout=f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue("[ERROR] Kan account abnormaal niet vinden" in f1.getvalue())
        self.assertTrue(f2.getvalue() == '')

    def test_bad_vereniging(self):
        # niet bestaande vereniging
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_hwl', 'normaal', '9999', stderr=f1, stdout=f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue("[ERROR] Kan vereniging 9999 niet vinden" in f1.getvalue())
        self.assertTrue(f2.getvalue() == '')

    def test_bad_functie(self):
        # niet bestaande functie
        self.functie_hwl.delete()
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_hwl', 'normaal', '1001', stderr=f1, stdout=f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue("[ERROR] Kan HWL functie van vereniging 1001 niet vinden" in f1.getvalue())
        self.assertTrue(f2.getvalue() == '')

    def test_maak_rcl(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_rcl', 'normaal', '18', '101', stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("Account 'normaal' is nu RCL Regio 101 Indoor" in f2.getvalue())

        # probeer nog een keer RCL te maken
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_rcl', 'normaal', '18', '101', stderr=f1, stdout=f2)
        self.assertTrue("[WARNING] Account 'normaal' is al RCL Regio 101 Indoor" in f2.getvalue())

    def test_maak_rcl_bad(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_rcl', 'bestaatniet', '18', '000', stderr=f1, stdout=f2)
        self.assertTrue("Account matching query does not exist" in f1.getvalue())
        self.assertTrue("Functie matching query does not exist" in f1.getvalue())
        self.assertTrue(f2.getvalue() == '')

    def test_maak_sec(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_sec', 'normaal', '1001', stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("Account 'normaal' is SEC gemaakt van vereniging [1001] Grote Club" in f2.getvalue())

        # nog een keer, dan is dit account al SEC
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_sec', 'normaal', '1001', stderr=f1, stdout=f2)
        self.assertTrue("[WARNING] Account 'normaal' is al SEC van vereniging [1001] Grote Club" in f2.getvalue())

        # account bestaat niet
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_sec', 'what', '1001', stderr=f1, stdout=f2)
        self.assertTrue("Account matching query does not exist" in f1.getvalue())

        # vereniging bestaat niet
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_sec', 'normaal', '9999', stderr=f1, stdout=f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue("NhbVereniging matching query does not exist" in f1.getvalue())

        # functie bestaat niet
        self.functie_sec.delete()
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_sec', 'normaal', '1001', stderr=f1, stdout=f2)
        self.assertTrue("Functie matching query does not exist" in f1.getvalue())

    def test_check_beheerders(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(48):
            management.call_command('check_beheerders', stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue() == '')        # geen foutmeldingen

        # koppel een account aan een functie, maar geen sporter
        self.functie_hwl.accounts.add(self.account_normaal)

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(50):
            management.call_command('check_beheerders', stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("LET OP: geen koppeling met NHB lid" in f2.getvalue())

        # maak account ook nhblid
        sporter = Sporter(
                    lid_nr=100042,
                    voornaam='Kees',
                    achternaam='Pijlpunt',
                    email='kees@pijlpunt.nl',
                    geboorte_datum='1900-10-20',
                    geslacht='M',
                    para_classificatie='',
                    is_actief_lid=False,
                    sinds_datum='2020-02-20',
                    bij_vereniging=None,
                    lid_tot_einde_jaar=0,
                    account=self.account_normaal)
        sporter.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(51):
            management.call_command('check_beheerders', stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("LET OP: geen lid meer bij een vereniging" in f2.getvalue())

        # maak lid bij een andere vereniging
        ver = NhbVereniging(
                    ver_nr=1042,
                    naam="Andere club",
                    plaats="Overkantje",
                    regio=self.nhbver1.regio)
        ver.save()
        sporter.is_actief_lid = True
        sporter.bij_vereniging = ver
        sporter.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(52):
            management.call_command('check_beheerders', stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("LET OP: geen lid bij deze vereniging" in f2.getvalue())

        # nu alles goed zetten
        sporter.bij_vereniging = self.nhbver1
        sporter.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(52):
            management.call_command('check_beheerders', stderr=f1, stdout=f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue(f1.getvalue() == '')
        self.assertFalse("LET OP:" in f2.getvalue())


# end of file
