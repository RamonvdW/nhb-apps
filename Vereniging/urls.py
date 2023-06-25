# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Vereniging import (view_accommodatie, view_externe_locaties, view_overzicht, view_ledenlijst,
                        view_lijst_verenigingen)

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


    # Accommodatie (voor gebruik van buiten Beheer vereniging)
    path('accommodaties/lijst/',
         view_lijst_verenigingen.LijstVerenigingenView.as_view(),
         name='lijst-verenigingen'),

    path('accommodaties/details/<ver_nr>/',
         view_accommodatie.AccommodatieDetailsView.as_view(),
         name='accommodatie-details'),

    # eigen accommodatie
    path('accommodatie-details/<ver_nr>/',
         view_accommodatie.VerenigingAccommodatieDetailsView.as_view(),
         name='vereniging-accommodatie-details'),


    # Wedstrijdlocaties
    path('externe-locaties/<ver_nr>/',
         view_externe_locaties.ExterneLocatiesView.as_view(),
         name='externe-locaties'),

    path('externe-locaties/<ver_nr>/details/<locatie_pk>/',
         view_externe_locaties.ExterneLocatieDetailsView.as_view(),
         name='locatie-details'),


    # voor de BB
    path('contact-geen-beheerders/',
         view_lijst_verenigingen.GeenBeheerdersView.as_view(),
         name='contact-geen-beheerders')
]

# end of file
