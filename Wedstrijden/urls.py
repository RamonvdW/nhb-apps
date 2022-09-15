# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Wedstrijden import (view_vereniging, view_manager, view_wijzig_wedstrijd, view_wijzig_sessies,
                         view_inschrijven, view_aanmeldingen, view_kortingscodes)

app_name = 'Wedstrijden'

urlpatterns = [

    # inschrijven
    path('<wedstrijd_pk>/info/',
         view_inschrijven.WedstrijdInfoView.as_view(),
         name='wedstrijd-info'),

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


    # afmelden
    path('afmelden/<inschrijving_pk>/',
         view_aanmeldingen.AfmeldenView.as_view(),
         name='afmelden'),


    # vereniging
    path('vereniging/',
         view_vereniging.VerenigingWedstrijdenView.as_view(),
         name='vereniging'),

    path('vereniging/kies-type/',
         view_vereniging.NieuweWedstrijdKiesType.as_view(),
         name='nieuwe-wedstrijd-kies-type'),


    # kortingscodes
    path('vereniging/kortingscodes/',
         view_kortingscodes.VerenigingKortingcodesView.as_view(),
         name='vereniging-codes'),

    path('vereniging/kortingscodes/nieuw/',
         view_kortingscodes.NieuweKortingcodesView.as_view(),
         name='vereniging-codes-nieuw-kies'),

    path('vereniging/kortingscodes/wijzig/<korting_pk>/',
         view_kortingscodes.VerenigingWijzigKortingcodesView.as_view(),
         name='vereniging-wijzig-code'),


    # manager
    path('manager/',
         view_manager.KalenderManagerView.as_view(),
         name='manager'),

    path('manager/<status>/',
         view_manager.KalenderManagerView.as_view(),
         name='manager-status'),


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
