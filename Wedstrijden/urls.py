# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Wedstrijden import (view_vereniging, view_manager, view_wijzig_wedstrijd, view_wijzig_sessies,
                         view_inschrijven, view_kwalificatie_scores, view_aanmeldingen, view_korting)

app_name = 'Wedstrijden'

# basis = /wedstrijden/

urlpatterns = [

    # inschrijven
    path('<wedstrijd_pk>/details/',
         view_inschrijven.WedstrijdDetailsView.as_view(),
         name='wedstrijd-details'),

    path('inschrijven/<wedstrijd_pk>/sporter/<boog_afk>/',
         view_inschrijven.WedstrijdInschrijvenSporter.as_view(),
         name='inschrijven-sporter-boog'),

    path('inschrijven/<wedstrijd_pk>/sporter/',
         view_inschrijven.WedstrijdInschrijvenSporter.as_view(),
         name='inschrijven-sporter'),

    path('inschrijven/<wedstrijd_pk>/groep/<lid_nr>/<boog_afk>/',
         view_inschrijven.WedstrijdInschrijvenGroepje.as_view(),
         name='inschrijven-groepje-lid-boog'),

    path('inschrijven/<wedstrijd_pk>/groep/',
         view_inschrijven.WedstrijdInschrijvenGroepje.as_view(),
         name='inschrijven-groepje'),

    path('inschrijven/<wedstrijd_pk>/familie/<lid_nr>/<boog_afk>/',
         view_inschrijven.WedstrijdInschrijvenFamilie.as_view(),
         name='inschrijven-familie-lid-boog'),

    path('inschrijven/<wedstrijd_pk>/familie/',
         view_inschrijven.WedstrijdInschrijvenFamilie.as_view(),
         name='inschrijven-familie'),

    path('inschrijven/<wedstrijd_pk>/handmatig/<lid_nr>/<boog_afk>/',
         view_inschrijven.WedstrijdInschrijvenHandmatig.as_view(),
         name='inschrijven-handmatig-lid-boog'),

    path('inschrijven/<wedstrijd_pk>/handmatig/',
         view_inschrijven.WedstrijdInschrijvenHandmatig.as_view(),
         name='inschrijven-handmatig'),

    # toevoegen aan winkelwagentje
    path('inschrijven/toevoegen-mandje/',
         view_inschrijven.ToevoegenAanMandjeView.as_view(),
         name='inschrijven-toevoegen-aan-mandje'),

    path('inschrijven/kwalificatie-scores-doorgeven/<inschrijving_pk>/',
         view_kwalificatie_scores.KwalificatieScoresOpgevenView.as_view(),
         name='inschrijven-kwalificatie-scores'),


    # afmelden
    path('afmelden/<inschrijving_pk>/',
         view_aanmeldingen.AfmeldenView.as_view(),
         name='afmelden'),


    # vereniging
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


    # gedeeld
    path('<wedstrijd_pk>/wijzig/',
         view_wijzig_wedstrijd.WijzigWedstrijdView.as_view(),
         name='wijzig-wedstrijd'),

    path('<wedstrijd_pk>/zet-status/',
         view_wijzig_wedstrijd.ZetStatusWedstrijdView.as_view(),
         name='zet-status'),

    path('<wedstrijd_pk>/sessies/',
         view_wijzig_sessies.WedstrijdSessiesView.as_view(),
         name='wijzig-sessies'),

    path('<wedstrijd_pk>/sessies/<sessie_pk>/wijzig/',
         view_wijzig_sessies.WijzigWedstrijdSessieView.as_view(),
         name='wijzig-sessie'),

    path('<wedstrijd_pk>/aanmeldingen/',
         view_aanmeldingen.KalenderAanmeldingenView.as_view(),
         name='aanmeldingen'),

    path('<wedstrijd_pk>/aanmeldingen/download/tsv/',
         view_aanmeldingen.DownloadAanmeldingenBestandTSV.as_view(),
         name='download-aanmeldingen-tsv'),

    path('<wedstrijd_pk>/aanmeldingen/download/csv/',
         view_aanmeldingen.DownloadAanmeldingenBestandCSV.as_view(),
         name='download-aanmeldingen-csv'),

    path('details-aanmelding/<inschrijving_pk>/',
         view_aanmeldingen.KalenderDetailsAanmeldingView.as_view(),
         name='details-aanmelding'),
]

# end of file
