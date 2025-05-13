# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Wedstrijden import (view_vereniging, view_manager, view_korting,
                         view_wijzig_wedstrijd, view_wijzig_sessies,
                         view_kwalificatie_scores, view_wedstrijd_details,
                         view_aanmeldingen, view_aanmelding_details)

app_name = 'Wedstrijden'

# basis = /wedstrijden/

urlpatterns = [

    # wedstrijden
    path('vereniging/lijst/',
         view_vereniging.VerenigingWedstrijdenView.as_view(),
         name='vereniging'),

    path('vereniging/lijst-zes-maanden/',
         view_vereniging.VerenigingZesMaandenWedstrijdenView.as_view(),
         name='vereniging-zes-maanden'),

    path('vereniging/lijst-een-jaar/',
         view_vereniging.VerenigingEenJaarWedstrijdenView.as_view(),
         name='vereniging-een-jaar'),

    path('vereniging/lijst-twee-jaar/',
         view_vereniging.VerenigingTweeJaarWedstrijdenView.as_view(),
         name='vereniging-twee-jaar'),

    path('vereniging/kies-type/',
         view_vereniging.NieuweWedstrijdKiesType.as_view(),
         name='nieuwe-wedstrijd-kies-type'),


    # kortingen
    path('vereniging/kortingen/',
         view_korting.KortingenView.as_view(),
         name='vereniging-kortingen'),

    path('vereniging/kortingen/nieuw/',
         view_korting.KiesNieuweKortingView.as_view(),
         name='vereniging-korting-nieuw-kies'),

    path('vereniging/kortingen/wijzig/<korting_pk>/',
         view_korting.WijzigKortingView.as_view(),
         name='vereniging-korting-wijzig'),


    # wedstrijd details
    path('<wedstrijd_pk>/details/',
         view_wedstrijd_details.WedstrijdDetailsView.as_view(),
         name='wedstrijd-details'),


    # manager
    path('manager/',
         view_manager.KalenderManagerView.as_view(),
         name='manager'),

    path('manager/<status>/',
         view_manager.KalenderManagerView.as_view(),
         name='manager-status'),

    path('manager/check-kwalificatie-scores/<wedstrijd_pk>/',
         view_kwalificatie_scores.CheckKwalificatieScoresView.as_view(),
         name='check-kwalificatie-scores'),

    path('manager/check-kwalificatie-scores/wedstrijd/<score_pk>/',
         view_kwalificatie_scores.CheckKwalificatieScoresWedstrijdView.as_view(),
         name='check-kwalificatie-scores-wedstrijd'),


    # gedeeld (TODO: met wie?)
    path('<wedstrijd_pk>/wijzig/',
         view_wijzig_wedstrijd.WijzigWedstrijdView.as_view(),
         name='wijzig-wedstrijd'),

    path('<wedstrijd_pk>/zet-status/',
         view_manager.ZetStatusWedstrijdView.as_view(),
         name='zet-status'),

    path('<wedstrijd_pk>/sessies/',
         view_wijzig_sessies.WedstrijdSessiesView.as_view(),
         name='wijzig-sessies'),

    path('<wedstrijd_pk>/sessies/<sessie_pk>/wijzig/',
         view_wijzig_sessies.WijzigWedstrijdSessieView.as_view(),
         name='wijzig-sessie'),


    # aanmeldingen
    path('<wedstrijd_pk>/aanmeldingen/',
         view_aanmeldingen.WedstrijdAanmeldingenView.as_view(),
         name='aanmeldingen'),

    path('<wedstrijd_pk>/aanmeldingen/download/tsv/',
         view_aanmeldingen.DownloadAanmeldingenBestandTSV.as_view(),
         name='download-aanmeldingen-tsv'),

    path('<wedstrijd_pk>/aanmeldingen/download/csv/',
         view_aanmeldingen.DownloadAanmeldingenBestandCSV.as_view(),
         name='download-aanmeldingen-csv'),


    # aanmelding details
    path('details-aanmelding/<inschrijving_pk>/',
         view_aanmelding_details.WedstrijdAanmeldingDetailsView.as_view(),
         name='details-aanmelding'),

    path('aanpassen/<inschrijving_pk>/',
         view_aanmelding_details.AanpassenView.as_view(),
         name='aanpassen'),

    path('afmelden/<inschrijving_pk>/',
         view_aanmelding_details.AfmeldenView.as_view(),
         name='afmelden'),
]

# end of file
