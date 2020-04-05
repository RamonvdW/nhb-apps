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

    path('activiteit/',
         views.ActiviteitView.as_view(),
         name='activiteit'),

    path('account-wissel/',
         views.LoginAsZoekView.as_view(),
         name='account-wissel'),
]

# end of file
