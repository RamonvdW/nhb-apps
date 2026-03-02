# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.models import Competitie, CompetitieIndivKlasse
from Competitie.operations import competities_aanmaken
from CompLaagBond.models import KampBK, DeelnemerBK, CutBK
from Geo.models import Regio
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging


class TestCompLaagBondCli(E2EHelpers, TestCase):
    """ unittests voor de Competitie applicatie, management command check_wedstrijdlocaties """

    def test_check_bk_inschrijvingen(self):

        f1, f2 = self.run_management_command('check_bk_inschrijvingen', '18')
        self.assertTrue('[ERROR] BK niet gevonden' in f1.getvalue())

        competities_aanmaken(2019)

        comp_18 = Competitie.objects.get(afstand=18)
        deelkamp_bk = KampBK.objects.get(competitie=comp_18)

        klasse = CompetitieIndivKlasse.objects.filter(competitie=comp_18, is_ook_voor_rk_bk=True)[0]

        CutBK.objects.create(
            kamp=deelkamp_bk,
            indiv_klasse=klasse)

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

        DeelnemerBK.objects.create(
                        kamp=deelkamp_bk,
                        sporterboog=sporterboog,
                        indiv_klasse=klasse,
                        bij_vereniging=ver)

        f1, f2 = self.run_management_command('check_bk_inschrijvingen', '18')
        self.assertFalse('ERROR' in f1.getvalue())
        self.assertTrue("geen afwijkingen" in f2.getvalue())

        # verbose
        f1, f2 = self.run_management_command('check_bk_inschrijvingen', '18', '--verbose')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertFalse('ERROR' in f1.getvalue())


# end of file
