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

    # instellingen volgende competitie
    path('instellingen-volgende-competitie/',
         views.InstellingenVolgendeCompetitieView.as_view(),
         name='instellingen-volgende-competitie'),

    path('aanmaken/',
         views.CompetitieAanmakenView.as_view(),
         name='aanmaken'),

    path('klassegrenzen/<afstand>/',
         views.KlassegrenzenView.as_view(),
         name='klassegrenzen'),

    # post-only, alle data gaat via parameters in de body ipv de url
    path('beheer-favorieten/wijzig/',
         views.WijzigFavorieteBestuurdersView.as_view(),
         name='wijzigfavoriet'),

    path('beheer-favorieten/',
         views.BeheerFavorieteBestuurdersView.as_view(),
         name='beheerfavorieten'),

    # post-only, alle data gaat via parameters in de body ipv de url
    path('wijzig-bestuurders/',
         views.KoppelBestuurdersOntvangWijzigingView.as_view(),
         name='wijzig-deelcomp-bestuurders'),

    path('kies-bestuurders/<deelcomp_pk>/',
         views.KoppelBestuurderDeelCompetitieView.as_view(),
         name='kies-deelcomp-bestuurder'),

    path('toon-bestuurders/<comp_pk>/',
         views.KoppelBestuurdersCompetitieView.as_view(),
         name='toon-competitie-bestuurders'),


]

# end of file
