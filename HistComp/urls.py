# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views

app_name = 'HistComp'

urlpatterns = [
    path('',
         views.HistCompAlleJarenView.as_view(),
         name='allejaren'),

    path('<jaar>/<comp_type>/<klasse>/indiv/',
         views.HistCompIndivView.as_view(),
         name='indiv'),

    path('<jaar>/<comp_type>/<klasse>/team/',
         views.HistCompTeamView.as_view(),
         name='team')
]

# end of file
