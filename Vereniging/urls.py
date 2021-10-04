# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import (view_accommodatie, view_externe_locaties, view_overzicht, view_ledenlijst,
               view_aanmelden, view_lijst_rk, view_lijst_verenigingen, view_wieschietwaar)

app_name = 'Vereniging'

urlpatterns = [

    path('',
         view_overzicht.OverzichtView.as_view(),
         name='overzicht'),

    path('leden-lijst/',
         view_ledenlijst.LedenLijstView.as_view(),
         name='ledenlijst'),

    path('leden-voorkeuren/',
         view_ledenlijst.LedenVoorkeurenView.as_view(),
         name='leden-voorkeuren'),

    path('leden-aanmelden/competitie/<comp_pk>/',
         view_aanmelden.LedenAanmeldenView.as_view(),
         name='leden-aanmelden'),

    path('leden-ingeschreven/competitie/<deelcomp_pk>/',
         view_aanmelden.LedenIngeschrevenView.as_view(),
         name='leden-ingeschreven'),

    path('competitie/<deelcomp_pk>/wie-schiet-waar/',
         view_wieschietwaar.WieSchietWaarView.as_view(),
         name='wie-schiet-waar'),


    # Accommodatie
    path('accommodaties/lijst/',
         view_lijst_verenigingen.LijstVerenigingenView.as_view(),
         name='lijst-verenigingen'),

    path('accommodaties/details/<vereniging_pk>/',
         view_accommodatie.AccommodatieDetailsView.as_view(),
         name='accommodatie-details'),

    path('accommodatie-details/<vereniging_pk>/',
         view_accommodatie.VerenigingAccommodatieDetailsView.as_view(),
         name='vereniging-accommodatie-details'),

    path('externe-locaties/<vereniging_pk>/',
         view_externe_locaties.ExterneLocatiesView.as_view(),
         name='externe-locaties'),

    path('externe-locaties/<vereniging_pk>/details/<locatie_pk>/',
         view_externe_locaties.ExterneLocatieDetailsView.as_view(),
         name='locatie-details'),


    path('lijst-rayonkampioenschappen/<rk_deelcomp_pk>/alles/',
         view_lijst_rk.VerenigingLijstRkSelectieAllesView.as_view(),
         name='lijst-rk-alles'),

    path('lijst-rayonkampioenschappen/<rk_deelcomp_pk>/',
         view_lijst_rk.VerenigingLijstRkSelectieView.as_view(),
         name='lijst-rk'),

    path('contact-geen-beheerders/',
         view_lijst_verenigingen.GeenBeheerdersView.as_view(),
         name='contact-geen-beheerders')
]

# end of file
