# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Competitie import views_info, views_klassengrenzen, views_kies, views_overzicht

app_name = 'Competitie'

# basis = /bondscompetities/

urlpatterns = [

    # openbare pagina's
    path('info/',
         views_info.InfoCompetitieView.as_view(),
         name='info-competitie'),

    path('info/teams/',
         views_info.InfoTeamCompetitieView.as_view(),
         name='info-teamcompetitie'),

    path('info/leeftijden/',
         views_info.redirect_leeftijden,  # oud; redirects naar nieuw
         name='info-leeftijden'),

    path('indoor/',
         views_kies.CompetitieKies18mView.as_view(),
         name='kies-18m'),

    path('25m1pijl/',
         views_kies.CompetitieKies25mView.as_view(),
         name='kies-25m'),

    path('<comp_pk_of_seizoen>/klassengrenzen-tonen/',
         views_klassengrenzen.KlassengrenzenTonenView.as_view(),
         name='klassengrenzen-tonen'),

    path('<comp_pk_of_seizoen>/',
         views_overzicht.CompetitieOverzichtView.as_view(),
         name='overzicht'),

    path('',
         views_kies.CompetitieKiesView.as_view(),
         name='kies'),
]

# end of file
