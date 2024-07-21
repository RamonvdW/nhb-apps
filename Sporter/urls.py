# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Sporter import view_profiel, view_profiel_test, view_voorkeuren, view_leeftijdsklassen

app_name = 'Sporter'

# basis = /sporter/

urlpatterns = [
    path('',
         view_profiel.ProfielView.as_view(),
         name='profiel'),

    path('voorkeuren/<sporter_pk>/',
         view_voorkeuren.VoorkeurenView.as_view(),
         name='voorkeuren-sporter'),

    path('voorkeuren/',
         view_voorkeuren.VoorkeurenView.as_view(),
         name='voorkeuren'),

    path('leeftijden/persoonlijk/',
         view_leeftijdsklassen.WedstrijdLeeftijdenPersoonlijkView.as_view(),
         name='leeftijdsgroepen-persoonlijk'),

    path('leeftijden/',
         view_leeftijdsklassen.InfoLeeftijdenView.as_view(),
         name='leeftijdsgroepen'),

    path('profiel-test/<case>/',
         view_profiel_test.ProfielTestView.as_view(),
         name='profiel-test'),

]

# end of file
