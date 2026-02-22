# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404, HttpResponseRedirect
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from Account.models import get_account
from Competitie.definities import (DEEL_RK, DEEL_BK,
                                   DEELNAME_NEE,
                                   KAMP_RANK_RESERVE, KAMP_RANK_NO_SHOW, KAMP_RANK_BLANCO)
from Competitie.models import (Competitie, CompetitieMatch,
                               KampioenschapIndivKlasseLimiet, KampioenschapTeamKlasseLimiet,
                               Kampioenschap, KampioenschapSporterBoog, KampioenschapTeam)
from Competitie.seizoenen import get_comp_pk
from Functie.rol import rol_get_huidige_functie
from HistComp.operations import get_hist_url
from Overig.helpers import make_valid_hashtag
from Sporter.models import Sporter
from types import SimpleNamespace
import datetime

TEMPLATE_COMPUITSLAGEN_BK_INDIV = 'compuitslagen/bk-indiv.dtl'


class UitslagenBKIndivView(TemplateView):

    """ Django class-based view voor de de uitslagen van de bondskampioenschappen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_BK_INDIV

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comp = None

    def dispatch(self, request, *args, **kwargs):
        """ converteer het seizoen naar een competitie
            stuur oude seizoenen door naar histcomp """
        try:
            comp_pk = get_comp_pk(kwargs['comp_pk_of_seizoen'])
            self.comp = (Competitie
                         .objects
                         .prefetch_related('boogtypen')
                         .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            url_hist = get_hist_url(kwargs['comp_pk_of_seizoen'], 'indiv', 'bk', kwargs['comp_boog'][:2])
            if url_hist:
                return HttpResponseRedirect(url_hist)
        else:
            self.comp.bepaal_fase()

        return super().dispatch(request, *args, **kwargs)

    def _maak_filter_knoppen(self, context, comp_boog):
        """ filter knoppen per rayon en per competitie boog type """

        # boogtype filters
        boogtypen = self.comp.boogtypen.order_by('volgorde')

        context['comp_boog'] = None
        context['boog_filters'] = boogtypen

        for boogtype in boogtypen:
            boogtype.sel = boogtype.afkorting.lower()

            if boogtype.afkorting.upper() == comp_boog.upper():
                boogtype.selected = True
                context['comp_boog'] = boogtype
                comp_boog = boogtype.afkorting.lower()

            boogtype.zoom_url = reverse('CompUitslagen:uitslagen-bk-indiv',
                                        kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url(),
                                                'comp_boog': boogtype.afkorting.lower()})
        # for

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if not self.comp:
            raise Http404('Competitie niet gevonden')

        context['comp'] = self.comp

        comp_boog = kwargs['comp_boog'][:2]          # afkappen voor de veiligheid
        self._maak_filter_knoppen(context, comp_boog)

        boogtype = context['comp_boog']
        if not boogtype:
            raise Http404('Boogtype niet bekend')

        try:
            deelkamp_bk = (Kampioenschap
                           .objects
                           .select_related('competitie')
                           .get(deel=DEEL_BK,
                                competitie__is_afgesloten=False,
                                competitie=self.comp))
        except Kampioenschap.DoesNotExist:
            raise Http404('Kampioenschap niet gevonden')

        context['deelkamp_bk'] = deelkamp_bk

        if self.comp.fase_indiv == 'O':
            context['bevestig_tot_datum'] = self.comp.begin_fase_P_indiv - datetime.timedelta(days=14)

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

        if self.comp.is_indoor():
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
                                    'result_volgorde',               # zet niet meegedaan (99) onderaan
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
                    deelnemer.klasse_hashtag = make_valid_hashtag(deelnemer.klasse_str)
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

                deelnemer.geen_deelname_risico = sporter.bij_vereniging != deelnemer.bij_vereniging

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

                    else:
                        deelnemer.scores_str_1 = "%s (%s+%s)" % (deelnemer.result_score_1 + deelnemer.result_score_2,
                                                                 deelnemer.result_score_1,
                                                                 deelnemer.result_score_2)
                        deelnemer.scores_str_2 = deelnemer.result_counts        # 25m1pijl only

                curr_teller.aantal_regels += 1
            # for

            context['deelnemers'] = deelnemers
            context['heeft_deelnemers'] = (len(deelnemers) > 0)

        context['canonical'] = reverse('CompUitslagen:uitslagen-bk-indiv',      # TODO: keep?
                                       kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url(),
                                               'comp_boog': comp_boog})

        context['robots'] = 'nofollow'   # prevent crawling filter result pages

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('Competitie:overzicht', kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url()}),
                self.comp.beschrijving.replace(' competitie', '')),
            (None, 'BK individueel')
        )

        return context


# end of file
