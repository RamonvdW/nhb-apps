# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path

from Functie import (view_activeer_rol, view_beheerders, view_beheerders_vereniging, view_email_beheerders,
                     view_koppel_beheerder, view_vhpg, view_wisselvanrol)

app_name = 'Functie'

# basis = /functie/

urlpatterns = [

    # post-only, alle data gaat via parameters in de body ipv de url
    path('wijzig/<functie_pk>/ontvang/',
         view_koppel_beheerder.OntvangBeheerderWijzigingenView.as_view(),
         name='ontvang-wijzigingen'),

    path('wijzig/<functie_pk>/',
         view_koppel_beheerder.WijzigBeheerdersView.as_view(),
         name='wijzig-beheerders'),

    path('wijzig-email/<functie_pk>/',
         view_koppel_beheerder.WijzigEmailView.as_view(),
         name='wijzig-email'),

    path('overzicht/vereniging/',
         view_beheerders_vereniging.BeheerdersVerenigingView.as_view(),
         name='overzicht-vereniging'),

    path('overzicht/',
         view_beheerders.LijstBeheerdersView.as_view(),
         name='overzicht'),

    path('overzicht/beheerders/sec-hwl/',
         view_email_beheerders.OverzichtEmailsSecHwlView.as_view(),
         name='emails-sec-hwl'),

    path('overzicht/beheerders/competitie/',
         view_email_beheerders.OverzichtEmailsCompetitieBeheerdersView.as_view(),
         name='emails-beheerders'),


    path('activeer-functie/<str:functie_pk>/',
         view_activeer_rol.ActiveerRolView.as_view(),
         name='activeer-functie'),

    path('activeer-functie-hwl/',
         view_activeer_rol.ActiveerRolView.as_view(),
         name='activeer-functie-hwl'),

    path('activeer-rol/<str:rol>/',
         view_activeer_rol.ActiveerRolView.as_view(),
         name='activeer-rol'),


    path('wissel-van-rol/',
         view_wisselvanrol.WisselVanRolView.as_view(),
         name='wissel-van-rol'),

    path('wissel-van-rol/secretaris/',
         view_wisselvanrol.WisselNaarSecretarisView.as_view(),
         name='wissel-naar-sec'),


    path('vhpg-acceptatie/',
         view_vhpg.VhpgAcceptatieView.as_view(),
         name='vhpg-acceptatie'),

    path('vhpg-afspraken/',
         view_vhpg.VhpgAfsprakenView.as_view(),
         name='vhpg-afspraken'),

    path('vhpg-overzicht/',
         view_vhpg.VhpgOverzichtView.as_view(),
         name='vhpg-overzicht'),
]

# end of file
