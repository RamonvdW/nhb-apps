# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Scheidsrechter import view_overzicht

app_name = 'Scheidsrechter'

# basis = /scheidsrechter/

urlpatterns = [
    path('',
         view_overzicht.OverzichtView.as_view(),
         name='overzicht'),

    path('korps/',
         view_overzicht.KorpsView.as_view(),
         name='korps'),

    path('wedstrijden/',
         view_overzicht.WedstrijdenView.as_view(),
         name='wedstrijden'),
]


# end of file
