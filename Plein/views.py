# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.shortcuts import redirect, render
from django.views.generic import TemplateView, ListView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Account.leeftijdsklassen import get_leeftijdsklassen
from Account.rol import rol_is_BKO
from Competitie.models import Competitie, models_bepaal_startjaar_nieuwe_competitie


TEMPLATE_PLEIN_BEZOEKER = 'plein/plein-bezoeker.dtl'
TEMPLATE_PLEIN_GEBRUIKER = 'plein/plein-gebruiker.dtl'
TEMPLATE_PLEIN_SCHUTTER = 'plein/plein-schutter.dtl'
TEMPLATE_PLEIN_BKO = 'plein/plein-bko.dtl'
TEMPLATE_PRIVACY = 'plein/privacy.dtl'
TEMPLATE_LEEFTIJDSKLASSEN = 'plein/leeftijdsklassen.dtl'

JA_NEE = {False: 'Nee', True: 'Ja'}


def site_root_view(request):
    """ simpele Django view functie om vanaf de top-level site naar het Plein te gaan """
    return redirect('Plein:plein')


class PleinView(View):
    """ Django class-based view voor het Plein """

    # class variables shared by all instances

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """

        template = TEMPLATE_PLEIN_BEZOEKER
        context = dict()

        if request.user.is_authenticated:
            template = TEMPLATE_PLEIN_GEBRUIKER

            huidige_jaar, leeftijd, is_jong, wlst, clst = get_leeftijdsklassen(self.request)
            if huidige_jaar:
                template = TEMPLATE_PLEIN_SCHUTTER
                context['plein_toon_leeftijdsklassen'] = True
                context['plein_is_jonge_schutter'] = is_jong
                context['plein_huidige_jaar'] = huidige_jaar
                context['plein_leeftijd'] = leeftijd
                context['plein_wlst'] = wlst
                context['plein_clst'] = clst
            else:
                # ouder lid
                context['plein_toon_leeftijdsklassen'] = False

            if rol_is_BKO(self.request):
                template = TEMPLATE_PLEIN_BKO

                objs = Competitie.objects.filter(is_afgesloten=False).order_by('begin_jaar', 'afstand')
                context['object_list'] = objs
                context['have_active_comps'] = (len(objs) > 0)

                for obj in objs:
                    obj.zet_fase()
                    obj.is_afgesloten_str = JA_NEE[obj.is_afgesloten]
                # for

                # als er nog geen competitie is voor het huidige jaar, geeft de BKO dan de optie om deze op te starten
                beginjaar = models_bepaal_startjaar_nieuwe_competitie()
                context['bko_kan_competitie_aanmaken'] = (len(objs.filter(begin_jaar=beginjaar)) == 0)
                if context['bko_kan_competitie_aanmaken']:
                    context['nieuwe_seizoen'] = "%s/%s" % (beginjaar, beginjaar+1)
            # if
        # if

        menu_dynamics(self.request, context)
        return render(request, template, context)


class PrivacyView(TemplateView):

    """ Django class-based view voor het Privacy bericht """

    # class variables shared by all instances
    template_name = TEMPLATE_PRIVACY

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context, actief='privacy')
        return context


class LeeftijdsklassenView(UserPassesTestMixin, TemplateView):
    """ Django class-based view voor de leeftijdsklassen """

    # class variables shared by all instances
    template_name = TEMPLATE_LEEFTIJDSKLASSEN
    login_url = '/account/login/'       # no reverse call

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_leeftijdsklassen(self.request)
        return (leeftijd is not None)

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
