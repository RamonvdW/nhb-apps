# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# Top level URL configuration

from django.conf import settings
from django.conf.urls import include
from django.urls import path
from django.contrib import admin
from Plein.views import site_root_view
from Plein.views_fout import (site_handler403_permission_denied,
                              site_handler404_page_not_found,
                              site_handler500_internal_server_error)
from Beheer.views import BeheerAdminSite

# replace the admin site
admin.site.__class__ = BeheerAdminSite

handler403 = site_handler403_permission_denied
handler404 = site_handler404_page_not_found
handler500 = site_handler500_internal_server_error

urlpatterns = [
    path('',                                site_root_view),
    path('account/',                        include('Account.urls')),
    path('beheer/',                         admin.site.urls),
    path('bondscompetities/hist/',          include('HistComp.urls')),
    path('bondscompetities/regio/',         include('CompRegio.urls')),
    path('bondscompetities/rk/',            include('CompRayon.urls')),
    path('bondscompetities/scores/',        include('CompScores.urls')),
    path('bondscompetities/uitslagen/',     include('CompUitslagen.urls')),
    path('bondscompetities/',               include('Competitie.urls')),
    path('functie/',                        include('Functie.urls')),
    path('handleiding/',                    include('Handleiding.urls')),
    path('kalender/',                       include('Kalender.urls')),
    path('logboek/',                        include('Logboek.urls')),
    path('overig/',                         include('Overig.urls')),
    path('plein/',                          include('Plein.urls')),
    path('records/',                        include('Records.urls')),
    path('sporter/',                        include('Sporter.urls')),
    path('sporter/bondspas/',               include('Bondspas.urls')),
    path('score/',                          include('Score.urls')),
    path('taken/',                          include('Taken.urls')),
    path('vereniging/',                     include('Vereniging.urls'))
]

if settings.ENABLE_WIKI:    # pragma: no cover
    # activeer single sign-on functionaliteit
    urlpatterns.append(path('idp/',    include('djangosaml2idp.urls')))

if settings.DEBUG:          # pragma: no cover
    import debug_toolbar
    urlpatterns.insert(0, path('__debug__', include(debug_toolbar.urls)))


# end of file
