# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views_planning_rayon, views_rayon_teams

app_name = 'CompRayon'

urlpatterns = [

    # planning rk
    path('planning/<rk_deelcomp_pk>/limieten/',
         views_planning_rayon.RayonLimietenView.as_view(),
         name='rayon-limieten'),

    path('planning/<rk_deelcomp_pk>/',
         views_planning_rayon.RayonPlanningView.as_view(),
         name='rayon-planning'),

    path('planning/wedstrijd/wijzig/<wedstrijd_pk>/',
         views_planning_rayon.WijzigRayonWedstrijdView.as_view(),
         name='rayon-wijzig-wedstrijd'),

    path('planning/wedstrijd/verwijder/<wedstrijd_pk>/',
         views_planning_rayon.VerwijderWedstrijdView.as_view(),
         name='rayon-verwijder-wedstrijd'),


    # RK selectie individueel
    path('lijst-rayonkampioenschappen/<rk_deelcomp_pk>/',
         views_planning_rayon.LijstRkSelectieView.as_view(),
         name='lijst-rk'),

    path('lijst-rayonkampioenschappen/<rk_deelcomp_pk>/bestand/',
         views_planning_rayon.LijstRkSelectieAlsBestandView.as_view(),
         name='lijst-rk-als-bestand'),

    path('lijst-rayonkampioenschappen/wijzig-status-rk-deelnemer/<deelnemer_pk>/',
         views_planning_rayon.WijzigStatusRkSchutterView.as_view(),
         name='wijzig-status-rk-deelnemer'),


    # RK teams
    path('<comp_pk>/teams/<subset>/',
         views_rayon_teams.RayonTeamsAlleView.as_view(),
         name='rayon-teams-alle'),

    path('<rk_deelcomp_pk>/teams/',
         views_rayon_teams.RayonTeamsRKOView.as_view(),
         name='rayon-teams'),
]

# end of file
