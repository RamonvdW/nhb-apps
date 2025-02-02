# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.shortcuts import render, reverse
from django.views.generic import View
from django.utils.safestring import mark_safe
from BasisTypen.definities import BLAZOEN2STR
from Competitie.models import Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse
from Competitie.seizoenen import get_comp_pk
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Score.definities import AG_NUL


TEMPLATE_COMPETITIE_KLASSENGRENZEN_TONEN = 'competitie/klassengrenzen-tonen.dtl'
TEMPLATE_COMPETITIE_BESTAAT_NIET = 'competitie/bestaat-niet.dtl'


class KlassengrenzenTonenView(View):

    """ deze view laat de vastgestelde aanvangsgemiddelden voor de volgende competitie zien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_KLASSENGRENZEN_TONEN

    @staticmethod
    def _get_indiv_klassen(comp, toon_aantal):
        """ geef een lijst van individuele competitie wedstrijdklassen terug
            met het AG geformatteerd voor presentatie.
        """
        klassen = (CompetitieIndivKlasse
                   .objects
                   .select_related('competitie')
                   .filter(competitie=comp)
                   .prefetch_related('regiocompetitiesporterboog_set')
                   .order_by('volgorde'))

        for obj in klassen:
            if obj.min_ag > AG_NUL:
                ag_str = "%5.3f" % obj.min_ag
                obj.min_ag_str = ag_str.replace('.', ',')       # nederlands: komma ipv punt

            if toon_aantal:
                obj.aantal = obj.regiocompetitiesporterboog_set.count()

            obj.blazoen_regio_str = BLAZOEN2STR[obj.blazoen1_regio]
            if obj.blazoen1_regio != obj.blazoen2_regio:
                obj.blazoen_regio_str += " of " + BLAZOEN2STR[obj.blazoen2_regio]

            obj.blazoen_rk_bk_str = BLAZOEN2STR[obj.blazoen_rk_bk]
        # for

        return klassen

    @staticmethod
    def _get_team_klassen(comp, aantal_pijlen):
        """ geef een lijst van team competitie wedstrijdklassen terug
            met het teamgemiddelde geformatteerd voor presentatie.
        """
        klassen = (CompetitieTeamKlasse
                   .objects
                   .select_related('competitie')
                   .filter(competitie=comp)
                   .order_by('volgorde'))

        for obj in klassen:
            if obj.min_ag > AG_NUL:
                ag_str = "%5.1f" % (obj.min_ag * aantal_pijlen)
                obj.min_ag_str = ag_str.replace('.', ',')  # nederlands: komma ipv punt

            obj.blazoen_regio_str = BLAZOEN2STR[obj.blazoen1_regio]
            if obj.blazoen2_regio != obj.blazoen1_regio:
                obj.blazoen_regio_str += " of " + BLAZOEN2STR[obj.blazoen2_regio]

            obj.blazoen_rk_bk_str = BLAZOEN2STR[obj.blazoen_rk_bk]
        # for

        return klassen

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """
        context = dict()

        try:
            comp_pk = get_comp_pk(kwargs['comp_pk_of_seizoen'])
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            # externe links naar een oude competitie komen hier --> geef ze een noindex foutmelding pagina
            self.template_name = TEMPLATE_COMPETITIE_BESTAAT_NIET
            context['robots'] = 'noindex'  # prevent indexing this outdated page
            context['bad_seizoen'] = kwargs['comp_pk_of_seizoen']
        else:
            context['comp'] = comp

            if comp.klassengrenzen_vastgesteld:
                if comp.is_indoor():
                    aantal_pijlen = 30
                else:
                    aantal_pijlen = 25

                rol_nu = rol_get_huidige(request)
                context['toon_aantal'] = toon_aantal = (rol_nu == Rol.ROL_BB)

                context['indiv_klassen'] = self._get_indiv_klassen(comp, toon_aantal)
                context['team_klassen'] = self._get_team_klassen(comp, aantal_pijlen)
                context['aantal_pijlen'] = aantal_pijlen
                context['rk_bk_klassen_vastgesteld'] = comp.klassengrenzen_vastgesteld_rk_bk

                context['aantal_indiv_regels'] = 2 + len(context['indiv_klassen'])

                context['aantal_team_rk_bk_regels'] = 2

                for team in context['team_klassen']:
                    if team.is_voor_teams_rk_bk:
                        context['aantal_team_rk_bk_regels'] += 1
                # for

                context['aantal_team_regels'] = 2 + len(context['team_klassen']) - (context['aantal_team_rk_bk_regels'] - 2)

            context['kruimels'] = (
                (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
                (reverse('Competitie:overzicht',
                         kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url()}), comp.beschrijving.replace(' competitie', '')),
                (None, 'Wedstrijdklassen')
            )

        return render(request, self.template_name, context)


# end of file
