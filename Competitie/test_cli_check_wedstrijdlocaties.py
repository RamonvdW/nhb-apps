# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from BasisTypen.models import IndivWedstrijdklasse, TeamWedstrijdklasse
from Competitie.models import Competitie, DeelCompetitie
from NhbStructuur.models import NhbRegio, NhbRayon, NhbVereniging
from TestHelpers.e2ehelpers import E2EHelpers
from Wedstrijden.models import CompetitieWedstrijdenPlan, CompetitieWedstrijd, WedstrijdLocatie
import io


class TestCompetitieCliCheckWedstrijdlocaties(E2EHelpers, TestCase):
    """ unittests voor de Competitie applicatie, management command check_wedstrijdlocaties """

    def setUp(self):
        """ initialisatie van de test case """

        dummy_datum = '2019-07-01'
        dummy_tijd = '10:00'

        indiv1, indiv2 = IndivWedstrijdklasse.objects.all()[:2]
        team1, team2 = TeamWedstrijdklasse.objects.all()[:2]

        regio_114 = NhbRegio.objects.get(regio_nr=114)
        rayon_1 = NhbRayon.objects.get(rayon_nr=1)
        rayon_2 = NhbRayon.objects.get(rayon_nr=2)
        rayon_3 = NhbRayon.objects.get(rayon_nr=3)

        ver = NhbVereniging(
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

        # een paar wedstrijden
        wed = CompetitieWedstrijd(
                    beschrijving='wed1',
                    vereniging=ver,
                    locatie=loc,
                    datum_wanneer=dummy_datum,
                    tijd_begin_aanmelden=dummy_tijd,
                    tijd_begin_wedstrijd=dummy_tijd,
                    tijd_einde_wedstrijd=dummy_tijd)
        wed.save()
        wed.indiv_klassen.add(indiv1)
        wed.team_klassen.add(team1)

        plan_bk = CompetitieWedstrijdenPlan()
        plan_bk.save()
        plan_bk.wedstrijden.add(wed)

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

        wed = CompetitieWedstrijd(
                    beschrijving='wed2',
                    vereniging=ver,
                    locatie=loc,
                    datum_wanneer=dummy_datum,
                    tijd_begin_aanmelden=dummy_tijd,
                    tijd_begin_wedstrijd=dummy_tijd,
                    tijd_einde_wedstrijd=dummy_tijd)
        wed.save()
        # geen klassen
        plan_rk = CompetitieWedstrijdenPlan()
        plan_rk.save()
        plan_rk.wedstrijden.add(wed)

        # locatie, geen vereniging
        wed = CompetitieWedstrijd(
                    beschrijving='wed3',
                    vereniging=None,
                    locatie=loc,
                    datum_wanneer=dummy_datum,
                    tijd_begin_aanmelden=dummy_tijd,
                    tijd_begin_wedstrijd=dummy_tijd,
                    tijd_einde_wedstrijd=dummy_tijd)
        wed.save()
        plan_rk.wedstrijden.add(wed)

        # wedstrijd met vereniging maar zonder locatie
        ver = NhbVereniging(
                ver_nr=1235,
                naam='ver2',
                plaats='stad2',
                regio=regio_114)
        ver.save()

        wed = CompetitieWedstrijd(
                    beschrijving='wed2',
                    vereniging=ver,
                    # locatie=None,
                    datum_wanneer=dummy_datum,
                    tijd_begin_aanmelden=dummy_tijd,
                    tijd_begin_wedstrijd=dummy_tijd,
                    tijd_einde_wedstrijd=dummy_tijd)
        wed.save()
        wed.indiv_klassen.add(indiv2)
        wed.team_klassen.add(team2)

        plan_rk.wedstrijden.add(wed)

        comp = Competitie(
            beschrijving='comp1',
            afstand='18',
            begin_jaar=2019,
            uiterste_datum_lid=dummy_datum,
            begin_aanmeldingen=dummy_datum,
            einde_aanmeldingen=dummy_datum,
            einde_teamvorming=dummy_datum,
            eerste_wedstrijd=dummy_datum,
            laatst_mogelijke_wedstrijd=dummy_datum,
            datum_klassengrenzen_rk_bk_teams=dummy_datum,
            rk_eerste_wedstrijd=dummy_datum,
            rk_laatste_wedstrijd=dummy_datum,
            bk_eerste_wedstrijd=dummy_datum,
            bk_laatste_wedstrijd=dummy_datum)
        comp.save()

        deelcomp_bk = DeelCompetitie(
                        competitie=comp,
                        laag='BK',
                        plan=plan_bk)
        deelcomp_bk.save()

        deelcomp_rk = DeelCompetitie(
                        competitie=comp,
                        nhb_rayon=rayon_3,
                        laag='RK',
                        plan=plan_rk)
        deelcomp_rk.save()

        # deelcomp zonder plan
        deelcomp_rk = DeelCompetitie(
                        competitie=comp,
                        nhb_rayon=rayon_2,
                        laag='RK')
        deelcomp_rk.save()

        # deelcomp met plan, zonder wedstrijden
        plan_rk_leeg = CompetitieWedstrijdenPlan()
        plan_rk_leeg.save()
        deelcomp_rk = DeelCompetitie(
                        competitie=comp,
                        laag='RK',
                        nhb_rayon=rayon_1,
                        plan=plan_rk_leeg)
        deelcomp_rk.save()

    def test_basis(self):
        # no args
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('check_wedstrijdlocaties', stderr=f1, stdout=f2)

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('check_wedstrijdlocaties', '--rk', stderr=f1, stdout=f2)
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[WARNING] Geen plan of wedstrijden voor deelcompetitie comp1 - Rayon 2" in f2.getvalue())
        self.assertTrue("[WARNING] Geen wedstrijden voor deelcompetitie comp1 - Rayon 1" in f2.getvalue())
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
        with self.assert_max_queries(20):
            management.call_command('check_wedstrijdlocaties', '--rk', stderr=f1, stdout=f2)
        self.assertTrue('met zichtbaar=False' in f2.getvalue())

# end of file
