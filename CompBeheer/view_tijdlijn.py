# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import Competitie
from Competitie.tijdlijn import is_open_voor_inschrijven_rk_teams
from Functie.definities import Rol
from Functie.rol import rol_get_huidige


TEMPLATE_COMPETITIE_OVERZICHT_TIJDLIJN = 'compbeheer/tijdlijn.dtl'


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
        return self.rol_nu in (Rol.ROL_BB,
                               Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL,
                               Rol.ROL_HWL, Rol.ROL_WL)

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

        comp.rk_teams_is_open, comp.rk_teams_vanaf_datum = is_open_voor_inschrijven_rk_teams(comp)

        context['comp'] = comp

        if self.rol_nu in (Rol.ROL_BB, Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL):
            comp_url = reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk})
        else:
            comp_url = reverse('Competitie:overzicht', kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url()})

        if self.rol_nu in (Rol.ROL_SEC, Rol.ROL_HWL, Rol.ROL_HWL):
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
                (None, 'Tijdlijn')
            )
        else:
            context['kruimels'] = (
                (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
                (comp_url, comp.beschrijving.replace(' competitie', '')),
                (None, 'Tijdlijn')
            )

        return context


# end of file
