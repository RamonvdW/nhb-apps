# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Functie import (view_overzicht, view_otp_controle, view_otp_koppelen, view_vhpg, view_wisselvanrol,
                     view_koppel_beheerder)

app_name = 'Functie'

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
         view_overzicht.OverzichtVerenigingView.as_view(),
         name='overzicht-vereniging'),

    path('overzicht/',
         view_overzicht.OverzichtView.as_view(),
         name='overzicht'),

    path('overzicht/alle-lid-nrs/sec-hwl/',
         view_overzicht.OverzichtEmailsSecHwlView.as_view(),
         name='sec-hwl-lid_nrs'),


    path('otp-koppelen-stap1/',
         view_otp_koppelen.OTPKoppelenStap1View.as_view(),
         name="otp-koppelen-stap1"),

    path('otp-koppelen-stap2/',
         view_otp_koppelen.OTPKoppelenStap2View.as_view(),
         name="otp-koppelen-stap2"),

    path('otp-koppelen-stap3/',
         view_otp_koppelen.OTPKoppelenStap3View.as_view(),
         name="otp-koppelen-stap3"),


    path('otp-controle/',
         view_otp_controle.OTPControleView.as_view(),
         name="otp-controle"),

    path('otp-loskoppelen/',
         view_otp_controle.OTPLoskoppelenView.as_view(),
         name='otp-loskoppelen'),


    path('activeer-functie/<str:functie_pk>/',
         view_wisselvanrol.ActiveerRolView.as_view(),
         name='activeer-functie'),

    path('activeer-rol/<str:rol>/',
         view_wisselvanrol.ActiveerRolView.as_view(),
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
