# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Vereniging import view_overzicht, view_ledenlijst, view_leden_voorkeuren, view_leden_leeftijdsklassen, view_verenigingen

app_name = 'Vereniging'

# basis: /vereniging/

urlpatterns = [

    # overzicht
    path('',
         view_overzicht.OverzichtView.as_view(),
         name='overzicht'),

    # ledenlijst
    path('leden-lijst/',
         view_ledenlijst.LedenLijstView.as_view(),
         name='ledenlijst'),

    # leden leeftijdsklassen / wedstrijdklassen
    path('leden-leeftijdsklassen/',
         view_leden_leeftijdsklassen.LedenLeeftijdsklassenView.as_view(),
         name='leden-leeftijdsklassen'),

    # leden voorkeuren
    path('leden-voorkeuren/',
         view_leden_voorkeuren.LedenVoorkeurenView.as_view(),
         name='leden-voorkeuren'),


    # lijst verenigingen
    path('lijst/',
         view_verenigingen.LijstVerenigingenView.as_view(),
         name='lijst'),

    # voor gebruik vanuit de lijst van verenigingen
    path('lijst/<ver_nr>/',
         view_verenigingen.VerenigingDetailsView.as_view(),
         name='lijst-details'),


    # voor de BB
    path('contact-geen-beheerders/',
         view_verenigingen.GeenBeheerdersView.as_view(),
         name='contact-geen-beheerders')
]

# end of file
