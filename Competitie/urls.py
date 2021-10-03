# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import (views_aangemeld,
               views_bb,
               views_info,
               views_klassegrenzen,
               views_overzicht,
               views_planning_regio,
               views_planning_bond,
               views_planning_rayon,
               views_regio_teams,
               views_rayon_teams)

app_name = 'Competitie'

urlpatterns = [

    path('',
         views_overzicht.CompetitieKiesView.as_view(),
         name='kies'),

    # openbare info
    path('info/',
         views_info.InfoCompetitieView.as_view(),
         name='info-competitie'),

    path('info/leeftijden/',
         views_info.InfoLeeftijdenView.as_view(),
         name='info-leeftijden'),

    path('<comp_pk>/klassegrenzen/tonen/',
         views_klassegrenzen.KlassegrenzenTonenView.as_view(),
         name='klassegrenzen-tonen'),


    # BB schermen
    path('instellingen-volgende-competitie/',
         views_bb.InstellingenVolgendeCompetitieView.as_view(),
         name='instellingen-volgende-competitie'),

    path('aanmaken/',
         views_bb.CompetitieAanmakenView.as_view(),
         name='aanmaken'),

    path('ag-vaststellen/<afstand>/',
         views_bb.AGVaststellenView.as_view(),
         name='ag-vaststellen-afstand'),

    path('<comp_pk>/klassegrenzen/vaststellen/',
         views_bb.KlassegrenzenVaststellenView.as_view(),
         name='klassegrenzen-vaststellen'),

    path('<comp_pk>/wijzig-datums/',
         views_bb.WijzigDatumsView.as_view(),
         name='wijzig-datums'),


    # RCL schermen
    path('<comp_pk>/instellingen/regio-<regio_nr>/',
         views_regio_teams.RegioInstellingenView.as_view(),
         name='regio-instellingen'),

    path('<comp_pk>/instellingen/globaal/',
         views_regio_teams.RegioInstellingenGlobaalView.as_view(),
         name='regio-instellingen-globaal'),

    path('<comp_pk>/ag-controle/regio-<regio_nr>/',
         views_regio_teams.AGControleView.as_view(),
         name='regio-ag-controle'),

    path('regio/<comp_pk>/teams/<subset>/',
         views_regio_teams.RegioTeamsAlleView.as_view(),
         name='regio-teams-alle'),

    path('regio/<deelcomp_pk>/teams/',
         views_regio_teams.RegioTeamsRCLView.as_view(),
         name='regio-teams'),

    path('regio/<deelcomp_pk>/poules/',
         views_regio_teams.RegioPoulesView.as_view(),
         name='regio-poules'),

    path('regio/poules/<poule_pk>/wijzig/',
         views_regio_teams.WijzigPouleView.as_view(),
         name='wijzig-poule'),

    path('regio/<deelcomp_pk>/team-ronde/',
         views_regio_teams.StartVolgendeTeamRondeView.as_view(),
         name='start-volgende-team-ronde'),


    # ingeschreven
    path('<comp_pk>/lijst-regiocompetitie/regio-<regio_pk>/dagdeel-behoefte/',
         views_aangemeld.Inschrijfmethode3BehoefteView.as_view(),
         name='inschrijfmethode3-behoefte'),

    path('<comp_pk>/lijst-regiocompetitie/regio-<regio_pk>/dagdeel-behoefte-als-bestand/',
         views_aangemeld.Inschrijfmethode3BehoefteAlsBestandView.as_view(),
         name='inschrijfmethode3-behoefte-als-bestand'),

    path('<comp_pk>/lijst-regiocompetitie/regio-<regio_pk>/gemaakte-keuzes/',
         views_aangemeld.Inschrijfmethode1BehoefteView.as_view(),
         name='inschrijfmethode1-behoefte'),

    path('<comp_pk>/lijst-regiocompetitie/regio-<regio_pk>/gemaakte-keuzes-als-bestand/',
         views_aangemeld.Inschrijfmethode1BehoefteAlsBestandView.as_view(),
         name='inschrijfmethode1-behoefte-als-bestand'),

    path('<comp_pk>/lijst-regiocompetitie/alles/',
         views_aangemeld.LijstAangemeldRegiocompAllesView.as_view(),
         name='lijst-regiocomp-alles'),

    path('<comp_pk>/lijst-regiocompetitie/rayon-<rayon_pk>/',
         views_aangemeld.LijstAangemeldRegiocompRayonView.as_view(),
         name='lijst-regiocomp-rayon'),

    path('<comp_pk>/lijst-regiocompetitie/regio-<regio_pk>/',
         views_aangemeld.LijstAangemeldRegiocompRegioView.as_view(),
         name='lijst-regiocomp-regio'),

    path('<comp_pk>/lijst-regiocompetitie/regio-<regio_pk>/als-bestand/',
         views_aangemeld.LijstAangemeldRegiocompAlsBestandView.as_view(),
         name='lijst-regiocomp-regio-als-bestand'),


    # RK selectie
    path('lijst-rayonkampioenschappen/<rk_deelcomp_pk>/',
         views_planning_rayon.LijstRkSelectieView.as_view(),
         name='lijst-rk'),

    path('lijst-rayonkampioenschappen/<rk_deelcomp_pk>/bestand/',
         views_planning_rayon.LijstRkSelectieAlsBestandView.as_view(),
         name='lijst-rk-als-bestand'),

    path('lijst-rayonkampioenschappen/wijzig-status-rk-deelnemer/<deelnemer_pk>/',
         views_planning_rayon.WijzigStatusRkSchutterView.as_view(),
         name='wijzig-status-rk-deelnemer'),


    # RK teams
    path('rk/<comp_pk>/teams/<subset>/',
         views_rayon_teams.RayonTeamsAlleView.as_view(),
         name='rayon-teams-alle'),

    path('rk/<rk_deelcomp_pk>/teams/',
         views_rayon_teams.RayonTeamsRKOView.as_view(),
         name='rayon-teams'),

    # planning regio
    path('planning/regio/<deelcomp_pk>/',
         views_planning_regio.RegioPlanningView.as_view(),
         name='regio-planning'),

    path('planning/regio/<deelcomp_pk>/afsluiten/',
         views_planning_regio.AfsluitenRegiocompView.as_view(),
         name='afsluiten-regiocomp'),

    path('planning/regio/<deelcomp_pk>/cluster/<cluster_pk>/',
         views_planning_regio.RegioClusterPlanningView.as_view(),
         name='regio-cluster-planning'),

    path('planning/regio/ronde/<ronde_pk>/',
         views_planning_regio.RegioRondePlanningView.as_view(),
         name='regio-ronde-planning'),

    path('planning/regio/regio-wedstrijden/<ronde_pk>/',
         views_planning_regio.RegioRondePlanningMethode1View.as_view(),
         name='regio-methode1-planning'),

    path('planning/regio/wedstrijd/wijzig/<wedstrijd_pk>/',
         views_planning_regio.WijzigWedstrijdView.as_view(),
         name='regio-wijzig-wedstrijd'),

    path('planning/regio/wedstrijd/verwijder/<wedstrijd_pk>/',
         views_planning_regio.VerwijderWedstrijdView.as_view(),
         name='regio-verwijder-wedstrijd'),


    # planning rk
    path('planning/rk/<rk_deelcomp_pk>/limieten/',
         views_planning_rayon.RayonLimietenView.as_view(),
         name='rayon-limieten'),

    path('planning/rk/<rk_deelcomp_pk>/',
         views_planning_rayon.RayonPlanningView.as_view(),
         name='rayon-planning'),

    path('planning/rk/wedstrijd/wijzig/<wedstrijd_pk>/',
         views_planning_rayon.WijzigRayonWedstrijdView.as_view(),
         name='rayon-wijzig-wedstrijd'),

    path('planning/rk/wedstrijd/verwijder/<wedstrijd_pk>/',
         views_planning_rayon.VerwijderWedstrijdView.as_view(),
         name='rayon-verwijder-wedstrijd'),


    # planning bk
    path('planning/bk/<deelcomp_pk>/',
         views_planning_bond.BondPlanningView.as_view(),
         name='bond-planning'),

    path('planning/bk/wedstrijd/verwijder/<wedstrijd_pk>/',
         views_planning_bond.VerwijderWedstrijdView.as_view(),
         name='bond-verwijder-wedstrijd'),


    path('<comp_pk>/doorzetten/rk/',
         views_planning_bond.DoorzettenNaarRKView.as_view(),
         name='bko-doorzetten-naar-rk'),

    path('<comp_pk>/doorzetten/bk/',
         views_planning_bond.DoorzettenNaarBKView.as_view(),
         name='bko-doorzetten-naar-bk'),

    # TODO: maak afsluiten competitie
    #path('<comp_pk>/afsluiten/',
    #     views_planning_bond.CompetitieAfsluitenView.as_view(),
    #     name='bko-afsluiten-competitie'),

    path('<comp_pk>/',
         views_overzicht.CompetitieOverzichtView.as_view(),
         name='overzicht'),

]

# end of file
