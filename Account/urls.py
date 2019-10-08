# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
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

    path('uitgelogd/',
         views.UitgelogdView.as_view(),
         name='uitgelogd'),

    path('registreer/',
         views.RegistreerView.as_view(),
         name='registreer'),

    path('aangemaakt/',
         views.aangemaakt,
         name='aangemaakt'),

    path('wachtwoord-vergeten/',
         views.WachtwoordVergetenView.as_view(),
         name='wachtwoord-vergeten')
]

# end of file
