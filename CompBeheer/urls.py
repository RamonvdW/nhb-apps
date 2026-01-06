# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from CompBeheer import views_bb, views_bko, view_stats, view_overzicht, view_wijzig_datums, view_tijdlijn, views_wf

app_name = 'CompBeheer'

# basis = /bondscompetities/beheer/

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
         view_stats.CompetitieStatistiekView.as_view(),
         name='statistiek'),

    path('wedstrijdformulieren/toestemming/',
         views_wf.ToestemmingView.as_view(),
         name='wf-toestemming-drive'),

    path('wedstrijdformulieren/aanmaken/',
         views_wf.AanmakenView.as_view(),
         name='wf-aanmaken'),

    path('<comp_pk>/klassengrenzen-vaststellen/',
         views_bb.KlassengrenzenVaststellenView.as_view(),
         name='klassengrenzen-vaststellen'),

    path('<comp_pk>/wijzig-datums/',
         view_wijzig_datums.WijzigDatumsView.as_view(),
         name='wijzig-datums'),


    # BKO schermen
    path('<comp_pk>/doorzetten/regio-naar-rk/',
         views_bko.DoorzettenRegioNaarRKView.as_view(),
         name='bko-doorzetten-regio-naar-rk'),

    path('<comp_pk>/doorzetten/rk-indiv-naar-bk/',
         views_bko.DoorzettenIndivRKNaarBKView.as_view(),
         name='bko-rk-indiv-doorzetten-naar-bk'),

    path('<comp_pk>/doorzetten/rk-teams-naar-bk/',
         views_bko.DoorzettenTeamsRKNaarBKView.as_view(),
         name='bko-rk-teams-doorzetten-naar-bk'),

    path('<comp_pk>/doorzetten/bk-indiv-kleine-klassen-zijn-samengevoegd/',
         views_bko.KleineBKKlassenZijnSamengevoegdIndivView.as_view(),
         name='bko-bk-indiv-kleine-klassen'),

    path('<comp_pk>/doorzetten/bk-teams-kleine-klassen-zijn-samengevoegd/',
         views_bko.KleineBKKlassenZijnSamengevoegdTeamsView.as_view(),
         name='bko-bk-teams-kleine-klassen'),

    path('<comp_pk>/doorzetten/bk-indiv-eindstand-bevestigen/',
         views_bko.BevestigEindstandBKIndivView.as_view(),
         name='bko-bevestig-eindstand-bk-indiv'),

    path('<comp_pk>/doorzetten/bk-teams-eindstand-bevestigen/',
         views_bko.BevestigEindstandBKTeamsView.as_view(),
         name='bko-bevestig-eindstand-bk-teams'),

    path('<comp_pk>/doorzetten/rk-bk-teams-klassengrenzen-vaststellen/',
         views_bko.KlassengrenzenVaststellenRkBkTeamsView.as_view(),
         name='klassengrenzen-vaststellen-rk-bk-teams'),


    # landing page voor beheerders
    path('<comp_pk>/',
         view_overzicht.CompetitieBeheerView.as_view(),
         name='overzicht'),

    # tijdlijn
    path('<comp_pk>/tijdlijn/',
         view_tijdlijn.CompetitieTijdlijnView.as_view(),
         name='tijdlijn'),
]

# end of file
