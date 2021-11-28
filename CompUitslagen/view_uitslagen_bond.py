# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import TemplateView
from django.http import Http404
from Competitie.models import Competitie, DeelCompetitie, LAAG_BK
from Competitie.menu import menu_dynamics_competitie


TEMPLATE_COMPUITSLAGEN_BOND = 'compuitslagen/uitslagen-bond.dtl'


class UitslagenBondView(TemplateView):

    """ Django class-based view voor de de uitslagen van de bondskampioenschappen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_BOND

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen geeft beveiliging
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        context['comp'] = comp

        comp_boog = kwargs['comp_boog'][:2]          # afkappen voor veiligheid

        try:
           deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(laag=LAAG_BK,
                             competitie__is_afgesloten=False,
                             competitie__pk=comp_pk))
        except DeelCompetitie.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return context


# end of file
