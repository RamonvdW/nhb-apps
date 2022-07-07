# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import view_overzicht

app_name = 'Opleidingen'

urlpatterns = [

    # wedstrijden
    path('',
         view_overzicht.OpleidingenOverzichtView.as_view(),
         name='overzicht'),
]

# end of file
