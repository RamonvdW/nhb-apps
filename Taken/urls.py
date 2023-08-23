# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Taken import views

app_name = 'Taken'

# basis = /taken/

urlpatterns = [

    path('',
         views.OverzichtView.as_view(),
         name='overzicht'),

    path('details/<taak_pk>/',
         views.DetailsView.as_view(),
         name='details'),
]

# end of file
