# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import Competitie, CompetitieMatch, update_uitslag_teamcompetitie
from CompLaagRegio.models import RegioComp, RegioRonde, RegioDeelnemer, RegioRondeTeam, RegioPoule
from Functie.definities import Rol
from Functie.rol import rol_get_huidige, rol_get_huidige_functie
from Score.definities import SCORE_WAARDE_VERWIJDERD, SCORE_TYPE_SCORE, SCORE_TYPE_GEEN
from Score.models import Score
from Sporter.models import SporterBoog
from types import SimpleNamespace
import datetime

TEMPLATE_COMPSCORES_TEAMS = 'compscores/rcl-scores-regio-teams.dtl'
TEMPLATE_COMPSCORES_TEAMS_SELECTEER = 'compscores/bko-selecteer-regio-ronde.dtl'


class TemplateScoresRegioTeamsView(TemplateView):

    """ Deze view geeft de beheerder de mogelijkheid om voor een specifieke team ronde
        de individuele scores te selecteren / koppelen aan een team.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPSCORES_TEAMS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deelcomp: RegioComp | None = None
        self.ronde_nr: int = 0

    def _bepaal_teams_en_scores(self, mag_database_wijzigen=False):

        assert isinstance(self.deelcomp, RegioComp)

        alle_regels = list()
        aantal_keuzes_nodig = 0

        # sporters waarvan we de scores op moeten zoeken
        sporterboog_pks = list()

        used_score_pks = list()

        # haal de beschikbare individuele scores op
        deelnemer2sporter_cache: dict[int, tuple[int, str]] = dict()    # [deelnemer_pk] = (sporterboog_pk, naam_str)
        sporterboog_cache: dict[int, SporterBoog] = dict()              # [sporterboog_pk] = SporterBoog
        for deelnemer in (RegioDeelnemer
                          .objects
                          .select_related('sporterboog',
                                          'sporterboog__sporter')
                          .filter(regiocomp=self.deelcomp)):

            sporterboog = deelnemer.sporterboog
            sporterboog_cache[sporterboog.pk] = sporterboog

            sporter = sporterboog.sporter
            tup = (sporterboog.pk, "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam()))
            deelnemer2sporter_cache[deelnemer.pk] = tup
        # for

        alle_sporterboog_pks = list()
        afstand = self.deelcomp.competitie.afstand

        # haal alle teams van de regio op
        for poule in (RegioPoule
                      .objects
                      .prefetch_related('teams')
                      .filter(regiocomp=self.deelcomp)
                      .order_by('beschrijving')):

            team_pks = poule.teams.values_list('pk', flat=True)

            # alle al gebruikte scores
            used_scores = list(RegioRondeTeam
                               .objects
                               .prefetch_related('scores_feitelijk')
                               .filter(team__in=team_pks)
                               .exclude(ronde_nr=self.ronde_nr)
                               .values_list('scores_feitelijk__pk', flat=True))
            used_score_pks.extend(used_scores)

            ronde_teams = (RegioRondeTeam
                           .objects
                           .select_related('team',
                                           'team__vereniging',
                                           'team__team_klasse')
                           .prefetch_related('deelnemers_feitelijk',
                                             'scores_feitelijk')
                           .filter(team__in=team_pks,
                                   ronde_nr=self.ronde_nr)
                           .order_by('team__vereniging__ver_nr',
                                     'team__volg_nr'))

            break_poule = poule.beschrijving
            prev_klasse = None
            for ronde_team in ronde_teams:

                regel = SimpleNamespace()

                regel.poule_str = break_poule
                break_poule = ""

                regel.ronde_team = ronde_team
                regel.team_str = ronde_team.team.maak_team_naam()

                klasse_str = ronde_team.team.team_klasse.beschrijving
                if klasse_str != prev_klasse:
                    regel.klasse_str = klasse_str
                    prev_klasse = klasse_str

                regel.deelnemers = list()
                for deelnemer in (ronde_team
                                  .deelnemers_feitelijk
                                  .all()):

                    try:
                        sporterboog_pk, naam_str = deelnemer2sporter_cache[deelnemer.pk]
                    except KeyError:
                        # sporter zit niet meer in de regiocompetitie
                        # dit komt (kort) voor na een overschrijving
                        # TODO: hoe verder afhandelen?
                        # TODO: sporter die overgestapt is naar andere vereniging binnen regio blijft wel zichtbaar
                        pass
                    else:
                        sporterboog_pks.append(sporterboog_pk)

                        if sporterboog_pk not in alle_sporterboog_pks:  # want deelnemer kan in meerdere teams voorkomen
                            alle_sporterboog_pks.append(sporterboog_pk)

                        deelnemer.naam_str = naam_str
                        deelnemer.sporterboog_pk = sporterboog_pk
                        deelnemer.gevonden_scores = None
                        deelnemer.kan_kiezen = False
                        deelnemer.keuze_nodig = False
                        regel.deelnemers.append(deelnemer)
                # for

                regel.score_pks_feitelijk = list(ronde_team
                                                 .scores_feitelijk
                                                 .values_list('pk', flat=True))

                alle_regels.append(regel)
            # for
        # for

        # via sporterboog_pks kunnen we alle scores vinden
        # bepaal welke relevant kunnen zijn
        score2match = dict()

        match_pks = list()
        for ronde in (RegioRonde
                      .objects
                      .filter(regiocomp=self.deelcomp)
                      .prefetch_related('matches')):
            match_pks.extend(list(ronde.matches.values_list('pk', flat=True)))
        # for

        # doorloop alle wedstrijden van deze plannen
        # de wedstrijd heeft een datum en uitslag met scores
        for match in (CompetitieMatch
                      .objects
                      .exclude(uitslag=None)
                      .select_related('uitslag',
                                      'vereniging')
                      .filter(pk__in=match_pks)
                      .prefetch_related('uitslag__scores')):

            # noteer welke scores interessant zijn
            # en de koppeling naar de wedstrijd, voor de datum
            for score in match.uitslag.scores.all():
                score2match[score.pk] = match
            # for
        # for

        # zoek de 'geen score' records voor alle relevante sporters
        sporterboog_pk2score_geen = dict()
        nieuwe_pks = alle_sporterboog_pks[:]
        nieuwe_pks.sort()
        for score in (Score.objects
                      .select_related('sporterboog')
                      .filter(sporterboog__pk__in=nieuwe_pks,
                              type=SCORE_TYPE_GEEN)):
            sporterboog_pk = score.sporterboog.pk
            sporterboog_pk2score_geen[sporterboog_pk] = score
            nieuwe_pks.remove(sporterboog_pk)
        # for

        if mag_database_wijzigen:
            # maak een 'geen score' record aan voor alle nieuwe_pks
            bulk = list()
            for sporterboog_pk in nieuwe_pks:
                sporterboog = sporterboog_cache[sporterboog_pk]
                score = Score(type=SCORE_TYPE_GEEN,
                              afstand_meter=0,
                              waarde=0,
                              sporterboog=sporterboog)
                bulk.append(score)
            # for
            Score.objects.bulk_create(bulk)

            for score in (Score.objects
                          .select_related('sporterboog')
                          .filter(sporterboog__pk__in=nieuwe_pks,
                                  type=SCORE_TYPE_GEEN)):
                sporterboog_pk = score.sporterboog.pk
                sporterboog_pk2score_geen[sporterboog_pk] = score
            # for
        else:
            # mag database niet wijzigen (tijdens GET)
            # dus make placeholder records aan
            for sporterboog_pk in nieuwe_pks:
                sporterboog = sporterboog_cache[sporterboog_pk]
                score = Score(
                            pk='geen_%s' % sporterboog.pk,
                            type=SCORE_TYPE_GEEN,
                            afstand_meter=0,
                            waarde=0,
                            sporterboog=sporterboog)
                sporterboog_pk2score_geen[sporterboog_pk] = score
            # for

        sporterboog2wedstrijdscores = dict()        # [sporterboog_pk] = [(score, wedstrijd), ...]
        early_date = datetime.date(year=2000, month=1, day=1)

        # doorloop alle scores van de relevante sporters
        for score in (Score
                      .objects
                      .select_related('sporterboog')
                      .exclude(waarde=SCORE_WAARDE_VERWIJDERD)
                      .filter(type=SCORE_TYPE_SCORE,
                              sporterboog__pk__in=sporterboog_pks,
                              afstand_meter=afstand)):

            score.block_selection = (score.pk in used_score_pks)
            sporterboog_pk = score.sporterboog.pk

            try:
                match = score2match[score.pk]
            except KeyError:
                # niet relevante score
                pass
            else:
                # optie A: eerst alle geblokkeerde opties, dan pas de keuzes
                # if score.block_selection:
                #    tup = (1, wedstrijd.datum_wanneer, wedstrijd.tijd_begin_wedstrijd, wedstrijd.pk, wedstrijd, score)
                # else:
                #    tup = (2, wedstrijd.datum_wanneer, wedstrijd.tijd_begin_wedstrijd, wedstrijd.pk, wedstrijd, score)

                # optie B: scores op datum houden
                tup = (1, match.datum_wanneer, match.tijd_begin_wedstrijd, match.pk, match, score)

                try:
                    sporterboog2wedstrijdscores[sporterboog_pk].append(tup)
                except KeyError:
                    # dit is de eerste entry
                    sporterboog2wedstrijdscores[sporterboog_pk] = [tup]

                    # voeg een "niet geschoten" optie toe
                    niet_geschoten = sporterboog_pk2score_geen[sporterboog_pk]
                    niet_geschoten.block_selection = False
                    tup = (3, early_date, 0, 0, None, niet_geschoten)   # None = wedstrijd
                    sporterboog2wedstrijdscores[sporterboog_pk].append(tup)
        # for

        # eerste anchor is een link op de pagina waar een keuze gemaakt moet worden
        # de gebruiker krijgt een knop om daarheen te navigeren
        eerste_anchor = None

        for regel in alle_regels:
            for deelnemer in regel.deelnemers:
                try:
                    tups = sporterboog2wedstrijdscores[deelnemer.sporterboog_pk]
                except KeyError:
                    # geen score voor deze sporter
                    deelnemer.gevonden_scores = list()
                else:
                    # sorteer de gevonden scores op wedstrijddatum
                    tups.sort()
                    deelnemer.gevonden_scores = [(wedstrijd, score) for _, _, _, _, wedstrijd, score in tups]
                    aantal = len(tups)
                    for _, score in deelnemer.gevonden_scores:
                        if score.block_selection:
                            aantal -= 1
                    # for
                    deelnemer.kan_kiezen = deelnemer.keuze_nodig = (aantal > 1)
                    if deelnemer.kan_kiezen:
                        deelnemer.id_radio = "id_sb_%s" % deelnemer.sporterboog_pk
                        for match, score in deelnemer.gevonden_scores:
                            if not score.block_selection:
                                score.id_radio = "id_score_%s" % score.pk
                                score.is_selected = (score.pk in regel.score_pks_feitelijk)
                                if score.is_selected:
                                    deelnemer.keuze_nodig = False
                        # for

                    if deelnemer.keuze_nodig:
                        if eerste_anchor is None:
                            deelnemer.anchor = eerste_anchor = "anchor_%s" % deelnemer.sporterboog.pk
                        aantal_keuzes_nodig += 1
            # for
        # for

        return alle_regels, aantal_keuzes_nodig, eerste_anchor

    def _verwerk_post(self, request):
        alle_regels, _, _ = self._bepaal_teams_en_scores(mag_database_wijzigen=True)

        # for k, v in request.POST.items():
        #     print('%s=%s' % (k, repr(v)))

        # verzamel de gewenste keuzes
        ronde_teams = dict()        # [ronde_team.pk] = (ronde_team, sporterboog_pk2score_pk)

        for regel in alle_regels:
            # regel = team
            try:
                team_scores = ronde_teams[regel.ronde_team.pk]
            except KeyError:
                team_scores = list()
                ronde_teams[regel.ronde_team.pk] = (regel.ronde_team, team_scores)

            for deelnemer in regel.deelnemers:
                if deelnemer.kan_kiezen:
                    score_pk_str = request.POST.get(deelnemer.id_radio, '')[:10]       # afkappen voor de veiligheid
                    # print('deelnemer.id_radio=%s --> score_pk_str=%s' % (deelnemer.id_radio, score_pk_str))
                    if score_pk_str:
                        # er is een keuze gemaakt
                        if score_pk_str.startswith('geen_'):
                            # zoek het echte 'geen score' record erbij
                            for _, score in deelnemer.gevonden_scores:
                                # print('  score.pk=%s, score=%s' % (score.pk, score))
                                if score.type == SCORE_TYPE_GEEN:
                                    # print('     geen score vertaald naar %s' % score.pk)
                                    team_scores.append(score.pk)
                                    break
                            # for
                        else:
                            try:
                                score_pk = int(score_pk_str)
                            except (ValueError, TypeError):
                                raise Http404('Verkeerde parameter')

                            for wedstrijd, score in deelnemer.gevonden_scores:
                                # print('  wedstrijd=%s, score.pk=%s, score=%s' % (repr(wedstrijd), score.pk, score))
                                if score.pk == score_pk:
                                    # het is echt een score van deze deelnemer
                                    team_scores.append(score.pk)
                                    break
                            # for
                else:
                    for wedstrijd, score in deelnemer.gevonden_scores:
                        if wedstrijd and not score.block_selection:
                            team_scores.append(score.pk)
                    # for
            # for
        # for

        for ronde_team, score_pks in ronde_teams.values():
            ronde_team.scores_feitelijk.set(score_pks)
        # for

        # trigger de achtergrond-taak om de teamscores opnieuw te berekenen
        update_uitslag_teamcompetitie()


class KoppelScoresRegioTeamsView(UserPassesTestMixin, TemplateScoresRegioTeamsView):

    """ Deze view geeft de RCL de mogelijkheid om voor de teamcompetitie de juiste individuele scores
        te selecteren voor sporters die meer dan 1 score neergezet hebben (inhalen/voorschieten).
    """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_RCL

    def _get_deelcomp_or_404(self, kwargs):
        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:7])  # afkappen voor de veiligheid
            self.deelcomp = (RegioComp
                             .objects
                             .select_related('competitie')
                             .get(pk=deelcomp_pk))
        except (ValueError, RegioComp.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        assert isinstance(self.deelcomp, RegioComp)

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        if self.deelcomp.functie != functie_nu:
            # niet de beheerder
            raise PermissionDenied('Niet de beheerder')

        if not self.deelcomp.regio_organiseert_teamcompetitie:
            raise Http404('Geen teamcompetitie in deze regio')

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        self._get_deelcomp_or_404(kwargs)
        assert isinstance(self.deelcomp, RegioComp)

        context['deelcomp'] = self.deelcomp
        context['huidige_ronde'] = '-'

        if 1 <= self.deelcomp.huidige_team_ronde <= 7:
            context['huidige_ronde'] = self.ronde_nr = self.deelcomp.huidige_team_ronde

            tup = self._bepaal_teams_en_scores()
            context['alle_regels'], context['aantal_keuzes_nodig'], context['anchor'] = tup
            context['url_opslaan'] = reverse('CompScores:selecteer-team-scores',
                                             kwargs={'deelcomp_pk': self.deelcomp.pk})

        comp = self.deelcomp.competitie
        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (reverse('CompLaagRegio:start-volgende-team-ronde',
                     kwargs={'deelcomp_pk': self.deelcomp.pk}), 'Team Ronde'),
            (None, 'Team scores')
        )

        return context

    def post(self, request, *args, **kwargs):

        self._get_deelcomp_or_404(kwargs)
        assert isinstance(self.deelcomp, RegioComp)

        if 1 <= self.deelcomp.huidige_team_ronde <= 7:
            self.ronde_nr = self.deelcomp.huidige_team_ronde

            self._verwerk_post(request)

        url = reverse('CompLaagRegio:start-volgende-team-ronde', kwargs={'deelcomp_pk': self.deelcomp.pk})
        return HttpResponseRedirect(url)


class CorrigeerRegioTeamRondeView(UserPassesTestMixin, TemplateScoresRegioTeamsView):

    """ Deze view geeft de BKO de mogelijkheid om een specifieke team ronde aan te passen,
        via hetzelfde scherm dat de RCL gebruikt
    """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.functie_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return rol_nu == Rol.ROL_BKO

    def _get_deelcomp_en_ronde_nr_or_404(self, kwargs):
        try:
            deelcomp_pk = int(kwargs['regiocomp_pk'][:7])  # afkappen voor de veiligheid
            self.deelcomp = (RegioComp
                             .objects
                             .select_related('competitie')
                             .get(pk=deelcomp_pk))
        except (ValueError, RegioComp.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        assert isinstance(self.deelcomp, RegioComp)

        if self.deelcomp.competitie.afstand != self.functie_nu.comp_type:
            # niet de beheerder
            raise PermissionDenied('Niet de beheerder')

        if not self.deelcomp.regio_organiseert_teamcompetitie:
            raise Http404('Geen teamcompetitie in deze regio')

        try:
            self.ronde_nr = int(kwargs['ronde_nr'][:2])     # afkappen voor de veiligheid
        except ValueError:
            self.ronde_nr = 999

        if not (0 < self.ronde_nr < self.deelcomp.huidige_team_ronde):
            raise Http404('Ronde niet gevonden')

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        self._get_deelcomp_en_ronde_nr_or_404(kwargs)
        assert isinstance(self.deelcomp, RegioComp)

        context['deelcomp'] = self.deelcomp
        context['huidige_ronde'] = self.ronde_nr

        tup = self._bepaal_teams_en_scores()
        context['alle_regels'], context['aantal_keuzes_nodig'], context['anchor'] = tup
        context['url_opslaan'] = reverse('CompScores:corrigeer-team-ronde',
                                         kwargs={'regiocomp_pk': self.deelcomp.pk,
                                                 'ronde_nr': self.ronde_nr})

        comp = self.deelcomp.competitie
        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (reverse('CompLaagRegio:start-volgende-team-ronde',
                     kwargs={'deelcomp_pk': self.deelcomp.pk}), 'Team Ronde'),
            (None, 'Team scores')
        )

        return context

    def post(self, request, *args, **kwargs):

        self._get_deelcomp_en_ronde_nr_or_404(kwargs)

        self._verwerk_post(request)

        url = reverse('CompScores:corrigeer-team-ronde-selecteer', kwargs={'comp_pk': self.deelcomp.competitie.pk})
        return HttpResponseRedirect(url)


class CorrigeerRegioTeamRondeSelecteerView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de BKO de mogelijkheid om voor een team ronde te kiezen (regio + ronde 1..7)
        en daarna de gekoppelde scores aan te passen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPSCORES_TEAMS_SELECTEER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.functie_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return rol_nu == Rol.ROL_BKO

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:7])    # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        if comp.afstand != self.functie_nu.comp_type:
            raise Http404('Geen toegang')

        context['regios'] = regios = list()
        for deelcomp in (RegioComp
                         .objects
                         .filter(competitie=comp)
                         .exclude(regio_organiseert_teamcompetitie=False)
                         .order_by('regio__regio_nr')):
            rondes = list()
            regio = SimpleNamespace(
                            regio_str=str(deelcomp.regio.regio_nr),
                            rondes=rondes)
            regios.append(regio)

            for ronde_nr in range(1, deelcomp.huidige_team_ronde):
                url = reverse('CompScores:corrigeer-team-ronde', kwargs={'regiocomp_pk': deelcomp.pk,
                                                                         'ronde_nr': ronde_nr})
                ronde = SimpleNamespace(
                                url=url,
                                tekst=str(ronde_nr))
                rondes.append(ronde)
            # for
        # for

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Correctie team ronde')
        )
        return context


# end of file
