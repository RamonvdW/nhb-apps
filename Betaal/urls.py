# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Betaal import view_webhooks, view_vereniging

app_name = 'Betaal'

# basis = /bestel/betaal/

urlpatterns = [

    # wedstrijden
    path('webhooks/mollie/',
         view_webhooks.simple_view_mollie_webhook,
         name='mollie-webhook'),

    path('vereniging/instellingen/',
         view=view_vereniging.BetalingInstellingenView.as_view(),
         name='vereniging-instellingen'),
]

# end of file
