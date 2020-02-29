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
         views.WijzigFavorieteBeheerdersView.as_view(),
         name='wijzigfavoriet'),

    path('beheer-favorieten/',
         views.BeheerFavorieteBeheerdersView.as_view(),
         name='beheerfavorieten'),

    # post-only, alle data gaat via parameters in de body ipv de url
    path('wijzig-beheerders/',
         views.KoppelBeheerdersOntvangWijzigingView.as_view(),
         name='wijzig-deelcomp-beheerders'),

    path('kies-beheerders/<deelcomp_pk>/',
         views.KoppelBeheerderDeelCompetitieView.as_view(),
         name='kies-deelcomp-beheerders'),

    path('toon-beheerders/<comp_pk>/',
         views.KoppelBeheerdersCompetitieView.as_view(),
         name='toon-competitie-beheerders'),

    path('lijst-verenigingen/',
         views.LijstVerenigingenView.as_view(),
         name='lijst-verenigingen'),
]

# end of file
