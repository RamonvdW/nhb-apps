# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from CompLaagRayon import (view_planning, view_formulieren, view_match_info_hwl,
                           view_indiv_rko, view_indiv_hwl, view_indiv_wijzig_status,
                           view_teams_rko, view_teams_hwl, view_bko)

app_name = 'CompLaagRayon'

# basis = /bondscompetities/rk/

urlpatterns = [

    # RKO: planning RK
    path('planning/<deelkamp_pk>/limieten/',
         view_planning.RayonLimietenView.as_view(),
         name='limieten'),

    path('planning/<deelkamp_pk>/',
         view_planning.RayonPlanningView.as_view(),
         name='planning'),

    path('planning/wedstrijd/wijzig/<match_pk>/',
         view_planning.WijzigRayonWedstrijdView.as_view(),
         name='wijzig-wedstrijd'),

    path('planning/wedstrijd/verwijder/<match_pk>/',
         view_planning.VerwijderWedstrijdView.as_view(),
         name='verwijder-wedstrijd'),


    # HWL: individueel
    path('lijst/<deelkamp_pk>/vereniging/',
         view_indiv_hwl.LijstRkSelectieView.as_view(),
         name='lijst-rk-ver'),


    # RKO: individueel
    path('lijst/<deelkamp_pk>/',
         view_indiv_rko.LijstRkSelectieView.as_view(),
         name='lijst-rk'),

    path('lijst/<deelkamp_pk>/bestand/',
         view_indiv_rko.LijstRkSelectieAlsBestandView.as_view(),
         name='lijst-rk-als-bestand'),


    # RK/HWL: individueel
    path('lijst/wijzig-status-rk-deelnemer/<deelnemer_pk>/',
         view_indiv_wijzig_status.WijzigStatusRkDeelnemerView.as_view(),
         name='wijzig-status-rk-deelnemer'),

    # Sporter: deelname bevestigen
    path('wijzig-status-rk-deelname/',
         view_indiv_wijzig_status.SporterWijzigStatusRkDeelnameView.as_view(),
         name='wijzig-status-rk-deelname'),


    # RKO: RK teams
    path('ingeschreven-teams/<comp_pk>/<subset>/',
         view_teams_rko.RayonTeamsAlleView.as_view(),
         name='rayon-teams-alle'),

    path('ingeschreven-teams/<deelkamp_pk>/',
         view_teams_rko.RayonTeamsRKOView.as_view(),
         name='rayon-teams'),


    # HWL: RK teams
    path('teams-vereniging/<deelkamp_pk>/nieuw/',
         view_teams_hwl.WijzigRKTeamsView.as_view(),
         name='teams-rk-nieuw'),

    path('teams-vereniging/<deelkamp_pk>/wijzig/<rk_team_pk>/',
         view_teams_hwl.WijzigRKTeamsView.as_view(),
         name='teams-rk-wijzig'),

    path('teams-vereniging/<deelkamp_pk>/',
         view_teams_hwl.TeamsRkView.as_view(),
         name='teams-rk'),

    path('teams-vereniging/koppelen/<rk_team_pk>/',
         view_teams_hwl.RKTeamsKoppelLedenView.as_view(),
         name='teams-rk-koppelen'),


    # HWL: download lijsten
    path('wedstrijd-informatie/<match_pk>/',
         view_match_info_hwl.RkMatchInfoView.as_view(),
         name='download-formulier'),

    path('download-formulier-teams/<match_pk>/<klasse_pk>/',
         view_formulieren.FormulierTeamsAlsBestandView.as_view(),
         name='formulier-teams-als-bestand'),


    # BKO
    path('<comp_pk>/extra-deelnemer/',
         view_bko.ExtraDeelnemerView.as_view(),
         name='rayon-extra-deelnemer'),

    path('<comp_pk>/extra-deelnemer/<deelnemer_pk>/toevoegen/',
         view_bko.ExtraDeelnemerView.as_view(),
         name='rayon-extra-deelnemer-toevoegen'),

    # BKO
    path('<comp_pk>/blanco-resultaat/',
         view_bko.GeefBlancoResultaatView.as_view(),
         name='geef-blanco-resultaat'),

    path('<comp_pk>/blanco-resultaat/<deelnemer_pk>/toevoegen/',
         view_bko.GeefBlancoResultaatView.as_view(),
         name='geef-deelnemer-blanco-resultaat'),

]

# end of file
