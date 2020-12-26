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
from Schutter.models import SchutterVoorkeuren
from .models import (LAAG_REGIO, INSCHRIJF_METHODE_3, DAGDEEL, DAGDEEL_AFKORTINGEN,
                     Competitie, DeelCompetitie, RegioCompetitieSchutterBoog)
import csv


TEMPLATE_COMPETITIE_AANGEMELD_REGIO = 'competitie/lijst-aangemeld-regio.dtl'
TEMPLATE_COMPETITIE_INSCHRIJFMETHODE3_BEHOEFTE = 'competitie/inschrijfmethode3-behoefte.dtl'

JA_NEE = {False: 'Nee', True: 'Ja'}

BLAZOEN_DT_C = 'DT Compound'
BLAZOEN_DT_R = 'DT Recurve (wens)'
BLAZOEN_40CM = '40cm'
BLAZOEN_60CM = '60cm'
BLAZOEN_60CM_C = '60cm Compound'

COMP_BLAZOENEN = {'18': (BLAZOEN_40CM, BLAZOEN_DT_C, BLAZOEN_DT_R, BLAZOEN_60CM),
                  '25': (BLAZOEN_60CM, BLAZOEN_60CM_C)}


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

        try:
            comp_pk = int(kwargs['comp_pk'][:6])        # afkappen voor veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Resolver404()

        comp.zet_fase()
        if comp.fase < 'B' or comp.fase > 'E':
            raise Resolver404()

        context['competitie'] = comp

        objs = (RegioCompetitieSchutterBoog
                .objects
                .select_related('klasse',
                                'klasse__indiv',
                                'deelcompetitie',
                                'deelcompetitie__nhb_regio',
                                'schutterboog',
                                'schutterboog__nhblid',
                                'bij_vereniging')
                .filter(deelcompetitie__competitie=comp,
                        deelcompetitie__laag=LAAG_REGIO)
                .order_by('klasse__indiv__volgorde', '-aanvangsgemiddelde'))

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

        try:
            comp_pk = int(kwargs['comp_pk'][:6])    # afkappen voor veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Resolver404()

        comp.zet_fase()
        if comp.fase < 'B' or comp.fase > 'E':
            raise Resolver404()

        context['competitie'] = comp

        try:
            rayon_pk = int(kwargs['rayon_pk'][:6])  # afkappen voor veiligheid
            rayon = NhbRayon.objects.get(pk=rayon_pk)
        except (ValueError, NhbRayon.DoesNotExist):
            raise Resolver404()

        context['inhoud'] = 'in ' + str(rayon)

        objs = (RegioCompetitieSchutterBoog
                .objects
                .select_related('klasse',
                                'klasse__indiv',
                                'deelcompetitie',
                                'deelcompetitie__nhb_regio__rayon',
                                'schutterboog',
                                'schutterboog__nhblid',
                                'bij_vereniging')
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

        try:
            comp_pk = int(kwargs['comp_pk'][:6])        # afkappen voor veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Resolver404()

        comp.zet_fase()
        if comp.fase < 'B' or comp.fase > 'E':
            raise Resolver404()

        context['competitie'] = comp

        try:
            regio_pk = int(kwargs['regio_pk'][:6])      # afkappen voor veiligheid
            regio = (NhbRegio
                     .objects
                     .select_related('rayon')
                     .get(pk=regio_pk))
        except (ValueError, NhbRegio.DoesNotExist):
            raise Resolver404()

        context['inhoud'] = 'in ' + str(regio)

        try:
            deelcomp = DeelCompetitie.objects.get(laag=LAAG_REGIO,
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
                                'bij_vereniging')
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

    def _maak_data_dagdeel_behoefte(self, context, deelcomp, objs, regio):
        """ voegt de volgende elementen toe aan de context:
                regio_verenigingen: lijst van NhbVereniging met counts_list met telling van dagdelen
                dagdelen: beschrijving van dagdelen voor de kolom headers
        """

        alles_mag = (deelcomp.toegestane_dagdelen == '')

        context['dagdelen'] = dagdelen = list()
        for afkorting, beschrijving in DAGDEEL:
            if alles_mag or (afkorting in deelcomp.toegestane_dagdelen):
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
        # objs = RegioCompetitieSchutterBoog
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
            som = 0
            for afkorting in DAGDEEL_AFKORTINGEN:
                if alles_mag or (afkorting in deelcomp.toegestane_dagdelen):
                    count = nhb_ver.counts_dict[afkorting]
                    nhb_ver.counts_list.append(count)
                    totals[afkorting] += count
                    som += count
            # for
            nhb_ver.counts_list.append(som)
        # for

        context['totalen'] = totalen = list()
        som = 0
        for afkorting in DAGDEEL_AFKORTINGEN:
            if alles_mag or (afkorting in deelcomp.toegestane_dagdelen):
                count = totals[afkorting]
                totalen.append(count)
                som += count
        # for
        totalen.append(som)

    def _maak_data_blazoen_behoefte(self, context, deelcomp, objs):
        """ maak het overzicht hoeveel blazoenen er nodig zijn
            voor elk dagdeel
        """

        afstand = deelcomp.competitie.afstand
        alles_mag = (deelcomp.toegestane_dagdelen == '')

        blazoenen = dict()
        for blazoen in COMP_BLAZOENEN[afstand]:
            blazoenen[blazoen] = afk_count = dict()
            for afkorting in DAGDEEL_AFKORTINGEN:
                afk_count[afkorting] = 0
            # for
        # for

        # schutters met recurve boog willen mogelijk DT
        voorkeur_dt = (SchutterVoorkeuren
                       .objects
                       .select_related('nhblid')
                       .filter(voorkeur_dutchtarget_18m=True)
                       .values_list('nhblid__nhb_nr', flat=True))

        # objs = RegioCompetitieSchutterBoog
        for obj in objs:
            boog_afkorting = obj.schutterboog.boogtype.afkorting
            if afstand == '18':
                # 18m wordt geschoten op 40cm blazoen
                #       uitzondering: alle Compound + Recurve klasse 1+2
                #       uitzondering: aspiranten schieten op 60cm blazoen
                # recurve schutters mogen voorkeur voor DT opgeven

                blazoen = BLAZOEN_40CM
                if boog_afkorting == 'C':
                    blazoen = 'DT Compound'
                elif boog_afkorting == 'R':
                    # deze schutter heeft misschien voorkeur voor DT
                    if obj.schutterboog.nhblid.nhb_nr in voorkeur_dt:
                        blazoen = BLAZOEN_DT_R

                # controleer of schutter een aspirant is
                if obj.klasse.indiv.niet_voor_rk_bk and not obj.klasse.indiv.is_onbekend:
                    # schutterboog is ingeschreven in een aspirant klasse
                    blazoen = BLAZOEN_60CM
            else:
                # 25m wordt geschoten op 60cm blazoen
                #       aspiranten schieten op 18m
                #       compound kan een eigen klein blazoen krijgen??
                blazoen = BLAZOEN_60CM
                if boog_afkorting == 'C':
                    blazoen = BLAZOEN_60CM_C

            try:
                blazoenen[blazoen][obj.inschrijf_voorkeur_dagdeel] += 1
            except KeyError:
                pass
        # for

        # converteer naar lijstjes met vaste volgorde van de dagdelen
        context['blazoen_count'] = blazoen_behoefte = list()
        for blazoen in COMP_BLAZOENEN[afstand]:     # bepaalt volgorde
            kolommen = list()
            blazoen_behoefte.append(kolommen)

            kolommen.append(blazoen)        # 1e kolom: beschrijving blazoen

            som = 0
            tellingen = blazoenen[blazoen]
            for afkorting in DAGDEEL_AFKORTINGEN:
                if alles_mag or (afkorting in deelcomp.toegestane_dagdelen):
                    count = tellingen[afkorting]
                    kolommen.append(count)
                    som += count
            # for
            kolommen.append(som)
        # for

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])        # afkappen voor veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Resolver404()

        comp.zet_fase()
        if comp.fase < 'B' or comp.fase > 'E':
            raise Resolver404()

        context['competitie'] = comp

        try:
            regio_pk = int(kwargs['regio_pk'][:6])      # afkappen voor veiligheid
            regio = (NhbRegio
                     .objects
                     .select_related('rayon')
                     .get(pk=regio_pk))
        except (ValueError, NhbRegio.DoesNotExist):
            raise Resolver404()

        context['regio'] = regio

        try:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(is_afgesloten=False,
                             laag=LAAG_REGIO,
                             competitie=comp,
                             nhb_regio=regio))
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
                                'schutterboog__boogtype',
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
        self._maak_data_dagdeel_behoefte(context, deelcomp, objs, regio)
        self._maak_data_blazoen_behoefte(context, deelcomp, objs)

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

        try:
            comp_pk = int(kwargs['comp_pk'][:6])        # afkappen voor veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Resolver404()

        comp.zet_fase()
        if comp.fase < 'B' or comp.fase > 'E':
            raise Resolver404()

        context['competitie'] = comp

        try:
            regio_pk = int(kwargs['regio_pk'][:6])      # afkappen voor veiligheid
            regio = (NhbRegio
                     .objects
                     .select_related('rayon')
                     .get(pk=regio_pk))
        except (ValueError, NhbRegio.DoesNotExist):
            raise Resolver404()

        try:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(is_afgesloten=False,
                             laag=LAAG_REGIO,
                             competitie=comp,
                             nhb_regio=regio))
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
        self._maak_data_dagdeel_behoefte(context, deelcomp, objs, regio)
        self._maak_data_blazoen_behoefte(context, deelcomp, objs)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="behoefte-%s.csv"' % regio.regio_nr

        writer = csv.writer(response)

        # voorkeur dagdelen per vereniging
        writer.writerow(['ver_nr', 'Naam'] + context['dagdelen'] + ['Totaal'])

        for nhb_ver in context['regio_verenigingen']:
            writer.writerow([nhb_ver.nhb_nr, nhb_ver.naam] + nhb_ver.counts_list)
        # for

        writer.writerow(['-', 'Totalen'] + context['totalen'])

        # blazoen behoefte
        writer.writerow(['-', '-'] + ['-' for _ in context['totalen']])
        writer.writerow(['-', 'Blazoen type'] + context['dagdelen'] + ['Totaal'])

        for behoefte in context['blazoen_count']:
            writer.writerow(behoefte)
        # for

        return response

# end of file
