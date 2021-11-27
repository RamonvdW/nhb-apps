# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from BasisTypen.models import IndivWedstrijdklasse
from Competitie.models import Competitie, CompetitieKlasse
from TestHelpers.e2ehelpers import E2EHelpers
import datetime
import io


class TestCompetitieCliCheckKlasse(E2EHelpers, TestCase):
    """ unittests voor de Competitie applicatie, management command check_klasse """

    def setUp(self):
        """ initialisatie van de test case """
        datum = datetime.date(year=2000, month=1, day=1)
        comp = Competitie(
                    beschrijving='Test',
                    afstand='18',
                    begin_jaar=2000,
                    uiterste_datum_lid=datum,
                    begin_aanmeldingen=datum,
                    einde_aanmeldingen=datum,
                    einde_teamvorming=datum,
                    eerste_wedstrijd=datum,
                    laatst_mogelijke_wedstrijd=datum,
                    datum_klassegrenzen_rk_bk_teams=datum,
                    rk_eerste_wedstrijd=datum,
                    rk_laatste_wedstrijd=datum,
                    bk_eerste_wedstrijd=datum,
                    bk_laatste_wedstrijd=datum)
        comp.save()

        indiv_1 = IndivWedstrijdklasse.objects.all()[1]
        indiv_2 = IndivWedstrijdklasse.objects.all()[2]

        CompetitieKlasse(
                competitie=comp,
                indiv=indiv_1,
                min_ag=1.0).save()

        CompetitieKlasse(
                competitie=comp,
                indiv=indiv_2,
                min_ag=2.0).save()

    def test_basis(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('check_klasse', stderr=f1, stdout=f2)

        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('Let op: gebruik --commit' in f2.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('check_klasse', '--commit', stderr=f1, stdout=f2)

        #print("f1: %s" % f1.getvalue())
        #print("f2: %s" % f2.getvalue())

        self.assertTrue(f1.getvalue() == '')
        self.assertTrue(f2.getvalue() == '')


# end of file
