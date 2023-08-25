# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Registreer import view_begin, view_registreer_lid, view_registreer_gast

app_name = 'Registreer'

# basis: /account/registreer/

urlpatterns = [

    path('',
         view_begin.RegistreerBeginView.as_view(),
         name='begin'),

    path('lid/',
         view_registreer_lid.RegistreerLidView.as_view(),
         name='lid'),

    path('gast/',
         view_registreer_gast.RegistreerGastView.as_view(),
         name='gast'),

    path('gast/meer-vragen/',
         view_registreer_gast.RegistreerGastVervolgView.as_view(),
         name='gast-meer-vragen'),

    path('gast/volgende-vraag/',
         view_registreer_gast.RegistreerGastVolgendeVraagView.as_view(),
         name='gast-volgende-vraag'),

    path('gast/opheffen/',
         view_registreer_gast.GastAccountOpheffenView.as_view(),
         name='opheffen')
]

# end of file
