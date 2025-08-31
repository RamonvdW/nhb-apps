# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Webwinkel import view_overzicht, view_product, view_manager

app_name = 'Webwinkel'

# basis = /webwinkel/

urlpatterns = [

    # gebruiker
    path('',
         view_overzicht.OverzichtView.as_view(),
         name='overzicht'),

    path('product-<product_pk>/',
         view_product.ProductView.as_view(),
         name='product'),


    # manager
    path('manager/',
         view_manager.ManagerView.as_view(),
         name='manager'),

    path('manager/voorraad/',
         view_manager.WebwinkelVoorraadView.as_view(),
         name='voorraad'),
]

# end of file
