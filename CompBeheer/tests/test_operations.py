# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.models import Competitie
from Competitie.test_utils.tijdlijn import zet_competitie_fases
from CompBeheer.operations.toegang import is_competitie_openbaar_voor_rol
from Functie.definities import Rol
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestCompBeheerOperations(E2EHelpers, TestCase):

    """ tests voor de CompBeheer applicatie, module: operations """

    def test_openbaar(self):
        einde_jaar = datetime.date(year=2000, month=12, day=31)
        comp = Competitie(
                    begin_jaar=2000)
        comp.save()
        comp = Competitie.objects.get(pk=comp.pk)

        zet_competitie_fases(comp, 'A', 'A')

        # altijd openbaar voor BB en BKO
        is_openbaar = is_competitie_openbaar_voor_rol(comp, Rol.ROL_BB)
        self.assertTrue(is_openbaar)

        is_openbaar = is_competitie_openbaar_voor_rol(comp, Rol.ROL_BKO)
        self.assertTrue(is_openbaar)

        # altijd openbaar voor RKO/RCL/HWL
        is_openbaar = is_competitie_openbaar_voor_rol(comp, Rol.ROL_RKO)
        self.assertTrue(is_openbaar)

        is_openbaar = is_competitie_openbaar_voor_rol(comp, Rol.ROL_RCL)
        self.assertTrue(is_openbaar)

        is_openbaar = is_competitie_openbaar_voor_rol(comp, Rol.ROL_HWL)
        self.assertTrue(is_openbaar)

        is_openbaar = is_competitie_openbaar_voor_rol(comp, Rol.ROL_WL)
        self.assertFalse(is_openbaar)

        is_openbaar = is_competitie_openbaar_voor_rol(comp, Rol.ROL_SEC)
        self.assertFalse(is_openbaar)

        is_openbaar = is_competitie_openbaar_voor_rol(comp, Rol.ROL_MO)
        self.assertFalse(is_openbaar)

        is_openbaar = is_competitie_openbaar_voor_rol(comp, Rol.ROL_SPORTER)
        self.assertFalse(is_openbaar)

        # vanaf fase B altijd openbaar
        comp.fase_indiv = 'C'
        is_openbaar = is_competitie_openbaar_voor_rol(comp, Rol.ROL_SPORTER)
        self.assertTrue(is_openbaar)


# end of file
