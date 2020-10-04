# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import (view_login, view_login_as, view_logout,
               view_aangemaakt,
               view_wachtwoord,
               view_activiteit)

app_name = 'Account'

urlpatterns = [
    path('login/',
         view_login.LoginView.as_view(),
         name='login'),

    path('logout/',
         view_logout.LogoutView.as_view(),
         name='logout'),

    path('aangemaakt/',
         view_aangemaakt.AangemaaktView.as_view(),
         name='aangemaakt'),

    path('wachtwoord-vergeten/',
         view_wachtwoord.WachtwoordVergetenView.as_view(),
         name='wachtwoord-vergeten'),

    path('nieuw-wachtwoord/',
         view_wachtwoord.NieuwWachtwoordView.as_view(),
         name='nieuw-wachtwoord'),

    path('activiteit/',
         view_activiteit.ActiviteitView.as_view(),
         name='activiteit'),

    path('account-wissel/',
         view_login_as.LoginAsZoekView.as_view(),
         name='account-wissel'),
]

# end of file
