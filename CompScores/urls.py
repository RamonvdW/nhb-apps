# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import view_scores, view_wedstrijden

app_name = 'CompScores'

urlpatterns = [

    # HWL: wedstrijden kaartje
    path('wedstrijden-bij-de-vereniging/',
         view_wedstrijden.WedstrijdenView.as_view(),
         name='wedstrijden'),

    path('waarschijnlijke-deelnemers/<wedstrijd_pk>/',
         view_wedstrijden.WaarschijnlijkeDeelnemersView.as_view(),
         name='waarschijnlijke-deelnemers'),

    path('waarschijnlijke-deelnemers/<wedstrijd_pk>/als-bestand/',
         view_wedstrijden.WaarschijnlijkeDeelnemersAlsBestandView.as_view(),
         name='waarschijnlijke-deelnemers-als-bestand'),

    # HWL: scores kaartje
    path('bij-de-vereniging/',
         view_wedstrijden.WedstrijdenScoresView.as_view(),
         name='wedstrijden-scores'),

    # RCL: scores
    path('regio/<deelcomp_pk>/',
         view_scores.ScoresRegioView.as_view(),
         name='scores-rcl'),

    # RCL: team scores uitkiezen
    path('teams/<deelcomp_pk>/',
         view_scores.ScoresRegioTeamsView.as_view(),
         name='selecteer-team-scores'),


    # HWL/RCL: scores invoeren/bekijken/accorderen voor specifieke wedstrijd
    path('uitslag-invoeren/<wedstrijd_pk>/',
         view_scores.WedstrijdUitslagInvoerenView.as_view(),
         name='uitslag-invoeren'),

    path('uitslag-controleren/<wedstrijd_pk>/',
         view_scores.WedstrijdUitslagControlerenView.as_view(),
         name='uitslag-controleren'),

    path('uitslag-accorderen/<wedstrijd_pk>/',
         view_scores.WedstrijdUitslagControlerenView.as_view(),
         name='uitslag-accorderen'),

    path('bekijk-uitslag/<wedstrijd_pk>/',
         view_scores.WedstrijdUitslagBekijkenView.as_view(),
         name='uitslag-bekijken'),


    path('dynamic/deelnemers-ophalen/',
         view_scores.DynamicDeelnemersOphalenView.as_view(),
         name='dynamic-deelnemers-ophalen'),

    path('dynamic/check-nhbnr/',
         view_scores.DynamicZoekOpBondsnummerView.as_view(),
         name='dynamic-check-nhbnr'),

    path('dynamic/scores-opslaan/',
         view_scores.DynamicScoresOpslaanView.as_view(),
         name='dynamic-scores-opslaan'),
]

# end of file
