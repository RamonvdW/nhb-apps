# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from HistComp import views, view_interland, view_regio, view_rk, view_bk

app_name = 'HistComp'

urlpatterns = [

    path('',
         views.HistCompTop.as_view(),
         name='top'),

    path('<seizoen>/<histcomp_type>/',
         views.HistCompTop.as_view(),
         name='seizoen-top'),

    # regio
    path('<seizoen>/<histcomp_type>/regio-individueel/<comp_boog>/',
         view_regio.HistRegioIndivView.as_view(),
         name='uitslagen-regio-indiv'),

    path('<seizoen>/<histcomp_type>/regio-individueel/<comp_boog>/<regio_nr>/',
         view_regio.HistRegioIndivView.as_view(),
         name='uitslagen-regio-indiv-n'),

    path('<seizoen>/<histcomp_type>/regio-teams/<team_type>/',
         view_regio.HistRegioTeamsView.as_view(),
         name='uitslagen-regio-teams'),

    path('<seizoen>/<histcomp_type>/regio-teams/<team_type>/<regio_nr>/',
         view_regio.HistRegioTeamsView.as_view(),
         name='uitslagen-regio-teams-n'),

    # rk
    path('<seizoen>/<histcomp_type>/rk-individueel/<comp_boog>/',
         view_rk.HistRkIndivView.as_view(),
         name='uitslagen-rk-indiv'),

    path('<seizoen>/<histcomp_type>/rk-individueel/<comp_boog>/<rayon_nr>/',
         view_rk.HistRkIndivView.as_view(),
         name='uitslagen-rk-indiv-n'),

    path('<seizoen>/<histcomp_type>/rk-teams/<team_type>/',
         view_rk.HistRkTeamsView.as_view(),
         name='uitslagen-rk-teams'),

    path('<seizoen>/<histcomp_type>/rk-teams/<team_type>/<rayon_nr>/',
         view_rk.HistRkTeamsView.as_view(),
         name='uitslagen-rk-teams-n'),

    # bk
    path('<seizoen>/<histcomp_type>/bk-individueel/<comp_boog>/',
         view_bk.HistBkIndivView.as_view(),
         name='uitslagen-bk-indiv'),

    path('<seizoen>/<histcomp_type>/bk-teams/<team_type>/',
         view_bk.HistBkTeamsView.as_view(),
         name='uitslagen-bk-teams'),


    # TODO: OLD
    path('indiv/<histcomp_pk>/',
         views.HistCompIndivView.as_view(),
         name='indiv'),

    # interland
    path('interland/',
         view_interland.InterlandView.as_view(),
         name='interland'),

    path('interland/als-bestand/<klasse_pk>/',
         view_interland.InterlandAlsBestandView.as_view(),
         name='interland-als-bestand')
]

# end of file
