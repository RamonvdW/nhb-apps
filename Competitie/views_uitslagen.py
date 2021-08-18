# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import TemplateView
from django.urls import reverse
from django.http import Http404
from BasisTypen.models import BoogType, TeamType
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging
from Competitie.models import (LAAG_REGIO, LAAG_RK, LAAG_BK, DEELNAME_NEE, TEAM_PUNTEN_MODEL_TWEE,
                               DeelCompetitie, DeelcompetitieKlasseLimiet,
                               RegiocompetitieTeamPoule, RegiocompetitieTeam, RegiocompetitieRondeTeam,
                               RegioCompetitieSchutterBoog, KampioenschapSchutterBoog)
from Competitie.operations.poules import maak_poule_schema
from Competitie.menu import menu_dynamics_competitie
from Functie.rol import Rollen, rol_get_huidige_functie, rol_get_huidige
from .models import Competitie
from types import SimpleNamespace


TEMPLATE_COMPETITIE_UITSLAGEN_VERENIGING_INDIV = 'competitie/uitslagen-vereniging-indiv.dtl'
TEMPLATE_COMPETITIE_UITSLAGEN_VERENIGING_TEAMS = 'competitie/uitslagen-vereniging-teams.dtl'
TEMPLATE_COMPETITIE_UITSLAGEN_REGIO_INDIV = 'competitie/uitslagen-regio-indiv.dtl'
TEMPLATE_COMPETITIE_UITSLAGEN_REGIO_TEAMS = 'competitie/uitslagen-regio-teams.dtl'
TEMPLATE_COMPETITIE_UITSLAGEN_RAYON_INDIV = 'competitie/uitslagen-rayon-indiv.dtl'
TEMPLATE_COMPETITIE_UITSLAGEN_BOND = 'competitie/uitslagen-bond.dtl'


def get_schutter_regio_nr(request):
    """ Geeft het regio nummer van de ingelogde schutter terug,
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
    elif rol_nu == Rollen.ROL_SCHUTTER:
        # schutter
        account = request.user
        if account.nhblid_set.count() > 0:
            nhblid = account.nhblid_set.all()[0]
            if nhblid.is_actief_lid and nhblid.bij_vereniging:
                nhb_ver = nhblid.bij_vereniging
                regio_nr = nhb_ver.regio.regio_nr

    return regio_nr


def get_schutter_ver_nr(request):

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
            if account.nhblid_set.count() > 0:
                nhblid = account.nhblid_set.all()[0]
                if nhblid.is_actief_lid and nhblid.bij_vereniging:
                    ver_nr = nhblid.bij_vereniging.ver_nr

    ver_nrs = list(NhbVereniging.objects.order_by('ver_nr').values_list('ver_nr', flat=True))
    if ver_nr not in ver_nrs:
        ver_nr = ver_nrs[0]

    return ver_nr


class UitslagenVerenigingIndivView(TemplateView):

    """ Django class-based view voor de de uitslagen van de competitie """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_UITSLAGEN_VERENIGING_INDIV

    @staticmethod
    def _maak_filter_knoppen(context, comp, ver_nr, comp_boog):
        """ filter knoppen per regio, gegroepeerd per rayon en per competitie boog type """

        # boogtype files
        boogtypen = BoogType.objects.order_by('volgorde').all()

        context['comp_boog'] = None
        context['boog_filters'] = boogtypen

        for boogtype in boogtypen:
            if boogtype.afkorting.upper() == comp_boog.upper():
                context['comp_boog'] = boogtype
                comp_boog = boogtype.afkorting.lower()
                # geen url --> knop disabled
            else:
                boogtype.zoom_url = reverse('Competitie:uitslagen-vereniging-indiv-n',
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
                             competitie__is_afgesloten=False,       # TODO: waarom hier opeens filteren?
                             nhb_regio__regio_nr=regio_nr))
        except DeelCompetitie.DoesNotExist:     # pragma: no cover
            raise Http404('Competitie niet gevonden')

        return deelcomp

    @staticmethod
    def _get_deelnemers(deelcomp, boogtype, ver_nr):
        deelnemers = (RegioCompetitieSchutterBoog
                      .objects
                      .select_related('schutterboog',
                                      'schutterboog__nhblid',
                                      'klasse',
                                      'klasse__indiv',
                                      'klasse__indiv__boogtype')
                      .filter(deelcompetitie=deelcomp,
                              bij_vereniging__ver_nr=ver_nr,
                              klasse__indiv__boogtype=boogtype)
                      .order_by('-gemiddelde'))

        rank = 1
        for deelnemer in deelnemers:
            lid = deelnemer.schutterboog.nhblid
            deelnemer.rank = rank
            deelnemer.naam_str = "[%s] %s" % (lid.nhb_nr, lid.volledige_naam())
            deelnemer.klasse_str = deelnemer.klasse.indiv.beschrijving
            rank += 1
        # for

        return deelnemers

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen geeft beveiliging
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        context['comp'] = comp

        comp_boog = kwargs['comp_boog'][:2]     # afkappen voor veiligheid

        # ver_nr is optioneel en resulteert in het nummer van de schutter
        try:
            ver_nr = kwargs['ver_nr'][:4]     # afkappen voor veiligheid
            ver_nr = int(ver_nr)
        except KeyError:
            # zoek de vereniging die bij de huidige gebruiker past
            ver_nr = get_schutter_ver_nr(self.request)
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
        context['url_terug'] = reverse('Competitie:uitslagen-regio-indiv-n',
                                       kwargs={'comp_pk': comp.pk,
                                               'zes_scores': 'alle',
                                               'comp_boog': comp_boog,
                                               'regio_nr': regio_nr})

        context['deelcomp'] = deelcomp = self._get_deelcomp(comp, regio_nr)

        context['deelnemers'] = deelnemers = self._get_deelnemers(deelcomp, boogtype, ver_nr)
        context['aantal_deelnemers'] = len(deelnemers)

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return context


class UitslagenRegioIndivView(TemplateView):

    """ Django class-based view voor de de individuele uitslagen van de competitie in 1 regio """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_UITSLAGEN_REGIO_INDIV
    url_name = 'Competitie:uitslagen-regio-indiv-n'
    order_gemiddelde = '-gemiddelde'

    def _maak_filter_knoppen(self, context, comp, gekozen_regio_nr, comp_boog, zes_scores):
        """ filter knoppen per regio, gegroepeerd per rayon en per competitie boog type """

        # boogtype files
        boogtypen = BoogType.objects.order_by('volgorde').all()

        context['comp_boog'] = None
        context['boog_filters'] = boogtypen

        for boogtype in boogtypen:
            if boogtype.afkorting.upper() == comp_boog.upper():
                context['comp_boog'] = boogtype
                comp_boog = boogtype.afkorting.lower()
                # geen url --> knop disabled
            else:
                boogtype.zoom_url = reverse(self.url_name,
                                            kwargs={'comp_pk': comp.pk,
                                                    'zes_scores': zes_scores,
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
                regio.break_before = (prev_rayon != regio.rayon.rayon_nr)
                prev_rayon = regio.rayon.rayon_nr

                regio.title_str = 'Regio %s' % regio.regio_nr
                if regio.regio_nr != gekozen_regio_nr:
                    regio.zoom_url = reverse(self.url_name,
                                             kwargs={'comp_pk': comp.pk,
                                                     'zes_scores': zes_scores,
                                                     'comp_boog': comp_boog,
                                                     'regio_nr': regio.regio_nr})
                else:
                    # geen zoom_url --> knop disabled
                    context['regio'] = regio
            # for

        # vereniging filters
        if context['comp_boog']:
            vers = (NhbVereniging
                    .objects
                    .select_related('regio')
                    .filter(regio__regio_nr=gekozen_regio_nr)
                    .order_by('ver_nr'))

            for ver in vers:
                ver.zoom_url = reverse('Competitie:uitslagen-vereniging-indiv-n',
                                       kwargs={'comp_pk': comp.pk,
                                               'comp_boog': comp_boog,
                                               'ver_nr': ver.ver_nr})
            # for

            context['ver_filters'] = vers

        context['zes_scores_checked'] = (zes_scores == 'zes')
        if zes_scores == 'alle':
            zes_scores_next = 'zes'
        else:
            zes_scores_next = 'alle'
        context['zes_scores_next'] = reverse(self.url_name,
                                             kwargs={'comp_pk': comp.pk,
                                                     'zes_scores': zes_scores_next,
                                                     'comp_boog': comp_boog,
                                                     'regio_nr': gekozen_regio_nr})

    @staticmethod
    def filter_zes_scores(deelnemers):
        return deelnemers.filter(aantal_scores__gte=6)

    @staticmethod
    def _split_aspiranten(asps, objs):
        klasse_str = asps[0].klasse_str
        rank_m = 0
        rank_v = 0
        asps_v = list()
        for deelnemer in asps:
            if deelnemer.schutterboog.nhblid.geslacht == 'V':
                if rank_v == 0:
                    deelnemer.klasse_str = klasse_str + ', meisjes'
                    deelnemer.break_klasse = True
                rank_v += 1
                deelnemer.rank = rank_v
                asps_v.append(deelnemer)
            else:
                if rank_m == 0:
                    deelnemer.klasse_str = klasse_str + ', jongens'
                    deelnemer.break_klasse = True
                rank_m += 1
                deelnemer.rank = rank_m
                objs.append(deelnemer)
        # for
        if len(asps_v):
            objs.extend(asps_v)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen geeft beveiliging
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        context['comp'] = comp

        zes_scores = kwargs['zes_scores']
        if zes_scores not in ('alle', 'zes'):
            zes_scores = 'alle'

        comp_boog = kwargs['comp_boog'][:2]     # afkappen voor veiligheid

        # regio_nr is optioneel (eerste binnenkomst zonder regio nummer)
        try:
            regio_nr = kwargs['regio_nr'][:3]   # afkappen voor veiligheid
            regio_nr = int(regio_nr)
        except KeyError:
            # bepaal welke (initiële) regio bij de huidige gebruiker past
            regio_nr = get_schutter_regio_nr(self.request)
        except ValueError:
            raise Http404('Verkeer regionummer')

        # voorkom 404 voor leden in de administratieve regio
        if regio_nr == 100:
            regio_nr = 101

        try:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_regio')
                        .get(laag=LAAG_REGIO,
                             competitie=comp,
                             competitie__is_afgesloten=False,
                             nhb_regio__regio_nr=regio_nr))
        except DeelCompetitie.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        context['deelcomp'] = deelcomp

        self._maak_filter_knoppen(context, comp, regio_nr, comp_boog, zes_scores)

        boogtype = context['comp_boog']
        if not boogtype:
            raise Http404('Boogtype niet bekend')

        deelnemers = (RegioCompetitieSchutterBoog
                      .objects
                      .filter(deelcompetitie=deelcomp)
                      .select_related('schutterboog',
                                      'schutterboog__nhblid',
                                      'bij_vereniging',
                                      'klasse',
                                      'klasse__indiv',
                                      'klasse__indiv__boogtype')
                      .filter(klasse__indiv__boogtype=boogtype)
                      .order_by('klasse__indiv__volgorde', self.order_gemiddelde))

        if zes_scores == 'zes':
            deelnemers = self.filter_zes_scores(deelnemers)

        klasse = -1
        rank = 0
        objs = list()
        asps = list()
        is_asp = False
        for deelnemer in deelnemers:

            deelnemer.break_klasse = (klasse != deelnemer.klasse.indiv.volgorde)
            if deelnemer.break_klasse:
                if len(asps):
                    self._split_aspiranten(asps, objs)
                    asps = list()

                deelnemer.klasse_str = deelnemer.klasse.indiv.beschrijving
                is_asp = False
                if deelnemer.klasse.indiv.niet_voor_rk_bk:
                    # dit is een aspiranten klassen of een klasse onbekend
                    for lkl in deelnemer.klasse.indiv.leeftijdsklassen.all():
                        if lkl.is_aspirant_klasse():
                            is_asp = True
                            break
                    # for

                rank = 0
            klasse = deelnemer.klasse.indiv.volgorde

            rank += 1
            lid = deelnemer.schutterboog.nhblid
            deelnemer.rank = rank
            deelnemer.naam_str = "[%s] %s" % (lid.nhb_nr, lid.volledige_naam())
            deelnemer.ver_str = str(deelnemer.bij_vereniging)

            if is_asp:
                asps.append(deelnemer)
            else:
                objs.append(deelnemer)
        # for

        if len(asps):
            # aspiranten opsplitsen in jongens en meisjes klasse
            self._split_aspiranten(asps, objs)

        context['deelnemers'] = objs

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return context


class UitslagenRegioTeamsView(TemplateView):

    """ Django class-based view voor de de team uitslagen van de competitie in 1 regio """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_UITSLAGEN_REGIO_TEAMS
    url_name = 'Competitie:uitslagen-regio-teams-n'

    def _maak_filter_knoppen(self, context, comp, gekozen_regio_nr, teamtype_afkorting):
        """ filter knoppen per regio, gegroepeerd per rayon en per competitie boog type """

        teamtypen = TeamType.objects.order_by('volgorde').all()

        context['teamtype'] = None
        context['teamtype_filters'] = teamtypen

        for team in teamtypen:
            if team.afkorting.upper() == teamtype_afkorting.upper():
                context['teamtype'] = team
                teamtype_afkorting = team.afkorting.lower()
                # geen url --> knop disabled
            else:
                team.zoom_url = reverse(self.url_name,
                                        kwargs={'comp_pk': comp.pk,
                                                'team_type': team.afkorting.lower(),
                                                'regio_nr': gekozen_regio_nr})
        # for

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

                regio.title_str = 'Regio %s' % regio.regio_nr
                if regio.regio_nr != gekozen_regio_nr:
                    regio.zoom_url = reverse(self.url_name,
                                             kwargs={'comp_pk': comp.pk,
                                                     'team_type': teamtype_afkorting,
                                                     'regio_nr': regio.regio_nr})
                else:
                    # geen zoom_url --> knop disabled
                    context['regio'] = regio
            # for

        # vereniging filters
        if context['teamtype']:
            ver_nrs = list()
            vers = list()
            for team in (RegiocompetitieTeam
                         .objects
                         .filter(deelcompetitie__competitie=comp,
                                 vereniging__regio__regio_nr=gekozen_regio_nr)
                         .order_by('vereniging__ver_nr')):
                if team.vereniging.ver_nr not in ver_nrs:
                    ver_nrs.append(team.vereniging.ver_nr)
                    vers.append(team.vereniging)
            # for

            if len(vers):
                for ver in vers:
                    ver.zoom_url = reverse('Competitie:uitslagen-vereniging-teams-n',
                                           kwargs={'comp_pk': comp.pk,
                                                   'team_type': context['teamtype'].afkorting.lower(),
                                                   'ver_nr': ver.ver_nr})
                # for

                context['ver_filters'] = vers

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen geeft beveiliging
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        context['comp'] = comp

        teamtype_afkorting = kwargs['team_type'][:2]     # afkappen voor veiligheid

        # regio_nr is optioneel (eerste binnenkomst zonder regio nummer)
        try:
            regio_nr = kwargs['regio_nr'][:3]   # afkappen voor veiligheid
            regio_nr = int(regio_nr)
        except KeyError:
            # bepaal welke (initiële) regio bij de huidige gebruiker past
            regio_nr = get_schutter_regio_nr(self.request)
        except ValueError:
            raise Http404('Verkeer regionummer')

        # voorkom 404 voor leden in de administratieve regio
        if regio_nr == 100:
            regio_nr = 101

        try:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_regio')
                        .get(laag=LAAG_REGIO,
                             competitie=comp,
                             competitie__is_afgesloten=False,
                             nhb_regio__regio_nr=regio_nr))
        except DeelCompetitie.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        context['deelcomp'] = deelcomp

        self._maak_filter_knoppen(context, comp, regio_nr, teamtype_afkorting)
        if not context['teamtype']:
            raise Http404('Verkeerd team type')

        # zoek alle regio teams erbij

        heeft_poules = False
        poules = (RegiocompetitieTeamPoule
                  .objects
                  .prefetch_related('teams')
                  .filter(deelcompetitie=deelcomp))

        team_pk2poule = dict()
        for poule in poules:
            heeft_poules = True
            heeft_teams = False

            for team in poule.teams.order_by('pk'):
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
                 .exclude(klasse=None)
                 .filter(deelcompetitie=deelcomp,
                         team_type=context['teamtype'])
                 .select_related('vereniging')
                 .order_by('klasse__team__volgorde'))
        pk2team = dict()
        for team in teams:
            pk2team[team.pk] = team
            team.rondes = list()
            team.ronde_scores = list()
            team.naam_str = "[%s] %s" % (team.vereniging.ver_nr, team.team_naam)
            team.totaal_score = 0
            team.totaal_punten = 0
            team.leden = dict()     # [deelnemer.pk] = [ronde status, ..]
        # for

        ronde_teams = (RegiocompetitieRondeTeam
                       .objects
                       .filter(team__in=teams)
                       .prefetch_related('deelnemers_geselecteerd',
                                         'deelnemers_feitelijk')
                       .order_by('ronde_nr'))
        for ronde_team in ronde_teams:
            team = pk2team[ronde_team.team.pk]
            team.rondes.append(ronde_team)
            team.ronde_scores.append(ronde_team.team_score)
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
                tup = (poule.pk, team.klasse.team.volgorde, team.totaal_punten, team.totaal_score, team.pk, poule, team)

                while len(team.ronde_scores) < 7:
                    team.ronde_scores.append('-')

                unsorted_teams.append(tup)
        # for
        unsorted_teams.sort()

        context['teams'] = teams = list()
        prev_klasse = None
        prev_poule = None
        rank = 0
        for tup in unsorted_teams:
            poule = tup[-2]
            team = tup[-1]

            if heeft_poules:
                if poule != prev_poule:
                    team.break_poule = True
                    team.poule_str = poule.beschrijving
                    if prev_poule:
                        team.schema = prev_poule.schema
                    prev_poule = poule

            if team.klasse != prev_klasse:
                team.break_klasse = True
                team.klasse_str = team.klasse.team.beschrijving
                prev_klasse = team.klasse
                rank = 1
            else:
                rank += 1

            team.rank = rank
            teams.append(team)
        # for

        if prev_poule:
            afsluiter = SimpleNamespace(
                            is_afsluiter=True,
                            break_poule=True,
                            schema=prev_poule.schema)
            teams.append(afsluiter)

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return context


class UitslagenVerenigingTeamsView(TemplateView):

    """ Django class-based view voor de de uitslagen van de teamcompetitie voor een specifieke vereniging """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_UITSLAGEN_VERENIGING_TEAMS

    @staticmethod
    def _maak_filter_knoppen(context, comp, ver_nr, teamtype_afkorting):
        """ filter knoppen voor de vereniging """

        teamtypen = TeamType.objects.order_by('volgorde').all()

        context['teamtype'] = None
        context['teamtype_filters'] = teamtypen

        for team in teamtypen:
            if team.afkorting.upper() == teamtype_afkorting.upper():
                context['teamtype'] = team
                teamtype_afkorting = team.afkorting.lower()
                # geen url --> knop disabled
            else:
                team.zoom_url = reverse('Competitie:uitslagen-vereniging-teams-n',
                                        kwargs={'comp_pk': comp.pk,
                                                'team_type': team.afkorting.lower(),
                                                'ver_nr': ver_nr})
        # for

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen geeft beveiliging
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        context['comp'] = comp

        teamtype_afkorting = kwargs['team_type'][:2]     # afkappen voor veiligheid

        # ver_nr is optioneel en resulteert in het nummer van de schutter
        try:
            ver_nr = kwargs['ver_nr'][:4]     # afkappen voor veiligheid
            ver_nr = int(ver_nr)
        except KeyError:
            # zoek de vereniging die bij de huidige gebruiker past
            ver_nr = get_schutter_ver_nr(self.request)
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
        context['url_terug'] = reverse('Competitie:uitslagen-regio-teams-n',
                                       kwargs={'comp_pk': comp.pk,
                                               'team_type': teamtype.afkorting.lower(),
                                               'regio_nr': regio_nr})

        context['deelcomp'] = DeelCompetitie.objects.get(competitie=comp, nhb_regio=ver.regio)

        # zoek alle verenigingsteams erbij
        teams = (RegiocompetitieTeam
                 .objects
                 .exclude(klasse=None)
                 .filter(deelcompetitie__competitie=comp,
                         team_type=context['teamtype'],
                         vereniging=ver)
                 .order_by('klasse__team__volgorde'))

        pk2team = dict()
        for team in teams:
            pk2team[team.pk] = team
            team.rondes = list()
            team.ronde_scores = list()
            team.naam_str = "[%s] %s" % (team.vereniging.ver_nr, team.team_naam)
            team.totaal_score = 0
            team.totaal_punten = 0
            team.leden = dict()     # [deelnemer.pk] = [ronde status, ..]
        # for

        ronde_teams = (RegiocompetitieRondeTeam
                       .objects
                       .filter(team__in=teams)
                       .prefetch_related('deelnemers_geselecteerd',
                                         'deelnemers_feitelijk')
                       .order_by('ronde_nr'))
        for ronde_team in ronde_teams:
            team = pk2team[ronde_team.team.pk]
            team.rondes.append(ronde_team)
            team.ronde_scores.append(ronde_team.team_score)
            team.totaal_score += ronde_team.team_score
            team.totaal_punten += ronde_team.team_punten

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
                if deelnemer.pk not in team.leden:
                    team.leden[deelnemer.pk] = voorgaand = list()
                    while len(voorgaand) < ronde_team.ronde_nr:
                        inzet = SimpleNamespace(tekst='-', score=-1)
                        voorgaand.append(inzet)
                    # while
                else:
                    voorgaand = team.leden[deelnemer.pk]

                score = (deelnemer.score1, deelnemer.score2, deelnemer.score3,
                         deelnemer.score4, deelnemer.score5, deelnemer.score6, deelnemer.score7)[ronde_team.ronde_nr - 1]

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
                          .select_related('schutterboog',
                                          'schutterboog__nhblid')
                          .filter(pk__in=pks)):
            pk2deelnemer[deelnemer.pk] = deelnemer
        # for

        for team in teams:
            # TODO: we kunnen de leden hier nog wat sorteren, bijvoorbeeld op score of aantal keer in team

            nieuw = list()
            for pk, voorgaand in team.leden.items():
                deelnemer = pk2deelnemer[pk]
                lid = deelnemer.schutterboog.nhblid
                deelnemer.naam_str = "[%s] %s" % (lid.nhb_nr, lid.volledige_naam())
                tup = (deelnemer, voorgaand[1:])
                nieuw.append(tup)
            # for

            team.leden = nieuw
        # for

        # sorteer de teams
        unsorted_teams = list()
        for team in teams:
            # TODO: zou moeten sorteren op team klasse volgorde, niet punten of score
            tup = (team.klasse.team.volgorde, team.totaal_punten, team.totaal_score, team.pk, team)

            while len(team.ronde_scores) < 7:
                team.ronde_scores.append('-')

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

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return context


class UitslagenRayonIndivView(TemplateView):

    """ Django class-based view voor de de uitslagen van de rayonkampioenschappen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_UITSLAGEN_RAYON_INDIV

    @staticmethod
    def _maak_filter_knoppen(context, comp, gekozen_rayon_nr, comp_boog):
        """ filter knoppen per rayon en per competitie boog type """

        # boogtype files
        boogtypen = BoogType.objects.order_by('volgorde').all()

        context['comp_boog'] = None
        context['boog_filters'] = boogtypen

        for boogtype in boogtypen:
            if boogtype.afkorting.upper() == comp_boog.upper():
                context['comp_boog'] = boogtype
                comp_boog = boogtype.afkorting.lower()
                # geen url --> knop disabled
            else:
                boogtype.zoom_url = reverse('Competitie:uitslagen-rayon-indiv-n',
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
                if rayon.rayon_nr != gekozen_rayon_nr:
                    rayon.zoom_url = reverse('Competitie:uitslagen-rayon-indiv-n',
                                             kwargs={'comp_pk': comp.pk,
                                                     'comp_boog': comp_boog,
                                                     'rayon_nr': rayon.rayon_nr})
                else:
                    # geen zoom_url --> knop disabled
                    context['rayon'] = rayon
            # for

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen geeft beveiliging
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        context['comp'] = comp

        comp_boog = kwargs['comp_boog'][:2]          # afkappen voor veiligheid

        # rayon_nr is optioneel (eerste binnenkomst zonder rayon nummer)
        try:
            rayon_nr = kwargs['rayon_nr'][:2]        # afkappen voor veiligheid
            rayon_nr = int(rayon_nr)
        except KeyError:
            rayon_nr = 1
        except ValueError:
            raise Http404('Verkeer rayonnummer')

        self._maak_filter_knoppen(context, comp, rayon_nr, comp_boog)

        boogtype = context['comp_boog']
        if not boogtype:
            raise Http404('Boogtype niet bekend')

        try:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_rayon')
                        .get(laag=LAAG_RK,
                             competitie__is_afgesloten=False,
                             competitie=comp,
                             nhb_rayon__rayon_nr=rayon_nr))
        except DeelCompetitie.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        context['deelcomp'] = deelcomp
        deelcomp.competitie.bepaal_fase()

        wkl2limiet = dict()    # [pk] = aantal

        if deelcomp.heeft_deelnemerslijst:
            # deelnemers/reserveschutters van het RK tonen
            deelnemers = (KampioenschapSchutterBoog
                          .objects
                          .exclude(bij_vereniging__isnull=True,      # attentie gevallen
                                   deelname=DEELNAME_NEE)            # geen schutters die zicht afgemeld hebben
                          .filter(deelcompetitie=deelcomp,
                                  klasse__indiv__boogtype=boogtype,
                                  volgorde__lte=48)                 # toon tot 48 schutters per klasse
                          .select_related('klasse__indiv',
                                          'schutterboog__nhblid',
                                          'bij_vereniging')
                          .order_by('klasse__indiv__volgorde',
                                    'volgorde'))

            for limiet in (DeelcompetitieKlasseLimiet
                           .objects
                           .select_related('klasse')
                           .filter(deelcompetitie=deelcomp)):
                wkl2limiet[limiet.klasse.pk] = limiet.limiet
            # for

            context['is_lijst_rk'] = True
        else:
            # competitie is nog in de regiocompetitie fase
            context['regiocomp_nog_actief'] = True

            # schutter moeten uit LAAG_REGIO gehaald worden, uit de 4 regio's van het rayon
            deelcomp_pks = (DeelCompetitie
                            .objects
                            .filter(laag=LAAG_REGIO,
                                    competitie__is_afgesloten=False,
                                    competitie=comp,
                                    nhb_regio__rayon__rayon_nr=rayon_nr)
                            .values_list('pk', flat=True))

            deelnemers = (RegioCompetitieSchutterBoog
                          .objects
                          .filter(deelcompetitie__pk__in=deelcomp_pks,
                                  klasse__indiv__boogtype=boogtype,
                                  aantal_scores__gte=6)
                          .select_related('klasse__indiv',
                                          'schutterboog__nhblid',
                                          'schutterboog__nhblid__bij_vereniging',
                                          'bij_vereniging')
                          .order_by('klasse__indiv__volgorde', '-gemiddelde'))

        klasse = -1
        rank = 0
        limiet = 24
        for deelnemer in deelnemers:
            deelnemer.break_klasse = (klasse != deelnemer.klasse.indiv.volgorde)
            if deelnemer.break_klasse:
                deelnemer.klasse_str = deelnemer.klasse.indiv.beschrijving
                rank = 1
                try:
                    limiet = wkl2limiet[deelnemer.klasse.pk]
                except KeyError:
                    limiet = 24
            klasse = deelnemer.klasse.indiv.volgorde

            lid = deelnemer.schutterboog.nhblid
            deelnemer.naam_str = "[%s] %s" % (lid.nhb_nr, lid.volledige_naam())
            deelnemer.ver_str = str(deelnemer.bij_vereniging)

            deelnemer.geen_deelname_risico = deelnemer.schutterboog.nhblid.bij_vereniging != deelnemer.bij_vereniging

            if deelcomp.heeft_deelnemerslijst:
                if deelnemer.rank > limiet:
                    deelnemer.is_reserve = True
            else:
                deelnemer.rank = rank
                rank += 1
        # for

        context['deelnemers'] = deelnemers

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return context


class UitslagenBondView(TemplateView):

    """ Django class-based view voor de de uitslagen van de bondskampioenschappen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_UITSLAGEN_BOND

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen geeft beveiliging
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        context['comp'] = comp

        comp_boog = kwargs['comp_boog'][:2]          # afkappen voor veiligheid

        try:
           deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(laag=LAAG_BK,
                             competitie__is_afgesloten=False,
                             competitie__pk=comp_pk))
        except DeelCompetitie.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return context


# end of file
