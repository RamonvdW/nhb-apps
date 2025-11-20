# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Kalender import view_landing_page, view_zoek, view_api

app_name = 'Kalender'

# basis = /kalender/

urlpatterns = [
    path('',
         view_landing_page.KalenderLandingPageView.as_view(),
         name='landing-page'),

    path('jaar/',
         view_landing_page.KalenderLandingPageJaarView.as_view(),
         name='landing-page-jaar'),

    path('<jaar_of_maand>/<int:jaar>/<maand>/',
         view_zoek.KalenderView.as_view(),
         name='simpel'),

    path('<jaar_of_maand>/<int:jaar>/<maand>/<soort>/<bogen>/',
         view_zoek.KalenderView.as_view(),
         name='pre-discipline'),

    path('<jaar_of_maand>/<int:jaar>/<maand>/<soort>/<bogen>/<discipline>/',
         view_zoek.KalenderView.as_view(),
         name='alles'),


    # backwards compatibility

    # TODO: verwijderen. 2024-11: wordt nog best veel gebruikt, niet alleen door zoekmachines
    path('pagina-<int:jaar>-<maand>/',
         view_zoek.KalenderView.as_view(),
         name='legacy'),

    path('<jaar_of_maand>/<maand>-<int:jaar>/',         
         view_zoek.KalenderView.as_view(),
         name='legacy-simpel'),

    path('<jaar_of_maand>/<maand>-<int:jaar>/<soort>/<bogen>/',
         view_zoek.KalenderView.as_view(),
         name='legacy-pre-discipline'),

    path('<jaar_of_maand>/<maand>-<int:jaar>/<soort>/<bogen>/<discipline>/',         # backwards compatibility
         view_zoek.KalenderView.as_view(),
         name='legacy-alles'),


    # API voor weergave kalender informatie op de hoofdsite
    path('api/lijst/<aantal_dagen_vooruit>/',
         view_api.ApiView.as_view(),
         name='api-lijst'),
]

# end of file
