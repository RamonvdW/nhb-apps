# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views

app_name = 'Schutter'

urlpatterns = [
    path('voorkeuren/',
         views.VoorkeurenView.as_view(),
         name='voorkeuren'),
]

# end of file
