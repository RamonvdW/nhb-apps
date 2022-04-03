# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import view_mandje

app_name = 'Mandje'

urlpatterns = [
    path('verwijderen/<inhoud_pk>/',
         view_mandje.VerwijderUitMandje.as_view(),
         name='verwijder-inschrijving'),

    path('code-toevoegen/',
         view_mandje.CodeToevoegenView.as_view(),
         name='code-toevoegen'),

    path('',
         view_mandje.ToonInhoudMandje.as_view(),
         name='toon-inhoud'),
]

# end of file
