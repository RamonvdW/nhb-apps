# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views, views_special

app_name = 'Records'

urlpatterns = [
    path('indiv/verbeterbaar/',
         views.RecordsVerbeterbaarKiesDisc.as_view(),
         name='indiv-verbeterbaar'),

    path('indiv/verbeterbaar/<str:disc>/',
         views.RecordsVerbeterbaarInDiscipline.as_view(),
         name='indiv-verbeterbaar-disc'),

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

    path('lijst-er/',
         views_special.RecordsSpecialERView.as_view(),
         name='lijst-er'),

    path('lijst-wr/',
         views_special.RecordsSpecialWRView.as_view(),
         name='lijst-wr'),

    path('',
         views.RecordsOverzichtView.as_view(),
         name='overzicht'),
]

# end of file
