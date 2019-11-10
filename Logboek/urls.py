# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views

app_name = 'Logboek'

urlpatterns = [
    path('',
         views.LogboekView.as_view(),
         name='logboek'),
]

# end of file
