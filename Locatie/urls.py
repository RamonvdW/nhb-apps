# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Locatie import view_accommodatie, view_externe_locaties

app_name = 'Locatie'

# basis: /vereniging/locatie/

urlpatterns = [

    # eigen accommodatie
    path('<ver_nr>/',
         view_accommodatie.VerenigingAccommodatieDetailsView.as_view(),
         name='accommodatie-details'),

    # locaties
    path('<ver_nr>/extern/',
         view_externe_locaties.ExterneLocatiesView.as_view(),
         name='externe-locaties'),

    path('<ver_nr>/extern/<locatie_pk>/',
         view_externe_locaties.ExterneLocatieDetailsView.as_view(),
         name='extern-locatie-details'),
]

# end of file
