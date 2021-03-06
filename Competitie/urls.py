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
               views_uitslagen,
               views_scores)

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

    path('ag-vaststellen/',
         views_bb.AGVaststellenView.as_view(),
         name='ag-vaststellen'),

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

    path('<comp_pk>/lijst-regiocompetitie/alles/',
         views_aangemeld.LijstAangemeldRegiocompAllesView.as_view(),
         name='lijst-regiocomp-alles'),

    path('<comp_pk>/lijst-regiocompetitie/rayon-<rayon_pk>/',
         views_aangemeld.LijstAangemeldRegiocompRayonView.as_view(),
         name='lijst-regiocomp-rayon'),

    path('<comp_pk>/lijst-regiocompetitie/regio-<regio_pk>/',
         views_aangemeld.LijstAangemeldRegiocompRegioView.as_view(),
         name='lijst-regiocomp-regio'),


    # RK selectie
    path('lijst-rayonkampioenschappen/<deelcomp_pk>/',
         views_planning_rayon.LijstRkSelectieView.as_view(),
         name='lijst-rk'),

    path('lijst-rayonkampioenschappen/<deelcomp_pk>/bestand/',
         views_planning_rayon.LijstRkSelectieAlsBestandView.as_view(),
         name='lijst-rk-als-bestand'),

    path('lijst-rayonkampioenschappen/wijzig-status-rk-deelnemer/<deelnemer_pk>/',
         views_planning_rayon.WijzigStatusRkSchutterView.as_view(),
         name='wijzig-status-rk-deelnemer'),


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
    path('planning/rk/<deelcomp_pk>/limieten/',
         views_planning_rayon.RayonLimietenView.as_view(),
         name='rayon-limieten'),

    path('planning/rk/<deelcomp_pk>/',
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


    # scores regio
    path('scores/regio/<deelcomp_pk>/',
         views_scores.ScoresRegioView.as_view(),
         name='scores-regio'),


    # uitslag invoeren
    path('scores/uitslag-invoeren/<wedstrijd_pk>/',
         views_scores.WedstrijdUitslagInvoerenView.as_view(),
         name='wedstrijd-uitslag-invoeren'),

    path('scores/uitslag-controleren/<wedstrijd_pk>/',
         views_scores.WedstrijdUitslagControlerenView.as_view(),
         name='wedstrijd-uitslag-controleren'),

    path('scores/uitslag-accorderen/<wedstrijd_pk>/',
         views_scores.WedstrijdUitslagControlerenView.as_view(),
         name='wedstrijd-geef-akkoord'),

    path('scores/bekijk-uitslag/<wedstrijd_pk>/',
         views_scores.WedstrijdUitslagBekijkenView.as_view(),
         name='wedstrijd-bekijk-uitslag'),

    path('scores/dynamic/deelnemers-ophalen/',
         views_scores.DynamicDeelnemersOphalenView.as_view(),
         name='dynamic-deelnemers-ophalen'),

    path('scores/dynamic/check-nhbnr/',
         views_scores.DynamicZoekOpNhbnrView.as_view(),
         name='dynamic-check-nhbnr'),

    path('scores/dynamic/scores-opslaan/',
         views_scores.DynamicScoresOpslaanView.as_view(),
         name='dynamic-scores-opslaan'),


    # competitie uitslagen
    path('<comp_pk>/uitslagen/<comp_boog>/vereniging/<ver_nr>/',
         views_uitslagen.UitslagenVerenigingView.as_view(),
         name='uitslagen-vereniging-n'),

    # TODO: wordt deze gebruikt?
    path('<comp_pk>/uitslagen/<comp_boog>/vereniging/',
         views_uitslagen.UitslagenVerenigingView.as_view(),
         name='uitslagen-vereniging'),

    path('<comp_pk>/uitslagen/<comp_boog>/<zes_scores>/regio/<regio_nr>/',
         views_uitslagen.UitslagenRegioView.as_view(),
         name='uitslagen-regio-n'),

    path('<comp_pk>/uitslagen/<comp_boog>/<zes_scores>/regio/',
         views_uitslagen.UitslagenRegioView.as_view(),
         name='uitslagen-regio'),

    path('<comp_pk>/uitslagen/<comp_boog>/<zes_scores>/regio-alt/<regio_nr>/',
         views_uitslagen.UitslagenRegioAltView.as_view(),
         name='uitslagen-regio-n-alt'),

    path('<comp_pk>/uitslagen/<comp_boog>/<zes_scores>/regio-alt/',
         views_uitslagen.UitslagenRegioAltView.as_view(),
         name='uitslagen-regio-alt'),

    path('<comp_pk>/uitslagen/<comp_boog>/rayon/',
         views_uitslagen.UitslagenRayonView.as_view(),
         name='uitslagen-rayon'),

    path('<comp_pk>/uitslagen/<comp_boog>/rayon/<rayon_nr>/',
         views_uitslagen.UitslagenRayonView.as_view(),
         name='uitslagen-rayon-n'),

    path('<comp_pk>/uitslagen/<comp_boog>/bond/',
         views_uitslagen.UitslagenBondView.as_view(),
         name='uitslagen-bond'),


    path('<comp_pk>/doorzetten/rk/',
         views_planning_bond.DoorzettenNaarRKView.as_view(),
         name='bko-doorzetten-naar-rk'),

    path('<comp_pk>/doorzetten/bk/',
         views_planning_bond.DoorzettenNaarBKView.as_view(),
         name='bko-doorzetten-naar-bk'),

    #path('<comp_pk>/afsluiten/',
    #     views_planning_bond.CompetitieAfsluitenView.as_view(),
    #     name='bko-afsluiten-competitie'),

    path('<comp_pk>/',
         views_overzicht.CompetitieOverzichtView.as_view(),
         name='overzicht'),

]

# end of file
