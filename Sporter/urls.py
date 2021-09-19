# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import (view_registreer_nhb, view_profiel, view_voorkeuren,
               view_aanmelden_afmelden, view_leeftijdsklassen)


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

    path('regiocompetitie/aanmelden/<deelcomp_pk>/<sporterboog_pk>/bevestig/',
         view_aanmelden_afmelden.RegiocompetitieAanmeldenBevestigView.as_view(),
         name='bevestig-aanmelden'),

    path('regiocompetitie/aanmelden/<deelcomp_pk>/<sporterboog_pk>/',
         view_aanmelden_afmelden.RegiocompetitieAanmeldenView.as_view(),
         name='aanmelden'),

    path('regiocompetitie/afmelden/<deelnemer_pk>/',
         view_aanmelden_afmelden.RegiocompetitieAfmeldenView.as_view(),
         name='afmelden'),

    # TODO: 'schietmomenten' vervangen door 'wedstrijden'
    path('regiocompetitie/<deelnemer_pk>/schietmomenten/',
         view_aanmelden_afmelden.SchutterSchietmomentenView.as_view(),
         name='schietmomenten'),
]

# end of file
