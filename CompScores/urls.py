# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views_scores

app_name = 'CompScores'

urlpatterns = [

    # RCL schermen
    path('regio/<deelcomp_pk>/',
         views_scores.ScoresRegioView.as_view(),
         name='scores-regio'),

    path('teams/<deelcomp_pk>/',
         views_scores.ScoresRegioTeamsView.as_view(),
         name='scores-regio-teams'),


    # HWL/RCL schermen
    path('uitslag-invoeren/<wedstrijd_pk>/',
         views_scores.WedstrijdUitslagInvoerenView.as_view(),
         name='wedstrijd-uitslag-invoeren'),

    path('uitslag-controleren/<wedstrijd_pk>/',
         views_scores.WedstrijdUitslagControlerenView.as_view(),
         name='wedstrijd-uitslag-controleren'),

    path('uitslag-accorderen/<wedstrijd_pk>/',
         views_scores.WedstrijdUitslagControlerenView.as_view(),
         name='wedstrijd-geef-akkoord'),

    path('bekijk-uitslag/<wedstrijd_pk>/',
         views_scores.WedstrijdUitslagBekijkenView.as_view(),
         name='wedstrijd-bekijk-uitslag'),

    path('dynamic/deelnemers-ophalen/',
         views_scores.DynamicDeelnemersOphalenView.as_view(),
         name='dynamic-deelnemers-ophalen'),

    path('dynamic/check-nhbnr/',
         views_scores.DynamicZoekOpBondsnummerView.as_view(),
         name='dynamic-check-nhbnr'),

    path('dynamic/scores-opslaan/',
         views_scores.DynamicScoresOpslaanView.as_view(),
         name='dynamic-scores-opslaan'),

]

# end of file
