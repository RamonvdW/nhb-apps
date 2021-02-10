# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import View
from django.urls import Resolver404
from django.shortcuts import render
from BasisTypen.models import IndivWedstrijdklasse
from .models import (AG_NUL, Competitie, CompetitieKlasse)
from .menu import menu_dynamics_competitie


TEMPLATE_COMPETITIE_KLASSEGRENZEN_TONEN = 'competitie/klassegrenzen-tonen.dtl'


class KlassegrenzenTonenView(View):

    """ deze view laat de vastgestelde aanvangsgemiddelden voor de volgende competitie zien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_KLASSEGRENZEN_TONEN

    @staticmethod
    def _get_indiv_klassen(context, comp):
        """ geef een lijst van IndivWedstrijdklasse terug
            met als extra velden "min_ag18" en "min_ag25"
        """

        if CompetitieKlasse.objects.filter(team=None).count() == 0:
            # er zijn nog geen klassen vastgesteld
            context['geen_klassen'] = True
            return None

        indiv_klassen = list()

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
                indiv.min_ag = min_ag
        # for

        return indiv_klassen

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """
        context = dict()

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen geeft beveiliging
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Resolver404()

        context['comp'] = comp

        context['indiv_klassen'] = self._get_indiv_klassen(context, comp)

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return render(request, self.template_name, context)


# end of file
