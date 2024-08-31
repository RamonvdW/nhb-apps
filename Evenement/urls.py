# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Evenement import view_aanmeldingen, view_afmelden, view_details, view_inschrijven, view_vereniging

app_name = 'Evenement'

# basis = /kalender/evenement/

urlpatterns = [
    # evenement details (met knoppen om in te schrijven)
    path('details/<evenement_pk>/',
         view_details.DetailsView.as_view(),
         name='details'),

    # afmelden door beheerder evenement (POST)
    path('afmelden/<inschrijving_pk>/',
         view_afmelden.AfmeldenView.as_view(),
         name='afmelden'),

    # inschrijven
    path('inschrijven/<evenement_pk>/sporter/',
         view_inschrijven.InschrijvenSporterView.as_view(),
         name='inschrijven-sporter'),

    path('inschrijven/<evenement_pk>/groep/',
         view_inschrijven.InschrijvenGroepjeView.as_view(),
         name='inschrijven-groepje'),

    path('inschrijven/<evenement_pk>/familie/<lid_nr>/',
         view_inschrijven.InschrijvenFamilieView.as_view(),
         name='inschrijven-familie-lid'),

    path('inschrijven/<evenement_pk>/familie/',
         view_inschrijven.InschrijvenFamilieView.as_view(),
         name='inschrijven-familie'),

    # toevoegen aan winkelwagentje
    path('inschrijven/toevoegen-mandje/',
         view_inschrijven.ToevoegenAanMandjeView.as_view(),
         name='inschrijven-toevoegen-aan-mandje'),


    # vereniging
    path('vereniging/lijst/',
         view_vereniging.VerenigingEvenementenView.as_view(),
         name='vereniging'),


    path('aanmeldingen/<evenement_pk>/',
         view_aanmeldingen.EvenementAanmeldingenView.as_view(),
         name='aanmeldingen'),

    path('details-aanmelding/<inschrijving_pk>/',
         view_aanmeldingen.EvenementDetailsAanmeldingView.as_view(),
         name='details-aanmelding'),

    path('aanmeldingen/<evenement_pk>/download/csv/',
         view_aanmeldingen.DownloadAanmeldingenBestandCSV.as_view(),
         name='download-aanmeldingen-csv'),

    path('details-afmelding/<afmelding_pk>/',
         view_aanmeldingen.EvenementDetailsAfmeldingView.as_view(),
         name='details-afmelding'),
]

# end of file
