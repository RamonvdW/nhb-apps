# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import (view_registreer_nhb, view_profiel, view_voorkeuren,
               view_inschrijven_uitschrijven, view_leeftijdsklassen)


app_name = 'Schutter'

urlpatterns = [
    path('',
         view_profiel.ProfielView.as_view(),
         name='profiel'),

    path('registreer/',
         view_registreer_nhb.RegistreerNhbNummerView.as_view(),
         name='registreer'),

    path('voorkeuren/<nhblid_pk>/',
         view_voorkeuren.VoorkeurenView.as_view(),
         name='voorkeuren-nhblid'),

    path('voorkeuren/',
         view_voorkeuren.VoorkeurenView.as_view(),
         name='voorkeuren'),

    path('leeftijdsklassen/',
         view_leeftijdsklassen.LeeftijdsklassenView.as_view(),
         name='leeftijdsklassen'),

    path('regiocompetitie/inschrijven/<deelcomp_pk>/<schutterboog_pk>/bevestig/',
         view_inschrijven_uitschrijven.RegiocompetitieInschrijvenBevestigView.as_view(),
         name='bevestig-inschrijven'),

    path('regiocompetitie/inschrijven/<deelcomp_pk>/<schutterboog_pk>/',
         view_inschrijven_uitschrijven.RegiocompetitieInschrijvenView.as_view(),
         name='inschrijven'),

    path('regiocompetitie/uitschrijven/<regiocomp_pk>/',
         view_inschrijven_uitschrijven.RegiocompetitieUitschrijvenView.as_view(),
         name='uitschrijven'),

]

# end of file
