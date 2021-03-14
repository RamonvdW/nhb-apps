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
        """ geef een lijst van IndivWedstrijdklasse terug
            met als extra velden "min_ag18" en "min_ag25"
        """

        indiv_klassen = list()  # gesorteerd
        indiv_dict = dict()     # [indiv.pk] = IndivWedstrijdklasse

        for obj in IndivWedstrijdklasse.objects.order_by('volgorde'):
            indiv_dict[obj.pk] = obj
            indiv_klassen.append(obj)
        # for

        for obj in (CompetitieKlasse
                    .objects
                    .select_related('competitie',
                                    'indiv')
                    .filter(team=None,
                            competitie=comp)):

            indiv = indiv_dict[obj.indiv.pk]
            min_ag = obj.min_ag

            if min_ag != AG_NUL:
                indiv.min_ag = "%5.3f" % min_ag
        # for

        return indiv_klassen

    @staticmethod
    def _get_team_klassen(comp):

        if comp.afstand == '18':
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        team_klassen = list()   # gesorteerd
        team_dict = dict()      # [team.pk] = TeamWedstrijdklasse

        for obj in TeamWedstrijdklasse.objects.order_by('volgorde'):
            team_dict[obj.pk] = obj
            team_klassen.append(obj)
        # for

        for obj in (CompetitieKlasse
                    .objects
                    .select_related('competitie',
                                    'team')
                    .filter(indiv=None,
                            competitie=comp)):

            team = team_dict[obj.team.pk]
            min_ag = obj.min_ag * aantal_pijlen

            if min_ag > AG_NUL:
                team.min_ag = "%5.1f" % min_ag
        # for

        return team_klassen

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
            context['indiv_klassen'] = self._get_indiv_klassen(comp)
            context['team_klassen'] = self._get_team_klassen(comp)

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return render(request, self.template_name, context)


# end of file
