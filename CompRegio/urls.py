# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import view_planning, view_teams, view_clusters

app_name = 'CompRegio'

urlpatterns = [

    path('clusters/',
         view_clusters.WijzigClustersView.as_view(),
         name='clusters'),

    # planning regio
    path('planning/<deelcomp_pk>/',
         view_planning.RegioPlanningView.as_view(),
         name='regio-planning'),

    path('planning/<deelcomp_pk>/afsluiten/',
         view_planning.AfsluitenRegiocompView.as_view(),
         name='afsluiten-regiocomp'),

    path('planning/<deelcomp_pk>/cluster/<cluster_pk>/',
         view_planning.RegioClusterPlanningView.as_view(),
         name='regio-cluster-planning'),

    path('planning/ronde/<ronde_pk>/',
         view_planning.RegioRondePlanningView.as_view(),
         name='regio-ronde-planning'),

    path('planning/regio-wedstrijden/<ronde_pk>/',
         view_planning.RegioRondePlanningMethode1View.as_view(),
         name='regio-methode1-planning'),

    path('planning/wedstrijd/wijzig/<wedstrijd_pk>/',
         view_planning.WijzigWedstrijdView.as_view(),
         name='regio-wijzig-wedstrijd'),

    path('planning/wedstrijd/verwijder/<wedstrijd_pk>/',
         view_planning.VerwijderWedstrijdView.as_view(),
         name='regio-verwijder-wedstrijd'),


    # RCL schermen
    path('<comp_pk>/instellingen/regio-<regio_nr>/',
         view_teams.RegioInstellingenView.as_view(),
         name='regio-instellingen'),

    path('<comp_pk>/instellingen/globaal/',
         view_teams.RegioInstellingenGlobaalView.as_view(),
         name='regio-instellingen-globaal'),

    path('<comp_pk>/ag-controle/regio-<regio_nr>/',
         view_teams.AGControleView.as_view(),
         name='regio-ag-controle'),

    path('<comp_pk>/teams/<subset>/',
         view_teams.RegioTeamsAlleView.as_view(),
         name='regio-teams-alle'),

    path('<deelcomp_pk>/teams/',
         view_teams.RegioTeamsRCLView.as_view(),
         name='regio-teams'),

    path('<deelcomp_pk>/poules/',
         view_teams.RegioPoulesView.as_view(),
         name='regio-poules'),

    path('poules/<poule_pk>/wijzig/',
         view_teams.WijzigPouleView.as_view(),
         name='wijzig-poule'),

    path('<deelcomp_pk>/team-ronde/',
         view_teams.StartVolgendeTeamRondeView.as_view(),
         name='start-volgende-team-ronde'),
]


# end of file
