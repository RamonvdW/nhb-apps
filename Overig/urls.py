# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Overig import view_activiteit, view_api

app_name = 'Overig'

# basis url: /overig/

urlpatterns = [
    path('activiteit/',
         view_activiteit.ActiviteitView.as_view(),
         name='activiteit'),

    path('otp-loskoppelen/',
         view_activiteit.OTPLoskoppelenView.as_view(),
         name='otp-loskoppelen'),

    path('api/lijst/csv/',
         view_api.ApiCsvLijstView.as_view(),
         name='api')
]

# end of file
