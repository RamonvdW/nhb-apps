# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from Scheidsrechter import view_overzicht, view_korps, view_beschikbaarheid, view_wedstrijden, view_competitie

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

    path('beschikbaarheid-inzien/statistiek/',
         view_beschikbaarheid.BeschikbaarheidStatsCSView.as_view(),
         name='beschikbaarheid-stats'),

    path('bondscompetitie/',
         view_competitie.CompetitieMatchesView.as_view(),
         name='competitie'),

    path('bondscompetitie/<match_pk>/details/',
         view_competitie.MatchDetailsView.as_view(),
         name='match-details'),

    path('bondscompetitie/<match_pk>/kies-scheidsrechters/',
         view_competitie.MatchDetailsCSView.as_view(),
         name='match-kies-scheidsrechter'),

    path('bondscompetitie/beschikbaarheid-opvragen/',
         view_beschikbaarheid.BeschikbaarheidCompetitieOpvragenView.as_view(),
         name='competitie-beschikbaarheid-opvragen'),

    path('bondscompetitie/<match_pk>/geselecteerde-scheidsrechters/',
         view_competitie.MatchHWLContactView.as_view(),
         name='match-hwl-contact'),

]


# end of file
