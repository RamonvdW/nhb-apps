# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.models import Competitie, DeelCompetitie, CompetitieIndivKlasse, CompetitieTeamKlasse, LAAG_RK, KampioenschapTeam, KampioenschapSchutterBoog
from Competitie.operations import competities_aanmaken
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
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

        regio_109 = NhbRegio.objects.get(regio_nr=109)
        boog_r = BoogType.objects.get(afkorting='R')
        comp_25 = Competitie.objects.get(afstand=25)
        deelcomp = DeelCompetitie.objects.get(competitie=comp_25,
                                              laag=LAAG_RK,
                                              nhb_rayon__rayon_nr=3)

        team_klasse = CompetitieTeamKlasse.objects.filter(competitie=comp_25,
                                                     is_voor_teams_rk_bk=True).all()[0]

        indiv_klasse = CompetitieIndivKlasse.objects.filter(competitie=comp_25,
                                                            is_voor_rk_bk=True).all()[0]

        ver = NhbVereniging(
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
                    deelcompetitie=deelcomp,
                    team_klasse=team_klasse,
                    vereniging=ver)
        team.save()

        deelnemer = KampioenschapSchutterBoog(
                        deelcompetitie=deelcomp,
                        sporterboog=sporterboog,
                        indiv_klasse=indiv_klasse,
                        bij_vereniging=ver)
        deelnemer.save()
        team.gekoppelde_schutters.add(deelnemer)

        deelnemer = KampioenschapSchutterBoog(
                        deelcompetitie=deelcomp,
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

# end of file