# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Bondspas import view_online

app_name = 'Bondspas'

# basis = /sporter/bondspas/

urlpatterns = [
    path('toon/',
         view_online.ToonBondspasView.as_view(),
         name='toon-bondspas'),

    path('dynamic/ophalen/',
         view_online.DynamicBondspasOphalenView.as_view(),
         name='dynamic-ophalen'),

    path('dynamic/download/',
         view_online.DynamicBondspasDownloadView.as_view(),
         name='dynamic-download'),

    path('toon/van-lid/<lid_nr>/',
         view_online.ToonBondspasBeheerderView.as_view(),
         name='toon-bondspas-van'),

    path('vereniging/van-lid/<lid_nr>/',
         view_online.ToonBondspasVerenigingView.as_view(),
         name='vereniging-bondspas-van')
]

# end of file
