# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Plein import views, views_fout

app_name = 'Plein'

# basis = /plein/

urlpatterns = [
    path('',
         views.PleinView.as_view(),
         name='plein'),

    path('handleidingen/',
         views.HandleidingenView.as_view(),
         name='handleidingen'),

    path('privacy/',
         views.PrivacyView.as_view(),
         name='privacy'),

    path('niet-ondersteund/',
         views.NietOndersteundView.as_view(),
         name='niet-ondersteund'),

    path('test-ui/',
         views.TestUIView.as_view(),
         name='test-ui'),

    path('test-speciale-pagina/<code>/',
         views_fout.TestSpecialePagina.as_view(),
         name='test-speciale-pagina'),
]

# end of file
