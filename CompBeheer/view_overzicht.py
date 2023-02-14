# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import Competitie, Regiocompetitie, Kampioenschap
from CompLaagRegio.plugin_overzicht import get_kaartjes_regio
from CompLaagRayon.plugin_overzicht import get_kaartjes_rayon
from CompLaagBond.plugin_overzicht import get_kaartjes_bond
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving
from Plein.menu import menu_dynamics
from Taken.operations import eval_open_taken
from types import SimpleNamespace


TEMPLATE_COMPETITIE_OVERZICHT_BEHEERDER = 'compbeheer/overzicht.dtl'


def get_kaartjes_beheer(rol_nu, functie_nu, comp, kaartjes_algemeen, kaartjes_indiv, kaartjes_teams):
    """ Deze functies levert kaartjes voor op de competitie beheerders pagina
        comp.fase_indiv/fase_teams zijn gezet
    """

    # Tijdlijn
    url = reverse('Competitie:tijdlijn', kwargs={'comp_pk': comp.pk})
    kaartje = SimpleNamespace(
                    prio=1,
                    titel="Tijdlijn",
                    icoon="schedule",
                    tekst="Toon de fases en planning van deze competitie.",
                    url=url)
    kaartjes_algemeen.append(kaartje)

    # Clusters beheren
    if rol_nu == Rollen.ROL_RCL:
        url = reverse('CompLaagRegio:clusters')
        kaartje = SimpleNamespace(
                    prio=5,
                    titel="Clusters",
                    icoon="group_work",
                    tekst="Verenigingen groeperen in geografische clusters.",
                    url=url)
        kaartjes_algemeen.append(kaartje)

    # Toon klassegrenzen (is een openbaar kaartje)
    if comp.klassengrenzen_vastgesteld:
        url = reverse('Competitie:klassengrenzen-tonen', kwargs={'comp_pk': comp.pk})
        kaartje = SimpleNamespace(
                    prio=5,
                    titel="Wedstrijdklassen",
                    icoon="equalizer",
                    tekst="Toon de wedstrijdklassen, klassengrenzen en blazoenen voor de competitie.",
                    url=url)
        kaartjes_algemeen.append(kaartje)

    # Uitslagen / Deelnemers (is een openbaar kaartje)
    if comp.fase_indiv >= 'C':
        url = reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk})
        kaartje = SimpleNamespace(
                    prio=9,
                    titel="Uitslagenlijsten",
                    icoon="scoreboard",
                    tekst="Toon de deelnemerslijsten en uitslagen van deze competitie.",
                    url=url)
        kaartjes_algemeen.append(kaartje)

    if rol_nu == Rollen.ROL_BB:

        # Wijzig datums
        url = reverse('CompBeheer:wijzig-datums', kwargs={'comp_pk': comp.pk})
        kaartje = SimpleNamespace(
                    prio=3,
                    titel="Wijzig datums",
                    icoon="build",
                    tekst="Belangrijke datums aanpassen voor de fases van deze nieuwe competitie.",
                    url=url)
        kaartjes_algemeen.append(kaartje)

        # TODO: Competitie afsluiten


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
        context['toon_functies'] = self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO)       # TODO: waarom niet voor RCL?

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

        if len(kaartjes_algemeen):
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
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Beheer')
        )

        menu_dynamics(self.request, context)
        return context


# end of file
