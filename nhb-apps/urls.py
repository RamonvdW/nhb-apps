# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# Top level URL configuration

from django.conf import settings
from django.conf.urls import include
from django.urls import path
from django.contrib import admin
from Plein.views import site_root_view
from Beheer.views import BeheerAdminSite

# replace the admin site
admin.site.__class__ = BeheerAdminSite

urlpatterns = [
    path('',            site_root_view),
    path('account/',    include('Account.urls')),
    path('beheer/',     admin.site.urls),
    path('competitie/', include('Competitie.urls')),
    path('hist/',       include('HistComp.urls')),
    path('overig/',     include('Overig.urls')),
    path('plein/',      include('Plein.urls')),
    path('logboek/',    include('Logboek.urls')),
    path('records/',    include('Records.urls')),
    path('idp/',        include('djangosaml2idp.urls')),        # single sign-on
]

if settings.DEBUG:          # pragma: no cover
    import debug_toolbar
    urlpatterns = [path('__debug__', include(debug_toolbar.urls)), ] + urlpatterns

# end of file
