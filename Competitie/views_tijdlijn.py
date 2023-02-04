# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import Competitie
from Functie.models import Rollen
from Functie.rol import rol_get_huidige
from Plein.menu import menu_dynamics
import datetime


TEMPLATE_COMPETITIE_OVERZICHT_TIJDLIJN = 'competitie/overzicht-tijdlijn.dtl'


class CompetitieTijdlijnView(UserPassesTestMixin, TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_OVERZICHT_TIJDLIJN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rollen.ROL_BB,
                               Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL,
                               Rollen.ROL_HWL, Rollen.ROL_WL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])  # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()                  # zet comp.fase
        comp.bepaal_openbaar(self.rol_nu)   # zet comp.is_openbaar

        comp.einde_fase_F = comp.laatst_mogelijke_wedstrijd + datetime.timedelta(days=7)
        comp.einde_fase_G = comp.einde_fase_F + datetime.timedelta(days=1)
        comp.einde_fase_K = comp.rk_eerste_wedstrijd - datetime.timedelta(days=14)
        comp.einde_fase_M = comp.rk_laatste_wedstrijd + datetime.timedelta(days=7)

        context['comp'] = comp

        if self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL):
            comp_url = reverse('Competitie:beheer', kwargs={'comp_pk': comp.pk})
        else:
            comp_url = reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk})

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (comp_url, comp.beschrijving.replace(' competitie', '')),
            (None, 'Tijdlijn')
        )

        menu_dynamics(self.request, context)
        return context


# end of file
