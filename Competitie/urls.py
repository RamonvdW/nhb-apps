# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Competitie import views_info, views_klassengrenzen, views_kies, views_overzicht, views_beheer, views_tijdlijn

app_name = 'Competitie'

urlpatterns = [

    path('',
         views_kies.CompetitieKiesView.as_view(),
         name='kies'),

    path('<comp_pk>/',
         views_overzicht.CompetitieOverzichtView.as_view(),
         name='overzicht'),

    path('<comp_pk>/klassengrenzen-tonen/',
         views_klassengrenzen.KlassengrenzenTonenView.as_view(),
         name='klassengrenzen-tonen'),

    path('info/',
         views_info.InfoCompetitieView.as_view(),
         name='info-competitie'),

    path('info/leeftijden/',
         views_info.redirect_leeftijden,  # oud; redirects naar nieuw
         name='info-leeftijden'),


    # voor beheerders
    path('<comp_pk>/beheer/',
         views_beheer.CompetitieBeheerView.as_view(),
         name='beheer'),

    path('<comp_pk>/tijdlijn/',
         views_tijdlijn.CompetitieTijdlijnView.as_view(),
         name='tijdlijn'),
]

# end of file
