# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Spelden import views

app_name = 'Spelden'

# basis = /webwinkel/spelden/

urlpatterns = [

    path('',
         views.BeginView.as_view(),
         name='begin'),

]

# end of file
