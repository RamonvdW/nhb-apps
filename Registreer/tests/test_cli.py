# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.models import Account
from BasisTypen.definities import GESLACHT_VROUW
from Registreer.definities import REGISTRATIE_FASE_AFGEWEZEN, REGISTRATIE_FASE_COMPLEET
from Registreer.models import GastRegistratie
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging


class TestRegistreerCli(E2EHelpers, TestCase):

    """ tests voor de Registreer application, command line interfaces (CLI) """

    def setUp(self):
        """ initialisatie van de test case """
        ver = Vereniging.objects.first()

        gast = GastRegistratie(
                    lid_nr=1,
                    fase=REGISTRATIE_FASE_AFGEWEZEN,
                    email='gast1@khsn.not',
                    email_is_bevestigd=True,
                    voornaam='Gast1',
                    achternaam='Gast')
        gast.save()

        gast = GastRegistratie(
                    lid_nr=2,
                    fase=REGISTRATIE_FASE_COMPLEET,
                    email='gast2@khsn.not',
                    email_is_bevestigd=True,
                    voornaam='Gast2',
                    achternaam='Gasten',
                    geboorte_datum='1972-01-01',
                    eigen_lid_nummer=3333,
                    club=ver.naam,
                    club_plaats=ver.plaats,
                    wa_id='1234')                   # zorgt voor match
        gast.save()
        gast.refresh_from_db()

        account = Account(
                        username='3333',
                        bevestigde_email=gast.email)
        account.save()

        # lever een match (moet op 2 punten overeen komen)
        sporter = Sporter(
                    lid_nr=3333,                    # zorgt voor 2e match
                    wa_id='1234',                   # zorgt voor 1e match
                    voornaam='Hallo',
                    achternaam='van de Gasten',
                    unaccented_naam='Gast van de Gasten',
                    email=gast.email,
                    geboorte_datum=gast.geboorte_datum,
                    geslacht=gast.geslacht,
                    bij_vereniging=ver,
                    sinds_datum='2000-01-01',
                    account=account)
        sporter.save()

        # lever een bijna-niets match (moet op 2 punten overeen komen)
        sporter = Sporter(
                    lid_nr=3334,
                    wa_id='1234',                   # zorgt voor 1e match
                    voornaam=gast.voornaam,         # zorgt voor 2e match
                    achternaam='van de Geesten',
                    unaccented_naam='Geest van de Geesten',
                    email='geen-match@khsn.not',
                    geboorte_datum='1971-02-03',
                    geslacht=GESLACHT_VROUW,
                    sinds_datum='2000-01-01')
        sporter.save()

    def test_all(self):
        ver = Vereniging.objects.first()

        f1, f2 = self.run_management_command('maak_gebruiker', str(ver.ver_nr), '199901',
                                             'Voornaam', '2000-01-01', 'BB+C')
        self.assertEqual(f1.getvalue(), '')

        f1, f2 = self.run_management_command('maak_gebruiker', '9999', '199901', 'Voornaam', '2000-01-01', 'BB+C')
        self.assertTrue("[ERROR] Vereniging 9999 niet gevonden" in f1.getvalue())

        f1, f2 = self.run_management_command('analyseer_gast_registraties')
        self.assertEqual(f1.getvalue(), '')


# end of file
