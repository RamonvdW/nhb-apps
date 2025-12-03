# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core.management.base import OutputWrapper
from BasisTypen.models import BoogType, TeamType
from Competitie.models import Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse
from CompKampioenschap.operations.storage_wedstrijdformulieren import (StorageWedstrijdformulieren, StorageError,
                                                                       zet_dirty, iter_dirty_wedstrijdformulieren,
                                                                       aantal_ontbrekende_wedstrijdformulieren_rk_bk)
from GoogleDrive.models import Bestand
from TestHelpers.e2ehelpers import E2EHelpers
import io


class TestCompKampioenschapStorage(E2EHelpers, TestCase):

    """ tests voor de CompKampioenschap module, operations Storage Wedstrijdformulieren """

    def setUp(self):
        pass

    def test_storage(self):
        # test de storage class
        out = OutputWrapper(io.StringIO())
        storage = StorageWedstrijdformulieren(out, 2025, [])

        res = storage._params_to_folder_name(18, True, True)
        self.assertEqual(res, 'Indoor Teams BK')

        res = storage._params_to_folder_name(18, True, False)
        self.assertEqual(res, 'Indoor Teams RK')

        res = storage._params_to_folder_name(25, False, True)
        self.assertEqual(res, '25m1pijl Individueel BK')

        with self.assertRaises(StorageError) as exc:
            res = storage._params_to_folder_name(42, False, False)
        self.assertEqual(str(exc.exception), 'Geen valide afstand: 42')

    def test_zet_dirty(self):
        # object bestaat niet
        Bestand.objects.all().delete()
        zet_dirty(2025, 25, 0, 1, True, True)

        # object bestaat wel
        bestand = Bestand.objects.create(
                                    begin_jaar=2025,
                                    afstand=18,
                                    rayon_nr=0,
                                    is_teams=True,
                                    is_bk=True,
                                    klasse_pk=1,
                                    is_dirty=False)
        zet_dirty(2025, 18, 0, 1, True, True)
        bestand.refresh_from_db()
        self.assertTrue(bestand.is_dirty)

        for obj in iter_dirty_wedstrijdformulieren(2025):
            self.assertEqual(obj.pk, bestand.pk)

    def test_ontbrekend(self):
        comp = Competitie.objects.create(begin_jaar=2025, beschrijving='test', afstand="18")

        boog_x = BoogType.objects.first()
        kl_indiv = CompetitieIndivKlasse.objects.create(
                                    competitie=comp,
                                    boogtype=boog_x,
                                    is_ook_voor_rk_bk=True,
                                    volgorde=1,
                                    beschrijving='test',
                                    min_ag=0)

        team_x = TeamType.objects.first()
        kl_team = CompetitieTeamKlasse.objects.create(
                                    competitie=comp,
                                    is_voor_teams_rk_bk=True,
                                    volgorde=1,
                                    beschrijving='test',
                                    team_type=team_x,
                                    team_afkorting='X',
                                    min_ag=0)

        Bestand.objects.create(
                            begin_jaar=2025,
                            afstand=18,
                            is_teams=True,
                            is_bk=True,
                            klasse_pk=1,
                            is_dirty=False)

        count = aantal_ontbrekende_wedstrijdformulieren_rk_bk(comp)
        self.assertEqual(count, 10)      # 2 klassen x (bk + 4 rk)

        Bestand.objects.create(
                            begin_jaar=2025,
                            afstand=18,
                            is_teams=False,
                            klasse_pk=kl_indiv.pk,
                            is_bk=False,
                            rayon_nr=1)

        Bestand.objects.create(
                            begin_jaar=2025,
                            afstand=18,
                            is_teams=True,
                            klasse_pk=kl_team.pk,
                            is_bk=True)

        count = aantal_ontbrekende_wedstrijdformulieren_rk_bk(comp)
        self.assertEqual(count, 8)

# end of file
