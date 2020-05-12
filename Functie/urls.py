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
         views.OntvangBeheerderWijzigingenView.as_view(),
         name='ontvang-wijzigingen'),

    path('wijzig/<functie_pk>/',
         views.WijzigBeheerdersView.as_view(),
         name='wijzig-beheerders'),

    path('wijzig-email/<functie_pk>/',
         views.WijzigEmailView.as_view(),
         name='wijzig-email'),

    path('overzicht/vereniging/',
         views.OverzichtVerenigingView.as_view(),
         name='overzicht-vereniging'),

    path('overzicht/',
         views.OverzichtView.as_view(),
         name='overzicht'),

    path('otp-controle/',
         views.OTPControleView.as_view(),
         name="otp-controle"),

    path('otp-koppelen/',
         views.OTPKoppelenView.as_view(),
         name="otp-koppelen"),

    path('activeer-functie/<str:functie_pk>/',
         views.ActiveerRolView.as_view(),
         name='activeer-functie'),

    path('activeer-rol/<str:rol>/',
         views.ActiveerRolView.as_view(),
         name='activeer-rol'),

    path('wissel-van-rol/',
         views.WisselVanRolView.as_view(),
         name='wissel-van-rol'),

    path('vhpg-acceptatie/',
         views.VhpgAcceptatieView.as_view(),
         name='vhpg-acceptatie'),

    path('vhpg-afspraken/',
         views.VhpgAfsprakenView.as_view(),
         name='vhpg-afspraken'),

    path('vhpg-overzicht/',
         views.VhpgOverzichtView.as_view(),
         name='vhpg-overzicht'),
]

# end of file
