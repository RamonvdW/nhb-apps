# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Spelden import views

app_name = 'Spelden'

# basis = /webwinkel/spelden/

urlpatterns = [

    path('',
         views.BeginView.as_view(),
         name='begin'),

    path('meesterspelden/',
         views.MeesterspeldenView.as_view(),
         name='groep-meesterspelden'),

    path('meesterspelden/hall-of-fame/',
         views.HallOfFameView.as_view(),
         name='meesterspelden-hall-of-fame'),

    path('graadspelden/',
         views.GraadspeldenView.as_view(),
         name='groep-graadspelden'),

    path('tussenspelden/',
         views.TussenspeldenView.as_view(),
         name='groep-tussenspelden'),

    path('target-awards/',
         views.TargetAwardsView.as_view(),
         name='groep-target-awards'),

    path('sterspelden/',
         views.SterspeldenView.as_view(),
         name='groep-sterspelden'),

    path('arrowhead/',
         views.ArrowheadView.as_view(),
         name='groep-arrowhead'),
]

# end of file
