# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, RequestFactory
from BasisTypen.models import TeamType
from Competitie import admin
from Competitie.models import (RegiocompetitieSporterBoog, RegiocompetitieTeam, RegiocompetitieRondeTeam,
                               KampioenschapTeam, KampioenschapIndivKlasseLimiet)
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompetitieAdmin(E2EHelpers, TestCase):

    """ tests voor de Competitie applicatie, Admin interface """

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()
        data.maak_bondscompetities()

        regio_nr = 101
        ver_nr = data.regio_ver_nrs[regio_nr][0]
        ver = cls.testdata.vereniging[ver_nr]
        deelcomp = cls.testdata.deelcomp18_regio[regio_nr]

        type_c = TeamType.objects.get(afkorting='C')

        team = RegiocompetitieTeam(
                    regiocompetitie=deelcomp,
                    vereniging=ver,
                    team_type=type_c)
        team.save()
        cls.team = team

        RegiocompetitieRondeTeam(team=team).save()

    def setUp(self):
        pass

    def test_filters(self):
        factory = RequestFactory()

        # TeamAGListFilter
        worker = admin.TeamAGListFilter(None,
                                        {'TeamAG': [None]},
                                        RegiocompetitieSporterBoog,
                                        admin.RegiocompetitieSporterBoogAdmin)
        _ = worker.queryset(None, RegiocompetitieSporterBoog.objects.all())

        worker = admin.TeamAGListFilter(None,
                                        {'TeamAG': ['Ontbreekt']},
                                        RegiocompetitieSporterBoog,
                                        admin.RegiocompetitieSporterBoogAdmin)
        _ = worker.queryset(None, RegiocompetitieSporterBoog.objects.all())

        # ZelfstandigIngeschrevenListFilter
        worker = admin.ZelfstandigIngeschrevenListFilter(None,
                                                         {'Zelfstandig': [None]},
                                                         RegiocompetitieSporterBoog,
                                                         admin.RegiocompetitieSporterBoogAdmin)
        _ = worker.queryset(None, RegiocompetitieSporterBoog.objects.all())

        worker = admin.ZelfstandigIngeschrevenListFilter(None,
                                                         {'Zelfstandig': ['Zelf']},
                                                         RegiocompetitieSporterBoog,
                                                         admin.RegiocompetitieSporterBoogAdmin)
        _ = worker.queryset(None, RegiocompetitieSporterBoog.objects.all())

        worker = admin.ZelfstandigIngeschrevenListFilter(None,
                                                         {'Zelfstandig': ['HWL']},
                                                         RegiocompetitieSporterBoog,
                                                         admin.RegiocompetitieSporterBoogAdmin)
        _ = worker.queryset(None, RegiocompetitieSporterBoog.objects.all())

        # IncompleetTeamFilter
        worker = admin.IncompleetTeamFilter(None,
                                            {'incompleet': [None]},
                                            KampioenschapTeam,
                                            admin.KampioenschapTeamAdmin)
        _ = worker.queryset(None, KampioenschapTeam.objects.all())

        worker = admin.IncompleetTeamFilter(None,
                                            {'incompleet': ['incompleet']},
                                            KampioenschapTeam,
                                            admin.KampioenschapTeamAdmin)
        _ = worker.queryset(None, KampioenschapTeam.objects.all())

        worker = admin.IncompleetTeamFilter(None,
                                            {'incompleet': ['compleet']},
                                            KampioenschapTeam,
                                            admin.KampioenschapTeamAdmin)
        _ = worker.queryset(None, KampioenschapTeam.objects.all())

        # TeamTypeFilter
        worker = admin.TeamTypeFilter(None,
                                      {'TeamType': [None]},
                                      RegiocompetitieTeam,
                                      admin.RegiocompetitieTeamAdmin)
        qs = worker.queryset(None, RegiocompetitieTeam.objects.all())
        self.assertEqual(1, qs.count())

        worker = admin.TeamTypeFilter(None,
                                      {'TeamType': ['R2']},
                                      RegiocompetitieTeam,
                                      admin.RegiocompetitieTeamAdmin)
        qs = worker.queryset(None, RegiocompetitieTeam.objects.all())
        self.assertEqual(0, qs.count())

        worker = admin.TeamTypeFilter(None,
                                      {'TeamType': ['C']},
                                      RegiocompetitieTeam,
                                      admin.RegiocompetitieTeamAdmin)
        qs = worker.queryset(None, RegiocompetitieTeam.objects.all())
        self.assertEqual(1, qs.count())

        # RondeTeamVerFilter
        request = factory.get('/beheer/Competitie/regiocompetitierondeteam/')
        worker = admin.RondeTeamVerFilter(request,
                                          {'RondeTeamVer': [self.team.vereniging.ver_nr]},
                                          RegiocompetitieRondeTeam,
                                          admin.RegiocompetitieRondeTeamAdmin)
        qs = worker.queryset(None, RegiocompetitieRondeTeam.objects.all())
        self.assertEqual(1, qs.count())

        request = factory.get('/beheer/Competitie/regiocompetitierondeteam/' +
                              '?team__regiocompetitie__competitie__id__exact=7')
        worker = admin.RondeTeamVerFilter(request,
                                          {'RondeTeamVer': [None]},
                                          RegiocompetitieRondeTeam,
                                          admin.RegiocompetitieRondeTeamAdmin)
        _ = worker.queryset(None, RegiocompetitieRondeTeam.objects.all())

        request = factory.get('/beheer/Competitie/regiocompetitierondeteam/' +
                              '?team__vereniging__regio__regio_nr__exact=101')
        worker = admin.RondeTeamVerFilter(request,
                                          {'RondeTeamVer': [None]},
                                          RegiocompetitieRondeTeam,
                                          admin.RegiocompetitieRondeTeamAdmin)
        tups = worker.lookups(None, admin.RegiocompetitieRondeTeamAdmin)
        self.assertEqual(tups, [(self.team.vereniging.ver_nr, str(self.team.vereniging))])
        _ = worker.queryset(None, RegiocompetitieRondeTeam.objects.all())

        request = factory.get('/beheer/Competitie/regiocompetitierondeteam/?RondeTeamType=C')
        worker = admin.RondeTeamVerFilter(request,
                                          {'RondeTeamVer': [None]},
                                          RegiocompetitieRondeTeam,
                                          admin.RegiocompetitieRondeTeamAdmin)
        _ = worker.queryset(None, RegiocompetitieRondeTeam.objects.all())

        # RondeTeamTypeFilter
        worker = admin.RondeTeamTypeFilter(None,
                                           {'RondeTeamType': ['C']},
                                           RegiocompetitieRondeTeam,
                                           admin.RegiocompetitieRondeTeamAdmin)
        qs = worker.queryset(None, RegiocompetitieRondeTeam.objects.all())
        self.assertEqual(1, qs.count())

        worker = admin.RondeTeamTypeFilter(None,
                                           {'RondeTeamType': [None]},
                                           RegiocompetitieRondeTeam,
                                           admin.RegiocompetitieRondeTeamAdmin)
        _ = worker.queryset(None, RegiocompetitieRondeTeam.objects.all())

        # KlasseLimietBoogTypeFilter
        worker = admin.KlasseLimietBoogTypeFilter(None,
                                                  {'BoogType': [None]},
                                                  KampioenschapIndivKlasseLimiet,
                                                  admin.KampioenschapIndivKlasseLimietAdmin)
        _ = worker.queryset(None, KampioenschapIndivKlasseLimiet.objects.all())

        worker = admin.KlasseLimietBoogTypeFilter(None,
                                                  {'BoogType': ['TR']},
                                                  KampioenschapIndivKlasseLimiet,
                                                  admin.KampioenschapIndivKlasseLimietAdmin)
        _ = worker.queryset(None, KampioenschapIndivKlasseLimiet.objects.all())

# end of file
