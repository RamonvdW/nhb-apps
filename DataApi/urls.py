# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path, re_path
from DataApi import view_ver, view_lid

app_name = 'DataApi'

# basis = /data-api/

urlpatterns = [
    path('v1/verenigingen/',
         view_ver.VerenigingenView.as_view(),
         name='verenigingen1'),

    path('v1/verenigingen',
         view_ver.VerenigingenView.as_view(),
         name='verenigingen2'),

    path('v1/accommodaties/',
         view_ver.AccommodatiesView.as_view(),
         name='accommodaties1'),

    path('v1/accommodaties',
         view_ver.AccommodatiesView.as_view(),
         name='accommodaties2'),

    path('v1/lidmaatschappen/',
         view_lid.LidmaatschappenView.as_view(),
         name='lidmaatschappen1'),

    path('v1/lidmaatschappen',
         view_lid.LidmaatschappenView.as_view(),
         name='lidmaatschappen2'),

    # catch-all voor alle andere versies en endpoints
    re_path(r'(.*)$',
         view_ver.BestaatNiet.as_view(),
         name='bestaat-niet'),
]

# end of file
