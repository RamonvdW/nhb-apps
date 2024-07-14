# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from CompLaagRegio import (view_clusters, view_planning, view_instellingen, view_teams_rcl, view_poules, view_teams_hwl,
                           view_keuze_zeven_wedstrijden, view_wieschietwaar, view_waarschijnlijke_deelnemers,
                           view_medailles, view_sporter_deelname)

app_name = 'CompLaagRegio'

# basis = /bondscompetities/regio/

urlpatterns = [

    path('waarschijnlijke-deelnemers/<match_pk>/',
         view_waarschijnlijke_deelnemers.WaarschijnlijkeDeelnemersView.as_view(),
         name='waarschijnlijke-deelnemers'),

    path('waarschijnlijke-deelnemers/<match_pk>/als-bestand/',
         view_waarschijnlijke_deelnemers.WaarschijnlijkeDeelnemersAlsBestandView.as_view(),
         name='waarschijnlijke-deelnemers-als-bestand'),


    # RCL: planning regio
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

    path('planning/wedstrijd/wijzig/<match_pk>/',
         view_planning.WijzigWedstrijdView.as_view(),
         name='regio-wijzig-wedstrijd'),

    path('planning/wedstrijd/verwijder/<match_pk>/',
         view_planning.VerwijderWedstrijdView.as_view(),
         name='regio-verwijder-wedstrijd'),


    # RCL: clusters
    path('clusters/',
         view_clusters.WijzigClustersView.as_view(),
         name='clusters'),


    # RCL: instellingen
    path('instellingen/<comp_pk>/regio-<regio_nr>/',
         view_instellingen.RegioInstellingenView.as_view(),
         name='regio-instellingen'),

    path('instellingen/<comp_pk>/globaal/',
         view_instellingen.RegioInstellingenGlobaalView.as_view(),
         name='regio-instellingen-globaal'),


    # RCL: teams
    path('<comp_pk>/ag-controle/regio-<regio_nr>/',
         view_teams_rcl.AGControleView.as_view(),
         name='regio-ag-controle'),

    path('<deelcomp_pk>/teams/als-bestand/',
         view_teams_rcl.RegioTeamsAlsBestand.as_view(),
         name='regio-teams-als-bestand'),

    path('<comp_pk>/teams/<subset>/',
         view_teams_rcl.RegioTeamsAlleView.as_view(),
         name='regio-teams-alle'),

    path('<deelcomp_pk>/teams/',
         view_teams_rcl.RegioTeamsRCLView.as_view(),
         name='regio-teams'),


    # RCL: poules
    path('poules/<deelcomp_pk>/',
         view_poules.RegioPoulesView.as_view(),
         name='regio-poules'),

    path('poules/wijzig/<poule_pk>/',
         view_poules.WijzigPouleView.as_view(),
         name='wijzig-poule'),

    path('<deelcomp_pk>/team-ronde/',
         view_teams_rcl.StartVolgendeTeamRondeView.as_view(),
         name='start-volgende-team-ronde'),


    # HWL
    path('wie-schiet-waar/<deelcomp_pk>/',
         view_wieschietwaar.WieSchietWaarView.as_view(),
         name='wie-schiet-waar'),

    # HWL: teams
    path('teams-vereniging/wijzig-aanvangsgemiddelde/<deelnemer_pk>/',
         view_teams_hwl.WijzigTeamAGView.as_view(),
         name='wijzig-ag'),

    path('teams-vereniging/koppelen/<team_pk>/',
         view_teams_hwl.TeamsRegioKoppelLedenView.as_view(),
         name='teams-regio-koppelen'),

    path('teams-vereniging/<deelcomp_pk>/wijzig/<team_pk>/',
         view_teams_hwl.WijzigRegioTeamsView.as_view(),
         name='teams-regio-wijzig'),

    path('teams-vereniging/<deelcomp_pk>/invallers/',
         view_teams_hwl.TeamsRegioInvallersView.as_view(),
         name='teams-regio-invallers'),

    path('teams-vereniging/invallers-koppelen/<ronde_team_pk>/',
         view_teams_hwl.TeamsRegioInvallersKoppelLedenView.as_view(),
         name='teams-regio-invallers-koppelen'),

    path('teams-vereniging/<deelcomp_pk>/',
         view_teams_hwl.TeamsRegioView.as_view(),
         name='teams-regio'),

    # sporter / HWL
    path('keuze-zeven-wedstrijden/<deelnemer_pk>/',
         view_keuze_zeven_wedstrijden.KeuzeZevenWedstrijdenView.as_view(),
         name='keuze-zeven-wedstrijden'),

    path('voorkeur-rk/',
         view_sporter_deelname.SporterVoorkeurRkView.as_view(),
         name='voorkeur-rk'),

    # RCL
    path('medailles/regio-<regio>/',
         view_medailles.ToonMedailles.as_view(),
         name='medailles')
]


# end of file
