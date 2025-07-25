# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.models import Competitie, Regiocompetitie, RegiocompetitieRonde
from Competitie.operations.competitie_opstarten import bepaal_volgende_week_nummer
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from TestHelpers.e2ehelpers import E2EHelpers


class TestCompetitieOperationsL(E2EHelpers, TestCase):

    """ tests voor de Competitie applicatie, functies voor de HWL """

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        regio_111 = Regio.objects.get(regio_nr=111)
        self.cluster = None

        # maak de HWL functie
        func_rcl = maak_functie("RCL 111", "RCL")
        func_rcl.regio = regio_111
        func_rcl.save()

        self.comp = Competitie(
                    beschrijving='test',
                    afstand="18",
                    begin_jaar=2019)
        self.comp.save()

        self.deelcomp = Regiocompetitie(
                            competitie=self.comp,
                            regio=regio_111,
                            functie=func_rcl)
        self.deelcomp.save()

        self.ronde = RegiocompetitieRonde(
                            regiocompetitie=self.deelcomp,
                            cluster=self.cluster,
                            week_nr=1,
                            beschrijving='test ronde 1')
        self.ronde.save()

    def test_volgende_week_nummer(self):
        # zet een jaar zonder week 53
        self.comp.begin_jaar = 2019
        self.comp.save(update_fields=['begin_jaar'])

        self.ronde.week_nr = 1
        self.ronde.save(update_fields=['week_nr'])
        nr = bepaal_volgende_week_nummer(self.deelcomp, self.cluster)
        self.assertEqual(nr, 2)

        self.ronde.week_nr = 30
        self.ronde.save(update_fields=['week_nr'])
        nr = bepaal_volgende_week_nummer(self.deelcomp, self.cluster)
        self.assertEqual(nr, 31)

        self.ronde.week_nr = 52
        self.ronde.save(update_fields=['week_nr'])
        nr = bepaal_volgende_week_nummer(self.deelcomp, self.cluster)
        self.assertEqual(nr, 1)

        # zet een jaar met week 53
        self.comp.begin_jaar = 2020
        self.comp.save(update_fields=['begin_jaar'])

        self.ronde.week_nr = 52
        self.ronde.save(update_fields=['week_nr'])
        nr = bepaal_volgende_week_nummer(self.deelcomp, self.cluster)
        self.assertEqual(nr, 53)

        # geen rondes
        RegiocompetitieRonde.objects.all().delete()
        nr = bepaal_volgende_week_nummer(self.deelcomp, self.cluster)
        self.assertEqual(nr, 37)

        # te veel rondes
        for lp in range(16):
            ronde = RegiocompetitieRonde(
                            regiocompetitie=self.deelcomp,
                            cluster=self.cluster,
                            week_nr=1 + lp,
                            beschrijving='test ronde %s' % (lp + 1))
            ronde.save()
        # for

        nr = bepaal_volgende_week_nummer(self.deelcomp, self.cluster)
        self.assertIsNone(nr)


# end of file
