# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import view_uitslagen_bond, view_uitslagen_rayon, view_uitslagen_regio, view_uitslagen_vereniging

app_name = 'CompUitslagen'

urlpatterns = [

    # competitie uitslagen
    path('<comp_pk>/<comp_boog>/vereniging/<ver_nr>/individueel/',
         view_uitslagen_vereniging.UitslagenVerenigingIndivView.as_view(),
         name='uitslagen-vereniging-indiv-n'),

    path('<comp_pk>/<team_type>/vereniging/<ver_nr>/teams/',
         view_uitslagen_vereniging.UitslagenVerenigingTeamsView.as_view(),
         name='uitslagen-vereniging-teams-n'),

    # TODO: wordt deze gebruikt?
    path('<comp_pk>/<comp_boog>/vereniging/',
         view_uitslagen_vereniging.UitslagenVerenigingIndivView.as_view(),
         name='uitslagen-vereniging-indiv'),

    # regio
    path('<comp_pk>/<comp_boog>/<zes_scores>/regio-individueel/<regio_nr>/',
         view_uitslagen_regio.UitslagenRegioIndivView.as_view(),
         name='uitslagen-regio-indiv-n'),

    path('<comp_pk>/<comp_boog>/<zes_scores>/regio-individueel/',
         view_uitslagen_regio.UitslagenRegioIndivView.as_view(),
         name='uitslagen-regio-indiv'),

    path('<comp_pk>/<team_type>/regio-teams/',
         view_uitslagen_regio.UitslagenRegioTeamsView.as_view(),
         name='uitslagen-regio-teams'),

    path('<comp_pk>/<team_type>/regio-teams/<regio_nr>/',
         view_uitslagen_regio.UitslagenRegioTeamsView.as_view(),
         name='uitslagen-regio-teams-n'),

    # rayon
    path('<comp_pk>/<comp_boog>/rayon-individueel/',
         view_uitslagen_rayon.UitslagenRayonIndivView.as_view(),
         name='uitslagen-rayon-indiv'),

    path('<comp_pk>/<comp_boog>/rayon-individueel/<rayon_nr>/',
         view_uitslagen_rayon.UitslagenRayonIndivView.as_view(),
         name='uitslagen-rayon-indiv-n'),

    path('<comp_pk>/<team_type>/rayon-teams/',
         view_uitslagen_rayon.UitslagenRayonTeamsView.as_view(),
         name='uitslagen-rayon-teams'),

    path('<comp_pk>/<team_type>/rayon-teams/<rayon_nr>/',
         view_uitslagen_rayon.UitslagenRayonTeamsView.as_view(),
         name='uitslagen-rayon-teams-n'),

    # bond
    path('<comp_pk>/<comp_boog>/bond/',
         view_uitslagen_bond.UitslagenBondView.as_view(),
         name='uitslagen-bond'),
]

# end of file
