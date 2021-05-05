# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views, view_maand, view_manager, view_vereniging, view_wijzig_wedstrijd

app_name = 'Kalender'

urlpatterns = [
    path('',
         views.KalenderLandingPageView.as_view(),
         name='landing-page'),

    path('pagina-<int:jaar>-<str:maand>/',
         view_maand.KalenderMaandView.as_view(),
         name='maand'),

    path('vereniging/',
         view_vereniging.VerenigingKalenderWedstrijdenView.as_view(),
         name='vereniging'),

    path('manager/',
         view_manager.KalenderManagerView.as_view(),
         name='manager'),

    path('<wedstrijd_pk>/wijzig/',
         view_wijzig_wedstrijd.WijzigKalenderWedstrijdView.as_view(),
         name='wijzig-wedstrijd'),

    path('<wedstrijd_pk>/zet-status/',
         view_wijzig_wedstrijd.ZetStatusKalenderWedstrijdView.as_view(),
         name='zet-status'),
]

# end of file
