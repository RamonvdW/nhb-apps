# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import TemplateView
from django.urls import reverse
from django.http import Http404
from Competitie.definities import TEAM_PUNTEN_MODEL_TWEE, TEAM_PUNTEN_MODEL_SOM_SCORES
from Competitie.models import (Competitie, Regiocompetitie,
                               RegiocompetitieTeamPoule, RegiocompetitieTeam, RegiocompetitieRondeTeam,
                               RegiocompetitieSporterBoog)
from Competitie.operations.poules import maak_poule_schema
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Plein.menu import menu_dynamics
from types import SimpleNamespace


TEMPLATE_COMPUITSLAGEN_REGIO_INDIV = 'compuitslagen/uitslagen-regio-indiv.dtl'
TEMPLATE_COMPUITSLAGEN_REGIO_TEAMS = 'compuitslagen/uitslagen-regio-teams.dtl'


def get_request_regio_nr(request):
    """ Geeft het regionummer van de ingelogde sporter terug,
        of 101 als er geen regio vastgesteld kan worden
    """
    regio_nr = 101

    rol_nu, functie_nu = rol_get_huidige_functie(request)

    if functie_nu:
        if functie_nu.nhb_ver:
            # HWL, WL
            regio_nr = functie_nu.nhb_ver.regio.regio_nr
        elif functie_nu.nhb_regio:
            # RCL
            regio_nr = functie_nu.nhb_regio.regio_nr
        elif functie_nu.nhb_rayon:
            # RKO
            regio = (NhbRegio
                     .objects
                     .filter(rayon=functie_nu.nhb_rayon,
                             is_administratief=False)
                     .order_by('regio_nr'))[0]
            regio_nr = regio.regio_nr
    elif rol_nu == Rollen.ROL_SPORTER:
        # sporter
        account = request.user
        if account.sporter_set.count() > 0:         # pragma: no branch
            sporter = account.sporter_set.select_related('bij_vereniging__regio').all()[0]
            if sporter.is_actief_lid and sporter.bij_vereniging:
                nhb_ver = sporter.bij_vereniging
                regio_nr = nhb_ver.regio.regio_nr

    return regio_nr


class UitslagenRegioIndivView(TemplateView):

    """ Django class-based view voor de individuele uitslagen van de competitie in 1 regio """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_REGIO_INDIV
    url_name = 'CompUitslagen:uitslagen-regio-indiv-n'

    def _maak_filter_knoppen(self, context, comp, gekozen_regio_nr, comp_boog):
        """ filter optie voor de regio """

        # boogtype filters
        boogtypen = comp.boogtypen.order_by('volgorde')

        context['comp_boog'] = None
        context['boog_filters'] = boogtypen

        for boogtype in boogtypen:
            boogtype.sel = 'boog_' + boogtype.afkorting
            if boogtype.afkorting.upper() == comp_boog.upper():
                context['comp_boog'] = boogtype
                comp_boog = boogtype.afkorting.lower()
                # geen url --> knop disabled
                boogtype.selected = True

            boogtype.zoom_url = reverse(self.url_name,
                                        kwargs={'comp_pk': comp.pk,
                                                'comp_boog': boogtype.afkorting.lower(),
                                                'regio_nr': gekozen_regio_nr})
        # for

        # regio filters
        if context['comp_boog']:
            regios = (NhbRegio
                      .objects
                      .select_related('rayon')
                      .filter(is_administratief=False)
                      .order_by('rayon__rayon_nr', 'regio_nr'))

            context['regio_filters'] = regios

            prev_rayon = 1
            for regio in regios:
                regio.sel = 'regio_%s' % regio.regio_nr
                regio.break_before = (prev_rayon != regio.rayon.rayon_nr)
                prev_rayon = regio.rayon.rayon_nr

                regio.title_str = 'Regio %s' % regio.regio_nr
                if regio.regio_nr == gekozen_regio_nr:
                    context['regio'] = regio
                    regio.selected = True

                regio.zoom_url = reverse(self.url_name,
                                         kwargs={'comp_pk': comp.pk,
                                                 'comp_boog': comp_boog,
                                                 'regio_nr': regio.regio_nr})
            # for

        # vereniging filters
        if context['comp_boog']:
            vers = (NhbVereniging
                    .objects
                    .select_related('regio')
                    .filter(regio__regio_nr=gekozen_regio_nr)
                    .order_by('ver_nr'))

            for ver in vers:
                ver.sel = 'ver_%s' % ver.ver_nr
                ver.zoom_url = reverse('CompUitslagen:uitslagen-vereniging-indiv-n',
                                       kwargs={'comp_pk': comp.pk,
                                               'comp_boog': comp_boog,
                                               'ver_nr': ver.ver_nr})
            # for

            context['ver_filters'] = vers

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

        # regio_nr is optioneel (eerste binnenkomst zonder regio nummer)
        try:
            regio_nr = kwargs['regio_nr'][:3]   # afkappen voor de veiligheid
            regio_nr = int(regio_nr)
        except KeyError:
            # bepaal welke (initiële) regio bij de huidige gebruiker past
            regio_nr = get_request_regio_nr(self.request)
        except ValueError:
            raise Http404('Verkeerde regionummer')

        # voorkom 404 voor leden in de administratieve regio
        if regio_nr == 100:
            regio_nr = 101

        try:
            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie',
                                        'nhb_regio')
                        .get(competitie=comp,
                             competitie__is_afgesloten=False,
                             nhb_regio__regio_nr=regio_nr))
        except Regiocompetitie.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        context['deelcomp'] = deelcomp

        self._maak_filter_knoppen(context, comp, regio_nr, comp_boog)

        boogtype = context['comp_boog']
        if not boogtype:
            raise Http404('Boogtype niet bekend')

        deelnemers = (RegiocompetitieSporterBoog
                      .objects
                      .filter(regiocompetitie=deelcomp)
                      .select_related('sporterboog__sporter',
                                      'bij_vereniging',
                                      'indiv_klasse__boogtype')
                      .filter(indiv_klasse__boogtype=boogtype)
                      .order_by('indiv_klasse__volgorde',
                                '-gemiddelde'))

        klasse = -1
        rank = 0
        objs = list()
        deelnemer_count = None
        for deelnemer in deelnemers:

            deelnemer.break_klasse = (klasse != deelnemer.indiv_klasse.volgorde)
            if deelnemer.break_klasse:
                deelnemer_count = deelnemer
                deelnemer.aantal_in_groep = 2   # 1 extra zodat balk doorloopt tot horizontale afsluiter
                deelnemer.is_eerste_groep = (klasse == -1)
                deelnemer.klasse_str = deelnemer.indiv_klasse.beschrijving
                rank = 0
            klasse = deelnemer.indiv_klasse.volgorde

            rank += 1
            sporter = deelnemer.sporterboog.sporter
            deelnemer.rank = rank
            deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())
            deelnemer.ver_str = str(deelnemer.bij_vereniging)

            # in plaats van allemaal 0,000 willen we het AG tonen tijdens de inschrijffase
            if comp.fase_indiv < 'F':
                deelnemer.gemiddelde = deelnemer.ag_voor_indiv

            deelnemer_count.aantal_in_groep += 1
            objs.append(deelnemer)
        # for

        context['deelnemers'] = objs
        context['heeft_deelnemers'] = (len(objs) > 0)

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Uitslagen regio individueel')
        )

        menu_dynamics(self.request, context)
        return context


class UitslagenRegioTeamsView(TemplateView):

    """ Django class-based view voor de teamuitslagen van de competitie in 1 regio """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_REGIO_TEAMS
    url_name = 'CompUitslagen:uitslagen-regio-teams-n'

    def _maak_filter_knoppen(self, context, comp, gekozen_regio_nr, teamtype_afkorting):
        """ filter knoppen per regio, gegroepeerd per rayon en per competitie boog type """

        context['teamtype'] = None
        context['teamtype_filters'] = teamtypen = comp.teamtypen.order_by('volgorde')

        for team in teamtypen:
            team.sel = team.afkorting
            if team.afkorting.upper() == teamtype_afkorting.upper():
                context['teamtype'] = team
                teamtype_afkorting = team.afkorting.lower()
                team.selected = True

            team.zoom_url = reverse(self.url_name,
                                    kwargs={'comp_pk': comp.pk,
                                            'team_type': team.afkorting.lower(),
                                            'regio_nr': gekozen_regio_nr})
        # for

        # TODO: wanneer komt het voor dat teamtype niet bestaat? Template laat altijd regios/verenigingen zien!

        # regio filters
        if context['teamtype']:
            regios = (NhbRegio
                      .objects
                      .select_related('rayon')
                      .filter(is_administratief=False)
                      .order_by('rayon__rayon_nr', 'regio_nr'))

            context['regio_filters'] = regios

            prev_rayon = 1
            for regio in regios:
                regio.break_before = (prev_rayon != regio.rayon.rayon_nr)
                prev_rayon = regio.rayon.rayon_nr

                regio.sel = 'regio_%s' % regio.regio_nr

                regio.title_str = 'Regio %s' % regio.regio_nr
                if regio.regio_nr == gekozen_regio_nr:
                    regio.selected = True
                    context['regio'] = regio

                regio.zoom_url = reverse(self.url_name,
                                         kwargs={'comp_pk': comp.pk,
                                                 'team_type': teamtype_afkorting,
                                                 'regio_nr': regio.regio_nr})
            # for

        # vereniging filters
        if context['teamtype']:
            ver_nrs = list()
            vers = list()
            for team in (RegiocompetitieTeam
                         .objects
                         .filter(regiocompetitie__competitie=comp,
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
                                           kwargs={'comp_pk': comp.pk,
                                                   'team_type': context['teamtype'].afkorting.lower(),
                                                   'ver_nr': ver.ver_nr})
                # for

                context['ver_filters'] = vers

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
                        .select_related('competitie', 'nhb_regio')
                        .get(competitie=comp,
                             competitie__is_afgesloten=False,
                             nhb_regio__regio_nr=regio_nr))
        except Regiocompetitie.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        context['deelcomp'] = deelcomp

        comp = deelcomp.competitie
        comp.bepaal_fase()
        if comp.fase_teams > 'F':
            deelcomp.huidige_team_ronde = 8     # voorkomt kleurmarkering ronde 7 als actieve ronde

        context['toon_punten'] = (deelcomp.regio_team_punten_model != TEAM_PUNTEN_MODEL_SOM_SCORES)

        self._maak_filter_knoppen(context, comp, regio_nr, teamtype_afkorting)
        if not context['teamtype']:
            raise Http404('Verkeerd team type')

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
                tup = (poule_pk2laagste_klasse_volgorde[poule.pk], team.team_klasse.volgorde,
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

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Uitslagen regio teams')
        )

        menu_dynamics(self.request, context)
        return context


# end of file
