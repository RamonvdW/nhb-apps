# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from CompUitslagen import (view_bk_indiv, view_bk_teams,
                           view_rk_indiv, view_rk_teams,
                           view_regio_indiv, view_regio_teams,
                           view_ver_indiv, view_ver_teams)

app_name = 'CompUitslagen'

# basis = /bondscompetities/uitslagen/

urlpatterns = [

    # competitie uitslagen
    path('<comp_pk_of_seizoen>/vereniging/<ver_nr>/individueel/<comp_boog>/',
         view_ver_indiv.UitslagenVerenigingIndivView.as_view(),
         name='uitslagen-vereniging-indiv-n'),

    path('<comp_pk_of_seizoen>/vereniging/<ver_nr>/teams/<team_type>/',
         view_ver_teams.UitslagenVerenigingTeamsView.as_view(),
         name='uitslagen-vereniging-teams-n'),

    path('<comp_pk_of_seizoen>/vereniging/<comp_boog>/',
         view_ver_indiv.UitslagenVerenigingIndivView.as_view(),
         name='uitslagen-vereniging-indiv'),

    # regio
    path('<comp_pk_of_seizoen>/regio-individueel/<regio_nr>/<comp_boog>/',
         view_regio_indiv.UitslagenRegioIndivView.as_view(),
         name='uitslagen-regio-indiv-n'),

    path('<comp_pk_of_seizoen>/regio-individueel/<comp_boog>/',
         view_regio_indiv.UitslagenRegioIndivView.as_view(),
         name='uitslagen-regio-indiv'),

    path('<comp_pk_of_seizoen>/regio-teams/<team_type>/',
         view_regio_teams.UitslagenRegioTeamsView.as_view(),
         name='uitslagen-regio-teams'),

    path('<comp_pk_of_seizoen>/regio-teams/<regio_nr>/<team_type>/',
         view_regio_teams.UitslagenRegioTeamsView.as_view(),
         name='uitslagen-regio-teams-n'),

    # RK
    path('<comp_pk_of_seizoen>/rk-individueel/<comp_boog>/',
         view_rk_indiv.UitslagenRayonIndivView.as_view(),
         name='uitslagen-rk-indiv'),

    path('<comp_pk_of_seizoen>/rk-individueel/<rayon_nr>/<comp_boog>/',
         view_rk_indiv.UitslagenRayonIndivView.as_view(),
         name='uitslagen-rk-indiv-n'),

    path('<comp_pk_of_seizoen>/rk-teams/<team_type>/',
         view_rk_teams.UitslagenRayonTeamsView.as_view(),
         name='uitslagen-rk-teams'),

    path('<comp_pk_of_seizoen>/rk-teams/<rayon_nr>/<team_type>/',
         view_rk_teams.UitslagenRayonTeamsView.as_view(),
         name='uitslagen-rk-teams-n'),

    # BK
    path('<comp_pk_of_seizoen>/bk-individueel/<comp_boog>/',
         view_bk_indiv.UitslagenBKIndivView.as_view(),
         name='uitslagen-bk-indiv'),

    path('<comp_pk_of_seizoen>/bk-teams/<team_type>/',
         view_bk_teams.UitslagenBKTeamsView.as_view(),
         name='uitslagen-bk-teams'),
]

# end of file
