# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import (view_accommodatie, view_overzicht, view_ledenlijst,
               view_aanmelden, view_wedstrijden, view_lijst_rk)

app_name = 'Vereniging'

urlpatterns = [

    path('',
         view_overzicht.OverzichtView.as_view(),
         name='overzicht'),

    path('leden-lijst/',
         view_ledenlijst.LedenLijstView.as_view(),
         name='ledenlijst'),

    path('leden-voorkeuren/',
         view_ledenlijst.LedenVoorkeurenView.as_view(),
         name='leden-voorkeuren'),

    path('leden-aanmelden/competitie/<comp_pk>/',
         view_aanmelden.LedenAanmeldenView.as_view(),
         name='leden-aanmelden'),

    path('leden-ingeschreven/competitie/<deelcomp_pk>/',
         view_aanmelden.LedenIngeschrevenView.as_view(),
         name='leden-ingeschreven'),

    path('accommodaties/lijst/',
         view_accommodatie.LijstVerenigingenView.as_view(),
         name='lijst-verenigingen'),

    path('accommodaties/details/<locatie_pk>/<vereniging_pk>/',
         view_accommodatie.AccommodatieDetailsView.as_view(),
         name='accommodatie-details'),

    path('accommodatie-details/<locatie_pk>/<vereniging_pk>/',
         view_accommodatie.VerenigingAccommodatieDetailsView.as_view(),
         name='vereniging-accommodatie-details'),

    path('regio-clusters/',
         view_accommodatie.WijzigClustersView.as_view(),
         name='clusters'),

    path('wedstrijden/',
         view_wedstrijden.WedstrijdenView.as_view(),
         name='wedstrijden'),

    path('lijst-rayonkampioenschappen/<deelcomp_pk>/',
         view_lijst_rk.VerenigingLijstRkSchuttersView.as_view(),
         name='lijst-rk'),
]

# end of file
