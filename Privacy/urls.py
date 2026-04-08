# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Privacy import view_overzicht, view_verklaring

app_name = 'Privacy'

# basis = /privacy/

urlpatterns = [
    path('',
         view_overzicht.OverzichtView.as_view(),
         name='overzicht'),

    path('verklaring/',
         view_verklaring.VerklaringView.as_view(),
         name='verklaring'),
]


# end of file
