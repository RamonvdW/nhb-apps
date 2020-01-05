# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from django.conf.urls import include
from . import views
import Logboek.views
import BasisTypen.views


app_name = 'Overig'

urlpatterns = [
    path('feedback/bedankt/',
         views.SiteFeedbackBedanktView.as_view(),
         name='feedback-bedankt'),

    # alleen voor de GET van het formulier
    path('feedback/<bevinding>/<op_pagina>/',
         views.SiteFeedbackView.as_view(),
         name='feedback-bevinding'),

    # alleen voor de POST van het formulier
    path('feedback/formulier/',
         views.SiteFeedbackView.as_view(),
         name='feedback-formulier'),

    # overzicht van verkregen feedback
    path('feedback/inzicht/',
         views.SiteFeedbackInzichtView.as_view(),
         name='feedback-inzicht'),

    # tijdelijke url dispatcher
    path('url/<code>/',
         views.SiteTijdelijkeUrlView.as_view(),
         name='tijdelijke-url'),

    # logboek
    path('logboek/',
         Logboek.views.LogboekView.as_view(),
         name='logboek'),

    # instellingen volgende competitie
    # TODO: move to other app
    path('instellingen-volgende-competitie/',
         BasisTypen.views.InstellingenVolgendeCompetitieView.as_view(),
         name='instellingen-volgende-competitie'),

    # TODO: move to other app
    path('aanvangsgemiddelden/',
         BasisTypen.views.AanvangsgemiddeldenView.as_view(),
         name='aanvangsgemiddelden'),

]

# end of file
