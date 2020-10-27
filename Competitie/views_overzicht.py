# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.shortcuts import render
from django.urls import Resolver404, reverse
from django.views.generic import TemplateView, ListView, View
from django.utils import timezone
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige_functie, rol_get_beschrijving
from NhbStructuur.models import NhbRayon, NhbRegio
from Score.models import zoek_meest_recente_automatisch_vastgestelde_ag
from .models import (LAAG_REGIO, LAAG_RK, LAAG_BK,
                     Competitie, DeelCompetitie, RegioCompetitieSchutterBoog)


TEMPLATE_COMPETITIE_OVERZICHT = 'competitie/overzicht.dtl'
TEMPLATE_COMPETITIE_OVERZICHT_HWL = 'competitie/overzicht-hwl.dtl'
TEMPLATE_COMPETITIE_OVERZICHT_BEHEERDER = 'competitie/overzicht-beheerder.dtl'
TEMPLATE_COMPETITIE_AANGEMELD_REGIO = 'competitie/lijst-aangemeld-regio.dtl'

JA_NEE = {False: 'Nee', True: 'Ja'}


def models_bepaal_startjaar_nieuwe_competitie():
    """ bepaal het start jaar van de nieuwe competitie """
    return timezone.now().year


class CompetitieOverzichtView(View):
    """ Deze view biedt de landing page vanuit het menu aan """

    # class variables shared by all instances
    # (none)

    @staticmethod
    def _get_competities(context, rol_nu, functie_nu):
        if functie_nu and functie_nu.comp_type != '':
            # haal alleen specifieke competities op (18m of 25m)
            # afhankelijk van de huidige functie
            comps = (Competitie
                     .objects
                     .filter(is_afgesloten=False,
                             afstand=functie_nu.comp_type)
                     .order_by('begin_jaar', 'afstand'))
        else:
            # haal alle competities op (18m en 25m)
            comps = (Competitie
                     .objects
                     .filter(is_afgesloten=False)
                     .order_by('begin_jaar', 'afstand'))

        for comp in comps:
            if rol_nu == Rollen.ROL_HWL:
                comp.url_inschrijvingen = reverse('Competitie:lijst-regiocomp-regio',
                                                  kwargs={'comp_pk': comp.pk,
                                                          'regio_pk': functie_nu.nhb_ver.regio.pk})
            elif rol_nu == Rollen.ROL_RCL:
                comp.url_inschrijvingen = reverse('Competitie:lijst-regiocomp-regio',
                                                  kwargs={'comp_pk': comp.pk,
                                                          'regio_pk': functie_nu.nhb_regio.pk})
            elif rol_nu == Rollen.ROL_RKO:
                comp.url_inschrijvingen = reverse('Competitie:lijst-regiocomp-rayon',
                                                  kwargs={'comp_pk': comp.pk,
                                                          'rayon_pk': functie_nu.nhb_rayon.pk})
            else:
                comp.url_inschrijvingen = reverse('Competitie:lijst-regiocomp-alles',
                                                  kwargs={'comp_pk': comp.pk})

            comp.zet_fase()
            if comp.fase == 'A1' and rol_nu == Rollen.ROL_BB:
                context['bb_kan_ag_vaststellen'] = True

            if comp.fase >= 'A2':
                context['toon_klassegrenzen'] = True
        # for
        context['competities'] = comps

    def _get_competitie_overzicht_beheerder(self, request, rol_nu, functie_nu):
        context = dict()

        context['huidige_rol'] = rol_get_beschrijving(request)
        context['toon_functies'] = rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO)
        context['bb_kan_ag_vaststellen'] = False

        self._get_competities(context, rol_nu, functie_nu)

        # kies de competities om het tijdschema van te tonen
        objs = list()
        if functie_nu:
            # toon de competitie waar de functie een rol in heeft (BKO/RKO/RCL)
            for deelcomp in (DeelCompetitie
                             .objects
                             .filter(is_afgesloten=False,
                                     functie=functie_nu)):
                objs.append(deelcomp.competitie)
            # for
        else:
            # toon alle competities (IT/BB)
            objs = (Competitie
                    .objects
                    .filter(is_afgesloten=False)
                    .order_by('begin_jaar', 'afstand'))

        context['object_list'] = objs
        context['have_active_comps'] = len(objs) > 0

        # kies de competities waarvoor de beheerder getoond kunnen worden
        for obj in objs:
            obj.zet_fase()
            obj.is_afgesloten_str = JA_NEE[obj.is_afgesloten]       # TODO: wordt niet gebruikt
        # for

        if rol_nu == Rollen.ROL_BB:
            context['rol_is_bb'] = True
            # als er nog geen competitie is voor het huidige jaar, geeft de BB dan de optie om deze op te starten
            beginjaar = models_bepaal_startjaar_nieuwe_competitie()
            context['nieuwe_seizoen'] = "%s/%s" % (beginjaar, beginjaar+1)
            context['bb_kan_competitie_aanmaken'] = (0 == objs.filter(begin_jaar=beginjaar).count())

            if context['bb_kan_ag_vaststellen']:
                # zoek uit wanneer dit voor het laatste gedaan is
                datum = zoek_meest_recente_automatisch_vastgestelde_ag()
                if datum:
                    context['bb_ag_nieuwste_datum'] = datum.strftime("%Y-%m-%d %H:%M")

            context['show_wijzig_datums'] = True
            for obj in objs:
                obj.url_wijzig_datums = reverse('Competitie:wijzig-datums', kwargs={'comp_pk': obj.pk})
            # for

            context['planning_deelcomp'] = (DeelCompetitie
                                            .objects
                                            .filter(laag=LAAG_BK)
                                            .select_related('competitie'))
            for obj in context['planning_deelcomp']:
                obj.titel = 'Planning %sm' % obj.competitie.afstand
                obj.tekst = 'Landelijke planning voor de %s.' % obj.competitie.beschrijving
                obj.url = reverse('Competitie:bond-planning', kwargs={'deelcomp_pk': obj.pk})
            # for

        if rol_nu == Rollen.ROL_RCL:
            context['planning_deelcomp'] = (DeelCompetitie
                                            .objects
                                            .filter(laag=LAAG_REGIO,
                                                    nhb_regio=functie_nu.nhb_regio,
                                                    competitie__afstand=functie_nu.comp_type)
                                            .select_related('nhb_regio', 'competitie'))
            for obj in context['planning_deelcomp']:
                obj.titel = 'Planning Regio'
                obj.tekst = 'Planning voor %s voor de %s.' % (obj.nhb_regio.naam, obj.competitie.beschrijving)
                obj.url = reverse('Competitie:regio-planning', kwargs={'deelcomp_pk': obj.pk})
            # for

        elif rol_nu == Rollen.ROL_RKO:
            context['planning_deelcomp'] = (DeelCompetitie
                                            .objects
                                            .filter(laag=LAAG_RK,
                                                    nhb_rayon=functie_nu.nhb_rayon,
                                                    competitie__afstand=functie_nu.comp_type)
                                            .select_related('nhb_rayon', 'competitie'))
            for obj in context['planning_deelcomp']:
                obj.titel = 'Planning %s' % obj.nhb_rayon.naam
                obj.tekst = 'Planning voor %s voor de %s.' % (obj.nhb_rayon.naam, obj.competitie.beschrijving)
                obj.url = reverse('Competitie:rayon-planning', kwargs={'deelcomp_pk': obj.pk})
            # for

        elif rol_nu == Rollen.ROL_BKO:
            context['planning_deelcomp'] = (DeelCompetitie
                                            .objects
                                            .filter(laag=LAAG_BK,
                                                    competitie__afstand=functie_nu.comp_type)
                                            .select_related('competitie'))
            for obj in context['planning_deelcomp']:
                obj.titel = 'Planning %sm' % obj.competitie.afstand
                obj.tekst = 'Landelijke planning voor de %s.' % obj.competitie.beschrijving
                obj.url = reverse('Competitie:bond-planning', kwargs={'deelcomp_pk': obj.pk})
            # for

        return context, TEMPLATE_COMPETITIE_OVERZICHT_BEHEERDER

    def _get_competitie_overzicht_hwl(self, request, rol_nu, functie_nu):
        context = dict()
        self._get_competities(context, rol_nu, functie_nu)

        # haal zowel de 18m als 25m deelcompetities op in de regio van de HWL
        context['planning_deelcomp'] = (DeelCompetitie
                                        .objects
                                        .filter(laag=LAAG_REGIO,
                                                nhb_regio=functie_nu.nhb_ver.regio))

        return context, TEMPLATE_COMPETITIE_OVERZICHT_HWL

    def _get_competitie_overzicht_schutter_bezoeker(self, rol_nu):
        # let op! Niet alleen voor schutter, maar ook voor gebruiker/anon
        context = dict()

        self._get_competities(context, Rollen.ROL_SCHUTTER, None)

        if rol_nu == Rollen.ROL_SCHUTTER:
            # TODO: wedstrijdkalender toevoegen
            pass

        return context, TEMPLATE_COMPETITIE_OVERZICHT

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """

        rol_nu, functie_nu = rol_get_huidige_functie(request)

        if rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL):
            context, template = self._get_competitie_overzicht_beheerder(request, rol_nu, functie_nu)
        elif rol_nu == Rollen.ROL_HWL:
            context, template = self._get_competitie_overzicht_hwl(request, rol_nu, functie_nu)
        else:
            context, template = self._get_competitie_overzicht_schutter_bezoeker(rol_nu)

        menu_dynamics(self.request, context, actief='competitie')
        return render(request, template, context)


# end of file
