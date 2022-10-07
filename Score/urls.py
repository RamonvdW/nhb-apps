# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Score import view_scoregeschiedenis


app_name = 'Score'

urlpatterns = [
    path('geschiedenis/',
         view_scoregeschiedenis.ScoreGeschiedenisView.as_view(),
         name='geschiedenis')
]

# end of file
