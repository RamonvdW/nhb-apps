# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Kalender import view_landing_page, view_maand, view_jaar, view_api

app_name = 'Kalender'

# basis = /kalender/

urlpatterns = [
    path('',
         view_landing_page.KalenderLandingPageView.as_view(),
         name='landing-page'),

    # TODO: verwijderen. 2024-11: wordt nog best veel gebruikt, niet alleen door zoekmachines
    path('pagina-<int:jaar>-<maand>/',                  # backwards compatibility
         view_maand.KalenderMaandView.as_view(),
         name='legacy'),

    path('maand/<maand>-<int:jaar>/<soort>/<bogen>/',
         view_maand.KalenderMaandView.as_view(),
         name='maand-pre-discipline'),

    path('maand/<maand>-<int:jaar>/<soort>/<bogen>/<discipline>/',
         view_maand.KalenderMaandView.as_view(),
         name='maand'),

    path('maand/<maand>-<int:jaar>/',
         view_maand.KalenderMaandView.as_view(),
         name='maand-simpel'),

    path('jaar/<maand>-<int:jaar>/<soort>/<bogen>/',
         view_jaar.KalenderJaarView.as_view(),
         name='jaar-pre-discipline'),

    path('jaar/<maand>-<int:jaar>/<soort>/<bogen>/<discipline>/',
         view_jaar.KalenderJaarView.as_view(),
         name='jaar'),

    path('jaar/<maand>-<int:jaar>/',
         view_jaar.KalenderJaarView.as_view(),
         name='jaar-simpel'),

    path('api/lijst/<aantal_dagen_vooruit>/',
         view_api.ApiView.as_view(),
         name='api-lijst'),
]

# end of file
