# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Opleiding import (view_inschrijven, view_overzicht, view_basiscursus,
                       view_vereniging, view_aanmeldingen, view_afmelden,
                       view_manager, view_aanpassingen)

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

    # vereniging
    path('vereniging/lijst/',
         view_vereniging.VerenigingOpleidingenView.as_view(),
         name='vereniging'),

    path('aanmeldingen/<opleiding_pk>/',
         view_aanmeldingen.OpleidingAanmeldingenView.as_view(),
         name='aanmeldingen'),

    path('aanmeldingen/<opleiding_pk>/download/csv/',
         view_aanmeldingen.DownloadAanmeldingenBestandCSV.as_view(),
         name='download-aanmeldingen-csv'),

    path('details-aanmelding/<inschrijving_pk>/',
         view_aanmeldingen.OpleidingDetailsAanmeldingView.as_view(),
         name='details-aanmelding'),

    # afmelden door beheerder evenement (POST)
    path('afmelden/<inschrijving_pk>/',
         view_afmelden.AfmeldenView.as_view(),
         name='afmelden'),

    path('details-afmelding/<afmelding_pk>/',
         view_aanmeldingen.OpleidingDetailsAfmeldingView.as_view(),
         name='details-afmelding'),

    # manager
    path('manager/',
         view_manager.ManagerOpleidingenView.as_view(),
         name='manager'),

    path('manager/niet-ingeschreven/',
         view_manager.NietIngeschrevenView.as_view(),
         name='niet-ingeschreven'),

    # aanpassingen persoonsgegevens
    path('manager/aanpassingen/',
         view_aanpassingen.AanpassingenView.as_view(),
         name='aanpassingen'),

    path('manager/toevoegen/',
         view_manager.OpleidingToevoegenView.as_view(),
         name='toevoegen'),

    path('manager/wijzig/<opleiding_pk>/',
         view_manager.WijzigOpleidingView.as_view(),
         name='wijzig-opleiding'),

    path('manager/wijzig/<opleiding_pk>/data-en-locaties/wijzig/<moment_pk>/',
         view_manager.WijzigMomentView.as_view(),
         name='wijzig-moment'),
]

# end of file
