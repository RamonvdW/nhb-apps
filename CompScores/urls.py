# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from CompScores import (view_wedstrijden, view_scores_dynamic,
                        view_indiv_scores_regio, view_indiv_scores_invoeren, view_indiv_scores_bekijken,
                        view_team_scores)

app_name = 'CompScores'

# basis = /bondscompetities/scores/

urlpatterns = [

    # HWL: wedstrijden kaartje
    path('wedstrijden-bij-de-vereniging/',
         view_wedstrijden.WedstrijdenView.as_view(),
         name='wedstrijden'),

    # HWL: scores kaartje
    path('bij-de-vereniging/',
         view_wedstrijden.WedstrijdenScoresView.as_view(),
         name='wedstrijden-scores'),


    # RCL: overzicht alle wedstrijden, knop per uitslag
    path('regio/<deelcomp_pk>/',
         view_indiv_scores_regio.ScoresRegioView.as_view(),
         name='scores-rcl'),


    # RCL: team scores koppelen voor de actieve ronde
    path('teams/<deelcomp_pk>/',
         view_team_scores.KoppelScoresRegioTeamsView.as_view(),
         name='selecteer-team-scores'),

    # BKO: team scores koppelen voor een afgesloten ronde
    path('teams/corrigeer-ronde/selecteer/<comp_pk>/',
         view_team_scores.CorrigeerRegioTeamRondeSelecteerView.as_view(),
         name='corrigeer-team-ronde-selecteer'),

    path('teams/corrigeer-ronde/<regiocomp_pk>/<ronde_nr>/',
         view_team_scores.CorrigeerRegioTeamRondeView.as_view(),
         name='corrigeer-team-ronde'),


    # HWL/RCL: scores invoeren voor specifieke wedstrijd
    # RCL: scores bekijken/accorderen voor specifieke wedstrijd
    path('uitslag-invoeren/<match_pk>/',
         view_indiv_scores_invoeren.WedstrijdUitslagInvoerenView.as_view(),
         name='uitslag-invoeren'),

    path('uitslag-controleren/<match_pk>/',
         view_indiv_scores_invoeren.WedstrijdUitslagControlerenView.as_view(),
         name='uitslag-controleren'),

    path('uitslag-accorderen/<match_pk>/',
         view_indiv_scores_invoeren.WedstrijdUitslagControlerenView.as_view(),
         name='uitslag-accorderen'),


    # HWL/WL: scores bekijken voor specifieke wedstrijd
    path('bekijk-uitslag/<match_pk>/',
         view_indiv_scores_bekijken.WedstrijdUitslagBekijkenView.as_view(),
         name='uitslag-bekijken'),


    # helpers voor uitslag invoeren
    path('dynamic/deelnemers-ophalen/',
         view_scores_dynamic.DynamicDeelnemersOphalenView.as_view(),
         name='dynamic-deelnemers-ophalen'),

    path('dynamic/check-bondsnummer/',
         view_scores_dynamic.DynamicZoekOpBondsnummerView.as_view(),
         name='dynamic-check-bondsnummer'),

    path('dynamic/scores-opslaan/',
         view_scores_dynamic.DynamicScoresOpslaanView.as_view(),
         name='dynamic-scores-opslaan'),
]

# end of file
