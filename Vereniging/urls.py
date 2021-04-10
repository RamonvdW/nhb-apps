# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import (view_accommodatie, view_overzicht, view_ledenlijst,
               view_aanmelden, view_wedstrijden, view_lijst_rk,
               view_schietmomenten, view_teams)

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

    path('leden-ingeschreven/voorkeur-teamcompetitie/<deelnemer_pk>/',
         view_aanmelden.ToggleVoorkeurTeamcompetitieView.as_view(),
         name='toggle-voorkeur-teamcompetitie'),

    path('leden-ingeschreven/wijzig-aanvangsgemiddelde/<deelnemer_pk>/',
         view_teams.WijzigTeamAGView.as_view(),
         name='wijzig-ag'),

    path('teams/regio/koppelen/<team_pk>/',
         view_teams.TeamsRegioKoppelLedenView.as_view(),
         name='teams-regio-koppelen'),

    path('teams/regio/<deelcomp_pk>/nieuw/',
         view_teams.WijzigRegioTeamsView.as_view(),
         name='teams-regio-nieuw'),

    path('teams/regio/<deelcomp_pk>/wijzig/<team_pk>/',
         view_teams.WijzigRegioTeamsView.as_view(),
         name='teams-regio-wijzig'),

    path('teams/regio/<deelcomp_pk>/',
         view_teams.TeamsRegioView.as_view(),
         name='teams-regio'),

    path('teams/rk/<deelcomp_pk>/',
         view_teams.TeamsRkView.as_view(),
         name='teams-rk'),

    # TODO: term 'schietmomenten' aanpassen?
    path('leden-ingeschreven/competitie/<deelcomp_pk>/schietmomenten/',
         view_schietmomenten.LedenSchietmomentView.as_view(),
         name='schietmomenten'),

    path('accommodaties/lijst/',
         view_accommodatie.LijstVerenigingenView.as_view(),
         name='lijst-verenigingen'),

    path('accommodaties/details/<vereniging_pk>/',
         view_accommodatie.AccommodatieDetailsView.as_view(),
         name='accommodatie-details'),

    path('accommodatie-details/<vereniging_pk>/',
         view_accommodatie.VerenigingAccommodatieDetailsView.as_view(),
         name='vereniging-accommodatie-details'),

    path('externe-locaties/<vereniging_pk>/',
         view_accommodatie.ExterneLocatiesView.as_view(),
         name='externe-locaties'),

    path('externe-locaties/<vereniging_pk>/details/<locatie_pk>/',
         view_accommodatie.ExterneLocatieDetailsView.as_view(),
         name='locatie-details'),

    path('regio-clusters/',
         view_accommodatie.WijzigClustersView.as_view(),
         name='clusters'),

    path('wedstrijden/',
         view_wedstrijden.WedstrijdenView.as_view(),
         name='wedstrijden'),

    path('uitslag-invoeren/',
         view_wedstrijden.WedstrijdenUitslagInvoerenView.as_view(),
         name='wedstrijden-uitslag-invoeren'),

    path('lijst-rayonkampioenschappen/<deelcomp_pk>/alles/',
         view_lijst_rk.VerenigingLijstRkSelectieAllesView.as_view(),
         name='lijst-rk-alles'),

    path('lijst-rayonkampioenschappen/<deelcomp_pk>/',
         view_lijst_rk.VerenigingLijstRkSelectieView.as_view(),
         name='lijst-rk'),
]

# end of file
