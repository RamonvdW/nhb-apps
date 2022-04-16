# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import view_mandje

app_name = 'Bestel'

urlpatterns = [
    path('mandje/verwijderen/<product_pk>/',
         view_mandje.VerwijderProductUitMandje.as_view(),
         name='mandje-verwijder-product'),

    path('mandje/code-toevoegen/',
         view_mandje.CodeToevoegenView.as_view(),
         name='mandje-code-toevoegen'),

    path('mandje/',
         view_mandje.ToonInhoudMandje.as_view(),
         name='toon-inhoud-mandje'),
]

# end of file
