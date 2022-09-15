# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from HistComp import views, view_interland

app_name = 'HistComp'

urlpatterns = [

    path('',
         views.HistCompTop.as_view(),
         name='top'),

    path('indiv/<histcomp_pk>/',
         views.HistCompIndivView.as_view(),
         name='indiv'),

    # interland
    path('interland/',
         view_interland.InterlandView.as_view(),
         name='interland'),

    path('interland/als-bestand/<klasse_pk>/',
         view_interland.InterlandAlsBestandView.as_view(),
         name='interland-als-bestand')
]

# end of file
