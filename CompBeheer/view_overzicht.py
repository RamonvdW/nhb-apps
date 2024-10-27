# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import Competitie, Regiocompetitie, Kampioenschap
from Competitie.tijdlijn import maak_comp_fase_beschrijvingen
from CompBeheer.plugin_overzicht import get_kaartjes_beheer
from CompLaagRegio.plugin_overzicht import get_kaartjes_regio
from CompLaagRayon.plugin_overzicht import get_kaartjes_rayon
from CompLaagBond.plugin_overzicht import get_kaartjes_bond
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving
from Taken.operations import eval_open_taken


TEMPLATE_COMPETITIE_OVERZICHT_BEHEERDER = 'compbeheer/overzicht.dtl'


class CompetitieBeheerView(UserPassesTestMixin, TemplateView):
    """ Deze view biedt de landing page vanuit het menu aan """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_OVERZICHT_BEHEERDER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        context['comp'] = comp

        comp.bepaal_fase()                     # zet comp.fase
        comp.bepaal_openbaar(self.rol_nu)      # zet comp.is_openbaar

        comp.fase_indiv_str, comp.fase_teams_str = maak_comp_fase_beschrijvingen(comp)

        if self.functie_nu:
            # kijk of deze rol nog iets te doen heeft
            context['rol_is_klaar'] = True

            # toon de competitie waar de functie een rol in heeft of had (BKO/RKO/RCL)
            for deelcomp in (Regiocompetitie
                             .objects
                             .filter(competitie=comp,
                                     functie=self.functie_nu)):
                if not deelcomp.is_afgesloten:
                    context['rol_is_klaar'] = False
            # for

            # toon de competitie waar de functie een rol in heeft of had (BKO/RKO/RCL)
            for deelcomp in (Kampioenschap
                             .objects
                             .filter(competitie=comp,
                                     functie=self.functie_nu)):
                if not deelcomp.is_afgesloten:
                    context['rol_is_klaar'] = False
            # for
        else:
            # toon alle competities (BB)
            context['rol_is_klaar'] = False

        # kaartjes ophalen bij de verschillende applicaties
        kaartjes_algemeen = list()
        kaartjes_indiv = list()
        kaartjes_teams = list()

        get_kaartjes_beheer(self.rol_nu, self.functie_nu, comp, kaartjes_algemeen, kaartjes_indiv, kaartjes_teams)
        get_kaartjes_regio(self.rol_nu, self.functie_nu, comp, kaartjes_algemeen, kaartjes_indiv, kaartjes_teams)
        get_kaartjes_rayon(self.rol_nu, self.functie_nu, comp, kaartjes_algemeen, kaartjes_indiv, kaartjes_teams)
        get_kaartjes_bond(self.rol_nu, self.functie_nu, comp, kaartjes_algemeen, kaartjes_indiv, kaartjes_teams)

        if len(kaartjes_algemeen):      # pragma: no branch
            kaartjes_algemeen.sort(key=lambda kaartje: kaartje.prio)
            context['kaartjes_algemeen'] = kaartjes_algemeen

        if len(kaartjes_indiv):
            kaartjes_indiv.sort(key=lambda kaartje: kaartje.prio)
            context['kaartjes_indiv'] = kaartjes_indiv

        if len(kaartjes_teams):
            kaartjes_teams.sort(key=lambda kaartje: kaartje.prio)
            context['kaartjes_teams'] = kaartjes_teams

        eval_open_taken(self.request)

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Beheer')
        )

        return context


# end of file
