# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from GoogleDrive import views_webhook, views_resultaat

app_name = 'GoogleDrive'

# basis = /google/

urlpatterns = [

    path('webhook/oauth/',
         views_webhook.OAuthWebhookView.as_view(),
         name='oauth-webhook'),

    path('resultaat-gelukt/',
         views_resultaat.ResultaatGeluktView.as_view(),
         name='resultaat-gelukt'),

    path('resultaat-mislukt/',
         views_resultaat.ResultaatMisluktView.as_view(),
         name='resultaat-mislukt'),
]

# end of file
