# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.views.generic import TemplateView
from Competitie.definities import DEEL_BK, DEELNAME_NEE, KAMP_RANK_RESERVE, KAMP_RANK_NO_SHOW, KAMP_RANK_UNKNOWN
from Competitie.models import (Competitie, CompetitieMatch,
                               Kampioenschap, KampioenschapSporterBoog, KampioenschapIndivKlasseLimiet)
from Plein.menu import menu_dynamics
import datetime

TEMPLATE_COMPUITSLAGEN_BK_INDIV = 'compuitslagen/uitslagen-bk-indiv.dtl'
TEMPLATE_COMPUITSLAGEN_BK_TEAMS = 'compuitslagen/uitslagen-bk-teams.dtl'


class UitslagenBKIndivView(TemplateView):

    """ Django class-based view voor de de uitslagen van de bondskampioenschappen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_BK_INDIV

    @staticmethod
    def _maak_filter_knoppen(context, comp, comp_boog):
        """ filter knoppen per rayon en per competitie boog type """

        # boogtype filters
        boogtypen = comp.boogtypen.order_by('volgorde')

        context['comp_boog'] = None
        context['boog_filters'] = boogtypen

        for boogtype in boogtypen:
            boogtype.sel = boogtype.afkorting.lower()

            if boogtype.afkorting.upper() == comp_boog.upper():
                boogtype.selected = True
                context['comp_boog'] = boogtype
                comp_boog = boogtype.afkorting.lower()

            boogtype.zoom_url = reverse('CompUitslagen:uitslagen-bk-indiv',
                                        kwargs={'comp_pk': comp.pk,
                                                'comp_boog': boogtype.afkorting.lower()})
        # for

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        context['comp'] = comp

        comp_boog = kwargs['comp_boog'][:2]          # afkappen voor de veiligheid
        self._maak_filter_knoppen(context, comp, comp_boog)

        boogtype = context['comp_boog']
        if not boogtype:
            raise Http404('Boogtype niet bekend')

        try:
            deelkamp_bk = (Kampioenschap
                           .objects
                           .select_related('competitie')
                           .get(deel=DEEL_BK,
                                competitie__is_afgesloten=False,
                                competitie__pk=comp_pk))
        except Kampioenschap.DoesNotExist:
            raise Http404('Kampioenschap niet gevonden')

        if comp.fase_indiv == 'O':
            context['bevestig_tot_datum'] = comp.begin_fase_P_indiv - datetime.timedelta(days=14)

        # haal de planning erbij: competitie klasse --> competitie match
        indiv2match = dict()    # [indiv_pk] = CompetitieMatch
        match_pks = list(deelkamp_bk.rk_bk_matches.values_list('pk', flat=True))
        for match in (CompetitieMatch
                      .objects
                      .prefetch_related('indiv_klassen')
                      .select_related('locatie')
                      .filter(pk__in=match_pks)):

            if match.locatie:
                match.adres_str = ", ".join(match.locatie.adres.split('\n'))

            for indiv in match.indiv_klassen.all():
                indiv2match[indiv.pk] = match
            # for
        # for

        wkl2limiet = dict()    # [pk] = aantal

        if comp.afstand == '18':
            aantal_pijlen = 2 * 30
        else:
            aantal_pijlen = 2 * 25

        if deelkamp_bk.heeft_deelnemerslijst:
            # deelnemers/reserveschutters van het BK tonen
            deelnemers = (KampioenschapSporterBoog
                          .objects
                          .exclude(bij_vereniging__isnull=True)      # attentie gevallen
                          .exclude(deelname=DEELNAME_NEE)            # geen sporters die zich afgemeld hebben
                          .filter(kampioenschap=deelkamp_bk,
                                  indiv_klasse__boogtype=boogtype,
                                  rank__lte=48)                      # toon tot 48 sporters per klasse
                          .select_related('indiv_klasse',
                                          'sporterboog__sporter',
                                          'sporterboog__sporter__bij_vereniging',
                                          'bij_vereniging')
                          .order_by('indiv_klasse__volgorde',
                                    'result_volgorde',               # is constant zolang er geen resultaat is
                                    'volgorde'))                     # inschrijf ranking

            for limiet in (KampioenschapIndivKlasseLimiet
                           .objects
                           .select_related('indiv_klasse')
                           .filter(kampioenschap=deelkamp_bk)):
                wkl2limiet[limiet.indiv_klasse.pk] = limiet.limiet
            # for

            # bepaal in welke klassen we de uitslag gaan tonen
            klasse2toon_uitslag = dict()        # [klasse volgorde] = True/False
            for deelnemer in deelnemers:
                if deelnemer.result_rank > 0:
                    klasse = deelnemer.indiv_klasse.volgorde
                    klasse2toon_uitslag[klasse] = True
            # for

            klasse = -1
            limiet = 24
            curr_teller = None
            for deelnemer in deelnemers:
                deelnemer.break_klasse = (klasse != deelnemer.indiv_klasse.volgorde)
                if deelnemer.break_klasse:
                    if klasse == -1:
                        deelnemer.is_eerste_break = True
                    indiv = deelnemer.indiv_klasse
                    deelnemer.klasse_str = indiv.beschrijving
                    try:
                        deelnemer.match = indiv2match[indiv.pk]
                    except KeyError:
                        pass

                    try:
                        limiet = wkl2limiet[deelnemer.indiv_klasse.pk]
                    except KeyError:
                        limiet = 24

                    curr_teller = deelnemer
                    curr_teller.aantal_regels = 2

                klasse = deelnemer.indiv_klasse.volgorde
                try:
                    toon_uitslag = klasse2toon_uitslag[klasse]
                except KeyError:
                    toon_uitslag = False
                deelnemer.toon_uitslag = toon_uitslag

                sporter = deelnemer.sporterboog.sporter
                deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())
                deelnemer.ver_str = str(deelnemer.bij_vereniging)

                deelnemer.geen_deelname_risico = deelnemer.sporterboog.sporter.bij_vereniging != deelnemer.bij_vereniging

                deelnemer.rk_score = round(deelnemer.gemiddelde * aantal_pijlen)

                if deelnemer.rank > limiet:
                    deelnemer.is_reserve = True

                if toon_uitslag:
                    # TODO: ondersteuning Indoor
                    if deelnemer.result_rank in (0, KAMP_RANK_RESERVE, KAMP_RANK_NO_SHOW):
                        deelnemer.geen_deelname = True
                        deelnemer.geen_rank = True
                        deelnemer.scores_str_1 = "-"
                        deelnemer.scores_str_2 = ""

                    elif deelnemer.result_rank < 100:
                        deelnemer.scores_str_1 = "%s (%s+%s)" % (deelnemer.result_score_1 + deelnemer.result_score_2,
                                                                 deelnemer.result_score_1,
                                                                 deelnemer.result_score_2)
                        deelnemer.scores_str_2 = deelnemer.result_counts        # 25m1pijl only
                        deelnemer.geen_rank = (deelnemer.result_rank == KAMP_RANK_UNKNOWN)

                curr_teller.aantal_regels += 1
            # for

            context['deelnemers'] = deelnemers
            context['heeft_deelnemers'] = (len(deelnemers) > 0)

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Uitslagen BK individueel')
        )

        menu_dynamics(self.request, context)
        return context


class UitslagenBKTeamsView(TemplateView):

    """ Django class-based view voor de de uitslagen van de bondskampioenschappen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_BK_TEAMS

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        context['comp'] = comp

        team_type = kwargs['team_type'][:3]           # afkappen voor de veiligheid

        try:
            deelkamp = (Kampioenschap
                        .objects
                        .select_related('competitie')
                        .get(deel=DEEL_BK,
                             competitie__is_afgesloten=False,
                             competitie__pk=comp_pk))
        except Kampioenschap.DoesNotExist:
            raise Http404('Kampioenschap niet gevonden')

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Uitslagen BK teams')
        )

        menu_dynamics(self.request, context)
        return context


# end of file
