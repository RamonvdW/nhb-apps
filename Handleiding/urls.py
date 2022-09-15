# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import path
from Handleiding import views

app_name = 'Handleiding'

urlpatterns = [
    path('',
         views.HandleidingView.as_view(),
         name='begin')
]

for pagina in settings.HANDLEIDING_PAGINAS:
    conf = path(pagina + '/', views.HandleidingView.as_view(), name=pagina)
    urlpatterns.append(conf)
# for


# end of file
