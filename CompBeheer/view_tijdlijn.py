# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import Competitie
from Competitie.tijdlijn import is_open_voor_inschrijven_rk_teams
from CompLaagRegio.models import RegioComp
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving


TEMPLATE_COMPETITIE_OVERZICHT_TIJDLIJN = 'compbeheer/tijdlijn.dtl'


class CompetitieTijdlijnView(UserPassesTestMixin, TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_OVERZICHT_TIJDLIJN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None
        self.functie_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_BB,
                               Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL,
                               Rol.ROL_HWL, Rol.ROL_WL)

    def _zet_teams_regio_specifiek(self, comp):
        # toon de RCL en HWL de regio-specifieke fase_D datum voor de teamcompetitie
        if comp.fase_teams > 'F':
            return

        # BB en BKO: toon fase C en D status voor elke regio
        # RKO: toon fase C en D satus voor elke regio van het rayon
        if self.rol_nu in (Rol.ROL_BB, Rol.ROL_BKO, Rol.ROL_RKO):
            comp.fase_c_per_regio = list()
            comp.fase_d_per_regio = list()
            comp.fase_f_per_regio = list()

            qset = (RegioComp
                             .objects
                             .filter(competitie=comp)
                             .select_related('competitie')
                             .order_by('regio__regio_nr'))

            if self.rol_nu == Rol.ROL_RKO:
                my_rayon_nr = self.functie_nu.rayon.rayon_nr
                qset = qset.filter(regio__rayon_nr=my_rayon_nr)

            for deelcomp in qset:
                deelcomp.bepaal_fase()
                if deelcomp.fase_teams == 'C':
                    comp.fase_c_per_regio.append(deelcomp)
                if deelcomp.fase_teams in ('C', 'D'):
                    comp.fase_d_per_regio.append(deelcomp)
                if deelcomp.fase_teams == 'F':
                    comp.fase_f_per_regio.append(deelcomp)
            # for

            if len(comp.fase_f_per_regio) > 0:
                comp.fase_teams = 'F'
                comp.fase_f_teams_actief = True

            if len(comp.fase_d_per_regio) > 0:
                comp.fase_teams = 'D'
                comp.fase_d_teams_actief = True

            if len(comp.fase_c_per_regio) > 0:
                comp.fase_teams = 'C'
                comp.fase_c_teams_actief = True

            return

        # kijk naar 1 regio voor de RCL en HWL en WL
        if self.functie_nu.vereniging:
            # HWL en WL
            regio = self.functie_nu.vereniging.regio
        else:
            # RCL
            regio = self.functie_nu.regio

        if regio:       # pragma: no branch
            deelcomp = RegioComp.objects.get(competitie=comp, regio=regio)
            deelcomp.bepaal_fase()
            comp.begin_fase_D_teams = deelcomp.begin_fase_D
            comp.fase_teams = deelcomp.fase_teams

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:7])  # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        context['rol'] = rol_get_beschrijving(self.request)

        comp.bepaal_fase()                  # zet comp.fase

        comp.rk_teams_is_open, comp.rk_teams_vanaf_datum = is_open_voor_inschrijven_rk_teams(comp)

        context['comp'] = comp

        self._zet_teams_regio_specifiek(comp)

        if self.rol_nu in (Rol.ROL_BB, Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL):
            comp_url = reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk})
        else:
            comp_url = reverse('Competitie:overzicht', kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url()})

        if self.rol_nu in (Rol.ROL_SEC, Rol.ROL_HWL, Rol.ROL_HWL):
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
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
