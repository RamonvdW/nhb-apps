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
               views_planning_bond)

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
