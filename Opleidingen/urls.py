# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Opleidingen import view_overzicht, view_basiscursus

app_name = 'Opleidingen'

# basis = /opleidingen/

urlpatterns = [

    # opleidingen
    path('',
         view_overzicht.OpleidingenOverzichtView.as_view(),
         name='overzicht'),

    path('basiscursus/',
         view_basiscursus.BasiscursusView.as_view(),
         name='basiscursus'),

    path('details/<opleiding_pk>/',
         view_overzicht.OpleidingDetailsView.as_view(),
         name='details'),

    # TODO: implement
    path('manager/',
         view_overzicht.OpleidingenOverzichtView.as_view(),
         name='manager'),

]

# end of file
