# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views

app_name = 'Competitie'

urlpatterns = [

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
]

# end of file
