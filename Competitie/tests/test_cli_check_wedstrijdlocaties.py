# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from Competitie.definities import DEEL_RK, DEEL_BK
from Competitie.models import Competitie, CompetitieMatch, CompetitieIndivKlasse, CompetitieTeamKlasse, Kampioenschap
from Competitie.operations import competities_aanmaken
from Geo.models import Regio, Rayon
from Locatie.models import WedstrijdLocatie
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import io


class TestCompetitieCliCheckWedstrijdlocaties(E2EHelpers, TestCase):
    """ unittests voor de Competitie applicatie, management command check_wedstrijdlocaties """

    def setUp(self):
        """ initialisatie van de test case """

        competities_aanmaken(2019)

        comp = Competitie.objects.get(afstand='25')
        comp.delete()

        comp = Competitie.objects.get(afstand='18')
        comp.beschrijving = 'comp1'
        comp.save(update_fields=['beschrijving'])

        dummy_datum = '2019-07-01'
        dummy_tijd = '10:00'

        indiv1, indiv2 = CompetitieIndivKlasse.objects.filter(competitie=comp)[:2]
        team1, team2 = CompetitieTeamKlasse.objects.filter(competitie=comp)[:2]

        regio_114 = Regio.objects.get(regio_nr=114)
        rayon_1 = Rayon.objects.get(rayon_nr=1)
        rayon_3 = Rayon.objects.get(rayon_nr=3)

        ver = Vereniging(
                    ver_nr=1234,
                    naam='ver1',
                    plaats='stad1',
                    regio=regio_114)
        ver.save()

        loc = WedstrijdLocatie(
                naam='loc1',
                discipline_indoor=True,
                banen_18m=10,
                banen_25m=0,
                max_sporters_18m=40,
                max_sporters_25m=0,
                adres='adres1',
                plaats='plaats1')
        loc.save()
        loc.verenigingen.add(ver)

        # wed1: indiv, team, loc, ver
        wed1 = CompetitieMatch(
                    competitie=comp,
                    beschrijving='wed1',
                    vereniging=ver,
                    locatie=loc,
                    datum_wanneer=dummy_datum,
                    tijd_begin_wedstrijd=dummy_tijd)
        wed1.save()
        wed1.indiv_klassen.add(indiv1)
        wed1.team_klassen.add(team1)

        loc = WedstrijdLocatie(
                naam='loc2',
                discipline_outdoor=True,
                banen_18m=0,
                banen_25m=0,
                max_sporters_18m=0,
                max_sporters_25m=0,
                buiten_banen=10,
                buiten_max_afstand=100,
                adres='adres2',
                plaats='plaats2')
        loc.save()
        loc.verenigingen.add(ver)
        self.loc2 = loc

        # wed2: loc, ver; geen indiv/teams
        wed2 = CompetitieMatch(
                    competitie=comp,
                    beschrijving='wed2',
                    vereniging=ver,
                    locatie=loc,
                    datum_wanneer=dummy_datum,
                    tijd_begin_wedstrijd=dummy_tijd)
        wed2.save()
        # geen klassen

        # wed2: loc; geen indiv/teams, ver
        wed3 = CompetitieMatch(
                    competitie=comp,
                    beschrijving='wed3',
                    vereniging=None,
                    locatie=loc,
                    datum_wanneer=dummy_datum,
                    tijd_begin_wedstrijd=dummy_tijd)
        wed3.save()

        # wedstrijd met vereniging maar zonder locatie
        ver = Vereniging(
                    ver_nr=1235,
                    naam='ver2',
                    plaats='stad2',
                    regio=regio_114)
        ver.save()

        # wed4: indiv, teams, ver; geen loc
        wed4 = CompetitieMatch(
                    competitie=comp,
                    beschrijving='wed4',
                    vereniging=ver,
                    # locatie=None,
                    datum_wanneer=dummy_datum,
                    tijd_begin_wedstrijd=dummy_tijd)
        wed4.save()
        wed4.indiv_klassen.add(indiv2)
        wed4.team_klassen.add(team2)

        deelkamp_bk = Kampioenschap.objects.get(
                        competitie=comp,
                        deel=DEEL_BK)
        deelkamp_bk.rk_bk_matches.add(wed1)

        deelkamp_rk = Kampioenschap.objects.get(
                        competitie=comp,
                        rayon=rayon_3,
                        deel=DEEL_RK)
        deelkamp_rk.rk_bk_matches.set([wed2, wed3, wed4])

        # deelcomp zonder wedstrijden
        # geen wijzigingen nodig
        deelkamp_rk = Kampioenschap.objects.get(
                        competitie=comp,
                        rayon=rayon_1,
                        deel=DEEL_RK)
        self.assertIsNotNone(deelkamp_rk)

    def test_basis(self):
        # no args
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('check_wedstrijdlocaties', stderr=f1, stdout=f2)

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(23):
            management.call_command('check_wedstrijdlocaties', '--rk', stderr=f1, stdout=f2)
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[WARNING] Geen rk_bk_matches voor RK Rayon 2" in f2.getvalue())
        self.assertTrue("[WARNING] Geen rk_bk_matches voor RK Rayon 1" in f2.getvalue())
        self.assertTrue("zonder banen 18m/25m opgaaf en zonder discipline_indoor en geen vereniging" in f2.getvalue())

        # bk (geen fouten)
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('check_wedstrijdlocaties', '--bk', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue(f2.getvalue() == '')

        # locatie niet zichtbaar
        self.loc2.zichtbaar = False
        self.loc2.save(update_fields=['zichtbaar'])
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(22):
            management.call_command('check_wedstrijdlocaties', '--rk', stderr=f1, stdout=f2)
        self.assertTrue('met zichtbaar=False' in f2.getvalue())

# end of file
