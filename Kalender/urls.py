# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views

app_name = 'Kalender'

urlpatterns = [
    path('',
         views.KalenderOverzichtView.as_view(),
         name='overzicht'),
]

# end of file
