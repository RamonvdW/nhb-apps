# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views

app_name = 'HistComp'

urlpatterns = [
    path('',
         views.HistCompAlleJarenView.as_view(),
         name='top'),

    path('indiv/<histcomp_pk>/',
         views.HistCompIndivView.as_view(),
         name='indiv'),

    path('team/<histcomp_pk>/',
         views.HistCompTeamView.as_view(),
         name='team')
]

# end of file
