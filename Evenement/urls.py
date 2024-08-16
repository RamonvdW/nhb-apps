# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Evenement import views

app_name = 'Evenement'

# basis = /kalender/evenement/

urlpatterns = [
    # evenement details
    path('details/<evenement_pk>/',
         views.DetailsView.as_view(),
         name='details'),

    # afmelden
    path('afmelden/<inschrijving_pk>/',
         views.AfmeldenView.as_view(),
         name='afmelden'),
]

# end of file
