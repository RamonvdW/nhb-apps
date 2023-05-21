# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Kalender import view_landing_page, view_maand, view_jaar

app_name = 'Kalender'

urlpatterns = [

    # wedstrijden
    path('',
         view_landing_page.KalenderLandingPageView.as_view(),
         name='landing-page'),

    path('pagina-<int:jaar>-<maand>/',                  # backwards compatibility
         view_maand.KalenderMaandView.as_view(),
         name='maand'),

    path('maand/<maand>-<int:jaar>/<soort>/',
         view_maand.KalenderMaandView.as_view(),
         name='maand-soort'),

    path('jaar/<maand>-<int:jaar>/<soort>/',
         view_jaar.KalenderJaarView.as_view(),
         name='jaar-soort'),
]

# end of file
