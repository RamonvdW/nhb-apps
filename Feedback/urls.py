# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import view_feedback


app_name = 'Feedback'

urlpatterns = [

    # overzicht van verkregen feedback
    path('inzicht/',
         view_feedback.InzichtView.as_view(),
         name='inzicht'),

    path('bedankt/',
         view_feedback.BedanktView.as_view(),
         name='bedankt'),

    # alleen voor de POST van het formulier
    path('formulier/',
         view_feedback.KrijgFeedbackView.as_view(),
         name='formulier'),

    # alleen voor de GET van het formulier
    path('<bevinding>/<op_pagina>/<path:volledige_url>/',
         view_feedback.KrijgFeedbackView.as_view(),
         name='bevinding'),
]

# end of file
