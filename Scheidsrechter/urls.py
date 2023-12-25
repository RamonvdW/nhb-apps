# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Scheidsrechter import view_overzicht, view_korps, view_beschikbaarheid, view_wedstrijden

app_name = 'Scheidsrechter'

# basis = /scheidsrechter/

urlpatterns = [
    path('',
         view_overzicht.OverzichtView.as_view(),
         name='overzicht'),

    path('korps/',
         view_korps.KorpsView.as_view(),
         name='korps'),

    path('korps-met-contactgegevens/',
         view_korps.KorpsCSView.as_view(),
         name='korps-met-contactgegevens'),

    path('korps-emailadressen/',
         view_korps.KorpsCSAlleEmailsView.as_view(),
         name='korps-emails'),

    path('wedstrijden/',
         view_wedstrijden.WedstrijdenView.as_view(),
         name='wedstrijden'),

    path('wedstrijden/<wedstrijd_pk>/details/',
         view_wedstrijden.WedstrijdDetailsView.as_view(),
         name='wedstrijd-details'),

    path('wedstrijden/<wedstrijd_pk>/kies-scheidsrechters/',
         view_wedstrijden.WedstrijdDetailsCSView.as_view(),
         name='wedstrijd-kies-scheidsrechters'),

    path('wedstrijden/<wedstrijd_pk>/geselecteerde-scheidsrechters/',
         view_wedstrijden.WedstrijdHWLContactView.as_view(),
         name='wedstrijd-hwl-contact'),

    path('beschikbaarheid-opvragen/',
         view_beschikbaarheid.BeschikbaarheidOpvragenView.as_view(),
         name='beschikbaarheid-opvragen'),

    path('beschikbaarheid-wijzigen/',
         view_beschikbaarheid.WijzigBeschikbaarheidView.as_view(),
         name='beschikbaarheid-wijzigen'),

    path('beschikbaarheid-inzien/',
         view_beschikbaarheid.BeschikbaarheidInzienCSView.as_view(),
         name='beschikbaarheid-inzien'),
]


# end of file
