# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Logboek import views

app_name = 'Logboek'

# basis = /logboek/

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
         views.LogboekCrmImportView.as_view(),
         name='import'),

    path('competitie/',
         views.LogboekCompetitieView.as_view(),
         name='competitie'),

    path('accommodaties/',
         views.LogboekAccommodatiesView.as_view(),
         name='accommodaties'),

    path('clusters/',
         views.LogboekClustersView.as_view(),
         name='clusters'),

    path('betalingen/',
         views.LogboekBetalingenView.as_view(),
         name='betalingen'),

    path('uitrol/',
         views.LogboekUitrolView.as_view(),
         name='uitrol'),

    path('opleidingen/',
         views.LogboekOpleidingenView.as_view(),
         name='opleidingen'),
]

# end of file
