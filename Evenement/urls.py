# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Evenement import view_afmelden, view_details, view_inschrijven

app_name = 'Evenement'

# basis = /kalender/evenement/

urlpatterns = [
    # evenement details
    path('details/<evenement_pk>/',
         view_details.DetailsView.as_view(),
         name='details'),

    # afmelden door beheerder evenement (POST)
    path('afmelden/<inschrijving_pk>/',
         view_afmelden.AfmeldenView.as_view(),
         name='afmelden'),

    # inschrijven
    path('inschrijven/<evenement_pk>/sporter/',
         view_inschrijven.InschrijvenSporter.as_view(),
         name='inschrijven-sporter'),

    path('inschrijven/<evenement_pk>/groep/<lid_nr>/',
         view_inschrijven.InschrijvenGroepje.as_view(),
         name='inschrijven-groepje-lid'),

    path('inschrijven/<evenement_pk>/groep/',
         view_inschrijven.InschrijvenGroepje.as_view(),
         name='inschrijven-groepje'),

    path('inschrijven/<evenement_pk>/familie/<lid_nr>/',
         view_inschrijven.InschrijvenFamilie.as_view(),
         name='inschrijven-familie-lid-boog'),

    path('inschrijven/<evenement_pk>/familie/',
         view_inschrijven.InschrijvenFamilie.as_view(),
         name='inschrijven-familie'),

    # path('inschrijven/<evenement_pk>/handmatig/<lid_nr>/<boog_afk>/',
    #      view_inschrijven.InschrijvenHandmatig.as_view(),
    #      name='inschrijven-handmatig-lid-boog'),

    # path('inschrijven/<evenement_pk>/handmatig/',
    #      view_inschrijven.InschrijvenHandmatig.as_view(),
    #      name='inschrijven-handmatig'),

    # toevoegen aan winkelwagentje
    path('inschrijven/toevoegen-mandje/',
         view_inschrijven.ToevoegenAanMandjeView.as_view(),
         name='inschrijven-toevoegen-aan-mandje'),
]

# end of file
