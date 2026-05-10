# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, RequestFactory
from BasisTypen.models import TeamType
from CompLaagRegio import admin
from CompLaagRegio.models import RegioDeelnemer, RegioTeam, RegioRondeTeam
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompetitieAdmin(E2EHelpers, TestCase):

    """ tests voor de CompLaagRegio applicatie, Admin interface """

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

        team = RegioTeam(
                    regiocomp=deelcomp,
                    vereniging=ver,
                    team_type=type_c)
        team.save()
        cls.team = team

        RegioRondeTeam(team=team).save()

    def setUp(self):
        pass

    def test_filters(self):
        factory = RequestFactory()

        # TeamAGListFilter
        worker = admin.TeamAGListFilter(None,
                                        {'TeamAG': [None]},
                                        RegioDeelnemer,
                                        admin.RegioDeelnemerAdmin)
        _ = worker.queryset(None, RegioDeelnemer.objects.all())

        worker = admin.TeamAGListFilter(None,
                                        {'TeamAG': ['Ontbreekt']},
                                        RegioDeelnemer,
                                        admin.RegioDeelnemerAdmin)
        _ = worker.queryset(None, RegioDeelnemer.objects.all())

        # ZelfstandigIngeschrevenListFilter
        worker = admin.ZelfstandigIngeschrevenListFilter(None,
                                                         {'Zelfstandig': [None]},
                                                         RegioDeelnemer,
                                                         admin.RegioDeelnemerAdmin)
        _ = worker.queryset(None, RegioDeelnemer.objects.all())

        worker = admin.ZelfstandigIngeschrevenListFilter(None,
                                                         {'Zelfstandig': ['Zelf']},
                                                         RegioDeelnemer,
                                                         admin.RegioDeelnemerAdmin)
        _ = worker.queryset(None, RegioDeelnemer.objects.all())

        worker = admin.ZelfstandigIngeschrevenListFilter(None,
                                                         {'Zelfstandig': ['HWL']},
                                                         RegioDeelnemer,
                                                         admin.RegioDeelnemerAdmin)
        _ = worker.queryset(None, RegioDeelnemer.objects.all())

        # IncompleetTeamFilter
        # worker = admin.IncompleetTeamFilter(None,
        #                                     {'incompleet': [None]},
        #                                     KampioenschapTeam,
        #                                     admin.KampioenschapTeamAdmin)
        # _ = worker.queryset(None, KampioenschapTeam.objects.all())

        # worker = admin.IncompleetTeamFilter(None,
        #                                     {'incompleet': ['incompleet']},
        #                                     KampioenschapTeam,
        #                                     admin.KampioenschapTeamAdmin)
        # _ = worker.queryset(None, KampioenschapTeam.objects.all())

        # worker = admin.IncompleetTeamFilter(None,
        #                                     {'incompleet': ['compleet']},
        #                                     KampioenschapTeam,
        #                                     admin.KampioenschapTeamAdmin)
        # _ = worker.queryset(None, KampioenschapTeam.objects.all())

        # TeamTypeFilter
        worker = admin.TeamTypeFilter(None,
                                      {'TeamType': [None]},
                                      RegioTeam,
                                      admin.RegioTeamAdmin)
        qs = worker.queryset(None, RegioTeam.objects.all())
        self.assertEqual(1, qs.count())

        worker = admin.TeamTypeFilter(None,
                                      {'TeamType': ['R2']},
                                      RegioTeam,
                                      admin.RegioTeamAdmin)
        qs = worker.queryset(None, RegioTeam.objects.all())
        self.assertEqual(0, qs.count())

        worker = admin.TeamTypeFilter(None,
                                      {'TeamType': ['C']},
                                      RegioTeam,
                                      admin.RegioTeamAdmin)
        qs = worker.queryset(None, RegioTeam.objects.all())
        self.assertEqual(1, qs.count())

        # RondeTeamVerFilter
        request = factory.get('/beheer/Competitie/regiocompetitierondeteam/')
        worker = admin.RondeTeamVerFilter(request,
                                          {'RondeTeamVer': [self.team.vereniging.ver_nr]},
                                          RegioRondeTeam,
                                          admin.RegioRondeTeamAdmin)
        qs = worker.queryset(None, RegioRondeTeam.objects.all())
        self.assertEqual(1, qs.count())

        request = factory.get('/beheer/Competitie/regiocompetitierondeteam/' +
                              '?team__regiocomp__competitie__id__exact=7')
        worker = admin.RondeTeamVerFilter(request,
                                          {'RondeTeamVer': [None]},
                                          RegioRondeTeam,
                                          admin.RegioRondeTeamAdmin)
        _ = worker.queryset(None, RegioRondeTeam.objects.all())

        request = factory.get('/beheer/Competitie/regiocompetitierondeteam/' +
                              '?team__vereniging__regio__regio_nr__exact=101')
        worker = admin.RondeTeamVerFilter(request,
                                          {'RondeTeamVer': [None]},
                                          RegioRondeTeam,
                                          admin.RegioRondeTeamAdmin)
        tups = worker.lookups(None, admin.RegioRondeTeamAdmin)
        self.assertEqual(tups, [(self.team.vereniging.ver_nr, str(self.team.vereniging))])
        _ = worker.queryset(None, RegioRondeTeam.objects.all())

        request = factory.get('/beheer/Competitie/regiocompetitierondeteam/?RondeTeamType=C')
        worker = admin.RondeTeamVerFilter(request,
                                          {'RondeTeamVer': [None]},
                                          RegioRondeTeam,
                                          admin.RegioRondeTeamAdmin)
        _ = worker.queryset(None, RegioRondeTeam.objects.all())

        # RondeTeamTypeFilter
        worker = admin.RondeTeamTypeFilter(None,
                                           {'RondeTeamType': ['C']},
                                           RegioRondeTeam,
                                           admin.RegioRondeTeamAdmin)
        qs = worker.queryset(None, RegioRondeTeam.objects.all())
        self.assertEqual(1, qs.count())

        worker = admin.RondeTeamTypeFilter(None,
                                           {'RondeTeamType': [None]},
                                           RegioRondeTeam,
                                           admin.RegioRondeTeamAdmin)
        _ = worker.queryset(None, RegioRondeTeam.objects.all())

        # KlasseLimietBoogTypeFilter
        # worker = admin.KlasseLimietBoogTypeFilter(None,
        #                                           {'BoogType': [None]},
        #                                           KampioenschapIndivKlasseLimiet,
        #                                           admin.KampioenschapIndivKlasseLimietAdmin)
        # _ = worker.queryset(None, KampioenschapIndivKlasseLimiet.objects.all())

        # worker = admin.KlasseLimietBoogTypeFilter(None,
        #                                           {'BoogType': ['TR']},
        #                                           KampioenschapIndivKlasseLimiet,
        #                                           admin.KampioenschapIndivKlasseLimietAdmin)
        # _ = worker.queryset(None, KampioenschapIndivKlasseLimiet.objects.all())

# end of file
