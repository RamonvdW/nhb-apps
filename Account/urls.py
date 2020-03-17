# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views

app_name = 'Account'

urlpatterns = [
    path('login/',
         views.LoginView.as_view(),
         name='login'),

    path('logout/',
         views.LogoutView.as_view(),
         name='logout'),

    path('registreer/',
         views.RegistreerNhbNummerView.as_view(),
         name='registreer'),

    path('aangemaakt/',
         views.AangemaaktView.as_view(),
         name='aangemaakt'),

    path('nieuwe-email/',
         views.EmailGewijzigdView.as_view(),
         name='nieuwe-email'),

    path('bevestigd/',
         views.BevestigdView.as_view(),
         name='bevestigd'),

    path('wachtwoord-vergeten/',
         views.WachtwoordVergetenView.as_view(),
         name='wachtwoord-vergeten'),

    path('otp-controle/',
         views.OTPControleView.as_view(),
         name="otp-controle"),

    path('otp-koppelen/',
         views.OTPKoppelenView.as_view(),
         name="otp-koppelen"),

    path('vhpg-acceptatie/',
         views.VhpgAcceptatieView.as_view(),
         name='vhpg-acceptatie'),

    path('vhpg-afspraken/',
         views.VhpgAfsprakenView.as_view(),
         name='vhpg-afspraken'),

    path('vhpg-overzicht/',
         views.VhpgOverzichtView.as_view(),
         name='vhpg-overzicht'),

    path('activiteit/',
         views.ActiviteitView.as_view(),
         name='activiteit')
]

# end of file
