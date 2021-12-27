# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import view_registreer_nhb, view_profiel, view_voorkeuren, view_leeftijdsklassen


app_name = 'Sporter'

urlpatterns = [
    path('',
         view_profiel.ProfielView.as_view(),
         name='profiel'),

    path('registreer/',
         view_registreer_nhb.RegistreerNhbNummerView.as_view(),
         name='registreer'),

    path('voorkeuren/<sporter_pk>/',
         view_voorkeuren.VoorkeurenView.as_view(),
         name='voorkeuren-sporter'),

    path('voorkeuren/',
         view_voorkeuren.VoorkeurenView.as_view(),
         name='voorkeuren'),

    path('leeftijdsklassen/',
         view_leeftijdsklassen.LeeftijdsklassenView.as_view(),
         name='leeftijdsklassen'),
]

# end of file
