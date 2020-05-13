# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views

app_name = 'Vereniging'

urlpatterns = [

    path('',
         views.OverzichtView.as_view(),
         name='overzicht'),

    path('leden-lijst/',
         views.LedenLijstView.as_view(),
         name='ledenlijst'),

    path('leden-voorkeuren/',
         views.LedenVoorkeurenView.as_view(),
         name='leden-voorkeuren'),

    path('leden-aanmelden/competitie/<comp_pk>/',
         views.LedenAanmeldenView.as_view(),
         name='leden-aanmelden')
]

# end of file
