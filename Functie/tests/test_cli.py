# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging


class TestFunctieCli(E2EHelpers, TestCase):

    """ tests voor de Functie command line interface (CLI) applicatie """

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_tst = maak_functie("Test test", "x")

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1001,
                    regio=Regio.objects.get(pk=111))
        ver.save()
        self.ver1 = ver

        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()

        self.functie_sec.vereniging = ver
        self.functie_sec.save()

    def test_maak_hwl(self):
        self.assertFalse(self.account_normaal.is_staff)
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('maak_hwl', 'normaal', '1001')
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("Account 'normaal' is HWL gemaakt van vereniging [1001] Grote Club" in f2.getvalue())

        # probeer nog een keer HWL te maken
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('maak_hwl', 'normaal', '1001')
        self.assertTrue("[WARNING] Account 'normaal' is al HWL van vereniging [1001] Grote Club" in f2.getvalue())

    def test_bad_account(self):
        # niet bestaand account
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('maak_hwl', 'abnormaal', '1001')
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue("[ERROR] Kan account abnormaal niet vinden" in f1.getvalue())
        self.assertTrue(f2.getvalue() == '')

    def test_bad_vereniging(self):
        # niet bestaande vereniging
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('maak_hwl', 'normaal', '9999')
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue("[ERROR] Kan vereniging 9999 niet vinden" in f1.getvalue())
        self.assertTrue(f2.getvalue() == '')

    def test_bad_functie(self):
        # niet bestaande functie
        self.functie_hwl.delete()
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('maak_hwl', 'normaal', '1001')
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue("[ERROR] Kan HWL functie van vereniging 1001 niet vinden" in f1.getvalue())
        self.assertTrue(f2.getvalue() == '')

    def test_maak_rcl(self):
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('maak_rcl', 'normaal', '18', '101')
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("Account 'normaal' is nu RCL Regio 101 Indoor" in f2.getvalue())

        # probeer nog een keer RCL te maken
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('maak_rcl', 'normaal', '18', '101')
        self.assertTrue("[WARNING] Account 'normaal' is al RCL Regio 101 Indoor" in f2.getvalue())

    def test_maak_rcl_bad(self):
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('maak_rcl', 'bestaat_niet', '18', '000')
        self.assertTrue("Account matching query does not exist" in f1.getvalue())
        self.assertTrue("Functie matching query does not exist" in f1.getvalue())
        self.assertTrue(f2.getvalue() == '')

    def test_maak_sec(self):
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('maak_sec', 'normaal', '1001')
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("Account 'normaal' is SEC gemaakt van vereniging [1001] Grote Club" in f2.getvalue())

        # nog een keer, dan is dit account al SEC
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('maak_sec', 'normaal', '1001')
        self.assertTrue("[WARNING] Account 'normaal' is al SEC van vereniging [1001] Grote Club" in f2.getvalue())

        # account bestaat niet
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('maak_sec', 'what', '1001')
        self.assertTrue("Account matching query does not exist" in f1.getvalue())

        # vereniging bestaat niet
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('maak_sec', 'normaal', '9999')
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue("Vereniging matching query does not exist" in f1.getvalue())

        # functie bestaat niet
        self.functie_sec.delete()
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('maak_sec', 'normaal', '1001')
        self.assertTrue("Functie matching query does not exist" in f1.getvalue())

    def test_check_beheerders(self):
        with self.assert_max_queries(55):
            f1, f2 = self.run_management_command('check_beheerders')
        self.assertTrue(f1.getvalue() == '')        # geen foutmeldingen

        # koppel een account aan een functie, maar geen sporter
        self.functie_hwl.accounts.add(self.account_normaal)

        with self.assert_max_queries(57):
            f1, f2 = self.run_management_command('check_beheerders')
        self.assertTrue(f1.getvalue() == '')
        # print('f2:', f2.getvalue())
        self.assertFalse("LET OP:" in f2.getvalue())    # we klagen niet meer over account niet gekoppeld aan sporter

        # maak account aan sporter
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

        with self.assert_max_queries(58):
            f1, f2 = self.run_management_command('check_beheerders')
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("LET OP: geen lid meer bij een vereniging" in f2.getvalue())

        # maak lid bij een andere vereniging
        ver = Vereniging(
                    ver_nr=1042,
                    naam="Andere club",
                    plaats="Overkantje",
                    regio=self.ver1.regio)
        ver.save()
        sporter.is_actief_lid = True
        sporter.bij_vereniging = ver
        sporter.save()

        with self.assert_max_queries(59):
            f1, f2 = self.run_management_command('check_beheerders')
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("LET OP: geen lid bij deze vereniging" in f2.getvalue())

        # nu alles goed zetten
        sporter.bij_vereniging = self.ver1
        sporter.account = self.account_normaal
        sporter.save()

        with self.assert_max_queries(59):
            f1, f2 = self.run_management_command('check_beheerders')
        self.assertTrue(f1.getvalue() == '')
        self.assertFalse("LET OP:" in f2.getvalue())

        # geef een account 2FA maar geen functie
        self.account_normaal.otp_is_actief = True
        self.account_normaal.save()
        sporter.account = self.account_normaal
        sporter.save()
        self.functie_hwl.accounts.clear()

        with self.assert_max_queries(59):
            f1, f2 = self.run_management_command('check_beheerders')
        self.assertTrue('maar niet meer gekoppeld aan een functie:\n  [100042] Kees Pijlpunt' in f2.getvalue())
        self.assertFalse('LET OP: geen actief lid' in f2.getvalue())

        # maak het lid niet-actief
        sporter.is_actief_lid = False
        sporter.save(update_fields=['is_actief_lid'])

        with self.assert_max_queries(59):
            f1, f2 = self.run_management_command('check_beheerders')
        # print('f2:', f2.getvalue())
        self.assertTrue('[100042] Kees Pijlpunt' in f2.getvalue())
        self.assertTrue('LET OP: geen actief lid' in f2.getvalue())

        # restore
        sporter.is_actief_lid = True
        sporter.save(update_fields=['is_actief_lid'])

        # maak een account BB, dan wordt de functie-check niet gedaan
        self.account_normaal.is_staff = True
        self.account_normaal.save(update_fields=['is_staff'])

        with self.assert_max_queries(59):
            f1, f2 = self.run_management_command('check_beheerders')
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertFalse('[100042] Kees Pijlpunt' in f2.getvalue())

        # restore
        self.account_normaal.is_staff = False
        self.account_normaal.save(update_fields=['is_staff'])

        with self.assert_max_queries(57):
            f1, f2 = self.run_management_command('check_beheerders', '--otp_uit')
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue('[100042] Kees Pijlpunt' in f2.getvalue())

# end of file
