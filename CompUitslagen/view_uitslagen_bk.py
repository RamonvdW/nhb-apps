# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import TemplateView
from django.urls import reverse
from django.http import Http404
from Competitie.models import (Competitie, CompetitieMatch, DeelKampioenschap,
                               KampioenschapSporterBoog, KampioenschapTeam,
                               KampioenschapIndivKlasseLimiet, KampioenschapTeamKlasseLimiet,
                               DEEL_BK, DEELNAME_NEE, KAMP_RANK_RESERVE, KAMP_RANK_NO_SHOW, KAMP_RANK_UNKNOWN)
from Functie.rol import rol_get_huidige_functie
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
            deelkamp_bk = (DeelKampioenschap
                           .objects
                           .select_related('competitie')
                           .get(deel=DEEL_BK,
                                competitie__is_afgesloten=False,
                                competitie__pk=comp_pk))
        except DeelKampioenschap.DoesNotExist:
            raise Http404('Kampioenschap niet gevonden')

        if comp.fase == 'P':
            context['bevestig_tot_datum'] = comp.bk_eerste_wedstrijd - datetime.timedelta(days=14)

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
                                  volgorde__lte=48)                  # toon tot 48 sporters per klasse
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

    @staticmethod
    def _maak_filter_knoppen(context, comp, teamtype_afkorting):
        """ filter knoppen per rayon en per competitie boog type """

        # team type filter
        context['teamtype'] = None
        context['teamtype_filters'] = teamtypen = comp.teamtypen.order_by('volgorde')

        for team in teamtypen:
            team.sel = 'team_' + team.afkorting
            if team.afkorting.upper() == teamtype_afkorting.upper():
                context['teamtype'] = team
                teamtype_afkorting = team.afkorting.lower()
                team.selected = True
            else:
                team.selected = False

            team.zoom_url = reverse('CompUitslagen:uitslagen-bk-teams',
                                    kwargs={'comp_pk': comp.pk,
                                            'team_type': team.afkorting.lower()})
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

        teamtype_afkorting = kwargs['team_type'][:3]           # afkappen voor de veiligheid

        self._maak_filter_knoppen(context, comp, teamtype_afkorting)

        teamtype = context['teamtype']
        if not teamtype:
            raise Http404('Team type niet bekend')

        try:
            deelkamp_bk = (DeelKampioenschap
                           .objects
                           .select_related('competitie')
                           .get(deel=DEEL_BK,
                                competitie__is_afgesloten=False,
                                competitie__pk=comp_pk))
        except DeelKampioenschap.DoesNotExist:
            raise Http404('Kampioenschap niet gevonden')

        # als de gebruiker ingelogd is, laat dan de voor de teams van zijn vereniging zien wie er in de teams zitten
        toon_team_leden_van_ver_nr = None
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        account = self.request.user
        if account.is_authenticated:
            if functie_nu and functie_nu.nhb_ver:
                # HWL, WL
                toon_team_leden_van_ver_nr = functie_nu.nhb_ver.ver_nr
            else:
                # geen beheerder, dus sporter
                if account.sporter_set.count() > 0:
                    sporter = account.sporter_set.all()[0]
                    if sporter.is_actief_lid and sporter.bij_vereniging:
                        toon_team_leden_van_ver_nr = sporter.bij_vereniging.ver_nr

        # haal de planning erbij: team klasse --> match
        teamklasse2match = dict()     # [team_klasse.pk] = competitiematch
        match_pks = list(deelkamp_bk.rk_bk_matches.values_list('pk', flat=True))
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

        # voor conversie team gemiddelde naar RK score
        if comp.afstand == '18':
            aantal_pijlen = 2 * 30
        else:
            aantal_pijlen = 2 * 25

        wkl2limiet = dict()  # [pk] = aantal
        for limiet in (KampioenschapTeamKlasseLimiet
                       .objects
                       .select_related('team_klasse')
                       .filter(kampioenschap=deelkamp_bk)):
            wkl2limiet[limiet.team_klasse.pk] = limiet.limiet
        # for

        bk_teams = (KampioenschapTeam
                    .objects
                    .filter(kampioenschap=deelkamp_bk,
                            team_klasse__team_type=teamtype)
                    .select_related('team_klasse',
                                    'vereniging')
                    .prefetch_related('gekoppelde_leden',
                                      'feitelijke_leden')
                    .order_by('team_klasse__volgorde',
                              'volgorde'))

        context['bk_teams'] = totaal_lijst = list()

        prev_klasse = ""
        rank = 0
        klasse_teams_done = list()
        klasse_teams_plan = list()
        aantal_regels = 0
        for team in bk_teams:

            if team.team_klasse != prev_klasse:
                if len(klasse_teams_done) > 0:
                    # er is uitslag, dus deze teams hebben niet meegedaan
                    for plan_team in klasse_teams_plan:
                        plan_team.rank = ''
                        plan_team.niet_deelgenomen = True
                    # for
                    teller = klasse_teams_done[0]
                elif len(klasse_teams_plan) > 0:
                    # er is geen uitslag, maar misschien hebben teams vrijstelling
                    if deelkamp_bk.is_afgesloten:
                        for plan_team in klasse_teams_plan:
                            plan_team.rank = ''
                            plan_team.niet_deelgenomen = True
                        # for
                    teller = klasse_teams_plan[0]
                else:
                    teller = None

                if teller:
                    teller.aantal_regels = aantal_regels
                    teller.break_klasse = True
                    if teller.team_klasse:
                        teller.klasse_str = teller.team_klasse.beschrijving
                        try:
                            teller.match = teamklasse2match[teller.team_klasse.pk]
                        except KeyError:
                            pass
                    else:
                        teller.klasse_str = "%s - Nog niet ingedeeld in een wedstrijdklasse" % team.team_type.beschrijving

                totaal_lijst.extend(klasse_teams_done)
                totaal_lijst.extend(klasse_teams_plan)
                klasse_teams_done = list()
                klasse_teams_plan = list()

                try:
                    limiet = wkl2limiet[team.team_klasse.pk]
                except KeyError:
                    limiet = 8
                    if "ERE" in team.team_klasse.beschrijving:
                        limiet = 12

                print('limiet=%s voor klasse %s' % (limiet, team.team_klasse))
                prev_klasse = team.team_klasse
                aantal_regels = 2
                rank = 0

            team.ver_nr = team.vereniging.ver_nr
            team.ver_str = str(team.vereniging)
            rk_score = round(team.aanvangsgemiddelde * aantal_pijlen)
            if rk_score < 10:
                team.rk_score_str = '(blanco)'
            else:
                team.rk_score_str = str(rk_score)
            team.toon_team_leden = False
            aantal_regels += 1

            if team.ver_nr == toon_team_leden_van_ver_nr:
                # TODO: optioneel maken: nodig om te weten wie naar deze wedstrijd moeten, maar niet nodig in eindstand
                team.toon_team_leden = True
                team.team_leden = list()
                for deelnemer in (team
                                  .gekoppelde_leden
                                  .select_related('sporterboog__sporter')
                                  .order_by('-gemiddelde')):                      # hoogste eerst
                    team.team_leden.append(deelnemer)
                    deelnemer.sporter_str = deelnemer.sporterboog.sporter.lid_nr_en_volledige_naam()
                # for
                aantal_regels += 1

            if team.rank > limiet:
                team.is_reserve = True

            if team.result_rank > 0:
                team.rank = team.result_rank
                if team.result_teamscore < 10:
                    team.bk_score_str = '(blanco)'
                else:
                    team.bk_score_str = str(team.result_teamscore)
                team.heeft_uitslag = True

                originele_lid_nrs = list(team.gekoppelde_leden.all().values_list('sporterboog__sporter__lid_nr', flat=True))
                deelnemers = list()
                lid_nrs = list()
                for deelnemer in team.feitelijke_leden.select_related('sporterboog__sporter'):
                    deelnemer.result_totaal = deelnemer.result_teamscore_1 + deelnemer.result_teamscore_2
                    if deelnemer.result_totaal < 10:
                        deelnemer.result_totaal = '-'
                    deelnemer.naam_str = deelnemer.sporterboog.sporter.lid_nr_en_volledige_naam()
                    lid_nr = deelnemer.sporterboog.sporter.lid_nr
                    if lid_nr not in originele_lid_nrs:
                        deelnemer.is_invaller = True
                    tup = (deelnemer.result_totaal, deelnemer.pk, deelnemer)
                    deelnemers.append(tup)

                    lid_nrs.append(deelnemer.sporterboog.sporter.lid_nr)
                # for
                for deelnemer in team.gekoppelde_leden.select_related('sporterboog__sporter'):
                    if deelnemer.sporterboog.sporter.lid_nr not in lid_nrs:
                        deelnemer.naam_str = deelnemer.sporterboog.sporter.lid_nr_en_volledige_naam()
                        deelnemer.is_uitvaller = True
                        deelnemer.result_totaal = '-'
                        tup = (deelnemer.gemiddelde, deelnemer.pk, deelnemer)
                        deelnemers.append(tup)
                # for

                deelnemers.sort(reverse=True)       # hoogste eerst
                team.deelnemers = [deelnemer for _, _, deelnemer in deelnemers]

                klasse_teams_done.append(team)
            else:
                # nog geen uitslag beschikbaar
                # TODO: geen rank invullen na de cut
                rank += 1
                team.rank = rank
                klasse_teams_plan.append(team)
        # for

        if len(klasse_teams_done) > 0:
            # er is uitslag, dus deze teams hebben niet meegedaan
            for plan_team in klasse_teams_plan:
                plan_team.rank = ''
                plan_team.niet_deelgenomen = True
            # for
            teller = klasse_teams_done[0]
        elif len(klasse_teams_plan) > 0:
            # er is geen uitslag, maar misschien hebben teams vrijstelling
            if deelkamp_bk.is_afgesloten:
                for plan_team in klasse_teams_plan:
                    plan_team.rank = ''
                    plan_team.niet_deelgenomen = True
                # for
            teller = klasse_teams_plan[0]
        else:
            teller = None

        if teller:
            teller.aantal_regels = aantal_regels
            teller.break_klasse = True
            if teller.team_klasse:
                teller.klasse_str = teller.team_klasse.beschrijving
                try:
                    teller.match = teamklasse2match[teller.team_klasse.pk]
                except KeyError:
                    pass
            else:
                teller.klasse_str = "%s - Nog niet ingedeeld in een wedstrijdklasse" % team.team_type.beschrijving

        totaal_lijst.extend(klasse_teams_done)
        totaal_lijst.extend(klasse_teams_plan)

        if bk_teams.count() == 0:
            context['geen_teams'] = True

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Uitslagen BK teams')
        )

        menu_dynamics(self.request, context)
        return context


# end of file
