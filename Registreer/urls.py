# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path

from Registreer import view_begin, view_registreer_lid, view_registreer_gast, view_beheer_gast_accounts

app_name = 'Registreer'

# basis: /account/registreer/

urlpatterns = [

    path('',
         view_begin.RegistreerBeginView.as_view(),
         name='begin'),


    # gewoon account aanmaken
    path('lid/',
         view_registreer_lid.RegistreerLidView.as_view(),
         name='lid'),


    # gast-account aanmaken
    path('gast/',
         view_registreer_gast.RegistreerGastView.as_view(),
         name='gast'),

    path('gast/meer-vragen/',
         view_registreer_gast.RegistreerGastVervolgView.as_view(),
         name='gast-meer-vragen'),

    path('gast/volgende-vraag/',
         view_registreer_gast.RegistreerGastVolgendeVraagView.as_view(),
         name='gast-volgende-vraag'),


    # beheer gast-accounts
    path('beheer-gast-accounts/',
         view_beheer_gast_accounts.GastAccountsView.as_view(),
         name='beheer-gast-accounts'),

    path('beheer-gast-accounts/<lid_nr>/details/',
         view_beheer_gast_accounts.GastAccountDetailsView.as_view(),
         name='beheer-gast-account-details'),

    path('beheer-gast-accounts/opheffen/',
         view_beheer_gast_accounts.GastAccountOpheffenView.as_view(),
         name='opheffen'),
]

# end of file
