# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Registreer import view_begin, view_registreer_nhb, view_registreer_gast


app_name = 'Registreer'

# baseline: /account/registreer/

urlpatterns = [

    path('',
         view_begin.RegistreerBeginView.as_view(),
         name='begin'),

    path('nhb-lid/',
         view_registreer_nhb.RegistreerNhbLidView.as_view(),
         name='nhb'),

    path('gast/',
         view_registreer_gast.RegistreerGastView.as_view(),
         name='gast'),

    path('gast/meer-vragen/',
         view_registreer_gast.RegistreerGastMeerView.as_view(),
         name='gast-meer-vragen'),
]

# end of file
