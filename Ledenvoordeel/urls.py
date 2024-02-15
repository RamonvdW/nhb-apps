# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Ledenvoordeel import views

app_name = 'Ledenvoordeel'

# basis = /ledenvoordeel/

urlpatterns = [

    path('',
         views.VoordeelOverzichtView.as_view(),
         name='overzicht'),

    path('walibi-2024/',
         views.VoordeelWalibiView.as_view(),
         name='walibi'),

]

# end of file
