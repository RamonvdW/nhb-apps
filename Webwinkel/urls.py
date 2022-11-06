# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Webwinkel import view_overzicht

app_name = 'Webwinkel'

urlpatterns = [

    # inschrijven
    path('',
         view_overzicht.OverzichtView.as_view(),
         name='overzicht'),

    # manager (wordt gebruikt door wissel van rol)
    path('',
         view_overzicht.OverzichtView.as_view(),
         name='manager'),

    #
    path('product-<product_pk>/',
         view_overzicht.ProductView.as_view(),
         name='product'),
]

# end of file
