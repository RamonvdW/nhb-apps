# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# Top level URL configuration

from django.conf import settings
from django.conf.urls import include
from django.urls import path
from Plein.views import site_root_view
from django.contrib import admin

urlpatterns = [
    path('',         site_root_view),
    path('account/', include('Account.urls')),
    path('plein/',   include('Plein.urls')),
    path('hist/',    include('HistComp.urls')),
    path('records/', include('Records.urls')),
    path('overig/',  include('Overig.urls')),
    path('admin/',   admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__', include(debug_toolbar.urls)),
    ] + urlpatterns

# end of file
