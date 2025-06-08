# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponse, Http404
from django.utils.formats import date_format
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.definities import (COMPETITIE_BLAZOENEN, BLAZOEN_DT, BLAZOEN_60CM_4SPOT,
                                   BLAZOEN_WENS_4SPOT, BLAZOEN_WENS_DT,
                                   BLAZOEN2STR, BLAZOEN2STR_COMPACT)
from Competitie.definities import (DAGDELEN, DAGDEEL_AFKORTINGEN, DAGDEEL2LABEL,
                                   INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_3)
from Competitie.models import (Competitie, CompetitieMatch,
                               Regiocompetitie, RegiocompetitieRonde, RegiocompetitieSporterBoog)
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Geo.models import Rayon, Regio
from Sporter.models import SporterVoorkeuren
from Vereniging.models import Vereniging
from codecs import BOM_UTF8
import textwrap
import csv


TEMPLATE_COMPETITIE_AANGEMELD_REGIO = 'compinschrijven/lijst-aangemeld-regio.dtl'
TEMPLATE_COMPETITIE_INSCHRIJFMETHODE1_BEHOEFTE = 'compinschrijven/inschrijfmethode1-behoefte.dtl'
TEMPLATE_COMPETITIE_INSCHRIJFMETHODE3_BEHOEFTE = 'compinschrijven/inschrijfmethode3-behoefte.dtl'

CONTENT_TYPE_CSV = 'text/csv; charset=UTF-8'

JA_NEE = {
    False: 'Nee',
    True: 'Ja'
}


def maak_regiocomp_zoom_knoppen(context, comp_pk, rayon=None, regio=None):

    """ Maak de zoom knoppen structuur voor de regiocompetitie deelnemers lijst """

    if rayon != regio:
        context['zoom_alles_url'] = reverse('CompInschrijven:lijst-regiocomp-alles', kwargs={'comp_pk': comp_pk})

    regios = (Regio
              .objects
              .select_related('rayon')
              .filter(is_administratief=False)
              .order_by('regio_nr'))

    rayons = Rayon.objects.all()

    context['zoom_rayons'] = list()
    for obj in rayons:
        context['zoom_rayons'].append(obj)

        obj.title_str = 'Rayon %s' % obj.rayon_nr
        if obj != rayon:
            obj.zoom_url = reverse('CompInschrijven:lijst-regiocomp-rayon',
                                   kwargs={'comp_pk': comp_pk, 'rayon_pk': obj.pk})

        obj.regios = list()
        for obj2 in regios:
            if obj2.rayon == obj:
                obj.regios.append(obj2)
                obj2.title_str = 'Regio %s' % obj2.regio_nr
                if obj2 != regio:
                    obj2.zoom_url = reverse('CompInschrijven:lijst-regiocomp-regio',
                                            kwargs={'comp_pk': comp_pk, 'regio_pk': obj2.pk})
    # for


def formatteer_objs(objs):

    lid2voorkeuren = dict()  # [lid_nr] = SporterVoorkeuren
    for voorkeuren in SporterVoorkeuren.objects.select_related('sporter').all():
        lid2voorkeuren[voorkeuren.sporter.lid_nr] = voorkeuren
    # for

    obj_aantal = None
    aantal = 0
    volgorde = -1
    for obj in objs:
        if volgorde != obj.indiv_klasse.volgorde:
            obj.nieuwe_klasse = True
            if obj_aantal:
                obj_aantal.aantal_in_klasse = aantal
                obj_aantal.aantal_regels = aantal + 2
            aantal = 0
            obj_aantal = obj
            volgorde = obj.indiv_klasse.volgorde

        obj.notities = obj.inschrijf_notitie

        try:
            voorkeuren = lid2voorkeuren[obj.sporterboog.sporter.lid_nr]
        except KeyError:
            obj.voorkeuren = SporterVoorkeuren()        # defaults
        else:
            obj.voorkeuren = voorkeuren

            if voorkeuren.para_voorwerpen:
                obj.notities += '\nSporter laat voorwerpen op de schietlijn staan\n'

            if voorkeuren.opmerking_para_sporter:
                obj.notities = obj.notities + '\n' + voorkeuren.opmerking_para_sporter

        obj.notities = obj.notities.replace('\n\n', '\n')
        obj.notities = textwrap.fill(obj.notities, 30)

        aantal += 1
    # for

    if obj_aantal:
        obj_aantal.aantal_in_klasse = aantal
        obj_aantal.aantal_regels = aantal + 2


class LijstAangemeldRegiocompAllesView(UserPassesTestMixin, TemplateView):

    """ Toon een lijst van SporterBoog die aangemeld zijn voor de regiocompetitie """

    template_name = TEMPLATE_COMPETITIE_AANGEMELD_REGIO
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rol.ROL_BB, Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])        # afkappen voor de veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        if not comp.is_open_voor_inschrijven():
            raise Http404('Verkeerde competitie fase')

        context['competitie'] = comp

        objs = (RegiocompetitieSporterBoog
                .objects
                .select_related('indiv_klasse',
                                'regiocompetitie',
                                'regiocompetitie__regio',
                                'sporterboog',
                                'sporterboog__sporter',
                                'bij_vereniging')
                .filter(regiocompetitie__competitie=comp)
                .order_by('indiv_klasse__volgorde',
                          '-ag_voor_indiv'))

        formatteer_objs(objs)

        context['object_list'] = objs

        context['inhoud'] = 'landelijk'
        maak_regiocomp_zoom_knoppen(context, comp_pk)

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Inschrijvingen')
        )

        return context


class LijstAangemeldRegiocompRayonView(UserPassesTestMixin, TemplateView):

    """ Toon een lijst van SporterBoog die aangemeld zijn voor de regiocompetitie """

    template_name = TEMPLATE_COMPETITIE_AANGEMELD_REGIO
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rol.ROL_BB, Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])    # afkappen voor de veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        if not comp.is_open_voor_inschrijven():
            raise Http404('Verkeerde competitie fase')

        context['competitie'] = comp

        try:
            rayon_pk = int(kwargs['rayon_pk'][:6])  # afkappen voor de veiligheid
            rayon = Rayon.objects.get(pk=rayon_pk)
        except (ValueError, Rayon.DoesNotExist):
            raise Http404('Rayon niet gevonden')

        context['inhoud'] = 'in ' + str(rayon)

        objs = (RegiocompetitieSporterBoog
                .objects
                .select_related('indiv_klasse',
                                'regiocompetitie',
                                'regiocompetitie__regio',
                                'sporterboog',
                                'sporterboog__sporter',
                                'bij_vereniging')
                .filter(regiocompetitie__competitie=comp,
                        regiocompetitie__regio__rayon_nr=rayon.rayon_nr)
                .order_by('indiv_klasse__volgorde',
                          '-ag_voor_indiv'))

        formatteer_objs(objs)

        context['object_list'] = objs

        maak_regiocomp_zoom_knoppen(context, comp_pk, rayon=rayon)

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Inschrijvingen')
        )

        return context


class LijstAangemeldRegiocompRegioView(UserPassesTestMixin, TemplateView):

    """ Toon een lijst van SporterBoog die aangemeld zijn voor de regiocompetitie """

    template_name = TEMPLATE_COMPETITIE_AANGEMELD_REGIO
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rol.ROL_BB, Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])        # afkappen voor de veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        if not comp.is_open_voor_inschrijven():
            raise Http404('Verkeerde competitie fase')

        context['competitie'] = comp

        try:
            regio_pk = int(kwargs['regio_pk'][:6])      # afkappen voor de veiligheid
            regio = (Regio
                     .objects
                     .select_related('rayon')
                     .get(pk=regio_pk))
        except (ValueError, Regio.DoesNotExist):
            raise Http404('Regio niet gevonden')

        context['regio'] = regio
        context['inhoud'] = 'in ' + str(regio)

        try:
            deelcomp = Regiocompetitie.objects.get(competitie=comp,
                                                   regio=regio)
        except Regiocompetitie.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        context['deelcomp'] = deelcomp

        objs = (RegiocompetitieSporterBoog
                .objects
                .select_related('indiv_klasse',
                                'regiocompetitie',
                                'sporterboog',
                                'sporterboog__sporter',
                                'sporterboog__boogtype',
                                'bij_vereniging')
                .filter(regiocompetitie=deelcomp)
                .order_by('indiv_klasse__volgorde',
                          '-ag_voor_indiv'))

        formatteer_objs(objs)

        context['object_list'] = objs

        if deelcomp.inschrijf_methode == INSCHRIJF_METHODE_1:
            context['show_gekozen_wedstrijden'] = True
            context['url_behoefte'] = reverse('CompInschrijven:inschrijfmethode1-behoefte',
                                              kwargs={'comp_pk': comp.pk,
                                                      'regio_pk': regio.pk})

        elif deelcomp.inschrijf_methode == INSCHRIJF_METHODE_3:
            context['show_dagdeel_telling'] = True
            context['url_behoefte'] = reverse('CompInschrijven:inschrijfmethode3-behoefte',
                                              kwargs={'comp_pk': comp.pk,
                                                      'regio_pk': regio.pk})

        context['url_download'] = reverse('CompInschrijven:lijst-regiocomp-regio-als-bestand',
                                          kwargs={'comp_pk': comp.pk,
                                                  'regio_pk': regio.pk})

        maak_regiocomp_zoom_knoppen(context, comp.pk, regio=regio)

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Inschrijvingen')
        )

        return context


class LijstAangemeldRegiocompAlsBestandView(LijstAangemeldRegiocompRegioView):

    """ Deze klasse wordt gebruikt om de lijst van aangemelde sporters in een regio
        te downloaden als csv bestand, inclusief voorkeur voor dagdelen (inschrijfmethode 3)
    """

    def get(self, request, *args, **kwargs):

        context = self.get_context_data(**kwargs)

        regio = context['regio']

        response = HttpResponse(content_type=CONTENT_TYPE_CSV)
        response['Content-Disposition'] = 'attachment; filename="aanmeldingen-regio-%s.csv"' % regio.regio_nr

        response.write(BOM_UTF8)
        writer = csv.writer(response, delimiter=";")  # ; is good for import with dutch regional settings

        heeft_dagdeel = context['deelcomp'].inschrijf_methode == INSCHRIJF_METHODE_3

        headers = ['Ver nr', 'Vereniging',
                   'Lid nr', 'Naam',
                   'Boog', 'Voorkeur team', 'Voorkeur eigen blazoen']
        if heeft_dagdeel:
            headers.append('Voorkeur dagdeel')
        headers.extend(['Inschrijf notitie', 'Voorwerpen op lijn', 'Para notitie',
                        'Wedstrijdklasse'])

        writer.writerow(headers)

        for deelnemer in context['object_list']:

            sporterboog = deelnemer.sporterboog
            voorkeuren = deelnemer.voorkeuren

            ver = deelnemer.bij_vereniging
            sporter = sporterboog.sporter
            boog = sporterboog.boogtype
            klasse = deelnemer.indiv_klasse
            team_str = 'Ja' if deelnemer.inschrijf_voorkeur_team else 'Nee'
            eigen_str = 'Ja' if voorkeuren.voorkeur_eigen_blazoen else 'Nee'
            para_voorwerpen = 'Ja' if voorkeuren.para_voorwerpen else 'Nee'

            if heeft_dagdeel:
                dagdeel_str = DAGDEEL2LABEL[deelnemer.inschrijf_voorkeur_dagdeel][1]  # lange beschrijving
                tup = (ver.ver_nr, ver.naam,
                       sporter.lid_nr, sporter.volledige_naam(),
                       boog.beschrijving, team_str, eigen_str, dagdeel_str,
                       deelnemer.inschrijf_notitie, para_voorwerpen, voorkeuren.opmerking_para_sporter,
                       klasse.beschrijving)
            else:
                tup = (ver.ver_nr, ver.naam,
                       sporter.lid_nr, sporter.volledige_naam(),
                       boog.beschrijving, team_str, eigen_str,
                       deelnemer.inschrijf_notitie, para_voorwerpen, voorkeuren.opmerking_para_sporter,
                       klasse.beschrijving)

            writer.writerow(tup)
        # for

        return response


class Inschrijfmethode3BehoefteView(UserPassesTestMixin, TemplateView):

    """ Toon de RCL de behoefte aan quotaplaatsen in een regio met inschrijfmethode 3 """

    template_name = TEMPLATE_COMPETITIE_INSCHRIJFMETHODE3_BEHOEFTE
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_RCL

    @staticmethod
    def _maak_data_dagdeel_behoefte(context, deelcomp, deelnemers, regio):
        """ voegt de volgende elementen toe aan de context:
                regio_verenigingen: lijst van Vereniging met counts_list met telling van dagdelen
                dagdelen: beschrijving van dagdelen voor de kolom headers
        """

        alles_mag = (deelcomp.toegestane_dagdelen == '')
        dagdelen_spl = deelcomp.toegestane_dagdelen.split(',')

        context['dagdelen'] = dagdelen = list()
        for afkorting, beschrijving in DAGDELEN:
            if alles_mag or (afkorting in dagdelen_spl):
                dagdelen.append(afkorting)
        # for

        # maak een lijst van alle verenigingen in deze regio
        context['regio_verenigingen'] = vers = list()
        nr2ver = dict()
        for ver in (Vereniging
                    .objects
                    .filter(regio=regio)
                    .order_by('ver_nr')):

            vers.append(ver)
            nr2ver[ver.ver_nr] = ver

            ver.blazoen_dict = dict()
        # for

        # sporter met voorkeur voor eigen blazoen (DT of 60cm 4spot)
        voorkeur_eigen_blazoen = (SporterVoorkeuren
                                  .objects
                                  .select_related('sporter')
                                  .filter(voorkeur_eigen_blazoen=True)
                                  .values_list('sporter__lid_nr', flat=True))

        alle_blazoenen = list()

        for deelnemer in deelnemers:
            # bepaal welk blazoen deze sporter nodig heeft
            klasse = deelnemer.indiv_klasse
            blazoenen = (klasse.blazoen1_regio, klasse.blazoen2_regio)

            if klasse.blazoen1_regio == klasse.blazoen2_regio:
                blazoen_str = BLAZOEN2STR[klasse.blazoen1_regio]
            else:
                # meerder mogelijkheden
                blazoen_str = BLAZOEN2STR[klasse.blazoen1_regio]     # ga uit van eerste optie bij geen voorkeur
                # blazoen_str = "%s of %s" % (BLAZOEN2STR[klasse.blazoen1_regio], BLAZOEN2STR[klasse.blazoen2_regio])
                if BLAZOEN_DT in blazoenen:
                    if deelnemer.sporterboog.sporter.lid_nr in voorkeur_eigen_blazoen:
                        blazoen_str = BLAZOEN2STR[BLAZOEN_WENS_DT]
                elif BLAZOEN_60CM_4SPOT in blazoenen:
                    if deelnemer.sporterboog.sporter.lid_nr in voorkeur_eigen_blazoen:
                        blazoen_str = BLAZOEN2STR[BLAZOEN_WENS_4SPOT]

            try:
                ver = nr2ver[deelnemer.bij_vereniging.ver_nr]
            except KeyError:
                pass
            else:
                try:
                    counts_dict = ver.blazoen_dict[blazoen_str]
                except KeyError:
                    counts_dict = dict()
                    for afkorting in DAGDEEL_AFKORTINGEN:
                        counts_dict[afkorting] = 0
                    # for
                    ver.blazoen_dict[blazoen_str] = counts_dict
                    if blazoen_str not in alle_blazoenen:
                        alle_blazoenen.append(blazoen_str)

                afkorting = deelnemer.inschrijf_voorkeur_dagdeel
                try:
                    counts_dict[afkorting] += 1
                except KeyError:
                    pass
        # for

        alle_blazoenen.sort()

        # convert dicts to lists en tel totalen
        totals = dict()
        for afkorting in DAGDEEL_AFKORTINGEN:
            totals[afkorting] = 0
        # for

        for ver in vers:
            ver.blazoen_list = list()

            for blazoen_str in alle_blazoenen:
                try:
                    counts_dict = ver.blazoen_dict[blazoen_str]
                except KeyError:
                    # blazoen niet nodig voor deze vereniging
                    pass
                else:
                    counts_list = list()

                    som = 0
                    for afkorting in DAGDEEL_AFKORTINGEN:
                        if alles_mag or (afkorting in dagdelen_spl):
                            count = counts_dict[afkorting]
                            counts_list.append(count)
                            totals[afkorting] += count
                            som += count
                    # for
                    counts_list.append(som)

                    if som > 0:
                        tup = (blazoen_str, counts_list)
                        ver.blazoen_list.append(tup)
            # for
        # for

        context['totalen'] = totalen = list()
        som = 0
        for afkorting in DAGDEEL_AFKORTINGEN:
            if alles_mag or (afkorting in dagdelen_spl):
                count = totals[afkorting]
                totalen.append(count)
                som += count
        # for
        totalen.append(som)

    @staticmethod
    def _maak_data_blazoen_behoefte(context):
        """ maak het overzicht hoeveel blazoenen er nodig zijn voor elk dagdeel """

        alle_blazoenen = list()
        blazoen_count = dict()
        for ver in context['regio_verenigingen']:
            for blazoen_str, counts_list in ver.blazoen_list:
                try:
                    counts = blazoen_count[blazoen_str]
                except KeyError:
                    counts = [0] * len(counts_list)
                    blazoen_count[blazoen_str] = counts
                    if blazoen_str not in alle_blazoenen:
                        alle_blazoenen.append(blazoen_str)

                for nr in range(len(counts_list)):
                    counts[nr] += counts_list[nr]
                # for
            # for
        # for

        alle_blazoenen.sort()

        # converteer naar lijstjes met vaste volgorde van de dagdelen
        context['blazoen_count'] = blazoen_behoefte = list()
        for blazoen_str in alle_blazoenen:
            counts = blazoen_count[blazoen_str]
            tup = (blazoen_str, counts)
            blazoen_behoefte.append(tup)
        # for

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])        # afkappen voor de veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        if not comp.is_open_voor_inschrijven():
            raise Http404('Verkeerde competitie fase')

        context['competitie'] = comp

        try:
            regio_pk = int(kwargs['regio_pk'][:6])      # afkappen voor de veiligheid
            regio = (Regio
                     .objects
                     .select_related('rayon')
                     .get(pk=regio_pk))
        except (ValueError, Regio.DoesNotExist):
            raise Http404('Regio niet gevonden')

        context['regio'] = regio

        try:
            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie')
                        .get(is_afgesloten=False,
                             competitie=comp,
                             regio=regio))
        except Regiocompetitie.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        if deelcomp.inschrijf_methode != INSCHRIJF_METHODE_3:
            raise Http404('Verkeerde inschrijfmethode')

        deelnemers = (RegiocompetitieSporterBoog
                      .objects
                      .select_related('indiv_klasse',
                                      'regiocompetitie',
                                      'bij_vereniging',
                                      'sporterboog',
                                      'sporterboog__boogtype',
                                      'sporterboog__sporter',
                                      'sporterboog__sporter__bij_vereniging')
                      .filter(regiocompetitie=deelcomp)
                      .order_by('indiv_klasse__volgorde',
                                'ag_voor_indiv'))

        # voeg de tabel met dagdeel-behoefte toe
        self._maak_data_dagdeel_behoefte(context, deelcomp, deelnemers, regio)
        self._maak_data_blazoen_behoefte(context)

        context['url_download'] = reverse('CompInschrijven:inschrijfmethode3-behoefte-als-bestand',
                                          kwargs={'comp_pk': comp.pk,
                                                  'regio_pk': regio.pk})

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (reverse('CompInschrijven:lijst-regiocomp-regio',
                     kwargs={'comp_pk': comp.pk,
                             'regio_pk': deelcomp.regio.regio_nr}), 'Inschrijvingen'),
            (None, 'Benodigde dagdelen')
        )

        return context


class Inschrijfmethode3BehoefteAlsBestandView(Inschrijfmethode3BehoefteView):

    """ Deze klasse wordt gebruikt om de lijst van aangemelde sporters in een regio
        te downloaden als csv bestand, inclusief voorkeur voor dagdelen (inschrijfmethode 3)
    """

    def get(self, request, *args, **kwargs):

        context = dict()

        try:
            comp_pk = int(kwargs['comp_pk'][:6])        # afkappen voor de veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        if not comp.is_open_voor_inschrijven():
            raise Http404('Verkeerde competitie fase')

        context['competitie'] = comp

        try:
            regio_pk = int(kwargs['regio_pk'][:6])      # afkappen voor de veiligheid
            regio = (Regio
                     .objects
                     .select_related('rayon')
                     .get(pk=regio_pk))
        except (ValueError, Regio.DoesNotExist):
            raise Http404('Regio niet gevonden')

        try:
            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie')
                        .get(is_afgesloten=False,
                             competitie=comp,
                             regio=regio))
        except Regiocompetitie.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        if deelcomp.inschrijf_methode != INSCHRIJF_METHODE_3:
            raise Http404('Verkeerde inschrijfmethode')

        objs = (RegiocompetitieSporterBoog
                .objects
                .select_related('indiv_klasse',
                                'regiocompetitie',
                                'bij_vereniging',
                                'sporterboog',
                                'sporterboog__sporter',
                                'sporterboog__sporter__bij_vereniging')
                .filter(regiocompetitie=deelcomp)
                .order_by('indiv_klasse__volgorde',
                          'ag_voor_indiv'))

        context['object_list'] = objs

        # voeg de tabel met dagdeel-behoefte toe
        # dict(ver) = dict("dagdeel_afkorting") = count
        # list[ver, ..] =
        self._maak_data_dagdeel_behoefte(context, deelcomp, objs, regio)
        self._maak_data_blazoen_behoefte(context)

        dagdelen = [DAGDEEL2LABEL[dagdeel][0] for dagdeel in context['dagdelen']]

        response = HttpResponse(content_type=CONTENT_TYPE_CSV)
        response['Content-Disposition'] = 'attachment; filename="behoefte-%s.csv"' % regio.regio_nr

        response.write(BOM_UTF8)
        writer = csv.writer(response, delimiter=";")      # ; is good for import with dutch regional settings

        # voorkeur dagdelen per vereniging
        writer.writerow(['ver_nr', 'Naam', 'Blazoen'] + dagdelen + ['Totaal'])

        for ver in context['regio_verenigingen']:
            for blazoen_str, counts_list in ver.blazoen_list:
                writer.writerow([ver.ver_nr, ver.naam, blazoen_str] + counts_list)
        # for

        writer.writerow(['-', '-', 'Totalen'] + context['totalen'])

        # blazoen behoefte
        writer.writerow(['-', '-', '-'] + ['-' for _ in context['totalen']])
        writer.writerow(['-', '-', 'Blazoen'] + dagdelen + ['Totaal'])

        for blazoen_str, behoefte in context['blazoen_count']:
            writer.writerow(['-', '-', blazoen_str] + behoefte)
        # for

        return response


class Inschrijfmethode1BehoefteView(UserPassesTestMixin, TemplateView):

    """ Toon de RCL de keuzes voor wedstrijden in een regio met inschrijfmethode 1 """

    template_name = TEMPLATE_COMPETITIE_INSCHRIJFMETHODE1_BEHOEFTE
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_RCL

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])        # afkappen voor de veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        if not comp.is_open_voor_inschrijven():
            raise Http404('Verkeerde competitie fase')

        context['competitie'] = comp

        try:
            regio_pk = int(kwargs['regio_pk'][:6])      # afkappen voor de veiligheid
            regio = (Regio
                     .objects
                     .select_related('rayon')
                     .get(pk=regio_pk))
        except (ValueError, Regio.DoesNotExist):
            raise Http404('Regio niet gevonden')

        context['regio'] = regio

        try:
            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie',
                                        'regio')
                        .get(is_afgesloten=False,
                             competitie=comp,
                             regio=regio))
        except Regiocompetitie.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        if deelcomp.inschrijf_methode != INSCHRIJF_METHODE_1:
            raise Http404('Verkeerde inschrijfmethode')

        afstand = deelcomp.competitie.afstand
        context['blazoenen'] = [BLAZOEN2STR_COMPACT[blazoen] for blazoen in COMPETITIE_BLAZOENEN[afstand]]

        # sporters met recurve boog willen mogelijk DT
        voorkeur_eigen_blazoen = (SporterVoorkeuren
                                  .objects
                                  .select_related('sporter')
                                  .filter(voorkeur_eigen_blazoen=True)
                                  .values_list('sporter__lid_nr', flat=True))

        match_pks = list()
        for ronde in (RegiocompetitieRonde
                      .objects
                      .filter(regiocompetitie=deelcomp)
                      .prefetch_related('matches')):
            match_pks.extend(ronde.matches.values_list('pk', flat=True))
        # for

        matches = (CompetitieMatch
                   .objects
                   .select_related('vereniging')
                   .prefetch_related('regiocompetitiesporterboog_set')
                   .filter(pk__in=match_pks)
                   .order_by('datum_wanneer',
                             'tijd_begin_wedstrijd',
                             'vereniging__ver_nr'))

        context['wedstrijden'] = matches

        for wedstrijd in matches:
            wedstrijd.beschrijving_str = "%s om %s" % (date_format(wedstrijd.datum_wanneer, "l j E Y"),
                                                       wedstrijd.tijd_begin_wedstrijd.strftime("%H:%M"))
            wedstrijd.locatie_str = str(wedstrijd.vereniging)
            wedstrijd.keuze_count = wedstrijd.regiocompetitiesporterboog_set.count()

            deelnemer_pks = list(wedstrijd.regiocompetitiesporterboog_set.values_list('pk', flat=True))

            blazoenen_dict = dict()
            for blazoen in COMPETITIE_BLAZOENEN[afstand]:
                blazoenen_dict[blazoen] = 0
            # for

            for deelnemer in (RegiocompetitieSporterBoog
                              .objects
                              .select_related('sporterboog',
                                              'sporterboog__boogtype',
                                              'sporterboog__sporter',
                                              'indiv_klasse')
                              .filter(pk__in=deelnemer_pks)):

                klasse = deelnemer.indiv_klasse

                blazoen = klasse.blazoen1_regio
                if klasse.blazoen1_regio != klasse.blazoen2_regio:
                    # meerder mogelijkheden
                    if BLAZOEN_DT in blazoenen_dict:
                        if deelnemer.sporterboog.sporter.lid_nr in voorkeur_eigen_blazoen:
                            blazoen = BLAZOEN_WENS_DT

                blazoenen_dict[blazoen] += 1
            # for  deelnemer

            # convert dict to list
            wedstrijd.blazoen_count = [blazoenen_dict[blazoen] for blazoen in COMPETITIE_BLAZOENEN[afstand]]

        # for  wedstrijd

        context['url_download'] = reverse('CompInschrijven:inschrijfmethode1-behoefte-als-bestand',
                                          kwargs={'comp_pk': comp.pk,
                                                  'regio_pk': regio.pk})

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (reverse('CompInschrijven:lijst-regiocomp-regio',
                     kwargs={'comp_pk': comp.pk,
                             'regio_pk': deelcomp.regio.regio_nr}), 'Inschrijvingen'),
            (None, 'Gekozen wedstrijden')
        )

        return context


class Inschrijfmethode1BehoefteAlsBestandView(Inschrijfmethode1BehoefteView):

    """ Deze klasse wordt gebruikt om de lijst van aangemelde sporters in een regio
        te downloaden als csv bestand, inclusief gekozen wedstrijden (inschrijfmethode 1)
    """

    # access check wordt door base class gedaan

    def get(self, request, *args, **kwargs):

        context = dict()

        try:
            comp_pk = int(kwargs['comp_pk'][:6])        # afkappen voor de veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        if not comp.is_open_voor_inschrijven():
            raise Http404('Verkeerde competitie fase')

        context['competitie'] = comp

        try:
            regio_pk = int(kwargs['regio_pk'][:6])      # afkappen voor de veiligheid
            regio = (Regio
                     .objects
                     .select_related('rayon')
                     .get(pk=regio_pk))
        except (ValueError, Regio.DoesNotExist):
            raise Http404('Regio niet gevonden')

        try:
            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie')
                        .get(is_afgesloten=False,
                             competitie=comp,
                             regio=regio))
        except Regiocompetitie.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        if deelcomp.inschrijf_methode != INSCHRIJF_METHODE_1:
            raise Http404('Verkeerde inschrijfmethode')

        afstand = deelcomp.competitie.afstand

        # sporters met recurve boog willen mogelijk DT
        voorkeur_eigen_blazoen = (SporterVoorkeuren
                                  .objects
                                  .select_related('sporter')
                                  .filter(voorkeur_eigen_blazoen=True)
                                  .values_list('sporter__lid_nr', flat=True))

        response = HttpResponse(content_type=CONTENT_TYPE_CSV)
        response['Content-Disposition'] = 'attachment; filename="inschrijf-keuzes-%s.csv"' % regio.regio_nr

        response.write(BOM_UTF8)
        writer = csv.writer(response, delimiter=";")      # ; is good for dutch regional settings

        blazoen_headers = [BLAZOEN2STR_COMPACT[blazoen] for blazoen in COMPETITIE_BLAZOENEN[afstand]]

        # wedstrijden header
        writer.writerow(['Nummer', 'Wedstrijd', 'Locatie', 'Blazoenen:'] + blazoen_headers)

        match_pks = list()
        for ronde in (RegiocompetitieRonde
                      .objects
                      .filter(regiocompetitie=deelcomp)
                      .prefetch_related('matches')):
            match_pks.extend(ronde.matches.values_list('pk', flat=True))
        # for

        matches = (CompetitieMatch
                   .objects
                   .select_related('vereniging')
                   .filter(pk__in=match_pks)
                   .order_by('datum_wanneer',
                             'tijd_begin_wedstrijd',
                             'vereniging__ver_nr'))

        # maak een blok met genummerde wedstrijden
        # deze nummers komen verderop terug in de kruisjes met de sporters
        nr = 0
        kolom_pks = list()
        for wedstrijd in matches:
            kolom_pks.append(wedstrijd.pk)
            nr += 1
            beschrijving_str = "%s om %s" % (date_format(wedstrijd.datum_wanneer, "l j E Y"),
                                             wedstrijd.tijd_begin_wedstrijd.strftime("%H:%M"))

            deelnemer_pks = wedstrijd.regiocompetitiesporterboog_set.values_list('pk', flat=True)

            blazoenen_dict = dict()
            for blazoen in COMPETITIE_BLAZOENEN[afstand]:
                blazoenen_dict[blazoen] = 0
            # for

            for deelnemer in (RegiocompetitieSporterBoog
                              .objects
                              .select_related('sporterboog',
                                              'sporterboog__boogtype',
                                              'sporterboog__sporter',
                                              'indiv_klasse')
                              .filter(pk__in=deelnemer_pks)):

                klasse = deelnemer.indiv_klasse

                blazoen = klasse.blazoen1_regio
                if klasse.blazoen1_regio != klasse.blazoen2_regio:
                    # meerdere mogelijkheden
                    if BLAZOEN_DT in blazoenen_dict:
                        if deelnemer.sporterboog.sporter.lid_nr in voorkeur_eigen_blazoen:
                            blazoen = BLAZOEN_WENS_DT

                blazoenen_dict[blazoen] += 1
            # for  deelnemer

            # convert dict to list
            blazoen_count = [blazoenen_dict[blazoen] for blazoen in COMPETITIE_BLAZOENEN[afstand]]

            # wedstrijd nr + beschrijving + blazoenen telling --> csv
            writer.writerow([nr, beschrijving_str, wedstrijd.vereniging, ''] + blazoen_count)
        # for

        # sporters header
        writer.writerow([])
        nummers = [str(nummer) for nummer in range(1, nr + 1)]
        writer.writerow(['Bondsnummer', 'Sporter', 'Vereniging', 'Wedstrijdklasse (individueel)'] + nummers)

        for deelnemer in (RegiocompetitieSporterBoog
                          .objects
                          .prefetch_related('inschrijf_gekozen_matches')
                          .select_related('indiv_klasse',
                                          'bij_vereniging',
                                          'sporterboog',
                                          'sporterboog__sporter')
                          .filter(regiocompetitie=deelcomp)
                          .order_by('bij_vereniging__ver_nr',
                                    'sporterboog__sporter__lid_nr')):

            pks = list(deelnemer.inschrijf_gekozen_matches.values_list('pk', flat=True))  # TODO: 1 query per deelnemer!

            kruisjes = list()
            for pk in kolom_pks:
                if pk in pks:
                    kruisjes.append('X')
                else:
                    kruisjes.append('')
            # for

            sporter = deelnemer.sporterboog.sporter
            klasse = deelnemer.indiv_klasse.beschrijving

            writer.writerow([sporter.lid_nr, sporter.volledige_naam(), sporter.bij_vereniging, klasse] + kruisjes)
        # for

        return response


# end of file
