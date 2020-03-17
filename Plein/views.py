# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige, rol_get_beschrijving
from .menu import menu_dynamics
from .leeftijdsklassen import get_leeftijdsklassen


TEMPLATE_PLEIN_BEZOEKER = 'plein/plein-bezoeker.dtl'            # niet ingelogd
TEMPLATE_PLEIN_GEBRUIKER = 'plein/plein-gebruiker.dtl'          # special (ROL_NONE)
TEMPLATE_PLEIN_SCHUTTER = 'plein/plein-schutter.dtl'            # schutter (ROL_SCHUTTER)
TEMPLATE_PLEIN_BEHEERDER = 'plein/plein-beheerder.dtl'          # beheerder (ROL_BB/BKO/RKO/RCL/CWZ)

TEMPLATE_LEEFTIJDSKLASSEN = 'plein/leeftijdsklassen.dtl'
TEMPLATE_PRIVACY = 'plein/privacy.dtl'


def site_root_view(request):
    """ simpele Django view functie om vanaf de top-level site naar het Plein te gaan """
    return redirect('Plein:plein')


class PleinView(View):
    """ Django class-based view voor het Plein """

    # class variables shared by all instances

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """

        # zet alles goed voor bezoekers / geen rol
        template = TEMPLATE_PLEIN_BEZOEKER
        context = dict()

        if request.user.is_authenticated:
            rol_nu = rol_get_huidige(request)

            if rol_nu == Rollen.ROL_NONE or rol_nu == None:
                template = TEMPLATE_PLEIN_GEBRUIKER

            elif rol_nu == Rollen.ROL_SCHUTTER:
                template = TEMPLATE_PLEIN_SCHUTTER
                huidige_jaar, leeftijd, is_jong, wlst, clst = get_leeftijdsklassen(request)
                if True: #is_jong:
                    context['plein_toon_leeftijdsklassen'] = True
                    context['plein_is_jonge_schutter'] = is_jong
                    context['plein_huidige_jaar'] = huidige_jaar
                    context['plein_leeftijd'] = leeftijd
                    context['plein_wlst'] = wlst
                    context['plein_clst'] = clst
                else:
                    # ouder lid
                    context['plein_toon_leeftijdsklassen'] = False

            else:   # rol_nu < Rollen.ROL_SCHUTTER:
                # beheerder
                template = TEMPLATE_PLEIN_BEHEERDER

                if rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB):
                    context['toon_nieuwe_accounts'] = True

                if rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_CWZ):
                    context['toon_functies'] = True

                if rol_nu == Rollen.ROL_BB:
                    context['rol_is_bb'] = True;
                elif rol_nu == Rollen.ROL_BKO:
                    context['rol_is_bko'] = True;
                elif rol_nu == Rollen.ROL_RKO:
                    context['rol_is_rko'] = True;
                elif rol_nu == Rollen.ROL_RCL:
                    context['rol_is_rcl'] = True;

                context['huidige_rol'] = rol_get_beschrijving(request)

        menu_dynamics(self.request, context)
        return render(request, template, context)


class PrivacyView(TemplateView):

    """ Django class-based view voor het Privacy bericht """

    # class variables shared by all instances
    template_name = TEMPLATE_PRIVACY

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['url_privacyverklaring'] = settings.PRIVACYVERKLARING_URL
        menu_dynamics(self.request, context, actief='privacy')
        return context


class LeeftijdsklassenView(UserPassesTestMixin, TemplateView):
    """ Django class-based view voor de leeftijdsklassen """

    # class variables shared by all instances
    template_name = TEMPLATE_LEEFTIJDSKLASSEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol = rol_get_huidige(self.request)
        return rol == Rollen.ROL_SCHUTTER

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        huidige_jaar, leeftijd, is_jong, wlst, clst = get_leeftijdsklassen(self.request)
        context['plein_is_jonge_schutter'] = is_jong
        context['plein_huidige_jaar'] = huidige_jaar
        context['plein_leeftijd'] = leeftijd
        context['plein_wlst'] = wlst
        context['plein_clst'] = clst

        menu_dynamics(self.request, context)
        return context


# end of file
