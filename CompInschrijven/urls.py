# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from . import view_hwl, view_sporter, view_aangemeld

app_name = 'CompInschrijven'

urlpatterns = [

    # Sporter
    path('aanmelden/<deelcomp_pk>/<sporterboog_pk>/bevestig/',
         view_sporter.RegiocompetitieAanmeldenBevestigView.as_view(),
         name='bevestig-aanmelden'),

    path('aanmelden/<deelcomp_pk>/<sporterboog_pk>/',
         view_sporter.RegiocompetitieAanmeldenView.as_view(),
         name='aanmelden'),

    path('afmelden/<deelnemer_pk>/',
         view_sporter.RegiocompetitieAfmeldenView.as_view(),
         name='afmelden'),

    # HWL
    path('leden-aanmelden/<comp_pk>/',
         view_hwl.LedenAanmeldenView.as_view(),
         name='leden-aanmelden'),

    path('leden-ingeschreven/<deelcomp_pk>/',
         view_hwl.LedenIngeschrevenView.as_view(),
         name='leden-ingeschreven'),


    # BB/BKO/RKO/RCL
    path('<comp_pk>/lijst-regiocompetitie/regio-<regio_pk>/dagdeel-behoefte/',
         view_aangemeld.Inschrijfmethode3BehoefteView.as_view(),
         name='inschrijfmethode3-behoefte'),

    path('<comp_pk>/lijst-regiocompetitie/regio-<regio_pk>/dagdeel-behoefte-als-bestand/',
         view_aangemeld.Inschrijfmethode3BehoefteAlsBestandView.as_view(),
         name='inschrijfmethode3-behoefte-als-bestand'),

    path('<comp_pk>/lijst-regiocompetitie/regio-<regio_pk>/gemaakte-keuzes/',
         view_aangemeld.Inschrijfmethode1BehoefteView.as_view(),
         name='inschrijfmethode1-behoefte'),

    path('<comp_pk>/lijst-regiocompetitie/regio-<regio_pk>/gemaakte-keuzes-als-bestand/',
         view_aangemeld.Inschrijfmethode1BehoefteAlsBestandView.as_view(),
         name='inschrijfmethode1-behoefte-als-bestand'),

    path('<comp_pk>/lijst-regiocompetitie/alles/',
         view_aangemeld.LijstAangemeldRegiocompAllesView.as_view(),
         name='lijst-regiocomp-alles'),

    path('<comp_pk>/lijst-regiocompetitie/rayon-<rayon_pk>/',
         view_aangemeld.LijstAangemeldRegiocompRayonView.as_view(),
         name='lijst-regiocomp-rayon'),

    path('<comp_pk>/lijst-regiocompetitie/regio-<regio_pk>/',
         view_aangemeld.LijstAangemeldRegiocompRegioView.as_view(),
         name='lijst-regiocomp-regio'),

    path('<comp_pk>/lijst-regiocompetitie/regio-<regio_pk>/als-bestand/',
         view_aangemeld.LijstAangemeldRegiocompAlsBestandView.as_view(),
         name='lijst-regiocomp-regio-als-bestand'),

]


# end of file
