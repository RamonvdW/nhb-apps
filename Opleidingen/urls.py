# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Opleidingen import view_overzicht

app_name = 'Opleidingen'

# basis = /opleidingen/

urlpatterns = [

    # opleidingen
    path('',
         view_overzicht.OpleidingenOverzichtView.as_view(),
         name='overzicht'),

    path('manager/',
         view_overzicht.OpleidingenOverzichtView.as_view(),
         name='manager'),

]

# end of file
