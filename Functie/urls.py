# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views

app_name = 'Functie'

urlpatterns = [

    # post-only, alle data gaat via parameters in de body ipv de url
    path('wijzig/<functie_pk>/ontvang/',
         views.OntvangWijzigingenView.as_view(),
         name='ontvang-wijzigingen'),

    path('wijzig/<functie_pk>/',
         views.WijzigView.as_view(),
         name='wijzig'),

    path('overzicht/vereniging/',
         views.OverzichtVerenigingView.as_view(),
         name='overzicht-vereniging'),

    path('overzicht/',
         views.OverzichtView.as_view(),
         name='overzicht'),

    path('wissel-van-rol/functie/<functie_pk>/',
         views.ActiveerRolView.as_view(),
         name='activeer-rol-functie'),

    path('wissel-van-rol/<str:rol>/',
         views.ActiveerRolView.as_view(),
         name='activeer-rol'),

    path('wissel-van-rol/',
         views.WisselVanRolView.as_view(),
         name='wissel-van-rol'),
]

# end of file
