# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import views_uitslagen

app_name = 'CompUitslagen'

urlpatterns = [

    # competitie uitslagen
    path('<comp_pk>/<comp_boog>/vereniging/<ver_nr>/individueel/',
         views_uitslagen.UitslagenVerenigingIndivView.as_view(),
         name='uitslagen-vereniging-indiv-n'),

    path('<comp_pk>/<team_type>/vereniging/<ver_nr>/teams/',
         views_uitslagen.UitslagenVerenigingTeamsView.as_view(),
         name='uitslagen-vereniging-teams-n'),

    # TODO: wordt deze gebruikt?
    path('<comp_pk>/<comp_boog>/vereniging/',
         views_uitslagen.UitslagenVerenigingIndivView.as_view(),
         name='uitslagen-vereniging-indiv'),

    path('<comp_pk>/<comp_boog>/<zes_scores>/regio-individueel/<regio_nr>/',
         views_uitslagen.UitslagenRegioIndivView.as_view(),
         name='uitslagen-regio-indiv-n'),

    path('<comp_pk>/<comp_boog>/<zes_scores>/regio-individueel/',
         views_uitslagen.UitslagenRegioIndivView.as_view(),
         name='uitslagen-regio-indiv'),

    path('<comp_pk>/<team_type>/regio-teams/',
         views_uitslagen.UitslagenRegioTeamsView.as_view(),
         name='uitslagen-regio-teams'),

    path('<comp_pk>/<team_type>/regio-teams/<regio_nr>/',
         views_uitslagen.UitslagenRegioTeamsView.as_view(),
         name='uitslagen-regio-teams-n'),

    path('<comp_pk>/<comp_boog>/rayon-individueel/',
         views_uitslagen.UitslagenRayonIndivView.as_view(),
         name='uitslagen-rayon-indiv'),

    path('<comp_pk>/<comp_boog>/rayon-individueel/<rayon_nr>/',
         views_uitslagen.UitslagenRayonIndivView.as_view(),
         name='uitslagen-rayon-indiv-n'),

    path('<comp_pk>/<team_type>/rayon-teams/',
         views_uitslagen.UitslagenRayonTeamsView.as_view(),
         name='uitslagen-rayon-teams'),

    path('<comp_pk>/<team_type>/rayon-teams/<rayon_nr>/',
         views_uitslagen.UitslagenRayonTeamsView.as_view(),
         name='uitslagen-rayon-teams-n'),

    path('<comp_pk>/<comp_boog>/bond/',
         views_uitslagen.UitslagenBondView.as_view(),
         name='uitslagen-bond'),
]

# end of file
