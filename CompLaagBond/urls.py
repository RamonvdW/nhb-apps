# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from CompLaagBond import views_planning_bond

app_name = 'CompLaagBond'

urlpatterns = [

    # base url: bondscompetities/bk/

    path('planning/<deelcomp_pk>/',
         views_planning_bond.BondPlanningView.as_view(),
         name='bond-planning'),
]

# end of file
