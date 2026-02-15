# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from CompLaagBond import (view_planning, view_indiv_bko, view_teams_bko, view_formulieren, view_kleine_klassen,
                          view_indiv_wijzig_status, view_bk_info_hwl)

app_name = 'CompLaagBond'

# basis = /bondscompetities/bk/

urlpatterns = [

    # BK planning
    path('planning/<deelkamp_pk>/limieten/',
         view_planning.WijzigLimietenView.as_view(),
         name='wijzig-limieten'),

    path('planning/<deelkamp_pk>/',
         view_planning.PlanningView.as_view(),
         name='planning'),

    path('planning/wedstrijd/wijzig/<match_pk>/',
         view_planning.WijzigWedstrijdView.as_view(),
         name='wijzig-wedstrijd'),

    path('planning/wedstrijd/verwijder/<match_pk>/',
         view_planning.VerwijderWedstrijdView.as_view(),
         name='verwijder-wedstrijd'),


    # BKO: individueel
    path('selectie/<deelkamp_pk>/',
         view_indiv_bko.LijstBkSelectieView.as_view(),
         name='bk-selectie'),

    path('selectie/<deelkamp_pk>/bestand/',
         view_indiv_bko.LijstBkSelectieAlsBestandView.as_view(),
         name='bk-selectie-als-bestand'),

    path('kleine-klassen-samenvoegen/<deelkamp_pk>/indiv/',
         view_kleine_klassen.KleineKlassenIndivView.as_view(),
         name='kleine-klassen-samenvoegen-indiv'),

    path('verplaats-deelnemer/',
         view_kleine_klassen.VerplaatsDeelnemerView.as_view(),
         name='verplaats-deelnemer'),

    # BKO
    path('selectie/wijzig-status-bk-deelnemer/<deelnemer_pk>/',
         view_indiv_wijzig_status.WijzigStatusBkDeelnemerView.as_view(),
         name='wijzig-status-bk-deelnemer'),

    # Sporter: deelname bevestigen
    path('wijzig-status-bk-deelname/',
         view_indiv_wijzig_status.SporterWijzigStatusBkDeelnameView.as_view(),
         name='wijzig-status-bk-deelname'),


    # BKO: teams
    path('teams/wijzig-status-bk-team/',
         view_teams_bko.WijzigStatusBkTeamView.as_view(),
         name='bk-teams-wijzig-status'),

    path('teams/<deelkamp_pk>/',
         view_teams_bko.LijstBkTeamsView.as_view(),
         name='bk-teams'),


    # BKO: download formulieren
    path('formulieren/indiv/<deelkamp_pk>/',
         view_formulieren.DownloadBkIndivFormulierenView.as_view(),
         name='formulier-indiv-lijst'),

    path('formulieren/teams/download/<match_pk>/<klasse_pk>/',
         view_formulieren.FormulierBkTeamsAlsBestandView.as_view(),
         name='formulier-teams-als-bestand'),

    # path('formulieren/teams/<deelkamp_pk>/',
    #      view_formulieren.DownloadBkTeamsFormulierenView.as_view(),
    #      name='formulier-teams-lijst'),


    # HWL/WL: wedstrijd informatie
    path('wedstrijd-informatie/<match_pk>/',
         view_bk_info_hwl.MatchInformatieView.as_view(),
         name='bk-match-informatie'),
]

# end of file
