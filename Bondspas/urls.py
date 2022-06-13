# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Bondspas import views


app_name = 'Bondspas'

urlpatterns = [
    path('toon/',
         views.ToonBondspasView.as_view(),
         name='toon-bondspas'),

    path('check-status/',
         views.DynamicBondspasCheckStatus.as_view(),
         name='dynamic-check-status'),
]

# end of file
