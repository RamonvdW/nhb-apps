# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import View
from django.http import Http404
from django.shortcuts import render
from BasisTypen.models import IndivWedstrijdklasse, TeamWedstrijdklasse
from .models import (AG_NUL, Competitie, CompetitieKlasse)
from .menu import menu_dynamics_competitie


TEMPLATE_COMPETITIE_KLASSEGRENZEN_TONEN = 'competitie/klassegrenzen-tonen.dtl'


class KlassegrenzenTonenView(View):

    """ deze view laat de vastgestelde aanvangsgemiddelden voor de volgende competitie zien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_KLASSEGRENZEN_TONEN

    @staticmethod
    def _get_indiv_klassen(comp):
        """ geef een lijst van individuele competitie wedstrijdklassen terug
            met het AG geformatteerd voor presentatie.
        """
        klassen = (CompetitieKlasse
                   .objects
                   .select_related('competitie',
                                   'indiv')
                   .filter(team=None,
                           competitie=comp)
                   .order_by('indiv__volgorde'))

        for obj in klassen:
            if obj.min_ag > AG_NUL:
                obj.min_ag_str = "%5.3f" % obj.min_ag
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

        for obj in klassen:
            if obj.min_ag > AG_NUL:
                obj.min_ag_str = "%5.1f" % (obj.min_ag * aantal_pijlen)
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

        if comp.klassegrenzen_vastgesteld:
            if comp.afstand == '18':
                aantal_pijlen = 30
            else:
                aantal_pijlen = 25

            context['indiv_klassen'] = self._get_indiv_klassen(comp)
            context['team_klassen'] = self._get_team_klassen(comp, aantal_pijlen)
            context['aantal_pijlen'] = aantal_pijlen

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return render(request, self.template_name, context)


# end of file
