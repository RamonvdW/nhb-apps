# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from CompBeheer import views_bb, views_bko

app_name = 'CompBeheer'

urlpatterns = [

    # base url: bondscompetities/manage/

    # BB schermen
    path('instellingen-volgende-competitie/',
         views_bb.InstellingenVolgendeCompetitieView.as_view(),
         name='instellingen-volgende-competitie'),

    path('aanmaken/',
         views_bb.CompetitieAanmakenView.as_view(),
         name='aanmaken'),

    path('ag-vaststellen/<afstand>/',
         views_bb.AGVaststellenView.as_view(),
         name='ag-vaststellen-afstand'),

    path('seizoen-afsluiten/',
         views_bb.SeizoenAfsluitenView.as_view(),
         name='bb-seizoen-afsluiten'),

    path('<comp_pk>/klassengrenzen-vaststellen/',
         views_bb.KlassengrenzenVaststellenView.as_view(),
         name='klassengrenzen-vaststellen'),

    path('<comp_pk>/wijzig-datums/',
         views_bb.WijzigDatumsView.as_view(),
         name='wijzig-datums'),


    # BKO schermen
    path('<comp_pk>/doorzetten-rk/',
         views_bko.DoorzettenNaarRKView.as_view(),
         name='bko-doorzetten-naar-rk'),

    path('<comp_pk>/doorzetten-bk/',
         views_bko.DoorzettenNaarBKView.as_view(),
         name='bko-doorzetten-naar-bk'),

    path('<comp_pk>/doorzetten-voorbij-bk/',
         views_bko.DoorzettenVoorbijBKView.as_view(),
         name='bko-doorzetten-voorbij-bk'),
]

# end of file
