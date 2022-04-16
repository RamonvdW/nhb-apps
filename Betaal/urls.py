# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import view_webhooks, view_vereniging


app_name = 'Betaal'

urlpatterns = [

    # wedstrijden
    path('webhooks/mollie/',
         view_webhooks.MollieWebhookView.as_view(),
         name='mollie-webhook'),

    path('vereniging/instellingen/',
         view=view_vereniging.BetalingenInstellenView.as_view(),
         name='vereniging-instellingen'),
]

# end of file
