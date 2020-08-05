# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import Resolver404, reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseRedirect, HttpResponse
from Plein.menu import menu_dynamics
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging
from Functie.rol import Rollen, rol_get_huidige
from .models import (LAAG_REGIO, INSCHRIJF_METHODE_3, DAGDEEL, DAGDEEL_AFKORTINGEN,
                     Competitie, DeelCompetitie, RegioCompetitieSchutterBoog)
import csv


TEMPLATE_COMPETITIE_AANGEMELD_REGIO = 'competitie/lijst-aangemeld-regio.dtl'
TEMPLATE_COMPETITIE_INSCHRIJFMETHODE3_BEHOEFTE = 'competitie/inschrijfmethode3-behoefte.dtl'

JA_NEE = {False: 'Nee', True: 'Ja'}


def maak_regiocomp_zoom_knoppen(context, comp_pk, rayon=None, regio=None):

    """ Maak de zoom knoppen structuur voor de regiocompetitie deelnemers lijst """

    if rayon != regio:
        context['zoom_alles_url'] = reverse('Competitie:lijst-regiocomp-alles', kwargs={'comp_pk': comp_pk})

    regios = (NhbRegio
              .objects
              .select_related('rayon')
              .filter(is_administratief=False))

    rayons = NhbRayon.objects.all()

    context['zoom_rayons'] = list()
    for obj in rayons:
        context['zoom_rayons'].append(obj)

        obj.title_str = 'Rayon %s' % obj.rayon_nr
        if obj != rayon:
            obj.zoom_url = reverse('Competitie:lijst-regiocomp-rayon',
                                   kwargs={'comp_pk': comp_pk, 'rayon_pk': obj.pk})

        obj.regios = list()
        for obj2 in regios:
            if obj2.rayon == obj:
                obj.regios.append(obj2)
                obj2.title_str = 'Regio %s' % obj2.regio_nr
                if obj2 != regio:
                    obj2.zoom_url = reverse('Competitie:lijst-regiocomp-regio',
                                            kwargs={'comp_pk': comp_pk, 'regio_pk': obj2.pk})
    # for


class LijstAangemeldRegiocompAllesView(UserPassesTestMixin, TemplateView):

    """ Toon een lijst van SchutterBoog die aangemeld zijn voor de regiocompetitie """

    template_name = TEMPLATE_COMPETITIE_AANGEMELD_REGIO

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL, Rollen.ROL_WL)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        comp_pk = kwargs['comp_pk']
        try:
            comp = Competitie.objects.get(pk=comp_pk)
        except Competitie.DoesNotExist:
            raise Resolver404()

        context['competitie'] = comp

        objs = (RegioCompetitieSchutterBoog
                .objects
                .select_related('klasse', 'klasse__indiv',
                                'deelcompetitie', 'deelcompetitie__nhb_regio',
                                'schutterboog', 'schutterboog__nhblid',
                                'schutterboog__nhblid__bij_vereniging')
                .filter(deelcompetitie__competitie=comp,
                        deelcompetitie__laag=LAAG_REGIO)
                .order_by('klasse__indiv__volgorde', 'aanvangsgemiddelde'))

        volgorde = -1
        for obj in objs:
            if volgorde != obj.klasse.indiv.volgorde:
                obj.nieuwe_klasse = True
                volgorde = obj.klasse.indiv.volgorde
        # for

        context['object_list'] = objs

        context['inhoud'] = 'landelijk'
        maak_regiocomp_zoom_knoppen(context, comp_pk)

        menu_dynamics(self.request, context, actief='competitie')
        return context


class LijstAangemeldRegiocompRayonView(UserPassesTestMixin, TemplateView):

    """ Toon een lijst van SchutterBoog die aangemeld zijn voor de regiocompetitie """

    template_name = TEMPLATE_COMPETITIE_AANGEMELD_REGIO

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL, Rollen.ROL_WL)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        comp_pk = kwargs['comp_pk']
        try:
            comp = Competitie.objects.get(pk=comp_pk)
        except Competitie.DoesNotExist:
            raise Resolver404()

        context['competitie'] = comp

        rayon_pk = kwargs['rayon_pk']
        try:
            rayon = NhbRayon.objects.get(pk=rayon_pk)
        except NhbRayon.DoesNotExist:
            raise Resolver404()

        context['inhoud'] = 'in ' + str(rayon)

        objs = (RegioCompetitieSchutterBoog
                .objects
                .select_related('klasse', 'klasse__indiv',
                                'deelcompetitie', 'deelcompetitie__nhb_regio__rayon',
                                'schutterboog', 'schutterboog__nhblid',
                                'schutterboog__nhblid__bij_vereniging')
                .filter(deelcompetitie__competitie=comp,
                        deelcompetitie__laag=LAAG_REGIO,
                        deelcompetitie__nhb_regio__rayon=rayon)
                .order_by('klasse__indiv__volgorde', 'aanvangsgemiddelde'))

        volgorde = -1
        for obj in objs:
            if volgorde != obj.klasse.indiv.volgorde:
                obj.nieuwe_klasse = True
                volgorde = obj.klasse.indiv.volgorde
        # for

        context['object_list'] = objs

        maak_regiocomp_zoom_knoppen(context, comp_pk, rayon=rayon)

        menu_dynamics(self.request, context, actief='competitie')
        return context


class LijstAangemeldRegiocompRegioView(UserPassesTestMixin, TemplateView):

    """ Toon een lijst van SchutterBoog die aangemeld zijn voor de regiocompetitie """

    template_name = TEMPLATE_COMPETITIE_AANGEMELD_REGIO

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL, Rollen.ROL_WL)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        comp_pk = kwargs['comp_pk']
        try:
            comp = Competitie.objects.get(pk=comp_pk)
        except Competitie.DoesNotExist:
            raise Resolver404()

        context['competitie'] = comp

        regio_pk = kwargs['regio_pk']
        try:
            regio = (NhbRegio
                     .objects
                     .select_related('rayon')
                     .get(pk=regio_pk))
        except NhbRegio.DoesNotExist:
            raise Resolver404()

        context['inhoud'] = 'in ' + str(regio)

        try:
            deelcomp = DeelCompetitie.objects.get(is_afgesloten=False,
                                                  laag=LAAG_REGIO,
                                                  competitie=comp,
                                                  nhb_regio=regio)
        except DeelCompetitie.DoesNotExist:
            raise Resolver404()

        objs = (RegioCompetitieSchutterBoog
                .objects
                .select_related('klasse',
                                'klasse__indiv',
                                'deelcompetitie',
                                'schutterboog',
                                'schutterboog__nhblid',
                                'schutterboog__nhblid__bij_vereniging')
                .filter(deelcompetitie=deelcomp)
                .order_by('klasse__indiv__volgorde', 'aanvangsgemiddelde'))

        volgorde = -1
        for obj in objs:
            obj.team_ja_nee = JA_NEE[obj.inschrijf_voorkeur_team]
            if volgorde != obj.klasse.indiv.volgorde:
                obj.nieuwe_klasse = True
                volgorde = obj.klasse.indiv.volgorde
        # for

        context['object_list'] = objs

        if deelcomp.inschrijf_methode == INSCHRIJF_METHODE_3:
            context['show_dagdeel_telling'] = True
            context['url_behoefte'] = reverse('Competitie:inschrijfmethode3-behoefte',
                                              kwargs={'comp_pk': comp.pk,
                                                      'regio_pk': regio.pk})

        maak_regiocomp_zoom_knoppen(context, comp.pk, regio=regio)

        menu_dynamics(self.request, context, actief='competitie')
        return context


class Inschrijfmethode3BehoefteView(UserPassesTestMixin, TemplateView):

    """ Toon de RCL de behoefte aan quotaplaatsen in een regio met inschrijfmethode 3 """

    template_name = TEMPLATE_COMPETITIE_INSCHRIJFMETHODE3_BEHOEFTE

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_RCL

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def _maak_data_dagdeel_behoefte(self, context, regio, objs):
        """ voegt de volgende elementen toe aan de context:
                regio_verenigingen: lijst van NhbVereniging met counts_list met telling van dagdelen
                dagdelen: beschrijving van dagdelen voor de kolom headers
        """

        context['dagdelen'] = dagdelen = list()
        for _, beschrijving in DAGDEEL:
            dagdelen.append(beschrijving)
        # for

        # maak een lijst van alle verenigingen in deze regio
        context['regio_verenigingen'] = vers = list()
        vers_dict = dict()
        for nhb_ver in (NhbVereniging
                        .objects
                        .filter(regio=regio)
                        .order_by('nhb_nr')
                        .all()):

            vers.append(nhb_ver)
            vers_dict[nhb_ver.nhb_nr] = nhb_ver

            nhb_ver.counts_dict = dict()
            for afkorting in DAGDEEL_AFKORTINGEN:
                nhb_ver.counts_dict[afkorting] = 0
            # for
        # for

        # doe de telling voor alle ingeschreven schutters
        for obj in objs:
            try:
                nhb_ver = vers_dict[obj.bij_vereniging.nhb_nr]
            except KeyError:
                pass
            else:
                afkorting = obj.inschrijf_voorkeur_dagdeel
                try:
                    nhb_ver.counts_dict[afkorting] += 1
                except KeyError:
                    pass
        # for

        # tel totalen
        totals = dict()
        for afkorting in DAGDEEL_AFKORTINGEN:
            totals[afkorting] = 0
        # for

        # convert dict to list
        for nhb_ver in vers:
            nhb_ver.counts_list = list()
            sum = 0
            for afkorting in DAGDEEL_AFKORTINGEN:
                count = nhb_ver.counts_dict[afkorting]
                nhb_ver.counts_list.append(count)
                totals[afkorting] += count
                sum += count
            # for
            nhb_ver.counts_list.append(sum)
        # for

        context['totalen'] = totalen = list()
        sum = 0
        for afkorting in DAGDEEL_AFKORTINGEN:
            count = totals[afkorting]
            totalen.append(count)
            sum += count
        # for
        totalen.append(sum)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        comp_pk = kwargs['comp_pk']
        try:
            comp = Competitie.objects.get(pk=comp_pk)
        except Competitie.DoesNotExist:
            raise Resolver404()

        context['competitie'] = comp

        regio_pk = kwargs['regio_pk']
        try:
            regio = (NhbRegio
                     .objects
                     .select_related('rayon')
                     .get(pk=regio_pk))
        except NhbRegio.DoesNotExist:
            raise Resolver404()

        context['regio'] = regio

        try:
            deelcomp = DeelCompetitie.objects.get(is_afgesloten=False,
                                                  laag=LAAG_REGIO,
                                                  competitie=comp,
                                                  nhb_regio=regio)
        except DeelCompetitie.DoesNotExist:
            raise Resolver404()

        if deelcomp.inschrijf_methode != INSCHRIJF_METHODE_3:
            raise Resolver404()

        objs = (RegioCompetitieSchutterBoog
                .objects
                .select_related('klasse',
                                'klasse__indiv',
                                'deelcompetitie',
                                'bij_vereniging',
                                'schutterboog',
                                'schutterboog__nhblid',
                                'schutterboog__nhblid__bij_vereniging')
                .filter(deelcompetitie=deelcomp)
                .order_by('klasse__indiv__volgorde', 'aanvangsgemiddelde'))

        volgorde = -1
        for obj in objs:
            obj.team_ja_nee = JA_NEE[obj.inschrijf_voorkeur_team]
            if volgorde != obj.klasse.indiv.volgorde:
                obj.nieuwe_klasse = True
                volgorde = obj.klasse.indiv.volgorde
        # for

        # voeg de tabel met dagdeel-behoefte toe
        self._maak_data_dagdeel_behoefte(context, regio, objs)

        # context['url_terug'] = reverse('Competitie:lijst-regiocomp-regio',
        #                                kwargs={'comp_pk': comp.pk,
        #                                        'regio_pk': regio.pk})

        context['url_download'] = reverse('Competitie:inschrijfmethode3-behoefte-als-bestand',
                                          kwargs={'comp_pk': comp.pk,
                                                  'regio_pk': regio.pk})

        menu_dynamics(self.request, context, actief='competitie')
        return context


class Inschrijfmethode3BehoefteAlsBestandView(Inschrijfmethode3BehoefteView):

    """ Deze klasse wordt gebruikt om de lijst van aangemelde schutters in een regio
        te downloaden als csv bestand
    """

    def get(self, request, *args, **kwargs):

        context = dict()

        comp_pk = kwargs['comp_pk']
        try:
            comp = Competitie.objects.get(pk=comp_pk)
        except Competitie.DoesNotExist:
            raise Resolver404()

        context['competitie'] = comp

        regio_pk = kwargs['regio_pk']
        try:
            regio = (NhbRegio
                     .objects
                     .select_related('rayon')
                     .get(pk=regio_pk))
        except NhbRegio.DoesNotExist:
            raise Resolver404()

        try:
            deelcomp = DeelCompetitie.objects.get(is_afgesloten=False,
                                                  laag=LAAG_REGIO,
                                                  competitie=comp,
                                                  nhb_regio=regio)
        except DeelCompetitie.DoesNotExist:
            raise Resolver404()

        objs = (RegioCompetitieSchutterBoog
                .objects
                .select_related('klasse',
                                'klasse__indiv',
                                'deelcompetitie',
                                'bij_vereniging',
                                'schutterboog',
                                'schutterboog__nhblid',
                                'schutterboog__nhblid__bij_vereniging')
                .filter(deelcompetitie=deelcomp)
                .order_by('klasse__indiv__volgorde', 'aanvangsgemiddelde'))

        context['object_list'] = objs

        if deelcomp.inschrijf_methode != INSCHRIJF_METHODE_3:
            raise Resolver404()

        # voeg de tabel met dagdeel-behoefte toe
        # dict(nhb_ver) = dict("dagdeel_afkorting") = count
        # list[nhb_ver, ..] =
        self._maak_data_dagdeel_behoefte(context, regio, objs)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="behoefte-%s.csv"' % regio.regio_nr

        writer = csv.writer(response)
        writer.writerow(['ver_nr', 'Naam'] + context['dagdelen'] + ['Totaal'])

        for nhb_ver in context['regio_verenigingen']:
            writer.writerow([nhb_ver.nhb_nr, nhb_ver.naam] + nhb_ver.counts_list)
        # for

        writer.writerow(['-', 'Totalen'] + context['totalen'])

        return response

# end of file
