# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Instaptoets import view_toets, view_stats

app_name = 'Instaptoets'

# base: /opleiding/instaptoets/

urlpatterns = [

    path('',
         view_toets.BeginToetsView.as_view(),
         name='begin'),

    path('uitslag/',
         view_toets.ToonUitslagView.as_view(),
         name='toon-uitslag'),

    path('volgende-vraag/',
         view_toets.VolgendeVraagView.as_view(),
         name='volgende-vraag'),

    path('vraag-antwoord/',
         view_toets.OntvangAntwoordView.as_view(),
         name='antwoord'),

    path('stats/',
         view_stats.StatsInstaptoetsView.as_view(),
         name='stats'),
]

# end of file
