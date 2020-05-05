# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views

app_name = 'Competitie'

urlpatterns = [

    path('',
         views.CompetitieOverzichtView.as_view(),
         name='overzicht'),

    path('instellingen-volgende-competitie/',
         views.InstellingenVolgendeCompetitieView.as_view(),
         name='instellingen-volgende-competitie'),

    path('aanmaken/',
         views.CompetitieAanmakenView.as_view(),
         name='aanmaken'),

    path('ag-vaststellen/',
         views.AGVaststellenView.as_view(),
         name='ag-vaststellen'),

    # TODO: afstand vervangen door comp_pk
    path('klassegrenzen/vaststellen/<afstand>/',
         views.KlassegrenzenVaststellenView.as_view(),
         name='klassegrenzen-vaststellen'),

    path('klassegrenzen/tonen/',
         views.KlassegrenzenTonenView.as_view(),
         name='klassegrenzen-tonen'),

    path('lijst-verenigingen/',
         views.LijstVerenigingenView.as_view(),
         name='lijst-verenigingen'),

    path('lijst-regio/<comp_pk>/',
         views.LijstAangemeldRegioView.as_view(),
         name='lijst-regio'),

    path('info/',
         views.InfoCompetitieView.as_view(),
         name='info-competitie'),

    path('wijzig-datums/<comp_pk>/',
         views.WijzigDatumsView.as_view(),
         name='wijzig-datums')
]

# end of file
