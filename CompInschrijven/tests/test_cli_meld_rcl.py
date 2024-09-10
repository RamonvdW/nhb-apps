# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType, ORGANISATIE_WA
from Competitie.models import Competitie, CompetitieIndivKlasse, Regiocompetitie, RegiocompetitieSporterBoog
from Competitie.operations import competities_aanmaken
from Competitie.test_utils.tijdlijn import zet_competitie_fase_regio_wedstrijden
from Geo.models import Regio
from Sporter.models import Sporter, SporterBoog
from Taken.models import Taak
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from unittest.mock import patch
from datetime import datetime, date


class TestCompInschrijvenCliMeldRcl(E2EHelpers, TestCase):
    """ unittests voor de CompInschrijven applicatie, management command meld_rcl_nieuwe_inschrijvingen """

    def setUp(self):
        """ initialisatie van de test case """

        # comp en deelcomp nodig
        competities_aanmaken(2019)

        self.regio_103 = Regio.objects.get(regio_nr=103)
        self.boog_bb = BoogType.objects.get(afkorting='BB', organisatie=ORGANISATIE_WA)

        self.comp_18m = Competitie.objects.get(afstand='18')

        self.deelcomp103_18m = (Regiocompetitie
                                .objects
                                .get(competitie=self.comp_18m,
                                     regio__regio_nr=103))

        self.indiv_klasse_bb = (CompetitieIndivKlasse
                                .objects
                                .filter(competitie=self.comp_18m,
                                        boogtype=self.boog_bb,
                                        is_ook_voor_rk_bk=False)
                                .all())[0]

        # maak een test vereniging
        self.ver = Vereniging(
                        naam="Grote Club",
                        ver_nr="1000",
                        regio=self.regio_103)
        self.ver.save()

        self.sporter = Sporter(
                            lid_nr=100001,
                            geslacht="M",
                            voornaam='Gert',
                            achternaam="Pijlhaler",
                            email="pijlhaler@test.not",
                            geboorte_datum=date(year=1972, month=3, day=4),
                            sinds_datum=date(year=2010, month=11, day=12),
                            bij_vereniging=self.ver)
        self.sporter.save()

        self.sporterboog = SporterBoog(
                                sporter=self.sporter,
                                boogtype=self.boog_bb,
                                voor_wedstrijd=True)
        self.sporterboog.save()

        self.beheerder = self.e2e_create_account('100002', 'beheerder@test.not', 'Beheerdertje')

    def test_basis(self):
        # TODO: vervang door evaluatie_datum.zet_test_datum('2019-08-01') uit Competitie/tijdlijn
        with patch('django.utils.timezone.localtime') as mock_timezone:
            # te vroeg/laat om een mail te sturen
            dt = datetime(year=2000, month=1, day=1, hour=19)
            mock_timezone.return_value = dt
            f1, f2 = self.run_management_command('meld_rcl_nieuwe_inschrijvingen')
            self.assertEqual(f1.getvalue(), '')
            self.assertTrue('skipping want uur=19' in f2.getvalue())

            # competitie niet in fase F
            dt = datetime(year=2000, month=1, day=1, hour=8)
            mock_timezone.return_value = dt
            f1, f2 = self.run_management_command('meld_rcl_nieuwe_inschrijvingen')
            self.assertEqual(f1.getvalue(), '')
            self.assertTrue('[INFO] Vandaag is 2000-01-01; gisteren is 1999-12-31' in f2.getvalue())

            # TODO: test fase D toevoegen

            # juiste fase en tijdstip, maar geen nieuwe inschrijvingen
            zet_competitie_fase_regio_wedstrijden(self.comp_18m)
            f1, f2 = self.run_management_command('meld_rcl_nieuwe_inschrijvingen')
            self.assertEqual(f1.getvalue(), '')
            self.assertTrue("[INFO] Aantal nieuwe taken aangemaakt voor de RCL's: 0" in f2.getvalue())

            dt_gister = date(year=2000, month=1, day=1)
            dt = datetime(year=2000, month=1, day=2, hour=8)
            mock_timezone.return_value = dt

            # schrijf iemand gisteren in
            deelnemer = RegiocompetitieSporterBoog(
                            regiocompetitie=self.deelcomp103_18m,
                            sporterboog=self.sporterboog,
                            bij_vereniging=self.ver,
                            indiv_klasse=self.indiv_klasse_bb)
            deelnemer.save()
            deelnemer.wanneer_aangemeld = dt_gister
            deelnemer.save(update_fields=['wanneer_aangemeld'])

            self.assertEqual(0, Taak.objects.count())

            f1, f2 = self.run_management_command('meld_rcl_nieuwe_inschrijvingen')
            self.assertEqual(f1.getvalue(), '')
            self.assertTrue('[INFO] RCL Regio 103 Indoor: 1 nieuwe aanmeldingen' in f2.getvalue())

            # zoek de taak op en controleer de inhoud
            self.assertEqual(1, Taak.objects.count())
            taak = Taak.objects.first()
            self.assertTrue('[100001] Gert Pijlhaler' in taak.beschrijving)
            self.assertTrue(' zelfstandig aangemeld' in taak.beschrijving)

            # nog een keer, terwijl de taak al bestaat
            f1, f2 = self.run_management_command('meld_rcl_nieuwe_inschrijvingen')
            self.assertEqual(f1.getvalue(), '')
            self.assertTrue("[INFO] Aantal nieuwe taken aangemaakt voor de RCL's: 0" in f2.getvalue())
            self.assertEqual(1, Taak.objects.count())

            # nog een keer, met de taak afgehandeld
            taak.is_afgerond = True
            taak.save(update_fields=['is_afgerond'])
            f1, f2 = self.run_management_command('meld_rcl_nieuwe_inschrijvingen')
            self.assertEqual(f1.getvalue(), '')
            self.assertTrue("[INFO] Aantal nieuwe taken aangemaakt voor de RCL's: 0" in f2.getvalue())
            self.assertEqual(1, Taak.objects.count())

            # verander wie de sporter ingeschreven heeft
            deelnemer.aangemeld_door = self.beheerder
            deelnemer.save(update_fields=['aangemeld_door'])

            f1, f2 = self.run_management_command('meld_rcl_nieuwe_inschrijvingen')
            # print("f1: %s" % f1.getvalue())
            # print("f2: %s" % f2.getvalue())
            self.assertEqual(f1.getvalue(), '')
            self.assertTrue('[INFO] RCL Regio 103 Indoor: 1 nieuwe aanmeldingen' in f2.getvalue())
            self.assertEqual(2, Taak.objects.count())

            taak2 = Taak.objects.exclude(pk=taak.pk).first()
            # print(taak2.beschrijving)
            self.assertTrue(' aangemeld door: 100002 Beheerdertje' in taak2.beschrijving)

# end of file
