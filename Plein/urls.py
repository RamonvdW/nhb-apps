# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
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

    path('leeftijdsklassen/',
         views.LeeftijdsklassenView.as_view(),
         name='leeftijdsklassen'),
]

# end of file
