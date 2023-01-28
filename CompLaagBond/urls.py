# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from CompLaagBond import view_planning, view_indiv

app_name = 'CompLaagBond'

urlpatterns = [

    # base url: bondscompetities/bk/

    path('<deelkamp_pk>/planning/',
         view_planning.PlanningView.as_view(),
         name='planning'),

    path('<deelkamp_pk>/limieten/',
         view_planning.WijzigLimietenView.as_view(),
         name='wijzig-limieten'),

    path('planning/wedstrijd/wijzig/<match_pk>/',
         view_planning.WijzigWedstrijdView.as_view(),
         name='wijzig-wedstrijd'),

    path('planning/wedstrijd/verwijder/<match_pk>/',
         view_planning.VerwijderWedstrijdView.as_view(),
         name='verwijder-wedstrijd'),

    # BKO: individueel
    path('selectie/<deelkamp_pk>/',
         view_indiv.LijstBkSelectieView.as_view(),
         name='bk-selectie'),

    path('selectie/<deelkamp_pk>/bestand/',
         view_indiv.LijstBkSelectieAlsBestandView.as_view(),
         name='bk-selectie-als-bestand'),

    path('selectie/wijzig-status-bk-deelnemer/<deelnemer_pk>/',
         view_indiv.WijzigStatusBkDeelnemerView.as_view(),
         name='wijzig-status-bk-deelnemer'),

]

# end of file
