# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import (views_aangemeld,
               views_bb,
               views_info,
               views_klassegrenzen,
               views_overzicht,
               views_planning,
               views_planning_bond,
               views_planning_rayon,
               views_tussenstand,
               views_uitslagen)

app_name = 'Competitie'

urlpatterns = [

    path('',
         views_overzicht.CompetitieOverzichtView.as_view(),
         name='overzicht'),


    path('klassegrenzen/tonen/',
         views_klassegrenzen.KlassegrenzenTonenView.as_view(),
         name='klassegrenzen-tonen'),


    path('lijst-regiocompetitie/<comp_pk>/regio-<regio_pk>/dagdeel-behoefte/',
         views_aangemeld.Inschrijfmethode3BehoefteView.as_view(),
         name='inschrijfmethode3-behoefte'),

    path('lijst-regiocompetitie/<comp_pk>/regio-<regio_pk>/dagdeel-behoefte-als-bestand/',
         views_aangemeld.Inschrijfmethode3BehoefteAlsBestandView.as_view(),
         name='inschrijfmethode3-behoefte-als-bestand'),

    path('lijst-regiocompetitie/<comp_pk>/alles/',
         views_aangemeld.LijstAangemeldRegiocompAllesView.as_view(),
         name='lijst-regiocomp-alles'),

    path('lijst-regiocompetitie/<comp_pk>/rayon-<rayon_pk>/',
         views_aangemeld.LijstAangemeldRegiocompRayonView.as_view(),
         name='lijst-regiocomp-rayon'),

    path('lijst-regiocompetitie/<comp_pk>/regio-<regio_pk>/',
         views_aangemeld.LijstAangemeldRegiocompRegioView.as_view(),
         name='lijst-regiocomp-regio'),


    path('lijst-rayonkampioenschappen/<deelcomp_pk>/',
         views_planning_rayon.LijstRkSchuttersView.as_view(),
         name='lijst-rk'),

    path('lijst-rayonkampioenschappen/wijzig-status-rk-deelnemer/<deelnemer_pk>/',
         views_planning_rayon.WijzigStatusRkSchutterView.as_view(),
         name='wijzig-status-rk-deelnemer'),


    path('info/',
         views_info.InfoCompetitieView.as_view(),
         name='info-competitie'),


    path('instellingen-volgende-competitie/',
         views_bb.InstellingenVolgendeCompetitieView.as_view(),
         name='instellingen-volgende-competitie'),

    path('aanmaken/',
         views_bb.CompetitieAanmakenView.as_view(),
         name='aanmaken'),

    path('ag-vaststellen/',
         views_bb.AGVaststellenView.as_view(),
         name='ag-vaststellen'),

    path('klassegrenzen/vaststellen/<afstand>/',
         views_bb.KlassegrenzenVaststellenView.as_view(),
         name='klassegrenzen-vaststellen'),

    path('wijzig-datums/<comp_pk>/',
         views_bb.WijzigDatumsView.as_view(),
         name='wijzig-datums'),


    path('planning/regiocompetitie/ronde/<ronde_pk>/',
         views_planning.RegioRondePlanningView.as_view(),
         name='regio-ronde-planning'),

    path('planning/regiocompetitie/cluster/<cluster_pk>/',
         views_planning.RegioClusterPlanningView.as_view(),
         name='regio-cluster-planning'),

    path('planning/regiocompetitie/afsluiten/<deelcomp_pk>/',
         views_planning.AfsluitenRegiocompView.as_view(),
         name='afsluiten-regiocomp'),

    path('planning/regiocompetitie/<deelcomp_pk>/',
         views_planning.RegioPlanningView.as_view(),
         name='regio-planning'),

    path('planning/bondscompetitie/<deelcomp_pk>/',
         views_planning.BondPlanningView.as_view(),
         name='bond-planning'),

    path('planning/wedstrijd/wijzig/<wedstrijd_pk>/',
         views_planning.WijzigWedstrijdView.as_view(),
         name='wijzig-wedstrijd'),

    path('planning/wedstrijd/verwijder/<wedstrijd_pk>/',
         views_planning.VerwijderWedstrijdView.as_view(),
         name='verwijder-wedstrijd'),


    path('planning/rayoncompetitie/<deelcomp_pk>/',
         views_planning_rayon.RayonPlanningView.as_view(),
         name='rayon-planning'),

    path('planning/wedstrijd-rayon/wijzig/<wedstrijd_pk>/',
         views_planning_rayon.WijzigRayonWedstrijdView.as_view(),
         name='wijzig-rayon-wedstrijd'),


    path('wedstrijd/uitslag-invoeren/<wedstrijd_pk>/',
         views_uitslagen.WedstrijdUitslagInvoerenView.as_view(),
         name='wedstrijd-uitslag-invoeren'),

    path('wedstrijd/uitslag-controleren/<wedstrijd_pk>/',
         views_uitslagen.WedstrijdUitslagControlerenView.as_view(),
         name='wedstrijd-uitslag-controleren'),

    path('wedstrijd/uitslag-accorderen/<wedstrijd_pk>/',
         views_uitslagen.WedstrijdUitslagControlerenView.as_view(),
         name='wedstrijd-geef-akkoord'),

    path('wedstrijd/bekijk-uitslag/<wedstrijd_pk>/',
         views_uitslagen.WedstrijdUitslagBekijkenView.as_view(),
         name='wedstrijd-bekijk-uitslag'),

    path('dynamic/deelnemers-ophalen/',
         views_uitslagen.DynamicDeelnemersOphalenView.as_view(),
         name='dynamic-deelnemers-ophalen'),

    path('dynamic/check-nhbnr/',
         views_uitslagen.DynamicZoekOpNhbnrView.as_view(),
         name='dynamic-check-nhbnr'),

    path('dynamic/scores-opslaan/',
         views_uitslagen.DynamicScoresOpslaanView.as_view(),
         name='dynamic-scores-opslaan'),


    path('tussenstand/',
         views_tussenstand.TussenstandView.as_view(),
         name='tussenstand'),

    path('tussenstand/<afstand>-<comp_boog>/regio/',
         views_tussenstand.TussenstandRegioView.as_view(),
         name='tussenstand-regio'),

    path('tussenstand/<afstand>-<comp_boog>/regio/<regio_nr>/',
         views_tussenstand.TussenstandRegioView.as_view(),
         name='tussenstand-regio-n'),

    path('tussenstand/<afstand>-<comp_boog>/regio-alt/',
         views_tussenstand.TussenstandRegioAltView.as_view(),
         name='tussenstand-regio-alt'),

    path('tussenstand/<afstand>-<comp_boog>/regio-alt/<regio_nr>/',
         views_tussenstand.TussenstandRegioAltView.as_view(),
         name='tussenstand-regio-n-alt'),

    path('tussenstand/<afstand>-<comp_boog>/rayon/',
         views_tussenstand.TussenstandRayonView.as_view(),
         name='tussenstand-rayon'),

    path('tussenstand/<afstand>-<comp_boog>/rayon/<rayon_nr>/',
         views_tussenstand.TussenstandRayonView.as_view(),
         name='tussenstand-rayon-n'),

    path('tussenstand/<afstand>-<comp_boog>/bond/',
         views_tussenstand.TussenstandBondView.as_view(),
         name='tussenstand-bond'),


    path('planning/doorzetten/<comp_pk>/rk/',
         views_planning_bond.DoorzettenNaarRKView.as_view(),
         name='bko-doorzetten-naar-rk'),

    path('planning/doorzetten/<comp_pk>/bk/',
         views_planning_bond.DoorzettenNaarBKView.as_view(),
         name='bko-doorzetten-naar-bk'),

    #path('planning/afsluiten/<comp_pk>/',
    #     views_planning_bond.CompetitieAfsluitenView.as_view(),
    #     name='bko-afsluiten-competitie'),
]

# end of file
