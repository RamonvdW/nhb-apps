# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import ListView
from Plein.menu import menu_dynamics
from BasisTypen.models import IndivWedstrijdklasse
from .models import (AG_NUL, CompetitieKlasse)


TEMPLATE_COMPETITIE_KLASSEGRENZEN_TONEN = 'competitie/klassegrenzen-tonen.dtl'


class KlassegrenzenTonenView(ListView):

    """ deze view laat de vastgestelde aanvangsgemiddelden voor de volgende competitie zien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_KLASSEGRENZEN_TONEN

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        objs = list()
        if CompetitieKlasse.objects.filter(team=None).count() == 0:
            return objs

        indiv_dict = dict()     # [indiv.pk] = IndivWedstrijdklasse
        for obj in IndivWedstrijdklasse.objects.order_by('volgorde'):
            indiv_dict[obj.pk] = obj
            objs.append(obj)
        # for

        for obj in CompetitieKlasse.objects.filter(team=None).select_related('competitie', 'indiv'):
            indiv = indiv_dict[obj.indiv.pk]
            min_ag = obj.min_ag
            if min_ag != AG_NUL:
                if obj.competitie.afstand == '18':
                    indiv.min_ag18 = obj.min_ag
                else:
                    indiv.min_ag25 = obj.min_ag
        # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context, actief='competitie')
        return context


# end of file
