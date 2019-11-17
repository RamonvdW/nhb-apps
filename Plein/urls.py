# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views

app_name = 'Plein'

urlpatterns = [
    path('',
         views.PleinView.as_view(),
         name='plein'),

    path('privacy/',
         views.PrivacyView.as_view(),
         name='privacy'),

    path('wissel-van-rol/<str:rol>/',
         views.ActiveerRolView.as_view(),
         name='activeer-rol'),

    path('wissel-van-rol/',
         views.WisselVanRolView.as_view(),
         name='wissel-van-rol'),

    path('leeftijdsklassen/',
         views.LeeftijdsklassenView.as_view(),
         name='leeftijdsklassen'),
]

# end of file
