# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
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
from Sporter.models import Sporter
from types import SimpleNamespace
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
                                        kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url(),
                                                'comp_boog': boogtype.afkorting.lower()})
        # for

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = get_comp_pk(kwargs['comp_pk_of_seizoen'])
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

        context['deelkamp_bk'] = deelkamp_bk

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

        if comp.is_indoor():
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

        context['canonical'] = reverse('CompUitslagen:uitslagen-bk-indiv',
                                       kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url(),
                                               'comp_boog': comp_boog})

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('Competitie:overzicht', kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url()}),
                comp.beschrijving.replace(' competitie', '')),
            (None, 'Uitslagen BK individueel')
        )

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
                                    kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url(),
                                            'team_type': team.afkorting.lower()})
        # for

    @staticmethod
    def _finalize_klasse(deelkamp_bk, done, plan, afgemeld):
        if len(done) > 0:
            teller = done[0]
            # er is uitslag, dus overige teams hebben niet meegedaan
            for plan_team in plan:
                plan_team.rank = ''
                plan_team.niet_deelgenomen = True
                plan_team.klasse_heeft_uitslag = True
            # for
            for afgemeld_team in afgemeld:
                afgemeld_team.rank = ''
                afgemeld_team.niet_deelgenomen = True
                afgemeld_team.klasse_heeft_uitslag = True
            # for

        elif len(plan) > 0:
            # er is geen uitslag, maar misschien hebben teams vrijstelling
            teller = plan[0]
            if deelkamp_bk.is_afgesloten:
                for plan_team in plan:
                    plan_team.rank = ''
                    plan_team.niet_deelgenomen = True
                # for
                for afgemeld_team in afgemeld:
                    afgemeld_team.rank = ''
                    afgemeld_team.niet_deelgenomen = True
                # for

        elif len(afgemeld) > 0:
            # alle teams afgemeld
            teller = afgemeld[0]
            if deelkamp_bk.is_afgesloten:
                for afgemeld_team in afgemeld:
                    afgemeld_team.rank = ''
                    afgemeld_team.niet_deelgenomen = True
                    afgemeld_team.klasse_heeft_uitslag = True
                # for

        else:
            teller = None

        return teller

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = get_comp_pk(kwargs['comp_pk_of_seizoen'])
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
            deelkamp_bk = (Kampioenschap
                           .objects
                           .select_related('competitie')
                           .get(deel=DEEL_BK,
                                competitie__is_afgesloten=False,
                                competitie__pk=comp_pk))
        except Kampioenschap.DoesNotExist:
            raise Http404('Kampioenschap niet gevonden')

        context['deelkamp_bk'] = deelkamp_bk

        # als de gebruiker ingelogd is, laat dan de voor de teams van zijn vereniging zien wie er in de teams zitten
        toon_team_leden_van_ver_nr = None
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        account = get_account(self.request)
        if account.is_authenticated:
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
        if comp.is_indoor():
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

        bk_cache = dict()      # [pk] = KampioenschapSporterBoog()
        for deelnemer in (KampioenschapSporterBoog
                          .objects
                          .filter(kampioenschap__competitie=deelkamp_bk.competitie,
                                  kampioenschap__deel=DEEL_RK)      # RK sporters in BK teams!
                          .select_related('sporterboog',
                                          'sporterboog__sporter')):
            deelnemer.naam_str = deelnemer.sporterboog.sporter.lid_nr_en_volledige_naam()
            bk_cache[deelnemer.pk] = deelnemer
        # for

        context['bk_teams'] = totaal_lijst = list()

        prev_klasse = ""
        klasse_teams_done = list()
        klasse_teams_plan = list()
        klasse_teams_afgemeld = list()
        aantal_regels = 0
        limiet = 0
        for team in (KampioenschapTeam
                     .objects
                     .filter(kampioenschap=deelkamp_bk,
                             team_klasse__team_type=teamtype)
                     .select_related('team_klasse',
                                     'vereniging')
                     .prefetch_related('gekoppelde_leden',
                                       'feitelijke_leden')
                     .order_by('team_klasse__volgorde',      # klassen in de uitslag
                               'result_rank',                # teams binnen elke klasse
                               'result_volgorde',            # indien gelijke rank (uitgevallen in finales)
                               'volgorde')):                 # indien niet meegedaan

            if team.team_klasse != prev_klasse:
                teller = self._finalize_klasse(deelkamp_bk, klasse_teams_done, klasse_teams_plan, klasse_teams_afgemeld)
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
                        teller.klasse_str = team.team_type.beschrijving + " - Nog niet ingedeeld in een wedstrijdklasse"

                totaal_lijst.extend(klasse_teams_done)
                totaal_lijst.extend(klasse_teams_plan)
                totaal_lijst.extend(klasse_teams_afgemeld)
                klasse_teams_done = list()
                klasse_teams_plan = list()
                klasse_teams_afgemeld = list()

                try:
                    limiet = wkl2limiet[team.team_klasse.pk]
                except KeyError:
                    limiet = 8
                    if "ERE" in team.team_klasse.beschrijving:
                        limiet = 12

                prev_klasse = team.team_klasse
                aantal_regels = 2

            team.ver_nr = team.vereniging.ver_nr
            team.ver_str = str(team.vereniging)
            team.toon_team_leden = False

            # teamsterkte vanuit de RK resultaten
            rk_score = round(team.aanvangsgemiddelde * aantal_pijlen)
            if rk_score < 10:
                team.rk_score_str = '(blanco)'
            else:
                team.rk_score_str = str(rk_score)

            team.bk_score_str = '-'
            aantal_regels += 1

            if team.result_rank > 0:
                team.is_reserve = False
                team.rank = team.result_rank
                if team.result_rank == KAMP_RANK_BLANCO:
                    team.bk_score_str = '(blanco)'
                else:
                    team.bk_score_str = str(team.result_teamscore)
                team.klasse_heeft_uitslag = True

                # de volgende statement worden aparte database queries
                originele_pks = list(team.gekoppelde_leden.values_list('pk', flat=True))
                feitelijke_pks = team.feitelijke_leden.values_list('pk', flat=True)

                unsorted = list()
                for pk in feitelijke_pks:
                    deelnemer = bk_cache[pk]
                    voor_uitslag = SimpleNamespace(
                                        naam_str=deelnemer.naam_str,
                                        is_uitvaller=False,
                                        is_invaller=deelnemer.pk not in originele_pks,
                                        result_totaal=deelnemer.result_bk_teamscore_1 + deelnemer.result_bk_teamscore_2)
                    tup = (voor_uitslag.result_totaal, pk, voor_uitslag)
                    unsorted.append(tup)
                    if not voor_uitslag.is_invaller:
                        originele_pks.remove(pk)
                # for

                # voeg de uitvallers toe
                for pk in originele_pks:
                    deelnemer = bk_cache[pk]
                    voor_uitslag = SimpleNamespace(
                                        naam_str=deelnemer.naam_str,
                                        is_uitvaller=True,
                                        is_invaller=False,
                                        result_totaal=0)
                    # gebruik gemiddelde zodat de uitvallers aan het einde van de lijst staan na sorteren
                    tup = (deelnemer.gemiddelde, pk, voor_uitslag)
                    unsorted.append(tup)
                # for

                unsorted.sort(reverse=True)       # hoogste eerst
                team.deelnemers = [voor_uitslag for _, _, voor_uitslag in unsorted]

                klasse_teams_done.append(team)
            else:
                # nog geen uitslag beschikbaar
                if team.deelname == DEELNAME_NEE:
                    team.niet_deelgenomen = True  # toont team in grijs
                    team.rank = ''
                    klasse_teams_afgemeld.append(team)
                else:
                    klasse_teams_plan.append(team)
                    if team.rank > limiet:
                        team.is_reserve = True

                # laat vereniging weten wie waar naartoe moet
                if team.ver_nr == toon_team_leden_van_ver_nr:
                    team.toon_team_leden = True

                    unsorted = list()
                    for pk in team.gekoppelde_leden.values_list('pk', flat=True):
                        deelnemer = bk_cache[pk]
                        tup = (deelnemer.gemiddelde, deelnemer.pk, deelnemer)
                        unsorted.append(tup)
                    # for
                    unsorted.sort(reverse=True)
                    team.team_leden = [deelnemer for _, _, deelnemer in unsorted]
        # for

        teller = self._finalize_klasse(deelkamp_bk, klasse_teams_done, klasse_teams_plan, klasse_teams_afgemeld)
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
                teller.klasse_str = "Nog niet ingedeeld in een wedstrijdklasse"

        totaal_lijst.extend(klasse_teams_done)
        totaal_lijst.extend(klasse_teams_plan)
        totaal_lijst.extend(klasse_teams_afgemeld)

        context['geen_teams'] = len(totaal_lijst) == 0

        context['canonical'] = reverse('CompUitslagen:uitslagen-bk-teams',
                                       kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url(),
                                               'team_type': teamtype_afkorting})

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('Competitie:overzicht', kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url()}),
                comp.beschrijving.replace(' competitie', '')),
            (None, 'Uitslagen BK teams')
        )

        return context


# end of file
