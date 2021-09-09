# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import (view_accommodatie, view_clusters, view_externe_locaties, view_overzicht, view_ledenlijst,
               view_aanmelden, view_wedstrijden, view_lijst_rk, view_lijst_verenigingen,
               view_schietmomenten, view_teams_regio, view_teams_rk)

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

    path('leden-ingeschreven/wijzig-aanvangsgemiddelde/<deelnemer_pk>/',
         view_teams_regio.WijzigTeamAGView.as_view(),
         name='wijzig-ag'),

    # TODO: term 'schietmomenten' aanpassen?
    path('leden-ingeschreven/competitie/<deelcomp_pk>/schietmomenten/',
         view_schietmomenten.LedenSchietmomentView.as_view(),
         name='schietmomenten'),


    # regio teams
    path('teams/regio/koppelen/<team_pk>/',
         view_teams_regio.TeamsRegioKoppelLedenView.as_view(),
         name='teams-regio-koppelen'),

    path('teams/regio/<deelcomp_pk>/nieuw/',
         view_teams_regio.WijzigRegioTeamsView.as_view(),
         name='teams-regio-nieuw'),

    path('teams/regio/<deelcomp_pk>/wijzig/<team_pk>/',
         view_teams_regio.WijzigRegioTeamsView.as_view(),
         name='teams-regio-wijzig'),

    path('teams/regio/<deelcomp_pk>/invallers/',
         view_teams_regio.TeamsRegioInvallersView.as_view(),
         name='teams-regio-invallers'),

    path('teams/regio/invallers-koppelen/<ronde_team_pk>/',
         view_teams_regio.TeamsRegioInvallersKoppelLedenView.as_view(),
         name='teams-regio-invallers-koppelen'),

    path('teams/regio/<deelcomp_pk>/',
         view_teams_regio.TeamsRegioView.as_view(),
         name='teams-regio'),


    # RK teams
    path('teams/rk/<deelcomp_pk>/',
         view_teams_rk.TeamsRkView.as_view(),
         name='teams-rk'),

    path('teams/rk/<deelcomp_pk>/nieuw/',
         view_teams_rk.WijzigRKTeamsView.as_view(),
         name='teams-rk-nieuw'),

    path('teams/rk/<deelcomp_pk>/wijzig/<team_pk>/',
         view_teams_rk.WijzigRKTeamsView.as_view(),
         name='teams-rk-wijzig'),


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

    path('regio-clusters/',
         view_clusters.WijzigClustersView.as_view(),
         name='clusters'),

    path('wedstrijden/<wedstrijd_pk>/waarschijnlijke-deelnemers/',
         view_wedstrijden.WaarschijnlijkeDeelnemersView.as_view(),
         name='waarschijnlijke-deelnemers'),

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

    path('contact-geen-beheerders/',
         view_lijst_verenigingen.GeenBeheerdersView.as_view(),
         name='contact-geen-beheerders')
]

# end of file
