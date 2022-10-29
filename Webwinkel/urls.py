# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Webwinkel import view_proto

app_name = 'Webwinkel'

urlpatterns = [

    # inschrijven
    path('prototype/',
         view_proto.PrototypeView.as_view(),
         name='prototype'),

    # inschrijven
    path('prototype/',
         view_proto.PrototypeView.as_view(),
         name='manager'),
]

# end of file
