# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from TijdelijkeCodes import view_ontvanger

app_name = 'TijdelijkeCodes'

# basis url: site:/tijdelijk-codes/

urlpatterns = [
    # tijdelijke url dispatcher
    path('<code>/',
         view_ontvanger.OntvangerView.as_view(),
         name='tijdelijke-url'),
]

# end of file
