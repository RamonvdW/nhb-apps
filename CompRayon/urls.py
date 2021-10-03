# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import view_planning, view_teams_rko, view_teams_hwl

app_name = 'CompRayon'

urlpatterns = [

    # RKO: planning RK
    path('planning/<rk_deelcomp_pk>/limieten/',
         view_planning.RayonLimietenView.as_view(),
         name='rayon-limieten'),

    path('planning/<rk_deelcomp_pk>/',
         view_planning.RayonPlanningView.as_view(),
         name='rayon-planning'),

    path('planning/wedstrijd/wijzig/<wedstrijd_pk>/',
         view_planning.WijzigRayonWedstrijdView.as_view(),
         name='rayon-wijzig-wedstrijd'),

    path('planning/wedstrijd/verwijder/<wedstrijd_pk>/',
         view_planning.VerwijderWedstrijdView.as_view(),
         name='rayon-verwijder-wedstrijd'),


    # RK selectie individueel
    path('lijst-rayonkampioenschappen/<rk_deelcomp_pk>/',
         view_planning.LijstRkSelectieView.as_view(),
         name='lijst-rk'),

    path('lijst-rayonkampioenschappen/<rk_deelcomp_pk>/bestand/',
         view_planning.LijstRkSelectieAlsBestandView.as_view(),
         name='lijst-rk-als-bestand'),

    path('lijst-rayonkampioenschappen/wijzig-status-rk-deelnemer/<deelnemer_pk>/',
         view_planning.WijzigStatusRkSchutterView.as_view(),
         name='wijzig-status-rk-deelnemer'),


    # RKO: RK teams
    path('ingeschreven-teams/<comp_pk>/<subset>/',
         view_teams_rko.RayonTeamsAlleView.as_view(),
         name='rayon-teams-alle'),

    path('ingeschreven-teams/<rk_deelcomp_pk>/',
         view_teams_rko.RayonTeamsRKOView.as_view(),
         name='rayon-teams'),


    # HWL: RK teams
    path('teams-vereniging/<rk_deelcomp_pk>/nieuw/',
         view_teams_hwl.WijzigRKTeamsView.as_view(),
         name='teams-rk-nieuw'),

    path('teams-vereniging/<rk_deelcomp_pk>/wijzig/<rk_team_pk>/',
         view_teams_hwl.WijzigRKTeamsView.as_view(),
         name='teams-rk-wijzig'),

    path('teams-vereniging/<rk_deelcomp_pk>/',
         view_teams_hwl.TeamsRkView.as_view(),
         name='teams-rk'),

    path('teams-vereniging/koppelen/<rk_team_pk>/',
         view_teams_hwl.RKTeamsKoppelLedenView.as_view(),
         name='teams-rk-koppelen'),

]

# end of file
