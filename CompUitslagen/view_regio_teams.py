# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404, HttpResponseRedirect
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from Competitie.definities import TEAM_PUNTEN_MODEL_TWEE, TEAM_PUNTEN_MODEL_SOM_SCORES
from Competitie.models import (Competitie, Regiocompetitie, RegiocompetitieTeam,
                               RegiocompetitieRondeTeam, RegiocompetitieTeamPoule)
from Competitie.seizoenen import get_comp_pk
from Competitie.operations.poules import maak_poule_schema
from Geo.models import Regio
from HistComp.operations import get_hist_url
from Overig.helpers import make_valid_hashtag
from Sporter.operations import get_request_regio_nr
from types import SimpleNamespace


TEMPLATE_COMPUITSLAGEN_REGIO_TEAMS = 'compuitslagen/regio-teams.dtl'


class UitslagenRegioTeamsView(TemplateView):

    """ Django class-based view voor de teamuitslagen van de competitie in 1 regio """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_REGIO_TEAMS

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
            url_hist = get_hist_url(kwargs['comp_pk_of_seizoen'], 'teams', 'regio', kwargs['team_type'][:3])
            if url_hist:
                return HttpResponseRedirect(url_hist)
        else:
            self.comp.bepaal_fase()

        return super().dispatch(request, *args, **kwargs)

    def _maak_filter_knoppen(self, context, gekozen_regio_nr, teamtype_afkorting):
        """ filter knoppen per regio, gegroepeerd per rayon en per competitie boog type """

        context['teamtype'] = None
        context['teamtype_filters'] = teamtypen = self.comp.teamtypen.order_by('volgorde')

        for team in teamtypen:
            team.opt_text = team.beschrijving
            team.sel = team.afkorting
            if team.afkorting.upper() == teamtype_afkorting.upper():
                # validatie van urlconf argument: gevraagde teamtype bestaat echt
                context['teamtype'] = team
                teamtype_afkorting = team.afkorting.lower()
                team.selected = True

            team.url_part = team.afkorting.lower()
        # for

        # regio filters
        if context['teamtype']:
            regios = (Regio
                      .objects
                      .select_related('rayon')
                      .filter(is_administratief=False)
                      .order_by('rayon__rayon_nr', 'regio_nr'))

            context['regio_filters'] = regios

            prev_rayon = 1
            for regio in regios:
                regio.break_before = (prev_rayon != regio.rayon_nr)
                prev_rayon = regio.rayon_nr

                regio.opt_text = 'Regio %s' % regio.regio_nr
                regio.sel = 'regio_%s' % regio.regio_nr
                if regio.regio_nr == gekozen_regio_nr:
                    regio.selected = True
                    context['regio'] = regio

                regio.url_part = str(regio.regio_nr)
            # for

        # vereniging filters
        if context['teamtype']:
            ver_nrs = list()
            vers = list()
            for team in (RegiocompetitieTeam
                         .objects
                         .filter(regiocompetitie__competitie=self.comp,
                                 vereniging__regio__regio_nr=gekozen_regio_nr)
                         .select_related('vereniging')
                         .order_by('vereniging__ver_nr')):
                if team.vereniging.ver_nr not in ver_nrs:
                    ver_nrs.append(team.vereniging.ver_nr)
                    vers.append(team.vereniging)
            # for

            if len(vers):
                for ver in vers:
                    ver.sel = 'ver_%s' % ver.ver_nr
                    ver.zoom_url = reverse('CompUitslagen:uitslagen-vereniging-teams-n',
                                           kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url(),
                                                   'team_type': '~1',       # gebruik team type filter
                                                   'ver_nr': ver.ver_nr})
                # for

                context['ver_filters'] = vers

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if not self.comp:
            raise Http404('Competitie niet gevonden')

        context['comp'] = self.comp

        teamtype_afkorting = kwargs['team_type'][:3]     # afkappen voor de veiligheid

        # regio_nr is optioneel (eerste binnenkomst zonder regio nummer)
        try:
            regio_nr = kwargs['regio_nr'][:3]   # afkappen voor de veiligheid
            regio_nr = int(regio_nr)
        except KeyError:
            # bepaal welke (initiële) regio bij de huidige gebruiker past
            regio_nr = get_request_regio_nr(self.request)
        except ValueError:
            raise Http404('Verkeerd regionummer')

        # voorkom 404 voor leden in de administratieve regio
        if regio_nr == 100:
            regio_nr = 101

        try:
            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie', 'regio')
                        .get(competitie=self.comp,
                             competitie__is_afgesloten=False,
                             regio__regio_nr=regio_nr))
        except Regiocompetitie.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        context['deelcomp'] = deelcomp

        comp = deelcomp.competitie
        comp.bepaal_fase()
        if comp.fase_teams > 'F':
            deelcomp.huidige_team_ronde = 8     # voorkomt kleurmarkering ronde 7 als actieve ronde

        context['toon_punten'] = (deelcomp.regio_team_punten_model != TEAM_PUNTEN_MODEL_SOM_SCORES)

        self._maak_filter_knoppen(context, regio_nr, teamtype_afkorting)
        if not context['teamtype']:
            raise Http404('Verkeerd team type')

        context['url_filters'] = reverse('CompUitslagen:uitslagen-regio-teams-n',
                                         kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url(),
                                                 'team_type': '~1',
                                                 'regio_nr': '~2'})

        # zoek alle regio teams erbij

        heeft_poules = False
        poules = (RegiocompetitieTeamPoule
                  .objects
                  .prefetch_related('teams')
                  .filter(regiocompetitie=deelcomp))

        team_pk2poule = dict()                      # [team.pk] = poule
        poule_pk2laagste_klasse_volgorde = dict()   # [team.pk] = team_klasse.volgorde
        for poule in poules:
            heeft_poules = True
            heeft_teams = False
            poule_pk2laagste_klasse_volgorde[poule.pk] = 9999

            for team in poule.teams.select_related('team_type', 'team_klasse'):
                if team.team_klasse:
                    poule_pk2laagste_klasse_volgorde[poule.pk] = min(poule_pk2laagste_klasse_volgorde[poule.pk],
                                                                     team.team_klasse.volgorde)

                if team.team_type == context['teamtype']:
                    team_pk2poule[team.pk] = poule
                    heeft_teams = True
            # for

            # alleen een poule schema maken als er teams zijn en er head-to-head wedstrijden gehouden worden
            if heeft_teams and deelcomp.regio_team_punten_model == TEAM_PUNTEN_MODEL_TWEE:
                maak_poule_schema(poule)
            else:
                poule.schema = None
        # for

        teams = (RegiocompetitieTeam
                 .objects
                 .exclude(team_klasse=None)
                 .filter(regiocompetitie=deelcomp,
                         team_type=context['teamtype'])
                 .select_related('vereniging',
                                 'team_klasse')
                 .order_by('team_klasse__volgorde'))
        pk2team = dict()
        for team in teams:
            pk2team[team.pk] = team
            team.rondes = list()
            team.ronde_scores = list()
            team.naam_str = "[%s] %s" % (team.vereniging.ver_nr, team.team_naam)
            team.totaal_score = 0
            team.totaal_punten = 0
            # team.leden_lijst = dict()     # [deelnemer.pk] = [ronde status, ..]
        # for

        ronde_teams = (RegiocompetitieRondeTeam
                       .objects
                       .filter(team__in=teams)
                       .prefetch_related('deelnemers_geselecteerd',
                                         'deelnemers_feitelijk')
                       .select_related('team')
                       .order_by('ronde_nr'))
        for ronde_team in ronde_teams:
            team = pk2team[ronde_team.team.pk]
            team.rondes.append(ronde_team)

            if ronde_team.ronde_nr < deelcomp.huidige_team_ronde:
                tup = (ronde_team.team_score, ronde_team.team_punten)
            else:
                tup = (ronde_team.team_score, -1)

            team.ronde_scores.append(tup)
            team.totaal_score += ronde_team.team_score
            team.totaal_punten += ronde_team.team_punten
        # for

        # sorteer de teams
        unsorted_teams = list()
        for team in teams:
            try:
                poule = team_pk2poule[team.pk]
            except KeyError:
                # team is niet in een poule geplaatst
                # laat deze voorlopig uit de uitslag
                pass
            else:
                tup = (poule_pk2laagste_klasse_volgorde[poule.pk], team.team_klasse.volgorde, poule.pk,
                       0-team.totaal_punten,        # hoogste WP bovenaan
                       0-team.totaal_score,         # hoogste score bovenaan
                       team.pk, poule, team)

                filler = ('-', -1)
                while len(team.ronde_scores) < 7:
                    team.ronde_scores.append(filler)

                unsorted_teams.append(tup)
        # for
        unsorted_teams.sort()

        context['teams'] = teams = list()
        prev_klasse = None
        prev_poule = None
        rank = 0
        aantal_team = None
        for tup in unsorted_teams:
            poule = tup[-2]
            team = tup[-1]

            if heeft_poules:
                if poule != prev_poule:
                    team.break_poule = True
                    team.poule_str = poule.beschrijving
                    if prev_poule:
                        team.schema = prev_poule.schema
                        teams[-1].onderrand = True
                    prev_poule = poule
                    prev_klasse = None

            if team.team_klasse != prev_klasse:
                team.break_klasse = True
                team.klasse_str = team.team_klasse.beschrijving
                team.klasse_hashtag = make_valid_hashtag(team.klasse_str)
                team.aantal_in_groep = 3        # inclusief afsluitende blauwe regel
                aantal_team = team
                if prev_klasse:
                    teams[-1].onderrand = True
                prev_klasse = team.team_klasse
                rank = 1
            else:
                rank += 1
                aantal_team.aantal_in_groep += 1

            team.rank = rank
            teams.append(team)
        # for

        if prev_poule:
            teams[-1].onderrand = True
            afsluiter = SimpleNamespace(
                            is_afsluiter=True,
                            break_poule=True,
                            schema=prev_poule.schema)
            teams.append(afsluiter)

        context['canonical'] = reverse('CompUitslagen:uitslagen-regio-teams',       # TODO: keep?
                                       kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url(),
                                               'team_type': teamtype_afkorting})

        context['robots'] = 'nofollow'   # prevent crawling filter result pages

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('Competitie:overzicht', kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url()}),
                comp.beschrijving.replace(' competitie', '')),
            (None, 'Regio teams')
        )

        return context


# end of file
