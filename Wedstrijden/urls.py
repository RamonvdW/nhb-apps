# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views

app_name = 'Wedstrijden'

urlpatterns = [

    path('locatie/details/<locatie_pk>/',
         views.WedstrijdLocatieDetailsView.as_view(),
         name='locatie-details'),

    path('locatie/details/vereniging/<locatie_pk>/',
         views.WedstrijdLocatieDetailsVerenigingView.as_view(),
         name='locatie-details-vereniging'),

    path('locaties/',
         views.WedstrijdLocatiesView.as_view(),
         name='locaties'),
]

# end of file
