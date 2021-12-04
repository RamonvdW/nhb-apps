# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import View
from django.http import Http404
from django.shortcuts import render
from BasisTypen.models import BLAZOEN2STR
from Functie.rol import rol_get_huidige, Rollen
from .models import (AG_NUL, Competitie, CompetitieKlasse)
from .menu import menu_dynamics_competitie


TEMPLATE_COMPETITIE_KLASSENGRENZEN_TONEN = 'competitie/klassengrenzen-tonen.dtl'


class KlassengrenzenTonenView(View):

    """ deze view laat de vastgestelde aanvangsgemiddelden voor de volgende competitie zien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_KLASSENGRENZEN_TONEN

    @staticmethod
    def _get_indiv_klassen(comp, toon_aantal):
        """ geef een lijst van individuele competitie wedstrijdklassen terug
            met het AG geformatteerd voor presentatie.
        """
        klassen = (CompetitieKlasse
                   .objects
                   .select_related('competitie',
                                   'indiv')
                   .filter(team=None,
                           competitie=comp)
                   .prefetch_related('regiocompetitieschutterboog_set')
                   .order_by('indiv__volgorde'))

        is_18m = (comp.afstand == '18')

        for obj in klassen:
            if obj.min_ag > AG_NUL:
                ag_str = "%5.3f" % obj.min_ag
                obj.min_ag_str = ag_str.replace('.', ',')       # nederlands: komma ipv punt

            if toon_aantal:
                obj.aantal = obj.regiocompetitieschutterboog_set.count()

            if is_18m:
                blazoenen = (obj.indiv.blazoen1_18m_regio, obj.indiv.blazoen2_18m_regio)
            else:
                blazoenen = (obj.indiv.blazoen1_25m_regio, obj.indiv.blazoen2_25m_regio)

            obj.blazoen_regio_str = BLAZOEN2STR[blazoenen[0]]
            if blazoenen[0] != blazoenen[1]:
                obj.blazoen_regio_str += " of " + BLAZOEN2STR[blazoenen[1]]

            if is_18m:
                obj.blazoen_rk_bk_str = BLAZOEN2STR[obj.indiv.blazoen_18m_rk_bk]
            else:
                obj.blazoen_rk_bk_str = BLAZOEN2STR[obj.indiv.blazoen_25m_rk_bk]
        # for

        return klassen

    @staticmethod
    def _get_team_klassen(comp, aantal_pijlen):
        """ geef een lijst van team competitie wedstrijdklassen terug
            met het teamgemiddelde geformatteerd voor presentatie.
        """
        klassen = (CompetitieKlasse
                   .objects
                   .select_related('competitie',
                                   'team')
                   .filter(indiv=None,
                           competitie=comp)
                   .order_by('team__volgorde'))

        is_18m = (comp.afstand == '18')

        for obj in klassen:
            if obj.min_ag > AG_NUL:
                ag_str = "%5.1f" % (obj.min_ag * aantal_pijlen)
                obj.min_ag_str = ag_str.replace('.', ',')  # nederlands: komma ipv punt

            if is_18m:
                obj.blazoen_regio_str = BLAZOEN2STR[obj.team.blazoen1_18m_regio]
                if obj.team.blazoen2_18m_regio != obj.team.blazoen1_18m_regio:
                    obj.blazoen_regio_str += " of " + BLAZOEN2STR[obj.team.blazoen2_18m_regio]

                obj.blazoen_rk_bk_str = BLAZOEN2STR[obj.team.blazoen1_18m_rk_bk]
                if obj.team.blazoen2_18m_rk_bk != obj.team.blazoen1_18m_rk_bk:
                    obj.blazoen_rk_bk_str += " of " + BLAZOEN2STR[obj.team.blazoen2_18m_rk_bk]
            else:
                obj.blazoen_regio_str = BLAZOEN2STR[obj.team.blazoen1_25m_regio]
                if obj.team.blazoen1_25m_regio != obj.team.blazoen2_25m_regio:
                    obj.blazoen_regio_str += " of " + BLAZOEN2STR[obj.team.blazoen2_25m_regio]

                obj.blazoen_rk_bk_str = BLAZOEN2STR[obj.team.blazoen_25m_rk_bk]
        # for

        return klassen

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """
        context = dict()

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen geeft beveiliging
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        context['comp'] = comp

        if comp.klassengrenzen_vastgesteld:
            if comp.afstand == '18':
                aantal_pijlen = 30
            else:
                aantal_pijlen = 25

            rol_nu = rol_get_huidige(request)
            context['toon_aantal'] = toon_aantal = (rol_nu == Rollen.ROL_BB)

            context['indiv_klassen'] = self._get_indiv_klassen(comp, toon_aantal)
            context['team_klassen'] = self._get_team_klassen(comp, aantal_pijlen)
            context['aantal_pijlen'] = aantal_pijlen
            context['rk_bk_klassen_vastgesteld'] = comp.klassengrenzen_vastgesteld_rk_bk

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return render(request, self.template_name, context)


# end of file
