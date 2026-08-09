# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Spelden import view_begin, view_info, view_bestel_stap1, view_bestel_stap2, view_bestel_stap3

app_name = 'Spelden'

# basis = /webwinkel/spelden/

urlpatterns = [

    path('',
         view_begin.BeginView.as_view(),
         name='begin'),

    path('meesterspelden/',
         view_info.MeesterspeldenView.as_view(),
         name='groep-meesterspelden'),

    path('meesterspelden/hall-of-fame/',
         view_info.HallOfFameView.as_view(),
         name='meesterspelden-hall-of-fame'),

    path('graadspelden/',
         view_info.GraadspeldenView.as_view(),
         name='groep-graadspelden'),

    path('tussenspelden/',
         view_info.TussenspeldenView.as_view(),
         name='groep-tussenspelden'),

    path('target-awards/',
         view_info.TargetAwardsView.as_view(),
         name='groep-target-awards'),

    path('sterspelden/',
         view_info.SterspeldenView.as_view(),
         name='groep-sterspelden'),

    path('arrowhead/',
         view_info.ArrowheadView.as_view(),
         name='groep-arrowhead'),


    path('bestel/stap1/',
         view_bestel_stap1.BestelStap1View.as_view(),
         name='bestel-stap1'),

    path('bestel/stap2/',
         view_bestel_stap2.BestelStap2View.as_view(),
         name='bestel-stap2'),

    path('bestel/stap3/',
         view_bestel_stap3.BestelStap3View.as_view(),
         name='bestel-stap3'),
]

# end of file
