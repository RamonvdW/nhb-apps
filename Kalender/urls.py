# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import (view_vereniging, view_manager,
               view_wijzig_wedstrijd, view_wijzig_sessies,
               view_landing_page, view_maand, view_inschrijven)

app_name = 'Kalender'

urlpatterns = [

    # wedstrijden
    path('',
         view_landing_page.KalenderLandingPageView.as_view(),
         name='landing-page'),

    path('pagina-<int:jaar>-<str:maand>/',
         view_maand.KalenderMaandView.as_view(),
         name='maand'),

    path('<wedstrijd_pk>/info/',
         view_maand.WedstrijdInfoView.as_view(),
         name='wedstrijd-info'),

    # inschrijven
    path('inschrijven/<wedstrijd_pk>/sporter/',
         view_inschrijven.WedstrijdInschrijvenSporter.as_view(),
         name='inschrijven-sporter'),

    path('inschrijven/<wedstrijd_pk>/groep/',
         view_inschrijven.WedstrijdInschrijvenGroepje.as_view(),
         name='inschrijven-groepje'),

    path('inschrijven/<wedstrijd_pk>/familie/',
         view_inschrijven.WedstrijdInschrijvenFamilie.as_view(),
         name='inschrijven-familie'),

    # toevoegen aan winkelwagentje
    path('inschrijven/toevoegen/',
         view_inschrijven.ToevoegenView.as_view(),
         name='inschrijven-toevoegen'),


    # vereniging
    path('vereniging/',
         view_vereniging.VerenigingKalenderWedstrijdenView.as_view(),
         name='vereniging'),

    # wedstrijd
    path('vereniging/kies-type/',
         view_vereniging.NieuweWedstrijdKiesType.as_view(),
         name='nieuwe-wedstrijd-kies-type'),

    # manager competitiezaken
    path('manager/',
         view_manager.KalenderManagerView.as_view(),
         name='manager'),


    path('<wedstrijd_pk>/wijzig/',
         view_wijzig_wedstrijd.WijzigKalenderWedstrijdView.as_view(),
         name='wijzig-wedstrijd'),

    path('<wedstrijd_pk>/zet-status/',
         view_wijzig_wedstrijd.ZetStatusKalenderWedstrijdView.as_view(),
         name='zet-status'),

    path('<wedstrijd_pk>/sessies/',
         view_wijzig_sessies.KalenderWedstrijdSessiesView.as_view(),
         name='wijzig-sessies'),

    path('<wedstrijd_pk>/sessies/<sessie_pk>/wijzig/',
         view_wijzig_sessies.WijzigKalenderWedstrijdSessieView.as_view(),
         name='wijzig-sessie'),
]

# end of file
