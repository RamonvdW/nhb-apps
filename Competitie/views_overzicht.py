# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.shortcuts import render
from django.urls import Resolver404, reverse
from django.views.generic import TemplateView, ListView, View
from django.utils import timezone
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige_functie, rol_get_beschrijving, rol_get_huidige
from BasisTypen.models import IndivWedstrijdklasse
from NhbStructuur.models import NhbRegio
from Score.models import zoek_meest_recente_automatisch_vastgestelde_ag
from .models import (AG_NUL, LAAG_REGIO, LAAG_RK, LAAG_BK,
                     Competitie, DeelCompetitie, CompetitieKlasse, RegioCompetitieSchutterBoog)
import datetime


TEMPLATE_COMPETITIE_OVERZICHT = 'competitie/overzicht.dtl'
TEMPLATE_COMPETITIE_OVERZICHT_HWL = 'competitie/overzicht-hwl.dtl'
TEMPLATE_COMPETITIE_OVERZICHT_BEHEERDER = 'competitie/overzicht-beheerder.dtl'
TEMPLATE_COMPETITIE_KLASSEGRENZEN_TONEN = 'competitie/klassegrenzen-tonen.dtl'
TEMPLATE_COMPETITIE_AANGEMELD_REGIO = 'competitie/lijst-aangemeld-regio.dtl'
TEMPLATE_COMPETITIE_INFO_COMPETITIE = 'competitie/info-competitie.dtl'


JA_NEE = {False: 'Nee', True: 'Ja'}


def models_bepaal_startjaar_nieuwe_competitie():
    """ bepaal het start jaar van de nieuwe competitie """
    return timezone.now().year


def zet_fase(comp):
    # fase A was totdat dit object gemaakt werd

    now = timezone.now()
    now = datetime.date(year=now.year, month=now.month, day=now.day)

    if now < comp.begin_aanmeldingen:
        # zijn de wedstrijdklassen vastgesteld?
        if CompetitieKlasse.objects.filter(competitie=comp).count() == 0:
            # A1 = aanvangsgemiddelden en klassegrenzen zijn vastgesteld
            comp.fase = 'A1'
            return

        # A2 = klassegrenzen zijn bepaald
        comp.fase = 'A2'
        return

    # B = open voor inschrijvingen
    if now < comp.einde_aanmeldingen:
        comp.fase = 'B'
        return

    # C = aanmaken teams; gesloten voor individuele inschrijvingen
    if now < comp.einde_teamvorming:
        comp.fase = 'C'
        return

    # D = aanmaken poules en afronden wedstrijdschema's
    if now < comp.eerste_wedstrijd:
        comp.fase = 'D'
        return

    # E = Begin wedstrijden
    comp.fase = 'E'


class CompetitieOverzichtView(View):
    """ Deze view biedt de landing page vanuit het menu aan """

    # class variables shared by all instances
    # (none)

    def _get_competities(self, context, rol_nu):
        comps = Competitie.objects.filter(is_afgesloten=False).order_by('begin_jaar', 'afstand')
        for comp in comps:
            comp.url_inschrijvingen = reverse('Competitie:lijst-regio', kwargs={'comp_pk': comp.pk})
            zet_fase(comp)
            if comp.fase == 'A1' and rol_nu == Rollen.ROL_BB:
                context['bb_kan_ag_vaststellen'] = True
        # for
        context['competities'] = comps

    def _get_competitie_overzicht_beheerder(self, request):
        context = dict()

        rol_nu, functie_nu = rol_get_huidige_functie(request)

        context['huidige_rol'] = rol_get_beschrijving(request)
        context['toon_functies'] = rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO)
        context['bb_kan_ag_vaststellen'] = False

        self._get_competities(context, rol_nu)

        # kies de competities om het tijdschema van de tonen
        objs = list()
        if rol_nu == Rollen.ROL_BB:
            # toon alle competities
            objs = (Competitie
                    .objects
                    .filter(is_afgesloten=False)
                    .order_by('begin_jaar', 'afstand'))
        elif functie_nu:
            # toon de competitie waar de functie een rol in heeft
            for deelcomp in (DeelCompetitie
                             .objects
                             .filter(is_afgesloten=False,
                                     functie=functie_nu)):
                objs.append(deelcomp.competitie)
            # for

        context['object_list'] = objs
        context['have_active_comps'] = len(objs) > 0

        # kies de competities waarvoor de beheerder getoond kunnen worden
        for obj in objs:
            zet_fase(obj)
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
                    context['bb_ag_nieuwste_datum'] = datum

            context['show_wijzig_datums'] = True
            for obj in objs:
                obj.url_wijzig_datums = reverse('Competitie:wijzig-datums', kwargs={'comp_pk': obj.pk})
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

    def _get_competitie_overzicht_hwl(self, request):
        context = dict()
        self._get_competities(context, Rollen.ROL_HWL)

        rol_nu, functie_nu = rol_get_huidige_functie(request)

        context['planning_deelcomp'] = (DeelCompetitie
                                        .objects
                                        .filter(laag=LAAG_REGIO,
                                                nhb_regio=functie_nu.nhb_ver.regio))

        return context, TEMPLATE_COMPETITIE_OVERZICHT_HWL

    @staticmethod
    def _get_competitie_overzicht_schutter():
        # let op! Niet alleen voor schutter, maar ook voor gebruiker/anon
        context = dict()
        return context, TEMPLATE_COMPETITIE_OVERZICHT

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """

        rol_nu = rol_get_huidige(self.request)
        if rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL):
            context, template = self._get_competitie_overzicht_beheerder(request)
        elif rol_nu == Rollen.ROL_HWL:
            context, template = self._get_competitie_overzicht_hwl(request)
        else:
            context, template = self._get_competitie_overzicht_schutter()

        menu_dynamics(self.request, context, actief='competitie')
        return render(request, template, context)


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


class LijstAangemeldRegioView(TemplateView):

    """ Toon een lijst van SchutterBoog die aangemeld zijn voor de regiocompetitie """

    template_name = TEMPLATE_COMPETITIE_AANGEMELD_REGIO

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        comp_pk = kwargs['comp_pk']

        try:
            context['competitie'] = Competitie.objects.get(pk=comp_pk)
        except Competitie.DoesNotExist:
            raise Resolver404()

        context['object_list'] = (RegioCompetitieSchutterBoog
                                  .objects
                                  .select_related('klasse', 'klasse__indiv', 'deelcompetitie', 'schutterboog', 'schutterboog__nhblid', 'schutterboog__nhblid__bij_vereniging')
                                  .filter(deelcompetitie__competitie=comp_pk)
                                  .order_by('klasse__indiv__volgorde', 'aanvangsgemiddelde'))

        volgorde = -1
        for obj in context['object_list']:
            if volgorde != obj.klasse.indiv.volgorde:
                obj.nieuwe_klasse = True
                volgorde = obj.klasse.indiv.volgorde
        # for

        menu_dynamics(self.request, context, actief='competitie')
        return context


class InfoCompetitieView(TemplateView):

    """ Django class-based view voor de Competitie Info """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_INFO_COMPETITIE

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['regios'] = (NhbRegio
                             .objects
                             .filter(is_administratief=False)
                             .select_related('rayon')
                             .order_by('regio_nr'))

        account = self.request.user
        if account and account.is_authenticated:
            if account.nhblid_set.count() > 0:
                nhblid = account.nhblid_set.all()[0]
                nhb_ver = nhblid.bij_vereniging
                if nhb_ver:
                    context['mijn_vereniging'] = nhb_ver
                    for obj in context['regios']:
                        if obj == nhb_ver.regio:
                            obj.mijn_regio = True
                    # for

        context['klassen_count'] = IndivWedstrijdklasse.objects.exclude(is_onbekend=True).count()

        menu_dynamics(self.request, context, actief='competitie')
        return context


# end of file
