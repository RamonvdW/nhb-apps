# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from CompUitslagen import view_uitslagen_bk, view_uitslagen_rk, view_uitslagen_regio, view_uitslagen_vereniging

app_name = 'CompUitslagen'

urlpatterns = [

    # competitie uitslagen
    path('<comp_pk>/<comp_boog>/vereniging/<ver_nr>/individueel/',
         view_uitslagen_vereniging.UitslagenVerenigingIndivView.as_view(),
         name='uitslagen-vereniging-indiv-n'),

    path('<comp_pk>/<team_type>/vereniging/<ver_nr>/teams/',
         view_uitslagen_vereniging.UitslagenVerenigingTeamsView.as_view(),
         name='uitslagen-vereniging-teams-n'),

    path('<comp_pk>/<comp_boog>/vereniging/',
         view_uitslagen_vereniging.UitslagenVerenigingIndivView.as_view(),
         name='uitslagen-vereniging-indiv'),

    # regio
    path('<comp_pk>/<comp_boog>/regio-individueel/<regio_nr>/',
         view_uitslagen_regio.UitslagenRegioIndivView.as_view(),
         name='uitslagen-regio-indiv-n'),

    path('<comp_pk>/<comp_boog>/alle/regio-individueel/<regio_nr>/',        # voor backwards compatibility
         view_uitslagen_regio.UitslagenRegioIndivView.as_view(),
         name='uitslagen-regio-indiv-n-alle'),

    path('<comp_pk>/<comp_boog>/zes/regio-individueel/<regio_nr>/',         # voor backwards compatibility
         view_uitslagen_regio.UitslagenRegioIndivView.as_view(),
         name='uitslagen-regio-indiv-n-zes'),

    path('<comp_pk>/<comp_boog>/regio-individueel/',
         view_uitslagen_regio.UitslagenRegioIndivView.as_view(),
         name='uitslagen-regio-indiv'),

    path('<comp_pk>/<comp_boog>/alle/regio-individueel/',                   # voor backwards compatibility
         view_uitslagen_regio.UitslagenRegioIndivView.as_view(),
         name='uitslagen-regio-indiv-alle'),

    path('<comp_pk>/<comp_boog>/zes/regio-individueel/',                    # voor backwards compatibility
         view_uitslagen_regio.UitslagenRegioIndivView.as_view(),
         name='uitslagen-regio-indiv-zes'),

    path('<comp_pk>/<team_type>/regio-teams/',
         view_uitslagen_regio.UitslagenRegioTeamsView.as_view(),
         name='uitslagen-regio-teams'),

    path('<comp_pk>/<team_type>/regio-teams/<regio_nr>/',
         view_uitslagen_regio.UitslagenRegioTeamsView.as_view(),
         name='uitslagen-regio-teams-n'),

    # rayon
    path('<comp_pk>/<comp_boog>/rk-individueel/',
         view_uitslagen_rk.UitslagenRayonIndivView.as_view(),
         name='uitslagen-rk-indiv'),

    path('<comp_pk>/<comp_boog>/rk-individueel/<rayon_nr>/',
         view_uitslagen_rk.UitslagenRayonIndivView.as_view(),
         name='uitslagen-rk-indiv-n'),

    path('<comp_pk>/<team_type>/rk-teams/',
         view_uitslagen_rk.UitslagenRayonTeamsView.as_view(),
         name='uitslagen-rk-teams'),

    path('<comp_pk>/<team_type>/rk-teams/<rayon_nr>/',
         view_uitslagen_rk.UitslagenRayonTeamsView.as_view(),
         name='uitslagen-rk-teams-n'),

    # bond
    path('<comp_pk>/<comp_boog>/bk-individueel/',
         view_uitslagen_bk.UitslagenBKIndivView.as_view(),
         name='uitslagen-bk-indiv'),

    path('<comp_pk>/<comp_boog>/bond-individueel/',         # FUTURE: tijdelijk tot afsluiten seizoen 2022/2023
         view_uitslagen_bk.UitslagenBKIndivView.as_view(),
         name='uitslagen-bk-indiv-oud'),

    path('<comp_pk>/<team_type>/bk-teams/',
         view_uitslagen_bk.UitslagenBKTeamsView.as_view(),
         name='uitslagen-bk-teams'),

]

# end of file
