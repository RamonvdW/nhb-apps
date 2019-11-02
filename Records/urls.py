# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views

app_name = 'Records'

urlpatterns = [
    path('indiv/<str:gesl>/<str:disc>/<str:lcat>/<str:makl>/',
         views.RecordsIndivZoom5View.as_view(),
         name='indiv-gdlm'),

    path('indiv/<str:gesl>/<str:disc>/<str:lcat>/',
         views.RecordsIndivZoom1234View.as_view(),
         name='indiv-gdl'),

    path('indiv/<str:gesl>/<str:disc>/',
         views.RecordsIndivZoom1234View.as_view(),
         name='indiv-gd'),

    path('indiv/<str:gesl>/',
         views.RecordsIndivZoom1234View.as_view(),
         name='indiv-g'),

    path('indiv/',
         views.RecordsIndivZoom1234View.as_view(),
         name='indiv'),

    path('zoek/',
         views.RecordsZoekView.as_view(),
         name='zoek'),

    path('record-<str:discipline>-<int:nummer>/',
         views.RecordsIndivSpecifiekView.as_view(),
         name='specifiek'),

    path('',
         views.RecordsOverzichtView.as_view(),
         name='overzicht'),

    # TODO: wijzigen/
    # TODO: toevoegen/
]

# end of file
