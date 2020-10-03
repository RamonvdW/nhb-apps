# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views

app_name = 'Logboek'

urlpatterns = [
    path('',
         views.LogboekRestView.as_view(),
         name='alles'),

    path('rest/',
         views.LogboekRestView.as_view(),
         name='rest'),

    path('records/',
         views.LogboekRecordsView.as_view(),
         name='records'),

    path('accounts/',
         views.LogboekAccountsView.as_view(),
         name='accounts'),

    path('rollen/',
         views.LogboekRollenView.as_view(),
         name='rollen'),

    path('crm-import/',
         views.LogboekNhbStructuurView.as_view(),
         name='nhbstructuur'),

    path('competitie/',
         views.LogboekCompetitieView.as_view(),
         name='competitie'),

    path('accommodaties/',
         views.LogboekAccommodatiesView.as_view(),
         name='accommodaties'),

    path('clusters/',
         views.LogboekClustersView.as_view(),
         name='clusters'),

    path('uitrol/',
         views.LogboekUitrolView.as_view(),
         name='uitrol'),

    path('import-oude-site/',
         views.LogboekImportView.as_view(),
         name='import'),
]

# end of file
