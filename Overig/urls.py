# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import view_feedback, view_tijdelijke_url, view_activiteit


app_name = 'Overig'

urlpatterns = [
    path('activiteit/',
         view_activiteit.ActiviteitView.as_view(),
         name='activiteit'),

    path('feedback/bedankt/',
         view_feedback.SiteFeedbackBedanktView.as_view(),
         name='feedback-bedankt'),

    # alleen voor de GET van het formulier
    path('feedback/<bevinding>/<op_pagina>/',
         view_feedback.SiteFeedbackView.as_view(),
         name='feedback-bevinding'),

    # alleen voor de POST van het formulier
    path('feedback/formulier/',
         view_feedback.SiteFeedbackView.as_view(),
         name='feedback-formulier'),

    # overzicht van verkregen feedback
    path('feedback/inzicht/',
         view_feedback.SiteFeedbackInzichtView.as_view(),
         name='feedback-inzicht'),


    # tijdelijke url dispatcher
    path('url/<code>/',
         view_tijdelijke_url.SiteTijdelijkeUrlView.as_view(),
         name='tijdelijke-url'),
]

# end of file
