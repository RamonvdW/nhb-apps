# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import view_betalingen, view_vereniging


app_name = 'Betalingen'

urlpatterns = [

    # wedstrijden
    path('mollie/webhook/',
         view_betalingen.MollieWebhookView.as_view(),
         name='mollie-webhook'),

    path('vereniging/instellingen/',
         view=view_vereniging.BetalingenInstellenView.as_view(),
         name='vereniging-instellingen'),
]

# end of file
