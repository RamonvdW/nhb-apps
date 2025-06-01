# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# Top level URL configuration

from django.urls import path
from django.conf import settings
from django.contrib import admin
from django.conf.urls import include
from Plein.views import site_root_view
from Plein.views_fout import (site_handler403_permission_denied,
                              site_handler404_page_not_found,
                              site_handler500_internal_server_error)

handler403 = site_handler403_permission_denied
handler404 = site_handler404_page_not_found
handler500 = site_handler500_internal_server_error

urlpatterns = [
    path('',                                site_root_view),
    path('account/',                        include('Account.urls')),
    path('account/registreer/',             include('Registreer.urls')),
    path('beheer/',                         admin.site.urls),
    path('bestel/',                         include('Bestelling.urls')),
    path('bestel/betaal/',                  include('Betaal.urls')),
    path('bondscompetities/beheer/',        include('CompBeheer.urls')),
    path('bondscompetities/regio/',         include('CompLaagRegio.urls')),
    path('bondscompetities/rk/',            include('CompLaagRayon.urls')),
    path('bondscompetities/bk/',            include('CompLaagBond.urls')),
    path('bondscompetities/deelnemen/',     include('CompInschrijven.urls')),
    path('bondscompetities/scores/',        include('CompScores.urls')),
    path('bondscompetities/uitslagen/',     include('CompUitslagen.urls')),
    path('bondscompetities/hist/',          include('HistComp.urls')),
    path('bondscompetities/',               include('Competitie.urls')),
    path('bondspas/',                       include('Bondspas.urls')),
    path('feedback/',                       include('Feedback.urls')),
    path('functie/',                        include('Functie.urls')),
    path('kalender/',                       include('Kalender.urls')),
    path('kalender/evenement/',             include('Evenement.urls')),
    path('ledenvoordeel/',                  include('Ledenvoordeel.urls')),
    path('logboek/',                        include('Logboek.urls')),
    path('opleiding/',                      include('Opleiding.urls')),
    path('opleiding/instaptoets/',          include('Instaptoets.urls')),
    path('overig/',                         include('Overig.urls')),
    path('plein/',                          include('Plein.urls')),
    path('records/',                        include('Records.urls')),
    path('scheidsrechter/',                 include('Scheidsrechter.urls')),
    path('sporter/',                        include('Sporter.urls')),
    path('score/',                          include('Score.urls')),
    path('taken/',                          include('Taken.urls')),
    path('tijdelijke-codes/',               include('TijdelijkeCodes.urls')),
    path('vereniging/',                     include('Vereniging.urls')),
    path('vereniging/locatie/',             include('Locatie.urls')),
    path('webwinkel/',                      include('Webwinkel.urls')),
    path('webwinkel/spelden/',              include('Spelden.urls')),
    path('wedstrijden/',                    include('Wedstrijden.urls')),
    path('wedstrijden/inschrijven/',        include('WedstrijdInschrijven.urls')),

    # direct van oude urls naar nieuwe urls
    # path('sporter/bondspas/', lambda request: redirect('ledenpas/', permanent=True)),
]

if settings.ENABLE_DEBUG_TOOLBAR:          # pragma: no cover
    import debug_toolbar
    urlpatterns.insert(0, path('__debug__', include(debug_toolbar.urls)))


# end of file
