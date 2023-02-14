# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from CompBeheer import views_bb, views_bko, view_overzicht, view_wijzig_datums

app_name = 'CompBeheer'

urlpatterns = [

    # base url: bondscompetities/beheer/

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

    path('statistiek/',
         views_bb.CompetitieStatistiekView.as_view(),
         name='statistiek'),

    path('<comp_pk>/klassengrenzen-vaststellen/',
         views_bb.KlassengrenzenVaststellenView.as_view(),
         name='klassengrenzen-vaststellen'),

    path('<comp_pk>/wijzig-datums/',
         view_wijzig_datums.WijzigDatumsView.as_view(),
         name='wijzig-datums'),


    # BKO schermen
    path('<comp_pk>/regio-doorzetten-naar-rk/',
         views_bko.DoorzettenRegioNaarRKView.as_view(),
         name='bko-doorzetten-regio-naar-rk'),

    path('<comp_pk>/rk-indiv-doorzetten-naar-bk/',
         views_bko.DoorzettenIndivRKNaarBKView.as_view(),
         name='bko-rk-indiv-doorzetten-naar-bk'),

    path('<comp_pk>/rk-teams-doorzetten-naar-bk/',
         views_bko.DoorzettenTeamsRKNaarBKView.as_view(),
         name='bko-rk-teams-doorzetten-naar-bk'),

    path('<comp_pk>/bk-indiv-eindstand-bevestigen/',
         views_bko.BevestigEindstandBKIndivView.as_view(),
         name='bko-bevestig-eindstand-bk-indiv'),

    path('<comp_pk>/bk-teams-eindstand-bevestigen/',
         views_bko.BevestigEindstandBKTeamsView.as_view(),
         name='bko-bevestig-eindstand-bk-teams'),

    path('<comp_pk>/rk-bk-teams-klassengrenzen/vaststellen/',
         views_bko.KlassengrenzenTeamsVaststellenView.as_view(),
         name='klassengrenzen-vaststellen-rk-bk-teams'),


    # landing page voor beheerders
    path('<comp_pk>/',
         view_overzicht.CompetitieBeheerView.as_view(),
         name='overzicht')
]

# end of file
