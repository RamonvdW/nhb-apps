# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from Competitie.definities import TEAM_PUNTEN_MODEL_SOM_SCORES
from Competitie.models import (Competitie, Regiocompetitie, RegiocompetitieSporterBoog,
                               RegiocompetitieTeam, RegiocompetitieRondeTeam)
from Competitie.seizoenen import get_comp_pk
from Vereniging.models import Vereniging
from types import SimpleNamespace


TEMPLATE_COMPUITSLAGEN_VERENIGING_TEAMS = 'compuitslagen/vereniging-teams.dtl'


class UitslagenVerenigingTeamsView(TemplateView):

    """ Django class-based view voor de de uitslagen van de teamcompetitie voor een specifieke vereniging """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_VERENIGING_TEAMS

    @staticmethod
    def _maak_filter_knoppen(context, comp, ver_nr, teamtype_afkorting):
        """ filter knoppen voor de vereniging """

        context['teamtype'] = None
        context['teamtype_filters'] = teamtypen = comp.teamtypen.order_by('volgorde')

        for team in teamtypen:
            team.sel = 'team_' + team.afkorting
            if team.afkorting.upper() == teamtype_afkorting.upper():
                team.selected = True
                context['teamtype'] = team
                teamtype_afkorting = team.afkorting.lower()

            team.zoom_url = reverse('CompUitslagen:uitslagen-vereniging-teams-n',
                                    kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url(),
                                            'team_type': team.afkorting.lower(),
                                            'ver_nr': ver_nr})
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

        teamtype_afkorting = kwargs['team_type'][:3]     # afkappen voor de veiligheid

        ver_nr = kwargs['ver_nr'][:4]  # afkappen voor de veiligheid
        try:
            ver_nr = int(ver_nr)
        except ValueError:
            raise Http404('Verkeerd verenigingsnummer')

        try:
            ver = Vereniging.objects.select_related('regio').get(ver_nr=ver_nr)
        except Vereniging.DoesNotExist:
            raise Http404('Vereniging niet gevonden')

        context['ver'] = ver

        self._maak_filter_knoppen(context, comp, ver_nr, teamtype_afkorting)

        teamtype = context['teamtype']
        if not teamtype:
            raise Http404('Team type niet bekend')

        regio_nr = ver.regio.regio_nr
        context['url_terug'] = reverse('CompUitslagen:uitslagen-regio-teams-n',
                                       kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url(),
                                               'team_type': teamtype.afkorting.lower(),
                                               'regio_nr': regio_nr})

        context['deelcomp'] = deelcomp = Regiocompetitie.objects.get(competitie=comp, regio=ver.regio)

        context['toon_punten'] = (deelcomp.regio_team_punten_model != TEAM_PUNTEN_MODEL_SOM_SCORES)

        # zoek alle verenigingsteams erbij
        teams = (RegiocompetitieTeam
                 .objects
                 .exclude(team_klasse=None)
                 .filter(regiocompetitie=deelcomp,
                         team_type=context['teamtype'],
                         vereniging=ver)
                 .prefetch_related('leden')
                 .order_by('team_klasse__volgorde'))

        pk2team = dict()
        for team in teams:
            pk2team[team.pk] = team
            team.rondes = list()
            team.ronde_scores = list()
            team.ronde_punten = list()
            team.naam_str = "[%s] %s" % (team.vereniging.ver_nr, team.team_naam)
            team.totaal_score = 0
            team.totaal_punten = 0
            team.leden_lijst = dict()     # [deelnemer.pk] = [ronde status, ..]
        # for

        if deelcomp.huidige_team_ronde >= 1:
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

                    if deelnemer.pk not in team.leden_lijst:
                        team.leden_lijst[deelnemer.pk] = voorgaand = list()
                        while len(voorgaand) < ronde_team.ronde_nr:
                            inzet = SimpleNamespace(tekst='-', score=-1)
                            voorgaand.append(inzet)
                        # while
                # for

                for deelnemer in ronde_team.deelnemers_feitelijk.all():
                    try:
                        voorgaand = team.leden_lijst[deelnemer.pk]
                    except KeyError:
                        team.leden_lijst[deelnemer.pk] = voorgaand = list()
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
                for deelnemer_pk, voorgaand in team.leden_lijst.items():
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
        else:
            # eerste ronde is nog niet gestart
            for team in teams:
                for deelnemer in team.leden.all():
                    team.leden_lijst[deelnemer.pk] = list()
                # for
            # for

        # converteer de team leden
        pks = list()
        for team in teams:
            pks.extend(team.leden_lijst.keys())
        # for

        pk2deelnemer = dict()
        for deelnemer in (RegiocompetitieSporterBoog
                          .objects
                          .select_related('sporterboog',
                                          'sporterboog__sporter')
                          .filter(pk__in=pks)):
            pk2deelnemer[deelnemer.pk] = deelnemer
        # for

        for team in teams:
            nieuw = list()
            for pk, voorgaand in team.leden_lijst.items():
                deelnemer = pk2deelnemer[pk]
                sporter = deelnemer.sporterboog.sporter
                deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())
                totaal = sum(inzet.score for inzet in voorgaand)
                tup = (totaal, deelnemer.pk, deelnemer, voorgaand[1:])
                nieuw.append(tup)
            # for

            # TODO: sorteren zou eerder moeten zodat de doorgestreepte nul altijd de onderste is
            nieuw.sort(reverse=True)
            team.leden_lijst = [(deelnemer, voorgaand) for _, _, deelnemer, voorgaand in nieuw]
        # for

        # sorteer de teams
        unsorted_teams = list()
        for team in teams:
            tup = (team.team_klasse.volgorde, team.totaal_punten, team.totaal_score, team.pk, team)

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
            team.klasse_str = team.team_klasse.beschrijving
            teams.append(team)
        # for

        context['geen_teams'] = (len(teams) == 0)

        context['aantal_regels'] = len(teams) * 3 + 3       # team, team score, punten
        for team in teams:
            context['aantal_regels'] += len(team.leden_lijst)

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('Competitie:overzicht', kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url()}),
                comp.beschrijving.replace(' competitie', '')),
            (context['url_terug'], 'Uitslag regio teams'),
            (None, 'Vereniging')
        )

        return context


# end of file
