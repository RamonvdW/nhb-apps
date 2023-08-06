# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Records import views, views_indiv, views_special, views_verbeterbaar

app_name = 'Records'

urlpatterns = [

    # verbeterbare records
    path('indiv/verbeterbaar/',
         views_verbeterbaar.RecordsVerbeterbaarKiesDisc.as_view(),
         name='indiv-verbeterbaar'),

    path('indiv/verbeterbaar/<disc>/<makl>/<lcat>/<gesl>/',
         views_verbeterbaar.RecordsVerbeterbaarInDiscipline.as_view(),
         name='indiv-verbeterbaar-disc'),


    # filteren van records
    path('indiv/<gesl>/<disc>/<lcat>/<makl>/<verb>/<para>/<nummer>/',
         views_indiv.RecordsIndivView.as_view(),
         name='indiv-all'),

    path('indiv/',
         views_indiv.RecordsIndivView.as_view(),
         name='indiv'),


    # zoek in de records
    path('zoek/',
         views.RecordsZoekView.as_view(),
         name='zoek'),


    # specifiek record zien
    path('record-<discipline>-<nummer>/',
         views.RecordsIndivSpecifiekView.as_view(),
         name='specifiek'),


    # speciale lijsten
    path('lijst-er/',
         views_special.RecordsSpecialERView.as_view(),
         name='lijst-er'),

    path('lijst-wr/',
         views_special.RecordsSpecialWRView.as_view(),
         name='lijst-wr'),


    # landing page
    path('',
         views.RecordsOverzichtView.as_view(),
         name='overzicht'),
]

# end of file
