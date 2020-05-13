# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views

app_name = 'Schutter'

urlpatterns = [
    path('',
         views.ProfielView.as_view(),
         name='profiel'),

    path('registreer/',
         views.RegistreerNhbNummerView.as_view(),
         name='registreer'),

    path('voorkeuren/<nhblid_pk>/',
         views.VoorkeurenView.as_view(),
         name='voorkeuren-nhblid'),

    path('voorkeuren/',
         views.VoorkeurenView.as_view(),
         name='voorkeuren'),

    path('leeftijdsklassen/',
         views.LeeftijdsklassenView.as_view(),
         name='leeftijdsklassen'),

    path('regiocompetitie/inschrijven/<deelcomp_pk>/<schutterboog_pk>/',
         views.RegiocompetitieInschrijvenView.as_view(),
         name='inschrijven'),

    path('regiocompetitie/uitschrijven/<regiocomp_pk>/',
         views.RegiocompetitieUitschrijvenView.as_view(),
         name='uitschrijven'),
]

# end of file
