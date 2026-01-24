# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from CompKampioenschap import view_import_uitslag, view_wf_status

app_name = 'CompKampioenschap'

# basis = /bondscompetities/kampioenschappen/

urlpatterns = [

    path('wedstrijdformulieren/status/',
         view_wf_status.StatusView.as_view(),
         name='wf-status'),

    path('importeer-uitslag/indiv/<int:status_pk>/',
         view_import_uitslag.ImporteerUitslagIndivView.as_view(),
         name='importeer-uitslag-indiv'),

    path('importeer-uitslag/teams/<int:status_pk>/',
         view_import_uitslag.ImporteerUitslagTeamsView.as_view(),
         name='importeer-uitslag-teams'),
]

# end of file
