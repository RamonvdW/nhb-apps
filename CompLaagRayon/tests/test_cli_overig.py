# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.definities import MUTATIE_INITIEEL
from Competitie.models import (CompetitieIndivKlasse, CompetitieMutatie,
                               KampioenschapIndivKlasseLimiet, KampioenschapSporterBoog, KampioenschapTeam)
from Competitie.tijdlijn import zet_competitie_fase_rk_prep
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompLaagRayonCliOverig(E2EHelpers, TestCase):

    """ tests voor de CompLaagRayon applicatie, overige management commando's """

    testdata = None
    rayon_nr = 3
    regio_nr = 101 + (rayon_nr - 1) * 4
    cut = 4

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()
        data.maak_bondscompetities()

        ver_nr = data.regio_ver_nrs[cls.regio_nr][0]
        data.maak_rk_deelnemers(18, ver_nr, cls.regio_nr)

        # zet de competities in fase J
        zet_competitie_fase_rk_prep(data.comp18)

        klasse = (CompetitieIndivKlasse
                  .objects
                  .filter(competitie=data.comp18,
                          boogtype=data.afkorting2boogtype_nhb['R'],
                          beschrijving__contains="Recurve klasse 6"))[0]

        # zet de cut op 16 voor de gekozen klasse
        KampioenschapIndivKlasseLimiet(
                kampioenschap=data.deelkamp18_rk[cls.rayon_nr],
                indiv_klasse=klasse,
                limiet=cls.cut).save()

        team = KampioenschapTeam(
                    kampioenschap=data.deelkamp18_rk[cls.rayon_nr])
        team.save()
        team.gekoppelde_leden.set(data.comp18_rk_deelnemers[:3])

        team = KampioenschapTeam(
                    kampioenschap=data.deelkamp18_rk[cls.rayon_nr],
                    volg_nr=2)
        team.save()

    def setUp(self):
        pass

    def test_check_rk(self):
        CompetitieMutatie(mutatie=MUTATIE_INITIEEL,
                          kampioenschap=self.testdata.deelkamp18_rk[self.rayon_nr]).save()
        self.verwerk_regiocomp_mutaties()

        # verpruts een ranking/volgorde
        deelnemer = KampioenschapSporterBoog.objects.filter(sporterboog__boogtype__afkorting='R', volgorde=self.cut).order_by('indiv_klasse__volgorde')[0]
        deelnemer.volgorde = 2
        deelnemer.save(update_fields=['volgorde'])

        deelnemer = KampioenschapSporterBoog.objects.filter(sporterboog__boogtype__afkorting='R', volgorde=1).order_by('indiv_klasse__volgorde')[0]
        deelnemer.rank = 0
        deelnemer.save(update_fields=['rank'])

        # maak een dubbele inschrijving
        deelnemer.pk = 0
        deelnemer.volgorde = 100
        deelnemer.save()

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('check_rk_inschrijvingen', '18', self.rayon_nr)
        _ = (f1, f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())

        self.assertTrue('Dubbele sporterboog' in f1.getvalue())
        self.assertTrue('klassen hebben geen afwijkingen' in f2.getvalue())

        # alle klassen hebben fouten
        KampioenschapSporterBoog.objects.exclude(indiv_klasse=deelnemer.indiv_klasse).delete()
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('check_rk_inschrijvingen', '18', self.rayon_nr, '--verbose')
        _ = (f1, f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertFalse('klassen hebben geen afwijkingen' in f2.getvalue())

        # niets gevonden
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('check_rk_inschrijvingen', '25', self.rayon_nr)
        self.assertTrue('Geen deelnemers gevonden' in f2.getvalue())

    def test_recalc(self):
        f1, f2 = self.run_management_command('recalc_rkteam_sterkte')
        _ = (f1, f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())

    def test_check_rk_uitslagen(self):
        f1, f2 = self.run_management_command('check_rk_uitslagen', '18')
        _ = (f1, f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())

        f1, f2 = self.run_management_command('check_rk_uitslagen', '25', '--verbose')
        _ = (f1, f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())


# end of file
