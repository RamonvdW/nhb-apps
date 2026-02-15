# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404, HttpResponseRedirect
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from Account.models import get_account
from Competitie.definities import DEEL_RK, DEELNAME_NEE, KAMP_RANK_RESERVE, KAMP_RANK_NO_SHOW, KAMP_RANK_BLANCO
from Competitie.models import (Competitie, CompetitieMatch, Regiocompetitie, RegiocompetitieSporterBoog,
                               Kampioenschap, KampioenschapSporterBoog, KampioenschapTeam,
                               KampioenschapIndivKlasseLimiet, KampioenschapTeamKlasseLimiet)
from Competitie.seizoenen import get_comp_pk
from Functie.rol import rol_get_huidige_functie
from Geo.models import Rayon
from HistComp.operations import get_hist_url
from Overig.helpers import make_valid_hashtag
from Sporter.models import Sporter
from Sporter.operations import get_request_rayon_nr
import datetime

TEMPLATE_COMPUITSLAGEN_RK_INDIV = 'compuitslagen/uitslagen-rk-indiv.dtl'
TEMPLATE_COMPUITSLAGEN_RK_TEAMS = 'compuitslagen/uitslagen-rk-teams.dtl'


class UitslagenRayonIndivView(TemplateView):

    """ Django class-based view voor de uitslagen van de rayonkampioenschappen individueel """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_RK_INDIV

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
            url_hist = get_hist_url(kwargs['comp_pk_of_seizoen'], 'indiv', 'rk', kwargs['comp_boog'][:2])
            if url_hist:
                return HttpResponseRedirect(url_hist)
        else:
            self.comp.bepaal_fase()

        return super().dispatch(request, *args, **kwargs)

    def _maak_filter_knoppen(self, context, gekozen_rayon_nr, comp_boog):
        """ filter knoppen per rayon en per competitie boog type """

        # boogtype filters
        boogtypen = self.comp.boogtypen.order_by('volgorde')

        context['comp_boog'] = None
        context['boog_filters'] = boogtypen

        for boogtype in boogtypen:
            boogtype.opt_text = boogtype.beschrijving
            boogtype.sel = boogtype.afkorting.lower()

            if boogtype.afkorting.upper() == comp_boog.upper():
                boogtype.selected = True
                context['comp_boog'] = boogtype
                comp_boog = boogtype.afkorting.lower()

            boogtype.url_part = boogtype.afkorting.lower()
        # for

        # rayon filters
        rayons = (Rayon
                  .objects
                  .order_by('rayon_nr')
                  .all())

        context['rayon_filters'] = rayons

        for rayon in rayons:
            rayon.opt_text = 'Rayon %s' % rayon.rayon_nr
            rayon.sel = 'rayon_%s' % rayon.pk
            rayon.url_part = str(rayon.rayon_nr)

            if rayon.rayon_nr == gekozen_rayon_nr:
                context['rayon'] = rayon
                rayon.selected = True
        # for

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if not self.comp:
            raise Http404('Competitie niet gevonden')

        context['comp'] = self.comp

        if self.comp.fase_indiv == 'J':
            context['bevestig_tot_datum'] = self.comp.begin_fase_L_indiv - datetime.timedelta(days=14)

        comp_boog = kwargs['comp_boog'][:2]          # afkappen voor de veiligheid

        # rayon_nr is optioneel (eerste binnenkomst zonder rayon nummer)
        try:
            rayon_nr = kwargs['rayon_nr'][:2]        # afkappen voor de veiligheid
            rayon_nr = int(rayon_nr)
        except KeyError:
            rayon_nr = get_request_rayon_nr(self.request)
        except ValueError:
            raise Http404('Verkeerd rayonnummer')

        self._maak_filter_knoppen(context, rayon_nr, comp_boog)

        context['url_filters'] = reverse('CompUitslagen:uitslagen-rk-indiv-n',
                                         kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url(),
                                                 'comp_boog': '~1',
                                                 'rayon_nr': '~2'})

        boogtype = context['comp_boog']
        if not boogtype:
            raise Http404('Boogtype niet bekend')

        try:
            deelkamp = (Kampioenschap
                        .objects
                        .select_related('competitie',
                                        'rayon')
                        .prefetch_related('rk_bk_matches')
                        .get(competitie=self.comp,
                             competitie__is_afgesloten=False,
                             deel=DEEL_RK,
                             rayon__rayon_nr=rayon_nr))
        except Kampioenschap.DoesNotExist:
            raise Http404('Kampioenschap niet gevonden')

        context['deelkamp'] = deelkamp

        # haal de planning erbij: competitie klasse --> competitie match
        indiv2match = dict()    # [indiv_pk] = CompetitieMatch
        match_pks = list(deelkamp.rk_bk_matches.values_list('pk', flat=True))
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
        is_lijst_rk = False

        if deelkamp.heeft_deelnemerslijst:
            # deelnemers/reserveschutters van het RK tonen
            deelnemers = (KampioenschapSporterBoog
                          .objects
                          .exclude(bij_vereniging__isnull=True)      # attentie gevallen
                          .exclude(deelname=DEELNAME_NEE)            # geen sporters die zich afgemeld hebben
                          .filter(kampioenschap=deelkamp,
                                  indiv_klasse__boogtype=boogtype,
                                  rank__lte=48)                      # toon tot 48 sporters per klasse
                          .select_related('indiv_klasse',
                                          'sporterboog__sporter',
                                          'sporterboog__sporter__bij_vereniging',
                                          'bij_vereniging')
                          .order_by('indiv_klasse__volgorde',
                                    'result_rank',                   # NO_SHOW is groot getal, dus onderaan de lijst
                                    'volgorde'))                     # inschrijf ranking

            for limiet in (KampioenschapIndivKlasseLimiet
                           .objects
                           .select_related('indiv_klasse')
                           .filter(kampioenschap=deelkamp)):
                wkl2limiet[limiet.indiv_klasse.pk] = limiet.limiet
            # for

            context['is_lijst_rk'] = is_lijst_rk = True
        else:
            # competitie is nog in de regiocompetitie fase
            context['regiocomp_nog_actief'] = True

            # sporters komen uit de 4 regio's van het rayon
            deelcomp_pks = (Regiocompetitie
                            .objects
                            .filter(competitie=self.comp,
                                    competitie__is_afgesloten=False,
                                    regio__rayon_nr=rayon_nr)
                            .values_list('pk', flat=True))

            deelnemers = (RegiocompetitieSporterBoog
                          .objects
                          .filter(regiocompetitie__pk__in=deelcomp_pks,
                                  indiv_klasse__boogtype=boogtype,
                                  aantal_scores__gte=self.comp.aantal_scores_voor_rk_deelname)
                          .select_related('indiv_klasse',
                                          'sporterboog__sporter',
                                          'sporterboog__sporter__bij_vereniging',
                                          'bij_vereniging')
                          .order_by('indiv_klasse__volgorde',
                                    '-gemiddelde'))

        # bepaal in welke klassen we de uitslag gaan tonen
        context['toon_uitslag'] = False
        klasse2toon_uitslag = dict()        # [klasse volgorde] = True/False
        if is_lijst_rk:
            for deelnemer in deelnemers:
                if deelnemer.result_rank > 0:
                    klasse = deelnemer.indiv_klasse.volgorde
                    klasse2toon_uitslag[klasse] = True
                    context['toon_uitslag'] = True
            # for

        klasse = -1
        limiet = 24
        curr_teller = None
        for deelnemer in deelnemers:
            # deelnemer kan zijn:
            #   is_lijst_rk == False --> RegiocompetitieSporterBoog
            #   is_lijst_rk == True  --> KampioenschapSporterBoog
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

                limiet = wkl2limiet.get(deelnemer.indiv_klasse.pk, 24)

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

            if not is_lijst_rk:
                # regio lijst
                if not deelnemer.inschrijf_voorkeur_rk_bk:
                    # zet alvast op "afgemeld"
                    # deelnemer.deelname = DEELNAME_NEE       # wordt niet gebruikt?!
                    deelnemer.geen_deelname = True

            if deelkamp.heeft_deelnemerslijst:
                if deelnemer.rank > limiet:
                    deelnemer.is_reserve = True

            if toon_uitslag:
                if deelnemer.result_rank in (0, KAMP_RANK_RESERVE, KAMP_RANK_NO_SHOW):
                    deelnemer.geen_deelname = True
                    deelnemer.geen_rank = True
                    deelnemer.scores_str_1 = "-"
                    deelnemer.scores_str_2 = ""

                elif deelnemer.result_rank == KAMP_RANK_BLANCO:
                    deelnemer.scores_str_1 = '-'
                    deelnemer.scores_str_2 = '(blanco)'
                    deelnemer.geen_rank = True

                elif deelnemer.result_rank < KAMP_RANK_BLANCO:      # pragma: no branch
                    deelnemer.scores_str_1 = "%s (%s+%s)" % (deelnemer.result_score_1 + deelnemer.result_score_2,
                                                             deelnemer.result_score_1,
                                                             deelnemer.result_score_2)
                    deelnemer.scores_str_2 = deelnemer.result_counts        # 25m1pijl only

            curr_teller.aantal_regels += 1
        # for

        context['deelnemers'] = deelnemers
        context['heeft_deelnemers'] = (len(deelnemers) > 0)

        context['canonical'] = reverse('CompUitslagen:uitslagen-rk-indiv',          # TODO: keep?
                                       kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url(),
                                               'comp_boog': comp_boog})

        context['robots'] = 'nofollow'   # prevent crawling filter result pages

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('Competitie:overzicht', kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url()}),
                self.comp.beschrijving.replace(' competitie', '')),
            (None, 'Uitslagen RK individueel')
        )

        return context


class UitslagenRayonTeamsView(TemplateView):

    """ Django class-based view voor de de uitslagen van de rayonkampioenschappen teams """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_RK_TEAMS

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
                         .prefetch_related('teamtypen')
                         .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            url_hist = get_hist_url(kwargs['comp_pk_of_seizoen'], 'teams', 'rk', kwargs['team_type'][:3])
            if url_hist:
                return HttpResponseRedirect(url_hist)
        else:
            self.comp.bepaal_fase()

        return super().dispatch(request, *args, **kwargs)

    def _maak_filter_knoppen(self, context, gekozen_rayon_nr, teamtype_afkorting):
        """ filter knoppen per rayon en per competitie boog type """

        # team type filter
        context['teamtype'] = None
        context['teamtype_filters'] = teamtypen = self.comp.teamtypen.order_by('volgorde')

        for team in teamtypen:
            team.opt_text = team.beschrijving
            team.sel = 'team_' + team.afkorting
            if team.afkorting.upper() == teamtype_afkorting.upper():
                context['teamtype'] = team
                teamtype_afkorting = team.afkorting.lower()
                team.selected = True
            else:
                team.selected = False

            team.url_part = team.afkorting.lower()
        # for

        # als het team type correct was, maak dan de rayon knoppen
        if context['teamtype']:
            # rayon filters
            rayons = (Rayon
                      .objects
                      .order_by('rayon_nr')
                      .all())

            context['rayon_filters'] = rayons

            for rayon in rayons:
                rayon.opt_text = 'Rayon %s' % rayon.rayon_nr
                rayon.sel = 'rayon_%s' % rayon.rayon_nr
                rayon.selected = (rayon.rayon_nr == gekozen_rayon_nr)
                if rayon.selected:
                    context['rayon'] = rayon

                rayon.url_part = str(rayon.rayon_nr)
            # for

    @staticmethod
    def _finalize_klasse(deelkamp, done: list, plan: list, afgemeld: list, all_match_scores: list, alle_ranks: list):
        if len(done) > 0:
            # er is uitslag, dus overige teams hebben niet meegedaan
            for plan_team in plan:
                plan_team.rank = ''
                plan_team.rk_score_str = '-'
                plan_team.niet_deelgenomen = True
                plan_team.klasse_heeft_uitslag = True
            # for
            for afgemeld_team in afgemeld:
                afgemeld_team.rank = ''
                afgemeld_team.rk_score_str = '-'
                afgemeld_team.niet_deelgenomen = True
                afgemeld_team.klasse_heeft_uitslag = True
            # for
            teller = done[0]

            for team in done:
                if all_match_scores.count(team.result_teamscore) == 1:
                    # shootoff resultaat is niet relevant
                    # dit verwijdert de meeste "(SO: 0)"
                    team.rk_shootoff_str = ''
                elif alle_ranks.count(team.result_rank) > 1:
                    # meerdere teams hebben dezelfde rank gekregen
                    # shootoff resultaat is meestal "(SO: 0)" en dus niet relevant
                    team.rk_shootoff_str = ''
            # for

        elif len(plan) > 0:
            # er is geen uitslag, maar misschien hebben teams vrijstelling
            teller = plan[0]
            if deelkamp.is_afgesloten:
                for plan_team in plan:
                    plan_team.rank = ''
                    plan_team.rk_score_str = '-'
                    plan_team.niet_deelgenomen = True
                # for
                for afgemeld_team in afgemeld:
                    afgemeld_team.rank = ''
                    afgemeld_team.rk_score_str = '-'
                    afgemeld_team.niet_deelgenomen = True
                # for

        elif len(afgemeld) > 0:
            # alle teams afgemeld
            teller = afgemeld[0]
            if deelkamp.is_afgesloten:
                for afgemeld_team in afgemeld:
                    afgemeld_team.rank = ''
                    afgemeld_team.rk_score_str = '-'
                    afgemeld_team.niet_deelgenomen = True
                # for

        else:
            teller = None

        return teller

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if not self.comp:
            raise Http404('Competitie niet gevonden')

        context['comp'] = self.comp

        teamtype_afkorting = kwargs['team_type'][:3]     # afkappen voor de veiligheid

        # rayon_nr is optioneel (eerste binnenkomst zonder rayon nummer)
        try:
            rayon_nr = kwargs['rayon_nr'][:2]        # afkappen voor de veiligheid
            rayon_nr = int(rayon_nr)
        except KeyError:
            rayon_nr = get_request_rayon_nr(self.request)
        except ValueError:
            raise Http404('Verkeerd rayonnummer')

        self._maak_filter_knoppen(context, rayon_nr, teamtype_afkorting)

        context['url_filters'] = reverse('CompUitslagen:uitslagen-rk-teams-n',
                                         kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url(),
                                                 'team_type': '~1',
                                                 'rayon_nr': '~2'})

        teamtype = context['teamtype']
        if not teamtype:
            raise Http404('Team type niet bekend')

        try:
            deelkamp = (Kampioenschap
                        .objects
                        .select_related('competitie',
                                        'rayon')
                        .prefetch_related('rk_bk_matches')
                        .get(competitie=self.comp,
                             competitie__is_afgesloten=False,
                             deel=DEEL_RK,
                             rayon__rayon_nr=rayon_nr))
        except Kampioenschap.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        context['deelkamp'] = deelkamp
        comp = deelkamp.competitie
        comp.bepaal_fase()

        wkl2limiet = dict()   # [pk] = limiet
        for limiet in (KampioenschapTeamKlasseLimiet
                       .objects
                       .select_related('team_klasse')
                       .filter(kampioenschap=deelkamp)):
            wkl2limiet[limiet.team_klasse.pk] = limiet.limiet
        # for

        # als de gebruiker ingelogd is, laat dan de voor de teams van zijn vereniging zien wie er in de teams zitten
        toon_team_leden_van_ver_nr = None
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        if self.request.user.is_authenticated:
            account = get_account(self.request)
            if functie_nu and functie_nu.vereniging:
                # HWL, WL
                toon_team_leden_van_ver_nr = functie_nu.vereniging.ver_nr
            else:
                # geen beheerder, dus sporter
                sporter = Sporter.objects.filter(account=account).first()
                if sporter and sporter.is_actief_lid and sporter.bij_vereniging:
                    toon_team_leden_van_ver_nr = sporter.bij_vereniging.ver_nr

        # haal de planning erbij: team klasse --> match
        teamklasse2match = dict()     # [team_klasse.pk] = competitiematch
        match_pks = list(deelkamp.rk_bk_matches.values_list('pk', flat=True))
        for match in (CompetitieMatch
                      .objects
                      .prefetch_related('team_klassen')
                      .select_related('locatie')
                      .filter(pk__in=match_pks)):

            if match.locatie:
                match.adres_str = ", ".join(match.locatie.adres.split('\n'))

            for klasse in match.team_klassen.all():
                teamklasse2match[klasse.pk] = match
        # for

        if comp.is_indoor():
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        context['rk_teams'] = totaal_lijst = list()

        prev_klasse = ""
        limiet = 8
        klasse_teams_done = list()
        klasse_teams_plan = list()
        klasse_teams_afgemeld = list()
        aantal_regels = 0
        alle_matchscores = list()        # voor bepalen "toon shootoff"
        alle_ranks = list()

        for team in (KampioenschapTeam
                     .objects
                     .filter(kampioenschap=deelkamp,
                             team_type=teamtype)
                     .exclude(team_klasse=None)
                     .select_related('team_klasse',
                                     'vereniging')
                     .prefetch_related('gekoppelde_leden',
                                       'feitelijke_leden')
                     .order_by('team_klasse__volgorde',
                               'result_rank',
                               'result_volgorde',            # bij gelijke rank (ook 2x blanco) deze volgorde aanhouden
                               '-aanvangsgemiddelde')):      # sterkste team eerst

            if team.team_klasse != prev_klasse:
                teller = self._finalize_klasse(deelkamp,
                                               klasse_teams_done, klasse_teams_plan, klasse_teams_afgemeld,
                                               alle_matchscores, alle_ranks)

                if teller:
                    teller.aantal_regels = aantal_regels
                    teller.break_klasse = True
                    if teller.team_klasse:
                        teller.klasse_str = teller.team_klasse.beschrijving
                        teller.klasse_hashtag = make_valid_hashtag(teller.klasse_str)
                        try:
                            teller.match = teamklasse2match[teller.team_klasse.pk]
                        except KeyError:
                            pass
                        limiet = wkl2limiet.get(team.team_klasse.pk, 8)
                    else:
                        teller.klasse_str = team.team_type.beschrijving + " - Nog niet ingedeeld in een wedstrijdklasse"
                        limiet = 99

                totaal_lijst.extend(klasse_teams_done)
                totaal_lijst.extend(klasse_teams_plan)
                totaal_lijst.extend(klasse_teams_afgemeld)
                klasse_teams_done = list()
                klasse_teams_plan = list()
                klasse_teams_afgemeld = list()
                alle_matchscores = list()
                alle_ranks = list()

                prev_klasse = team.team_klasse
                aantal_regels = 2

            team.ver_nr = team.vereniging.ver_nr
            team.ver_str = str(team.vereniging)
            ag = float(team.aanvangsgemiddelde) * aantal_pijlen
            team.ag_str = "%05.1f" % ag
            team.ag_str = team.ag_str.replace('.', ',')
            team.toon_team_leden = False
            team.niet_deelgenomen = False
            team.rk_score_str = ''
            team.rk_shootoff_str = ''
            aantal_regels += 1

            if team.result_rank > 0:

                if team.result_rank == KAMP_RANK_BLANCO:
                    team.geen_rank = True
                    team.rk_score_str = '(blanco)'

                elif team.result_rank in (KAMP_RANK_NO_SHOW, KAMP_RANK_RESERVE):
                    team.niet_deelgenomen = True
                    team.geen_rank = True

                else:
                    team.rank = team.result_rank
                    team.rk_score_str = str(team.result_teamscore)
                    team.rk_shootoff_str = '(SO: %s)' % team.result_shootoff
                    alle_matchscores.append(team.result_teamscore)
                    alle_ranks.append(team.result_rank)

                team.klasse_heeft_uitslag = True

                originele_lid_nrs = list(team
                                         .gekoppelde_leden.all()
                                         .values_list('sporterboog__sporter__lid_nr', flat=True))
                deelnemers = list()
                if not team.niet_deelgenomen:
                    lid_nrs = list()
                    for deelnemer in team.feitelijke_leden.select_related('sporterboog__sporter'):
                        tup = (deelnemer.gemiddelde, deelnemer.pk, deelnemer)
                        deelnemers.append(tup)      # toevoegen voordat result_totaal een string wordt

                        deelnemer.naam_str = deelnemer.sporterboog.sporter.lid_nr_en_volledige_naam()
                        lid_nr = deelnemer.sporterboog.sporter.lid_nr
                        if lid_nr not in originele_lid_nrs:
                            deelnemer.is_invaller = True

                        lid_nrs.append(deelnemer.sporterboog.sporter.lid_nr)
                    # for
                    for deelnemer in team.gekoppelde_leden.select_related('sporterboog__sporter'):
                        if deelnemer.sporterboog.sporter.lid_nr not in lid_nrs:
                            tup = (deelnemer.gemiddelde, deelnemer.pk, deelnemer)
                            deelnemers.append(tup)

                            deelnemer.naam_str = deelnemer.sporterboog.sporter.lid_nr_en_volledige_naam()
                            deelnemer.is_uitvaller = True
                            deelnemer.result_totaal = '-'
                    # for

                    deelnemers.sort(reverse=True)       # hoogste eerst

                team.deelnemers = [deelnemer for _, _, deelnemer in deelnemers]

                klasse_teams_done.append(team)
            else:
                # nog geen uitslag beschikbaar
                if team.deelname == DEELNAME_NEE:
                    team.niet_deelgenomen = True  # toont team in grijs
                    klasse_teams_afgemeld.append(team)
                else:
                    team.rank = len(klasse_teams_plan) + 1
                    klasse_teams_plan.append(team)

                if team.rank > limiet:
                    team.is_reserve = True

                # toon teamleden waar ze heen moeten
                if team.ver_nr == toon_team_leden_van_ver_nr:
                    team.toon_team_leden = True
                    team.team_leden = list()
                    for deelnemer in (team
                                      .gekoppelde_leden
                                      .select_related('sporterboog__sporter')
                                      .order_by('-gemiddelde')):                      # hoogste eerst
                        team.team_leden.append(deelnemer)
                        deelnemer.sporter_str = deelnemer.sporterboog.sporter.lid_nr_en_volledige_naam()
                    # for
        # for

        teller = self._finalize_klasse(deelkamp,
                                       klasse_teams_done, klasse_teams_plan, klasse_teams_afgemeld,
                                       alle_matchscores, alle_ranks)
        if teller:
            teller.aantal_regels = aantal_regels
            teller.break_klasse = True
            if teller.team_klasse:
                teller.klasse_str = teller.team_klasse.beschrijving
                teller.klasse_hashtag = make_valid_hashtag(teller.klasse_str)
                try:
                    teller.match = teamklasse2match[teller.team_klasse.pk]
                except KeyError:
                    pass
            else:
                teller.klasse_str = team.team_type.beschrijving + " - Nog niet ingedeeld in een wedstrijdklasse"

        totaal_lijst.extend(klasse_teams_done)
        totaal_lijst.extend(klasse_teams_plan)
        totaal_lijst.extend(klasse_teams_afgemeld)

        if len(totaal_lijst) == 0:
            context['geen_teams'] = True

        context['canonical'] = reverse('CompUitslagen:uitslagen-rk-teams',      # TODO: keep?
                                       kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url(),
                                               'team_type': teamtype_afkorting})

        context['robots'] = 'nofollow'   # prevent crawling filter result pages

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('Competitie:overzicht', kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url()}),
                comp.beschrijving.replace(' competitie', '')),
            (None, 'Uitslagen RK teams')
        )

        return context


# end of file
