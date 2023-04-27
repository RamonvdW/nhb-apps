# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Account import view_login, view_login_as, view_logout, view_wachtwoord, view_otp_controle, view_otp_koppelen

app_name = 'Account'

urlpatterns = [
    path('login/',
         view_login.LoginView.as_view(),
         name='login'),

    path('logout/',
         view_logout.LogoutView.as_view(),
         name='logout'),

    path('wachtwoord-vergeten/',
         view_wachtwoord.WachtwoordVergetenView.as_view(),
         name='wachtwoord-vergeten'),

    path('nieuw-wachtwoord/',
         view_wachtwoord.NieuwWachtwoordView.as_view(),
         name='nieuw-wachtwoord'),

    path('account-wissel/',
         view_login_as.LoginAsZoekView.as_view(),
         name='account-wissel'),

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
]

# end of file
