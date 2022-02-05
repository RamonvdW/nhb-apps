# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views, views_indiv, views_special, views_verbeterbaar

app_name = 'Records'

urlpatterns = [
    path('indiv/verbeterbaar/',
         views_verbeterbaar.RecordsVerbeterbaarKiesDisc.as_view(),
         name='indiv-verbeterbaar'),

    path('indiv/verbeterbaar/<str:disc>/',
         views_verbeterbaar.RecordsVerbeterbaarInDiscipline.as_view(),
         name='indiv-verbeterbaar-disc'),

    path('indiv/<str:gesl>/<str:disc>/<str:lcat>/<str:makl>/<str:verb>/<str:para>/<int:nummer>/',
         views_indiv.RecordsIndivView.as_view(),
         name='indiv-all'),

    path('indiv/',
         views_indiv.RecordsIndivView.as_view(),
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
