# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import DeelKampioenschap, DEEL_RK, DEEL_BK
from Functie.models import Rollen
from Functie.rol import rol_get_huidige_functie
from Plein.menu import menu_dynamics


TEMPLATE_COMPLAAGBOND_PLANNING_LANDELIJK = 'complaagbond/planning-landelijk.dtl'


class BondPlanningView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de planning voor een competitie op het landelijke niveau """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPLAAGBOND_PLANNING_LANDELIJK
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelkamp_pk = int(kwargs['deelkamp_pk'][:6])  # afkappen voor de veiligheid
            deelkamp = (DeelKampioenschap
                        .objects
                        .select_related('competitie')
                        .get(pk=deelkamp_pk,
                             deel=DEEL_BK))
        except (KeyError, DeelKampioenschap.DoesNotExist):
            raise Http404('Kampioenschap niet gevonden')

        if self.rol_nu == Rollen.ROL_BKO:
            if deelkamp.competitie.afstand != self.functie_nu.comp_type:
                raise Http404('Verkeerde competitie (2)')

        context['deelcomp_bk'] = deelkamp

        context['rayon_deelkamps'] = (DeelKampioenschap
                                      .objects
                                      .filter(deel=DEEL_RK,
                                              competitie=deelkamp.competitie)
                                      .order_by('nhb_rayon__rayon_nr',
                                                'deel'))

        comp = deelkamp.competitie

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Planning')
        )

        menu_dynamics(self.request, context)
        return context


# end of file
