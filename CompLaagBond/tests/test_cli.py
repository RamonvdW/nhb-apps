# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.definities import DEEL_RK, DEEL_BK
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse,
                               Kampioenschap, KampioenschapTeam, KampioenschapSporterBoog,
                               KampioenschapIndivKlasseLimiet)
from Competitie.operations import competities_aanmaken
from Geo.models import Regio
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import os


class TestCompLaagBondCli(E2EHelpers, TestCase):
    """ unittests voor de Competitie applicatie, management command check_wedstrijdlocaties """

    def test_basis(self):

        f1, f2 = self.run_management_command('bk_lijst_zonder_rk', '18', '--indiv', '--teams')
        self.assertTrue('[ERROR] Geen competitie beschikbaar' in f1.getvalue())

        competities_aanmaken(2019)

        f1, f2 = self.run_management_command('bk_lijst_zonder_rk', '18')
        self.assertTrue('[ERROR] Verplicht: --indiv en/of --teams' in f1.getvalue())

        f1, f2 = self.run_management_command('bk_lijst_zonder_rk', '18', '--indiv',)

        regio_109 = Regio.objects.get(regio_nr=109)
        boog_r = BoogType.objects.get(afkorting='R')
        comp_25 = Competitie.objects.get(afstand=25)
        deelkamp = Kampioenschap.objects.get(competitie=comp_25,
                                             deel=DEEL_RK,
                                             rayon__rayon_nr=3)

        team_klasse = CompetitieTeamKlasse.objects.filter(competitie=comp_25,
                                                          is_voor_teams_rk_bk=True).first()

        indiv_klasse = CompetitieIndivKlasse.objects.filter(competitie=comp_25,
                                                            is_ook_voor_rk_bk=True).first()

        ver = Vereniging(
                    ver_nr=1234,
                    naam='Test ver',
                    regio=regio_109)
        ver.save()

        sporter = Sporter(
                    lid_nr=100001,
                    geslacht='M',
                    voornaam='Ad',
                    achternaam='de Admin',
                    geboorte_datum='1966-06-06',
                    sinds_datum='2020-02-02',
                    adres_code='1234AB56',
                    account=None,
                    bij_vereniging=ver)
        sporter.save()
        sporterboog = SporterBoog(
                            sporter=sporter,
                            boogtype=boog_r,
                            voor_wedstrijd=True)
        sporterboog.save()

        team = KampioenschapTeam(
                    kampioenschap=deelkamp,
                    team_klasse=team_klasse,
                    vereniging=ver)
        team.save()

        deelnemer = KampioenschapSporterBoog(
                        kampioenschap=deelkamp,
                        sporterboog=sporterboog,
                        indiv_klasse=indiv_klasse,
                        bij_vereniging=ver)
        deelnemer.save()
        team.gekoppelde_leden.add(deelnemer)

        deelnemer = KampioenschapSporterBoog(
                        kampioenschap=deelkamp,
                        sporterboog=sporterboog,
                        indiv_klasse=indiv_klasse,
                        bij_vereniging=ver,
                        kampioen_label='hoi')
        deelnemer.save()

        f1, f2 = self.run_management_command('bk_lijst_zonder_rk', '25', '--indiv',)

        f1, f2 = self.run_management_command('bk_lijst_zonder_rk', '25', '--teams')

        f1, f2 = self.run_management_command('bk_lijst_zonder_rk', '18', '--indiv', '--teams')

        # clean-up
        os.remove('bk_lijst.xlsx')

    def test_check_bk_inschrijvingen(self):

        f1, f2 = self.run_management_command('check_bk_inschrijvingen', '18')
        self.assertTrue('[ERROR] BK niet gevonden' in f1.getvalue())

        competities_aanmaken(2019)

        comp_18 = Competitie.objects.get(afstand=18)
        deelkamp_bk = Kampioenschap.objects.get(competitie=comp_18, deel=DEEL_BK)

        klasse = CompetitieIndivKlasse.objects.filter(competitie=comp_18, is_ook_voor_rk_bk=True)[0]

        KampioenschapIndivKlasseLimiet(
            kampioenschap=deelkamp_bk,
            indiv_klasse=klasse).save()

        f1, f2 = self.run_management_command('check_bk_inschrijvingen', '18')
        self.assertTrue("[WARNING] Geen deelnemers gevonden" in f2.getvalue())

        # deelnemer aanmaken
        regio_109 = Regio.objects.get(regio_nr=109)
        boog_r = BoogType.objects.get(afkorting='R')

        ver = Vereniging(
                    ver_nr=1234,
                    naam='Test ver',
                    regio=regio_109)
        ver.save()

        sporter = Sporter(
                    lid_nr=100001,
                    geslacht='M',
                    voornaam='Ad',
                    achternaam='de Admin',
                    geboorte_datum='1966-06-06',
                    sinds_datum='2020-02-02',
                    adres_code='1234AB56',
                    account=None,
                    bij_vereniging=ver)
        sporter.save()
        sporterboog = SporterBoog(
                            sporter=sporter,
                            boogtype=boog_r,
                            voor_wedstrijd=True)
        sporterboog.save()

        deelnemer = KampioenschapSporterBoog(
                        kampioenschap=deelkamp_bk,
                        sporterboog=sporterboog,
                        indiv_klasse=klasse,
                        bij_vereniging=ver)
        deelnemer.save()

        f1, f2 = self.run_management_command('check_bk_inschrijvingen', '18')
        self.assertFalse('ERROR' in f1.getvalue())
        self.assertTrue("geen afwijkingen" in f2.getvalue())

        # verbose
        f1, f2 = self.run_management_command('check_bk_inschrijvingen', '18', '--verbose')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertFalse('ERROR' in f1.getvalue())


# end of file
