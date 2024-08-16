# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Evenement import views

app_name = 'Evenement'

# basis = /evenement/

urlpatterns = [

    path('',
         views.LandingPageView.as_view(),
         name='landing-page'),
]

# end of file
