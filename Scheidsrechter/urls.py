# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Scheidsrechter import view_overzicht, view_korps, view_beschikbaarheid, view_wedstrijden

app_name = 'Scheidsrechter'

# basis = /scheidsrechter/

urlpatterns = [
    path('',
         view_overzicht.OverzichtView.as_view(),
         name='overzicht'),

    path('korps/',
         view_korps.KorpsView.as_view(),
         name='korps'),

    path('korps-met-contactgegevens/',
         view_korps.KorpsMetContactGegevensView.as_view(),
         name='korps-met-contactgegevens'),

    path('wedstrijden/',
         view_wedstrijden.WedstrijdenView.as_view(),
         name='wedstrijden'),

    path('wedstrijden/details/<wedstrijd_pk>/',
         view_wedstrijden.WedstrijdDetailsView.as_view(),
         name='wedstrijd-details'),

    path('beschikbaarheid-opvragen/',
         view_beschikbaarheid.BeschikbaarheidOpvragenView.as_view(),
         name='beschikbaarheid-opvragen'),

    path('beschikbaarheid-wijzigen/',
         view_beschikbaarheid.WijzigBeschikbaarheidView.as_view(),
         name='beschikbaarheid-wijzigen'),

    path('beschikbaarheid-inzien/',
         view_beschikbaarheid.BeschikbaarheidInzienView.as_view(),
         name='beschikbaarheid-inzien'),
]


# end of file
