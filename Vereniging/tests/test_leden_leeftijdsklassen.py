# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Sporter.models import Sporter, SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
from unittest.mock import patch
from datetime import date


class TestVerenigingLedenLeeftijdsklassen(E2EHelpers, TestCase):

    """ tests voor de Vereniging applicatie, view leden-leeftijdsklassen """

    test_after = ('BasisTypen', 'ImportCRM', 'Functie', 'Sporter', 'Competitie')

    url_leden_leeftijdsklassen = '/vereniging/leden-leeftijdsklassen/'

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        regio_111 = Regio.objects.get(regio_nr=111)

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=regio_111)
        ver.save()
        self.ver1 = ver

        # maak de HWL functie
        # de functie is nodig zodat de BB er naartoe kan wisselen om sporter instellingen te doen
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()

        # maak de SEC functie
        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.vereniging = ver
        self.functie_sec.save()

        # maak het lid aan dat SEC wordt
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Secretaris",
                    email="rdesecretaris@gmail.not",
                    geboorte_datum=date(year=1972, month=3, day=4),
                    sinds_datum=date(year=2010, month=11, day=12),
                    bij_vereniging=ver)
        sporter.save()

        self.account_sec = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        self.functie_sec.accounts.add(self.account_sec)

        sporter.account = self.account_sec
        sporter.save()
        self.sporter_100001 = sporter

        # maak een jeugdlid aan
        sporter = Sporter(
                    lid_nr=100002,
                    geslacht="V",
                    voornaam="Ramona",
                    achternaam="de Jeugdschutter",
                    email="",
                    geboorte_datum=date(year=2010, month=3, day=4),
                    sinds_datum=date(year=2010, month=11, day=12),
                    bij_vereniging=ver)
        sporter.save()
        self.sporter_100002 = sporter

        # maak nog een jeugdlid aan, in dezelfde leeftijdsklasse
        sporter = Sporter(
                    lid_nr=100012,
                    geslacht="V",
                    voornaam="Andrea",
                    achternaam="de Jeugdschutter",
                    email="",
                    geboorte_datum=date(year=2010, month=10, day=4),
                    sinds_datum=date(year=2010, month=10, day=10),
                    bij_vereniging=ver)
        sporter.save()
        self.sporter_100012 = sporter

        # geslacht X, zonder keuze wedstrijdgeslacht
        self.sporter_100003 = Sporter.objects.create(
                                    lid_nr=100003,
                                    geslacht="X",
                                    voornaam="X1",
                                    achternaam="de Testerin",
                                    email="",
                                    geboorte_datum=date(year=1972, month=3, day=4),
                                    sinds_datum=date(year=2010, month=11, day=12),
                                    bij_vereniging=ver)

        SporterVoorkeuren.objects.create(
                            sporter=self.sporter_100003,
                            wedstrijd_geslacht_gekozen=False)

        # geslacht X, met keuze wedstrijdgeslacht
        self.sporter_100004 = Sporter.objects.create(
                                    lid_nr=100004,
                                    geslacht="X",
                                    voornaam="X2",
                                    achternaam="de Testerin",
                                    email="",
                                    geboorte_datum=date(year=1972, month=3, day=4),
                                    sinds_datum=date(year=2010, month=11, day=12),
                                    bij_vereniging=ver)

        SporterVoorkeuren.objects.create(
                            sporter=self.sporter_100004,
                            wedstrijd_geslacht_gekozen=True,
                            wedstrijd_geslacht="V")

        # geslacht X, zonder voorkeuren
        self.sporter_100005 = Sporter.objects.create(
                                    lid_nr=100005,
                                    geslacht="X",
                                    voornaam="X3",
                                    achternaam="de Testerin",
                                    email="",
                                    geboorte_datum=date(year=1972, month=3, day=4),
                                    sinds_datum=date(year=2010, month=11, day=12),
                                    bij_vereniging=ver)

    def test_anon(self):
        resp = self.client.get(self.url_leden_leeftijdsklassen)
        self.assert403(resp)

    def test_sec(self):
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        with patch('django.utils.timezone.localtime') as mock_timezone:
            dt = date(year=2020, month=6, day=1)        # <= month 6
            mock_timezone.return_value = dt

            resp = self.client.get(self.url_leden_leeftijdsklassen)


        with patch('django.utils.timezone.localtime') as mock_timezone:
            dt = date(year=2020, month=7, day=1)        # > month 6
            mock_timezone.return_value = dt

            resp = self.client.get(self.url_leden_leeftijdsklassen)



# end of file
