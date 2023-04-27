# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Overig import view_tijdelijke_url, view_activiteit

app_name = 'Overig'

# basis url: /overig/

urlpatterns = [
    path('activiteit/',
         view_activiteit.ActiviteitView.as_view(),
         name='activiteit'),

    # oude interface, voor backwards compatibility
    # TODO: verwijder in v20 of later
    path('url/<code>/',
         view_tijdelijke_url.SiteTijdelijkeUrlView.as_view(),
         name='tijdelijke-url'),
]

# end of file
