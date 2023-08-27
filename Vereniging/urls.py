# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Vereniging import view_overzicht, view_ledenlijst, view_lijst

app_name = 'Vereniging'

# basis: /vereniging/

urlpatterns = [

    # overzicht
    path('',
         view_overzicht.OverzichtView.as_view(),
         name='overzicht'),

    # ledenlijst - normaal
    path('leden-lijst/',
         view_ledenlijst.LedenLijstView.as_view(),
         name='ledenlijst'),

    path('leden-voorkeuren/',
         view_ledenlijst.LedenVoorkeurenView.as_view(),
         name='leden-voorkeuren'),


    # lijst verenigingen
    path('lijst/',
         view_lijst.LijstView.as_view(),
         name='lijst'),

    # voor gebruik vanuit de lijst van verenigingen
    path('lijst/<ver_nr>/',
         view_lijst.DetailsView.as_view(),
         name='lijst-details'),


    # voor de BB
    path('contact-geen-beheerders/',
         view_lijst.GeenBeheerdersView.as_view(),
         name='contact-geen-beheerders')
]

# end of file
