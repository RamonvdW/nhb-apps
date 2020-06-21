# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views_bb, views_planning, views_overzicht

app_name = 'Competitie'

urlpatterns = [

    path('',
         views_overzicht.CompetitieOverzichtView.as_view(),
         name='overzicht'),

    path('instellingen-volgende-competitie/',
         views_bb.InstellingenVolgendeCompetitieView.as_view(),
         name='instellingen-volgende-competitie'),

    path('aanmaken/',
         views_bb.CompetitieAanmakenView.as_view(),
         name='aanmaken'),

    path('ag-vaststellen/',
         views_bb.AGVaststellenView.as_view(),
         name='ag-vaststellen'),

    path('klassegrenzen/vaststellen/<afstand>/',
         views_bb.KlassegrenzenVaststellenView.as_view(),
         name='klassegrenzen-vaststellen'),

    path('klassegrenzen/tonen/',
         views_overzicht.KlassegrenzenTonenView.as_view(),
         name='klassegrenzen-tonen'),

    path('lijst-regio/<comp_pk>/',
         views_overzicht.LijstAangemeldRegioView.as_view(),
         name='lijst-regio'),

    path('info/',
         views_overzicht.InfoCompetitieView.as_view(),
         name='info-competitie'),

    path('tussenstand/',
         views_overzicht.TussenstandView.as_view(),
         name='tussenstand'),

    path('wijzig-datums/<comp_pk>/',
         views_bb.WijzigDatumsView.as_view(),
         name='wijzig-datums'),

    path('planning/regiocompetitie/ronde/<ronde_pk>/',
         views_planning.RegioRondePlanningView.as_view(),
         name='regio-ronde-planning'),

    path('planning/regiocompetitie/cluster/<cluster_pk>/',
         views_planning.RegioClusterPlanningView.as_view(),
         name='regio-cluster-planning'),

    path('planning/regiocompetitie/<deelcomp_pk>/',
         views_planning.RegioPlanningView.as_view(),
         name='regio-planning'),

    path('planning/rayoncompetitie/<deelcomp_pk>/',
         views_planning.RayonPlanningView.as_view(),
         name='rayon-planning'),

    path('planning/bondscompetitie/<deelcomp_pk>/',
         views_planning.BondPlanningView.as_view(),
         name='bond-planning'),

    path('planning/wedstrijd/wijzig/<wedstrijd_pk>/',
         views_planning.WijzigWedstrijdView.as_view(),
         name='wijzig-wedstrijd'),

    path('planning/wedstrijd/verwijder/<wedstrijd_pk>/',
         views_planning.VerwijderWedstrijdView.as_view(),
         name='verwijder-wedstrijd')
]

# end of file
