# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Logboek.models import schrijf_in_logboek
from Account.rol import rol_is_BKO
from .models import TeamType, TeamTypeBoog, BoogType, WedstrijdKlasse, WedstrijdKlasseBoog, WedstrijdKlasseLeeftijd


TEMPLATE_COMPETITIE_DEFAULTS = 'basistypen/competitie-defaults.dtl'


class InstellingenVolgendeCompetitieView(UserPassesTestMixin, ListView):

    """ deze view laat de defaults voor de volgende competitie zien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_DEFAULTS
    login_url = '/account/login/'       # no reverse call

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        res = rol_is_BKO(self.request)
        return res

    def _get_queryset_teamtypen(self):
        objs = TeamType.objects.all()
        for teamtype in objs:
            boogtypen = [obj.boogtype.afkorting for obj in TeamTypeBoog.objects.select_related('boogtype').filter(teamtype=teamtype)]
            teamtype.boogtypen = "+".join(boogtypen)
        # for
        return objs

    def _get_queryset_indivklassen(self):
        objs = WedstrijdKlasse.objects.filter(is_voor_teams=False)
        for klasse in objs:
            # add boogtypen
            boogtypen = [obj.boogtype.afkorting for obj in WedstrijdKlasseBoog.objects.select_related('boogtype').filter(wedstrijdklasse=klasse)]
            klasse.boogtypen = "+".join(boogtypen)

            # add leeftijdsklassen
            leeftijden = [obj.leeftijdsklasse.afkorting for obj in WedstrijdKlasseLeeftijd.objects.select_related('leeftijdsklasse').filter(wedstrijdklasse=klasse)]
            klasse.leeftijden = "+".join(leeftijden)
        # for
        return objs

    def _get_queryset_teamklassen(self):
        objs = WedstrijdKlasse.objects.filter(is_voor_teams=True)
        for klasse in objs:
            # add boogtypen
            boogtypen = [obj.boogtype.afkorting for obj in WedstrijdKlasseBoog.objects.select_related('boogtype').filter(wedstrijdklasse=klasse)]
            klasse.boogtypen = "+".join(boogtypen)
        # for
        return objs

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        self.teamtypen = self._get_queryset_teamtypen()
        self.indivklassen = self._get_queryset_indivklassen()
        self.teamklassen = self._get_queryset_teamklassen()
        return None

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['teamtypen'] = self.teamtypen
        context['indivklassen'] = self.indivklassen
        context['teamklassen'] = self.teamklassen
        menu_dynamics(self.request, context)
        return context

# end of file
