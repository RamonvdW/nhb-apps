# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Opleiding import view_inschrijven, view_overzicht, view_basiscursus

app_name = 'Opleiding'

# basis = /opleiding/

urlpatterns = [

    # opleidingen
    path('',
         view_overzicht.OpleidingenOverzichtView.as_view(),
         name='overzicht'),

    path('basiscursus/',
         view_basiscursus.BasiscursusView.as_view(),
         name='basiscursus'),

    path('inschrijven/basiscursus/',
         view_inschrijven.InschrijvenBasiscursusView.as_view(),
         name='inschrijven-basiscursus'),

    # toevoegen aan winkelwagentje (POST only)
    path('inschrijven/toevoegen-mandje/',
         view_inschrijven.ToevoegenAanMandjeView.as_view(),
         name='inschrijven-toevoegen-aan-mandje'),

    path('details/<opleiding_pk>/',
         view_overzicht.OpleidingDetailsView.as_view(),
         name='details'),

    # TODO: implement
    path('manager/',
         view_overzicht.OpleidingenOverzichtView.as_view(),
         name='manager'),

]

# end of file
