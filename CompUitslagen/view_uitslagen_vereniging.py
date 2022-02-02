# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import TemplateView
from django.urls import reverse
from django.http import Http404
from BasisTypen.models import BoogType, TeamType
from NhbStructuur.models import NhbVereniging
from Competitie.models import (LAAG_REGIO, TEAM_PUNTEN_MODEL_SOM_SCORES, Competitie, DeelCompetitie,
                               RegiocompetitieTeam, RegiocompetitieRondeTeam, RegioCompetitieSchutterBoog)
from Competitie.menu import menu_dynamics_competitie
from Functie.rol import rol_get_huidige_functie
from types import SimpleNamespace


TEMPLATE_COMPUITSLAGEN_VERENIGING_INDIV = 'compuitslagen/uitslagen-vereniging-indiv.dtl'
TEMPLATE_COMPUITSLAGEN_VERENIGING_TEAMS = 'compuitslagen/uitslagen-vereniging-teams.dtl'


def get_sporter_ver_nr(request):

    """ Geeft het vereniging nhb nummer van de ingelogde schutter terug,
        of 101 als er geen regio vastgesteld kan worden
    """
    ver_nr = -1

    if request.user.is_authenticated:
        rol_nu, functie_nu = rol_get_huidige_functie(request)

        if functie_nu and functie_nu.nhb_ver:
            # HWL, WL, SEC
            ver_nr = functie_nu.nhb_ver.ver_nr

        if ver_nr < 0:
            # pak de vereniging van de ingelogde gebruiker
            account = request.user
            if account.sporter_set.count() > 0:
                sporter = account.sporter_set.all()[0]
                if sporter.is_actief_lid and sporter.bij_vereniging:
                    ver_nr = sporter.bij_vereniging.ver_nr

    ver_nrs = list(NhbVereniging.objects.order_by('ver_nr').values_list('ver_nr', flat=True))
    if ver_nr not in ver_nrs:
        ver_nr = ver_nrs[0]

    return ver_nr


class UitslagenVerenigingIndivView(TemplateView):

    """ Django class-based view voor de de uitslagen van de competitie """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_VERENIGING_INDIV

    @staticmethod
    def _maak_filter_knoppen(context, comp, ver_nr, comp_boog):
        """ filter knoppen per regio, gegroepeerd per rayon en per competitie boog type """

        # boogtype files
        boogtypen = BoogType.objects.order_by('volgorde').all()

        context['comp_boog'] = None
        context['boog_filters'] = boogtypen

        for boogtype in boogtypen:
            boogtype.sel = 'boog_' + boogtype.afkorting
            if boogtype.afkorting.upper() == comp_boog.upper():
                boogtype.selected = True
                context['comp_boog'] = boogtype
                comp_boog = boogtype.afkorting.lower()
                # geen url --> knop disabled

            boogtype.zoom_url = reverse('CompUitslagen:uitslagen-vereniging-indiv-n',
                                        kwargs={'comp_pk': comp.pk,
                                                'comp_boog': boogtype.afkorting.lower(),
                                                'ver_nr': ver_nr})
        # for

    @staticmethod
    def _get_deelcomp(comp, regio_nr):
        if regio_nr == 100:
            regio_nr = 101

        try:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_regio')
                        .get(laag=LAAG_REGIO,
                             competitie=comp,
                             competitie__is_afgesloten=False,       # FUTURE: op meer plekken dit filter toepassen
                             nhb_regio__regio_nr=regio_nr))
        except DeelCompetitie.DoesNotExist:     # pragma: no cover
            raise Http404('Competitie niet gevonden')

        return deelcomp

    @staticmethod
    def _get_deelnemers(deelcomp, boogtype, ver_nr):
        deelnemers = (RegioCompetitieSchutterBoog
                      .objects
                      .select_related('sporterboog',
                                      'sporterboog__sporter',
                                      'klasse',
                                      'klasse__indiv',
                                      'klasse__indiv__boogtype')
                      .filter(deelcompetitie=deelcomp,
                              bij_vereniging__ver_nr=ver_nr,
                              klasse__indiv__boogtype=boogtype)
                      .order_by('-gemiddelde'))

        rank = 1
        for deelnemer in deelnemers:
            sporter = deelnemer.sporterboog.sporter
            deelnemer.rank = rank
            deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())
            deelnemer.klasse_str = deelnemer.klasse.indiv.beschrijving
            rank += 1

            # if deelnemer.score1 == 0:
            #     deelnemer.score1 = '-'
            # if deelnemer.score2 == 0:
            #     deelnemer.score2 = '-'
            # if deelnemer.score3 == 0:
            #     deelnemer.score3 = '-'
            # if deelnemer.score4 == 0:
            #     deelnemer.score4 = '-'
            # if deelnemer.score5 == 0:
            #     deelnemer.score5 = '-'
            # if deelnemer.score6 == 0:
            #     deelnemer.score6 = '-'
            # if deelnemer.score7 == 0:
            #     deelnemer.score7 = '-'
        # for

        return deelnemers

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

        comp_boog = kwargs['comp_boog'][:2]     # afkappen voor de veiligheid

        # ver_nr is optioneel en resulteert in het nummer van de schutter
        try:
            ver_nr = kwargs['ver_nr'][:4]     # afkappen voor de veiligheid
            ver_nr = int(ver_nr)
        except KeyError:
            # zoek de vereniging die bij de huidige gebruiker past
            ver_nr = get_sporter_ver_nr(self.request)
        except ValueError:
            raise Http404('Verkeerd verenigingsnummer')

        try:
            ver = NhbVereniging.objects.select_related('regio').get(ver_nr=ver_nr)
        except NhbVereniging.DoesNotExist:
            raise Http404('Vereniging niet gevonden')

        context['ver'] = ver

        self._maak_filter_knoppen(context, comp, ver_nr, comp_boog)

        boogtype = context['comp_boog']
        if not boogtype:
            raise Http404('Boogtype niet bekend')

        regio_nr = ver.regio.regio_nr
        context['url_terug'] = reverse('CompUitslagen:uitslagen-regio-indiv-n',
                                       kwargs={'comp_pk': comp.pk,
                                               'zes_scores': 'alle',
                                               'comp_boog': comp_boog,
                                               'regio_nr': regio_nr})

        context['deelcomp'] = deelcomp = self._get_deelcomp(comp, regio_nr)

        context['deelnemers'] = deelnemers = self._get_deelnemers(deelcomp, boogtype, ver_nr)
        context['aantal_deelnemers'] = len(deelnemers)
        context['aantal_regels'] = len(deelnemers) + 3

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (context['url_terug'], 'Uitslag regio individueel'),
            (None, 'Vereniging')
        )

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return context


class UitslagenVerenigingTeamsView(TemplateView):

    """ Django class-based view voor de de uitslagen van de teamcompetitie voor een specifieke vereniging """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_VERENIGING_TEAMS

    @staticmethod
    def _maak_filter_knoppen(context, comp, ver_nr, teamtype_afkorting):
        """ filter knoppen voor de vereniging """

        teamtypen = TeamType.objects.order_by('volgorde').all()

        context['teamtype'] = None
        context['teamtype_filters'] = teamtypen

        for team in teamtypen:
            team.sel = 'team_' + team.afkorting
            if team.afkorting.upper() == teamtype_afkorting.upper():
                team.selected = True
                context['teamtype'] = team
                teamtype_afkorting = team.afkorting.lower()

            team.zoom_url = reverse('CompUitslagen:uitslagen-vereniging-teams-n',
                                    kwargs={'comp_pk': comp.pk,
                                            'team_type': team.afkorting.lower(),
                                            'ver_nr': ver_nr})
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

        teamtype_afkorting = kwargs['team_type'][:2]     # afkappen voor de veiligheid

        # ver_nr is optioneel en resulteert in het nummer van de sporter
        try:
            ver_nr = kwargs['ver_nr'][:4]     # afkappen voor de veiligheid
            ver_nr = int(ver_nr)
        except KeyError:
            # TODO: onmogelijk om hier te komen (ivm URL design)
            # zoek de vereniging die bij de huidige gebruiker past
            ver_nr = get_sporter_ver_nr(self.request)
        except ValueError:
            raise Http404('Verkeerd verenigingsnummer')

        try:
            ver = NhbVereniging.objects.select_related('regio').get(ver_nr=ver_nr)
        except NhbVereniging.DoesNotExist:
            raise Http404('Vereniging niet gevonden')

        context['ver'] = ver

        self._maak_filter_knoppen(context, comp, ver_nr, teamtype_afkorting)

        teamtype = context['teamtype']
        if not teamtype:
            raise Http404('Team type niet bekend')

        regio_nr = ver.regio.regio_nr
        context['url_terug'] = reverse('CompUitslagen:uitslagen-regio-teams-n',
                                       kwargs={'comp_pk': comp.pk,
                                               'team_type': teamtype.afkorting.lower(),
                                               'regio_nr': regio_nr})

        context['deelcomp'] = deelcomp = DeelCompetitie.objects.get(competitie=comp, nhb_regio=ver.regio)

        context['toon_punten'] = (deelcomp.regio_team_punten_model != TEAM_PUNTEN_MODEL_SOM_SCORES)

        # zoek alle verenigingsteams erbij
        teams = (RegiocompetitieTeam
                 .objects
                 .exclude(klasse=None)
                 .filter(deelcompetitie=deelcomp,
                         team_type=context['teamtype'],
                         vereniging=ver)
                 .order_by('klasse__team__volgorde'))

        pk2team = dict()
        for team in teams:
            pk2team[team.pk] = team
            team.rondes = list()
            team.ronde_scores = list()
            team.ronde_punten = list()
            team.naam_str = "[%s] %s" % (team.vereniging.ver_nr, team.team_naam)
            team.totaal_score = 0
            team.totaal_punten = 0
            team.leden = dict()     # [deelnemer.pk] = [ronde status, ..]
        # for

        ronde_teams = (RegiocompetitieRondeTeam
                       .objects
                       .filter(team__in=teams)
                       .prefetch_related('deelnemers_geselecteerd',
                                         'deelnemers_feitelijk',
                                         'scorehist_feitelijk')
                       .order_by('ronde_nr'))
        for ronde_team in ronde_teams:
            team = pk2team[ronde_team.team.pk]
            team.rondes.append(ronde_team)
            team.ronde_scores.append(ronde_team.team_score)

            if ronde_team.ronde_nr < deelcomp.huidige_team_ronde:
                team.ronde_punten.append(ronde_team.team_punten)
            else:
                team.ronde_punten.append(-1)

            team.totaal_score += ronde_team.team_score
            team.totaal_punten += ronde_team.team_punten

            # haal de bevroren scores op
            sb2score = dict()               # [sporterboog.pk] = score_waarde
            for scorehist in (ronde_team
                              .scorehist_feitelijk
                              .select_related('score',
                                              'score__sporterboog')
                              .all()):
                sb2score[scorehist.score.sporterboog.pk] = scorehist.nieuwe_waarde
            # for

            geselecteerd_pks = list()
            for deelnemer in ronde_team.deelnemers_geselecteerd.all():
                geselecteerd_pks.append(deelnemer.pk)

                if deelnemer.pk not in team.leden:
                    team.leden[deelnemer.pk] = voorgaand = list()
                    while len(voorgaand) < ronde_team.ronde_nr:
                        inzet = SimpleNamespace(tekst='-', score=-1)
                        voorgaand.append(inzet)
                    # while
            # for

            for deelnemer in ronde_team.deelnemers_feitelijk.all():
                try:
                    voorgaand = team.leden[deelnemer.pk]
                except KeyError:
                    team.leden[deelnemer.pk] = voorgaand = list()
                    while len(voorgaand) < ronde_team.ronde_nr:
                        inzet = SimpleNamespace(tekst='-', score=-1)
                        voorgaand.append(inzet)
                    # while

                try:
                    score = sb2score[deelnemer.sporterboog.pk]
                except KeyError:
                    # geen score van deze sporter
                    score = 0

                score_str = str(score)
                if deelnemer.pk not in geselecteerd_pks:
                    score_str = '* ' + score_str
                else:
                    geselecteerd_pks.remove(deelnemer.pk)

                inzet = SimpleNamespace(
                            tekst=score_str,
                            score=score)

                voorgaand.append(inzet)
            # for

            # samenvatting van deze ronde maken
            laagste_inzet = None
            laagste_score = 9999
            aantal_scores = 0
            for deelnemer_pk, voorgaand in team.leden.items():
                # iedereen die voorheen in het team zaten door laten groeien
                if len(voorgaand) <= ronde_team.ronde_nr:
                    if deelnemer_pk in geselecteerd_pks:
                        # was geselecteerd voor deze ronde, dus uitvaller
                        inzet = SimpleNamespace(tekst='-', score=-1)
                    else:
                        # niet geselecteerd voor deze ronde
                        inzet = SimpleNamespace(tekst='', score=-1)
                    voorgaand.append(inzet)

                # track het aantal scores en de laagste score
                inzet = voorgaand[-1]
                if inzet.score >= 0:
                    aantal_scores += 1
                    if inzet.score < laagste_score:
                        laagste_score = inzet.score
                        laagste_inzet = inzet
            # for
            if aantal_scores > 3 and laagste_inzet:
                # de score die buiten de top-3 valt wegstrepen
                laagste_inzet.is_laagste = True
        # for

        # converteer de team leden
        pks = list()
        for team in teams:
            pks.extend(team.leden.keys())
        # for

        pk2deelnemer = dict()
        for deelnemer in (RegioCompetitieSchutterBoog
                          .objects
                          .select_related('sporterboog',
                                          'sporterboog__sporter')
                          .filter(pk__in=pks)):
            pk2deelnemer[deelnemer.pk] = deelnemer
        # for

        for team in teams:
            nieuw = list()
            for pk, voorgaand in team.leden.items():
                deelnemer = pk2deelnemer[pk]
                sporter = deelnemer.sporterboog.sporter
                deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())
                totaal = sum(inzet.score for inzet in voorgaand)
                tup = (totaal, deelnemer.pk, deelnemer, voorgaand[1:])
                nieuw.append(tup)
            # for

            # TODO: sorteren zou eerder moeten zodat de doorgestreepte nul altijd de onderste is
            nieuw.sort(reverse=True)
            team.leden = [(deelnemer, voorgaand) for _, _, deelnemer, voorgaand in nieuw]
        # for

        # sorteer de teams
        unsorted_teams = list()
        for team in teams:
            tup = (team.klasse.team.volgorde, team.totaal_punten, team.totaal_score, team.pk, team)

            while len(team.ronde_scores) < 7:
                team.ronde_scores.append('-')

            while len(team.ronde_punten) < 7:
                team.ronde_punten.append(-1)

            unsorted_teams.append(tup)
        # for
        unsorted_teams.sort()

        context['teams'] = teams = list()
        for tup in unsorted_teams:
            team = tup[-1]
            team.klasse_str = team.klasse.team.beschrijving
            teams.append(team)
        # for

        context['geen_teams'] = (len(teams) == 0)

        context['aantal_regels'] = len(teams) * 3 + 4       # team, team score, punten
        for team in teams:
            context['aantal_regels'] += len(team.leden)

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (context['url_terug'], 'Uitslag regio teams'),
            (None, 'Vereniging')
        )

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return context


# end of file
