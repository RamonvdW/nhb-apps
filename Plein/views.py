# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.shortcuts import redirect, render
from django.db.models import F
from django.views.generic import TemplateView, ListView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group
from Plein.menu import menu_dynamics
from Account.models import AccountEmail
from Account.leeftijdsklassen import get_leeftijdsklassen
from Account.rol import Rollen, rol_get_huidige_functie, rol_get_huidige, rol_get_beschrijving


TEMPLATE_PLEIN_BEZOEKER = 'plein/plein-bezoeker.dtl'            # niet ingelogd
TEMPLATE_PLEIN_GEBRUIKER = 'plein/plein-gebruiker.dtl'          # special (ROL_NONE)
TEMPLATE_PLEIN_SCHUTTER = 'plein/plein-schutter.dtl'            # schutter (ROL_SCHUTTER)
TEMPLATE_PLEIN_BEHEERDER = 'plein/plein-beheerder.dtl'          # beheerder (ROL_BB/BKO/RKO/RCL/CWZ)

TEMPLATE_LEEFTIJDSKLASSEN = 'plein/leeftijdsklassen.dtl'
TEMPLATE_NIEUWEACCOUNTS = 'plein/account-activiteit.dtl'
TEMPLATE_PRIVACY = 'plein/privacy.dtl'

JA_NEE = {False: 'Nee', True: 'Ja'}


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
            rol_nu, functie_nu = rol_get_huidige_functie(request)

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

                if rol_nu == Rollen.ROL_BB:
                    context['rol_is_bb'] = True;
                elif rol_nu == Rollen.ROL_BKO:
                    context['rol_is_bko'] = True;
                elif rol_nu == Rollen.ROL_RKO:
                    context['rol_is_rko'] = True;
                elif rol_nu == Rollen.ROL_RCL:
                    context['rol_is_rcl'] = True;

                if functie_nu:
                    context['huidige_rol'] = Group.objects.get(pk=functie_nu).name
                else:
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


class AccountActiviteitView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de leeftijdsklassen """

    # class variables shared by all instances
    template_name = TEMPLATE_NIEUWEACCOUNTS

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol = rol_get_huidige(self.request)
        return (rol in (Rollen.ROL_IT, Rollen.ROL_BB))


    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['nieuwe_accounts'] = AccountEmail.objects.all().order_by('-account__date_joined')[:50]
        context['recente_activiteit'] = AccountEmail.objects.all().filter(account__last_login__isnull=False).order_by('-account__last_login')[:50]
        context['inlog_pogingen'] = AccountEmail.objects.all().filter(account__laatste_inlog_poging__isnull=False).filter(account__last_login__lt=F('account__laatste_inlog_poging')).order_by('-account__laatste_inlog_poging')
        menu_dynamics(self.request, context)
        return context


# end of file
