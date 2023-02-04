# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import TemplateView
from django.urls import reverse
from django.http import Http404
from NhbStructuur.models import NhbRayon
from Competitie.models import (Competitie, Regiocompetitie, KampioenschapIndivKlasseLimiet, CompetitieMatch,
                               RegiocompetitieSporterBoog, KampioenschapSporterBoog, KampioenschapTeam,
                               Kampioenschap, DEEL_RK, DEELNAME_NEE, KAMP_RANK_UNKNOWN, KAMP_RANK_RESERVE, KAMP_RANK_NO_SHOW)
from Functie.models import Rollen
from Functie.rol import rol_get_huidige_functie
from Plein.menu import menu_dynamics
import datetime

TEMPLATE_COMPUITSLAGEN_RK_INDIV = 'compuitslagen/uitslagen-rk-indiv.dtl'
TEMPLATE_COMPUITSLAGEN_RK_TEAMS = 'compuitslagen/uitslagen-rk-teams.dtl'


def get_request_rayon_nr(request):
    """ Geeft het rayon nummer van de ingelogde gebruiker/beheerder terug,
        of 1 als er geen rayon vastgesteld kan worden
    """
    rayon_nr = 1

    rol_nu, functie_nu = rol_get_huidige_functie(request)

    if functie_nu:
        if functie_nu.nhb_ver:
            # HWL, WL
            rayon_nr = functie_nu.nhb_ver.regio.rayon.rayon_nr
        elif functie_nu.nhb_regio:
            # RCL
            rayon_nr = functie_nu.nhb_regio.rayon.rayon_nr
        elif functie_nu.nhb_rayon:
            # RKO
            rayon_nr = functie_nu.nhb_rayon.rayon_nr

    elif rol_nu == Rollen.ROL_SPORTER:
        account = request.user
        if account.is_authenticated:                                    # pragma: no branch
            if account.sporter_set.count() > 0:                         # pragma: no branch
                sporter = account.sporter_set.all()[0]
                if sporter.is_actief_lid and sporter.bij_vereniging:
                    nhb_ver = sporter.bij_vereniging
                    rayon_nr = nhb_ver.regio.rayon.rayon_nr

    return rayon_nr


class UitslagenRayonIndivView(TemplateView):

    """ Django class-based view voor de uitslagen van de rayonkampioenschappen individueel """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_RK_INDIV

    @staticmethod
    def _maak_filter_knoppen(context, comp, gekozen_rayon_nr, comp_boog):
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

            boogtype.zoom_url = reverse('CompUitslagen:uitslagen-rayon-indiv-n',
                                        kwargs={'comp_pk': comp.pk,
                                                'comp_boog': boogtype.afkorting.lower(),
                                                'rayon_nr': gekozen_rayon_nr})
        # for

        if context['comp_boog']:
            # rayon filters
            rayons = (NhbRayon
                      .objects
                      .order_by('rayon_nr')
                      .all())

            context['rayon_filters'] = rayons

            for rayon in rayons:
                rayon.title_str = 'Rayon %s' % rayon.rayon_nr
                rayon.sel = 'rayon_%s' % rayon.pk
                rayon.zoom_url = reverse('CompUitslagen:uitslagen-rayon-indiv-n',
                                         kwargs={'comp_pk': comp.pk,
                                                 'comp_boog': comp_boog,
                                                 'rayon_nr': rayon.rayon_nr})

                if rayon.rayon_nr == gekozen_rayon_nr:
                    context['rayon'] = rayon
                    rayon.selected = True
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

        if comp.fase == 'J':
            context['bevestig_tot_datum'] = comp.rk_eerste_wedstrijd - datetime.timedelta(days=14)

        comp_boog = kwargs['comp_boog'][:2]          # afkappen voor de veiligheid

        # rayon_nr is optioneel (eerste binnenkomst zonder rayon nummer)
        try:
            rayon_nr = kwargs['rayon_nr'][:2]        # afkappen voor de veiligheid
            rayon_nr = int(rayon_nr)
        except KeyError:
            rayon_nr = get_request_rayon_nr(self.request)
        except ValueError:
            raise Http404('Verkeerd rayonnummer')

        self._maak_filter_knoppen(context, comp, rayon_nr, comp_boog)

        boogtype = context['comp_boog']
        if not boogtype:
            raise Http404('Boogtype niet bekend')

        try:
            deelkamp = (Kampioenschap
                        .objects
                        .select_related('competitie',
                                        'nhb_rayon')
                        .prefetch_related('rk_bk_matches')
                        .get(competitie__is_afgesloten=False,
                             competitie=comp,
                             deel=DEEL_RK,
                             nhb_rayon__rayon_nr=rayon_nr))
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
                                    'result_volgorde',               # is constant zolang er geen resultaat is
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
                            .filter(competitie__is_afgesloten=False,
                                    competitie=comp,
                                    nhb_regio__rayon__rayon_nr=rayon_nr)
                            .values_list('pk', flat=True))

            deelnemers = (RegiocompetitieSporterBoog
                          .objects
                          .filter(regiocompetitie__pk__in=deelcomp_pks,
                                  indiv_klasse__boogtype=boogtype,
                                  aantal_scores__gte=comp.aantal_scores_voor_rk_deelname)
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
            #   is_lijst_rk == False --> RegioCompetitieSporterBoog
            #   is_lijst_rk == True  --> KampioenschapSchutterBoog
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
            (None, 'Uitslagen RK individueel')
        )

        menu_dynamics(self.request, context)
        return context


class UitslagenRayonTeamsView(TemplateView):

    """ Django class-based view voor de de uitslagen van de rayonkampioenschappen teams """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_RK_TEAMS

    @staticmethod
    def _maak_filter_knoppen(context, comp, gekozen_rayon_nr, teamtype_afkorting):
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

            team.zoom_url = reverse('CompUitslagen:uitslagen-rayon-teams-n',
                                    kwargs={'comp_pk': comp.pk,
                                            'team_type': team.afkorting.lower(),
                                            'rayon_nr': gekozen_rayon_nr})
        # for

        # als het team type correct was, maak dan de rayon knopppen
        if context['teamtype']:
            # rayon filters
            rayons = (NhbRayon
                      .objects
                      .order_by('rayon_nr')
                      .all())

            context['rayon_filters'] = rayons

            for rayon in rayons:
                rayon.title_str = 'Rayon %s' % rayon.rayon_nr
                rayon.sel = 'rayon_%s' % rayon.rayon_nr
                rayon.selected = (rayon.rayon_nr == gekozen_rayon_nr)
                if rayon.selected:
                    context['rayon'] = rayon

                rayon.zoom_url = reverse('CompUitslagen:uitslagen-rayon-teams-n',
                                         kwargs={'comp_pk': comp.pk,
                                                 'team_type': teamtype_afkorting,
                                                 'rayon_nr': rayon.rayon_nr})
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

        teamtype_afkorting = kwargs['team_type'][:3]     # afkappen voor de veiligheid

        # rayon_nr is optioneel (eerste binnenkomst zonder rayon nummer)
        try:
            rayon_nr = kwargs['rayon_nr'][:2]        # afkappen voor de veiligheid
            rayon_nr = int(rayon_nr)
        except KeyError:
            rayon_nr = get_request_rayon_nr(self.request)
        except ValueError:
            raise Http404('Verkeerd rayonnummer')

        self._maak_filter_knoppen(context, comp, rayon_nr, teamtype_afkorting)

        teamtype = context['teamtype']
        if not teamtype:
            raise Http404('Team type niet bekend')

        try:
            deelkamp = (Kampioenschap
                        .objects
                        .select_related('competitie',
                                        'nhb_rayon')
                        .prefetch_related('rk_bk_matches')
                        .get(competitie=comp,
                             competitie__is_afgesloten=False,
                             deel=DEEL_RK,
                             nhb_rayon__rayon_nr=rayon_nr))
        except Kampioenschap.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        context['deelkamp'] = deelkamp
        comp = deelkamp.competitie
        comp.bepaal_fase()

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

        if comp.afstand == '18':
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        rk_teams = (KampioenschapTeam
                    .objects
                    .filter(kampioenschap=deelkamp,
                            team_type=teamtype)
                    .select_related('team_klasse',
                                    'vereniging')
                    .prefetch_related('gekoppelde_leden',
                                      'feitelijke_leden')
                    .order_by('team_klasse__volgorde',
                              'result_rank',
                              '-aanvangsgemiddelde'))       # sterkste team eerst

        context['rk_teams'] = totaal_lijst = list()

        prev_klasse = ""
        rank = 0
        klasse_teams_done = list()
        klasse_teams_plan = list()
        aantal_regels = 0
        for team in rk_teams:

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
                    if deelkamp.is_afgesloten:
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

                prev_klasse = team.team_klasse
                aantal_regels = 2
                rank = 0

            team.ver_nr = team.vereniging.ver_nr
            team.ver_str = str(team.vereniging)
            team.ag_str = "%05.1f" % (team.aanvangsgemiddelde * aantal_pijlen)
            team.ag_str = team.ag_str.replace('.', ',')
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

            # TODO: dit scherm is zowel een kandidaat-deelnemerslijst als de uitslag

            if team.result_rank > 0:
                team.rank = team.result_rank
                team.rk_score_str = str(team.result_teamscore)
                team.heeft_uitslag = True

                originele_lid_nrs = list(team.gekoppelde_leden.all().values_list('sporterboog__sporter__lid_nr', flat=True))
                deelnemers = list()
                lid_nrs = list()
                for deelnemer in team.feitelijke_leden.select_related('sporterboog__sporter'):
                    deelnemer.result_totaal = deelnemer.result_teamscore_1 + deelnemer.result_teamscore_2
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
            if deelkamp.is_afgesloten:
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

        if rk_teams.count() == 0:
            context['geen_teams'] = True

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Uitslagen RK teams')
        )

        menu_dynamics(self.request, context)
        return context


# end of file
