# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Bestel import (view_mandje, view_bestelling, view_activiteit, view_overboeking,
                    view_kies_transport, view_afleveradres)

app_name = 'Bestel'

# basis = /bestel/

urlpatterns = [

    path('mandje/verwijderen/<product_pk>/',
         view_mandje.VerwijderProductUitMandje.as_view(),
         name='mandje-verwijder-product'),

    path('mandje/',
         view_mandje.ToonInhoudMandje.as_view(),
         name='toon-inhoud-mandje'),

    path('mandje/transport/',
         view_kies_transport.KiesTransportView.as_view(),
         name='kies-transport'),

    path('mandje/afleveradres/',
         view_afleveradres.WijzigAfleveradresView.as_view(),
         name='wijzig-afleveradres'),

    path('overzicht/',
         view_bestelling.ToonBestellingenView.as_view(),
         name='toon-bestellingen'),

    path('details/<bestel_nr>/',
         view_bestelling.ToonBestellingDetailsView.as_view(),
         name='toon-bestelling-details'),

    path('afrekenen/<bestel_nr>/',
         view_bestelling.BestellingAfrekenenView.as_view(),
         name='bestelling-afrekenen'),

    path('annuleer/<bestel_nr>/',
         view_bestelling.AnnuleerBestellingView.as_view(),
         name='annuleer-bestelling'),

    path('check-status/<bestel_nr>/',
         view_bestelling.DynamicBestellingCheckStatus.as_view(),
         name='dynamic-check-status'),

    path('na-de-betaling/<bestel_nr>/',
         view_bestelling.BestellingAfgerondView.as_view(),
         name='na-de-betaling'),


    # HWL view
    path('vereniging/overboeking-ontvangen/',
         view=view_overboeking.OverboekingOntvangenView.as_view(),
         name='overboeking-ontvangen'),

    # manager view
    path('activiteit/',
         view_activiteit.BestelActiviteitView.as_view(),
         name='activiteit'),

    path('omzet/',
         view_activiteit.BestelOmzetView.as_view(),
         name='omzet'),
]

# end of file
