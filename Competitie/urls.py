# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views_bb, views_info, views_klassengrenzen, views_kies, views_overzicht, views_planning_bond

app_name = 'Competitie'

urlpatterns = [

    path('',
         views_kies.CompetitieKiesView.as_view(),
         name='kies'),

    # openbare info
    path('info/',
         views_info.InfoCompetitieView.as_view(),
         name='info-competitie'),

    path('info/leeftijden/',
         views_info.redirect_leeftijden,        # oud; redirects naar nieuw
         name='info-leeftijden'),

    path('<comp_pk>/klassengrenzen/tonen/',
         views_klassengrenzen.KlassengrenzenTonenView.as_view(),
         name='klassengrenzen-tonen'),


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

    path('<comp_pk>/klassengrenzen/vaststellen/',
         views_bb.KlassengrenzenVaststellenView.as_view(),
         name='klassengrenzen-vaststellen'),

    path('<comp_pk>/wijzig-datums/',
         views_bb.WijzigDatumsView.as_view(),
         name='wijzig-datums'),


    # planning bk
    path('planning/bk/<deelcomp_pk>/',
         views_planning_bond.BondPlanningView.as_view(),
         name='bond-planning'),


    # BKO
    path('<comp_pk>/doorzetten/rk/',
         views_planning_bond.DoorzettenNaarRKView.as_view(),
         name='bko-doorzetten-naar-rk'),

    path('<comp_pk>/doorzetten/bk/',
         views_planning_bond.DoorzettenNaarBKView.as_view(),
         name='bko-doorzetten-naar-bk'),

    path('<comp_pk>/doorzetten/voorbij-bk/',
         views_planning_bond.DoorzettenVoorbijBKView.as_view(),
         name='bko-doorzetten-voorbij-bk'),


    # BB
    path('seizoen-afsluiten/',
         views_bb.SeizoenAfsluitenView.as_view(),
         name='bb-seizoen-afsluiten'),


    path('<comp_pk>/',
         views_overzicht.CompetitieOverzichtView.as_view(),
         name='overzicht'),

]

# end of file
