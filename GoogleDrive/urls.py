# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from GoogleDrive import views_toestemming, views_webhook

app_name = 'GoogleDrive'

# basis = /google/

urlpatterns = [

    path('toestemming/',
         views_toestemming.ToestemmingView.as_view(),
         name='toestemming-drive'),

    path('webhook/oauth/',
         views_webhook.OAuthWebhookView.as_view(),
         name='oauth-webhook'),
]

# end of file
