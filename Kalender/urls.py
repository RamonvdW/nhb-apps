# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import view_landing_page, view_maand

app_name = 'Kalender'

urlpatterns = [

    # wedstrijden
    path('',
         view_landing_page.KalenderLandingPageView.as_view(),
         name='landing-page'),

    path('pagina-<int:jaar>-<str:maand>/',
         view_maand.KalenderMaandView.as_view(),
         name='maand'),
]

# end of file
