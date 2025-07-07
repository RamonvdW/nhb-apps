# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, JsonResponse, Http404, UnreadablePostError
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count
from django.views.generic import TemplateView, View
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.operations.wedstrijdcapaciteit import bepaal_waarschijnlijke_deelnemers
from Competitie.models import (CompetitieMatch, update_uitslag_teamcompetitie,
                               Regiocompetitie, RegiocompetitieRonde, RegiocompetitieSporterBoog,
                               RegiocompetitieTeam, RegiocompetitieRondeTeam, RegiocompetitieTeamPoule)
from Functie.definities import Rol
from Functie.rol import rol_get_huidige, rol_get_huidige_functie
from Score.definities import SCORE_WAARDE_VERWIJDERD, SCORE_TYPE_SCORE, SCORE_TYPE_GEEN
from Score.models import Score, ScoreHist, Uitslag
from Sporter.models import SporterBoog
from types import SimpleNamespace
import datetime
import json


TEMPLATE_COMPSCORES_TEAMS = 'compscores/rcl-scores-regio-teams.dtl'
TEMPLATE_COMPSCORES_REGIO = 'compscores/rcl-scores-regio.dtl'
TEMPLATE_COMPSCORES_INVOEREN = 'compscores/scores-invoeren.dtl'
TEMPLATE_COMPSCORES_BEKIJKEN = 'compscores/scores-bekijken.dtl'


class ScoresRegioView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de RCL een lijst met wedstrijden en toegang tot scores/accorderen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPSCORES_REGIO
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_RCL

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])            # afkappen voor de veiligheid
            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie')
                        .get(pk=deelcomp_pk))
        except (ValueError, Regiocompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        if deelcomp.functie != functie_nu:
            # niet de beheerder
            raise PermissionDenied('Niet de beheerder')

        context['deelcomp'] = deelcomp

        comp = deelcomp.competitie
        # TODO: check competitie fase

        # regiocompetitie bestaat uit rondes
        # elke ronde heeft een plan met wedstrijden

        match_pks = list()
        match2beschrijving = dict()

        for ronde in (RegiocompetitieRonde
                      .objects
                      .prefetch_related('matches')
                      .filter(regiocompetitie=deelcomp)):

            for match in ronde.matches.all():
                match_pks.append(match.pk)
                beschrijving = ronde.beschrijving
                if not beschrijving and ronde.cluster:
                    beschrijving = ronde.cluster.naam
                if not beschrijving:
                    beschrijving = "?? (ronde)"
                match2beschrijving[match.pk] = beschrijving
            # for
        # for

        matches = (CompetitieMatch
                   .objects
                   .select_related('uitslag',
                                   'vereniging')
                   .filter(pk__in=match_pks)
                   .annotate(scores_count=Count('uitslag__scores'))
                   .order_by('datum_wanneer', 'tijd_begin_wedstrijd',
                             'pk'))     # vaste sortering bij gelijke datum/tijd

        for match in matches:
            heeft_uitslag = (match.uitslag and match.scores_count > 0)

            beschrijving = match2beschrijving[match.pk]
            if match.beschrijving != beschrijving:
                match.beschrijving = beschrijving

            # geef RCL de mogelijkheid om de scores aan te passen
            # de HWL/WL krijgen deze link vanuit Vereniging.Wedstrijden
            if heeft_uitslag and not match.uitslag.is_bevroren:
                match.url_uitslag_controleren = reverse('CompScores:uitslag-controleren',
                                                        kwargs={'match_pk': match.pk})
            else:
                # TODO: knop pas beschikbaar maken op wedstrijddatum tot datum+N
                match.url_uitslag_invoeren = reverse('CompScores:uitslag-invoeren',
                                                     kwargs={'match_pk': match.pk})
        # for

        context['wedstrijden'] = matches

        context['aantal_regels'] = matches.count() + 2

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}),
             comp.beschrijving.replace(' competitie', '')),
            (None, 'Scores')
        )

        return context


def mag_deelcomp_wedstrijd_wijzigen(wedstrijd, functie_nu, deelcomp):
    """ controleer toestemming om scoreverwerking te doen voor deze wedstrijd """
    if (functie_nu.rol == 'RCL'
            and functie_nu.regio == deelcomp.regio
            and functie_nu.comp_type == deelcomp.competitie.afstand):
        # RCL van deze regiocompetitie
        return True

    if functie_nu.rol in ('HWL', 'WL') and functie_nu.vereniging == wedstrijd.vereniging:
        # (H)WL van de organiserende vereniging
        return True

    return False


def bepaal_match_en_deelcomp_of_404(match_pk, mag_database_wijzigen=False):
    try:
        match_pk = int(match_pk[:6])        # afkappen voor de veiligheid
        match = (CompetitieMatch
                 .objects
                 .select_related('uitslag')
                 .prefetch_related('uitslag__scores')
                 .get(pk=match_pk))
    except (ValueError, CompetitieMatch.DoesNotExist):
        raise Http404('Wedstrijd niet gevonden')

    rondes = match.regiocompetitieronde_set.all()
    if len(rondes) == 0:
        raise Http404('Geen regio wedstrijd')
    ronde = rondes[0]

    deelcomp = ronde.regiocompetitie

    # maak de uitslag aan indien nog niet gedaan
    if not match.uitslag:
        uitslag = Uitslag()
        if deelcomp.competitie.is_indoor():
            uitslag.max_score = 300
            uitslag.afstand = 18
        else:
            uitslag.max_score = 250
            uitslag.afstand = 25

        if mag_database_wijzigen:
            uitslag.save()
            match.uitslag = uitslag
            match.save(update_fields=['uitslag'])
    else:
        uitslag = match.uitslag

    match.max_score = uitslag.max_score
    match.afstand = uitslag.afstand

    return match, deelcomp, ronde


class WedstrijdUitslagInvoerenView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de RCL, HWL en WL de uitslag van een wedstrijd invoeren """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPSCORES_INVOEREN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'
    is_controle = False
    kruimel = 'Invoeren'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_RCL, Rol.ROL_HWL, Rol.ROL_WL)

    @staticmethod
    def _team_naam_toevoegen(scores, deelcomp):
        """ aan elke score de teamnaam en vsg toevoegen """

        sporterboog_pks = scores.values_list('sporterboog__pk', flat=True)

        deelnemers = (RegiocompetitieSporterBoog
                      .objects
                      .filter(regiocompetitie=deelcomp,
                              sporterboog__pk__in=sporterboog_pks))

        ronde_teams = (RegiocompetitieRondeTeam
                       .objects
                       .select_related('team')
                       .prefetch_related('deelnemers_feitelijk')
                       .filter(team__regiocompetitie=deelcomp,
                               ronde_nr=deelcomp.huidige_team_ronde))

        deelnemer_pk2teamnaam = dict()
        for ronde_team in ronde_teams:
            team_naam = ronde_team.team.maak_team_naam_kort()
            for deelnemer in ronde_team.deelnemers_feitelijk.all():
                deelnemer_pk2teamnaam[deelnemer.pk] = team_naam
            # for
        # for

        sporterboog_pk2tup = dict()
        for deelnemer in deelnemers:
            team_gem = deelnemer.ag_voor_team
            if not deelcomp.regio_heeft_vaste_teams:
                # pak VSG, indien beschikbaar
                if deelnemer.aantal_scores > 0:
                    team_gem = deelnemer.gemiddelde

            try:
                sporterboog_pk2tup[deelnemer.sporterboog.pk] = (team_gem, deelnemer_pk2teamnaam[deelnemer.pk])
            except KeyError:
                # geen teamschutter
                pass
        # for

        for score in scores:
            try:
                score.team_gem, score.team_naam = sporterboog_pk2tup[score.sporterboog.pk]
            except KeyError:
                score.team_naam = "-"
                score.team_gem = ""
        # for

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        match_pk = kwargs['match_pk'][:6]     # afkappen voor de veiligheid
        match, deelcomp, ronde = bepaal_match_en_deelcomp_of_404(match_pk)

        context['wedstrijd'] = match
        context['deelcomp'] = deelcomp

        if not mag_deelcomp_wedstrijd_wijzigen(match, self.functie_nu, deelcomp):
            raise PermissionDenied('Niet de beheerder')

        context['is_controle'] = self.is_controle
        context['is_akkoord'] = (match.uitslag and match.uitslag.is_bevroren)

        if self.is_controle:
            context['url_geef_akkoord'] = reverse('CompScores:uitslag-accorderen',
                                                  kwargs={'match_pk': match.pk})

        if match.uitslag:
            scores = (match
                      .uitslag
                      .scores
                      .filter(type=SCORE_TYPE_SCORE)
                      .exclude(waarde=SCORE_WAARDE_VERWIJDERD)
                      .select_related('sporterboog',
                                      'sporterboog__boogtype',
                                      'sporterboog__sporter',
                                      'sporterboog__sporter__bij_vereniging')
                      .order_by('sporterboog__sporter__lid_nr',
                                'sporterboog__pk'))        # belangrijk i.v.m. zelfde volgorde by dynamisch toevoegen
            context['scores'] = scores

            self._team_naam_toevoegen(scores, deelcomp)

        context['url_check_bondsnummer'] = reverse('CompScores:dynamic-check-bondsnummer')
        context['url_opslaan'] = reverse('CompScores:dynamic-scores-opslaan')
        context['url_deelnemers_ophalen'] = reverse('CompScores:dynamic-deelnemers-ophalen')

        teams = (RegiocompetitieTeam
                 .objects
                 .filter(regiocompetitie=deelcomp)
                 .select_related('vereniging'))
        for team in teams:
            team.naam_str = team.maak_team_naam_kort()
        context['teams'] = teams

        # plan = wedstrijd.competitiewedstrijdenplan_set.first()
        # ronde = DeelcompetitieRonde.objects.get(plan=plan)

        if self.rol_nu == Rol.ROL_RCL:
            context['url_terug'] = reverse('CompScores:scores-rcl',
                                           kwargs={'deelcomp_pk': deelcomp.pk})

            comp = deelcomp.competitie
            context['kruimels'] = (
                (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
                (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}),
                    comp.beschrijving.replace(' competitie', '')),
                (reverse('CompScores:scores-rcl', kwargs={'deelcomp_pk': deelcomp.pk}), 'Scores'),
                (None, self.kruimel)
            )
        else:
            context['url_terug'] = reverse('CompScores:wedstrijden-scores')
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
                (reverse('CompScores:wedstrijden-scores'), 'Scores'),
                (None, self.kruimel)
            )

        return context


class WedstrijdUitslagControlerenView(WedstrijdUitslagInvoerenView):

    """ Deze view laat de RCL de uitslag van een wedstrijd aanpassen en accorderen """

    is_controle = True
    kruimel = 'Controleer'

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'ik geef akkoord voor deze uitslag'
            gebruikt wordt door de RCL.
        """

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        match_pk = kwargs['match_pk'][:6]     # afkappen voor de veiligheid
        match, deelcomp, _ = bepaal_match_en_deelcomp_of_404(match_pk, mag_database_wijzigen=True)

        if not mag_deelcomp_wedstrijd_wijzigen(match, functie_nu, deelcomp):
            raise PermissionDenied('Niet de beheerder')

        uitslag = match.uitslag
        if not uitslag.is_bevroren:
            uitslag.is_bevroren = True
            uitslag.save()

        url = reverse('CompScores:uitslag-controleren',
                      kwargs={'match_pk': match.pk})

        return HttpResponseRedirect(url)


class DynamicDeelnemersOphalenView(UserPassesTestMixin, View):

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rol.ROL_RCL, Rol.ROL_HWL, Rol.ROL_WL)

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'waarschijnlijke deelnemers ophalen' gebruikt wordt

            Dit is een POST by-design, om caching te voorkomen.
        """

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnreadablePostError):
            # garbage in
            raise Http404('Geen valide verzoek')

        try:
            deelcomp_pk = int(str(data['deelcomp_pk'])[:6])   # afkappen voor extra veiligheid
            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie')
                        .get(pk=deelcomp_pk))
        except (KeyError, ValueError, Regiocompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        try:
            match_pk = int(str(data['wedstrijd_pk'])[:6])   # afkappen voor extra veiligheid
            match = (CompetitieMatch
                     .objects
                     .get(pk=match_pk))
        except (KeyError, ValueError, CompetitieMatch.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        sporters, teams = bepaal_waarschijnlijke_deelnemers(deelcomp.competitie.afstand, deelcomp, match)

        out = dict()
        out['deelnemers'] = deelnemers = list()
        for sporter in sporters:
            deelnemers.append({
                'pk': sporter.sporterboog_pk,
                'lid_nr': sporter.lid_nr,
                'naam': sporter.volledige_naam,
                'ver_nr': sporter.ver_nr,
                'ver_naam': sporter.ver_naam,
                'boog': sporter.boog,
                'team_gem': sporter.team_gem,
                'team_pk': sporter.team_pk,
            })
        # for

        return JsonResponse(out)


class DynamicZoekOpBondsnummerView(UserPassesTestMixin, View):

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rol.ROL_RCL, Rol.ROL_HWL, Rol.ROL_WL)

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Zoek' gebruikt wordt
        """

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnreadablePostError):
            # garbage in
            raise Http404('Geen valide verzoek')

        # zoek een
        # print('data: %s' % repr(data))

        out = dict()

        try:
            lid_nr = int(str(data['lid_nr'])[:6])               # afkappen voor extra veiligheid
            match_pk = int(str(data['wedstrijd_pk'])[:6])       # afkappen voor extra veiligheid
            match = CompetitieMatch.objects.get(pk=match_pk)
        except (KeyError, ValueError, CompetitieMatch.DoesNotExist):
            # garbage in
            out['fail'] = 1
            # raise Http404('Geen valide verzoek')
        else:
            rondes = match.regiocompetitieronde_set.all()
            if len(rondes) == 0:
                raise Http404('Geen competitie wedstrijd')
            ronde = rondes[0]

            # zoek schuttersboog die ingeschreven zijn voor deze competitie
            competitie = ronde.regiocompetitie.competitie

            deelnemers = (RegiocompetitieSporterBoog
                          .objects
                          .select_related('sporterboog',
                                          'sporterboog__boogtype',
                                          'sporterboog__sporter',
                                          'sporterboog__sporter__bij_vereniging')
                          .filter(regiocompetitie__competitie=competitie,
                                  sporterboog__sporter__lid_nr=lid_nr))

            if len(deelnemers) == 0:
                out['fail'] = 1         # is niet ingeschreven voor deze competitie
            else:
                out['deelnemers'] = list()

                geen_lid = True
                for deelnemer in deelnemers:
                    sporterboog = deelnemer.sporterboog
                    sporter = sporterboog.sporter
                    boog = sporterboog.boogtype

                    # volgende blok wordt een paar keer uitgevoerd, maar dat maak niet uit
                    ver = sporter.bij_vereniging
                    if not ver:
                        # niet lid bij een vereniging, dan niet toe te voegen
                        geen_lid = True
                        continue

                    out['vereniging'] = str(ver)
                    out['regio'] = str(ver.regio)
                    out['lid_nr'] = sporter.lid_nr
                    out['naam'] = sporter.volledige_naam()
                    out['ver_nr'] = sporter.bij_vereniging.ver_nr
                    out['ver_naam'] = sporter.bij_vereniging.naam

                    sub = {
                        'pk': sporterboog.pk,
                        'boog': boog.beschrijving,
                        'team_pk': 0,
                        'team_gem': ''
                    }

                    if deelnemer.inschrijf_voorkeur_team:
                        # TODO: gebruikt ronde team ag!
                        sub['team_gem'] = deelnemer.ag_voor_team
                        if not ronde.regiocompetitie.regio_heeft_vaste_teams:
                            if deelnemer.aantal_scores > 0:
                                sub['team_gem'] = deelnemer.gemiddelde

                        sub['vsg'] = sub['team_gem']        # TODO: obsolete vsg

                        # zoek het huidige team erbij
                        teams = deelnemer.regiocompetitieteam_set.all()
                        if teams.count() > 0:
                            # sporter is gekoppeld aan een team
                            sub['team_pk'] = teams[0].pk

                    out['deelnemers'].append(sub)
                # for

                if geen_lid and len(out['deelnemers']) == 0:
                    out['fail'] = 1

        return JsonResponse(out)


class DynamicScoresOpslaanView(UserPassesTestMixin, View):

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rol.ROL_RCL, Rol.ROL_HWL, Rol.ROL_WL)

    @staticmethod
    def nieuwe_score(bulk, uitslag, sporterboog_pk, waarde, when, door_account):
        # print('nieuwe score: %s = %s' % (sporterboog_pk, waarde))
        try:
            sporterboog = SporterBoog.objects.get(pk=sporterboog_pk)
        except SporterBoog.DoesNotExist:
            # garbage --> ignore
            return

        score_obj = Score(sporterboog=sporterboog,
                          waarde=waarde,
                          afstand_meter=uitslag.afstand)
        score_obj.save()
        uitslag.scores.add(score_obj)

        hist = ScoreHist(
                    score=score_obj,
                    oude_waarde=0,
                    nieuwe_waarde=waarde,
                    when=when,
                    door_account=door_account,
                    notitie="Invoer uitslag wedstrijd")
        bulk.append(hist)

    @staticmethod
    def bijgewerkte_score(bulk, score_obj, waarde, when, door_account):
        if score_obj.waarde != waarde:
            # print('bijgewerkte score: %s --> %s' % (score_obj, waarde))

            hist = ScoreHist(
                        score=score_obj,
                        oude_waarde=score_obj.waarde,
                        nieuwe_waarde=waarde,
                        when=when,
                        door_account=door_account,
                        notitie="Invoer uitslag wedstrijd")
            bulk.append(hist)

            score_obj.waarde = waarde
            score_obj.save()
        # else: zelfde score

    def scores_opslaan(self, uitslag, data, when, door_account):
        """ sla de scores op
            data bevat sporterboog_pk + score
            als score leeg is moet pk uit de uitslag gehaald worden
        """

        # doorloop alle scores in de uitslag en haal de sporterboog erbij
        # hiermee kunnen we snel controleren of iemand al in de uitslag
        # voorkomt
        pk2score_obj = dict()
        for score_obj in uitslag.scores.select_related('sporterboog').all():
            pk2score_obj[score_obj.sporterboog.pk] = score_obj
        # for
        # print('pk2score_obj: %s' % repr(pk2score_obj))

        bulk = list()
        for key, value in data.items():
            if key == 'wedstrijd_pk':
                # geen sporterboog
                continue

            try:
                pk = int(str(key)[:6])     # afkappen voor de veiligheid
            except ValueError:
                # fout pk: ignore
                continue        # met de for-loop

            try:
                score_obj = pk2score_obj[pk]
            except KeyError:
                # sporterboog zit nog niet in de uitslag
                score_obj = None

            if isinstance(value, str) and value == '':
                # lege invoer betekent: schutter deed niet mee
                if score_obj:
                    # verwijder deze score uit de uitslag, maar behoud de geschiedenis
                    self.bijgewerkte_score(bulk, score_obj, SCORE_WAARDE_VERWIJDERD, when, door_account)
                # laat tegen exceptie hieronder aanlopen

            # sla de score op
            try:
                waarde = int(str(value)[:4])   # afkappen voor de veiligheid
            except ValueError:
                # foute score: ignore
                continue

            if 0 <= waarde <= uitslag.max_score:
                # print('score geaccepteerd: %s %s' % (pk, waarde))
                # score opslaan
                if not score_obj:
                    # het is een nieuwe score
                    self.nieuwe_score(bulk, uitslag, pk, waarde, when, door_account)
                else:
                    self.bijgewerkte_score(bulk, score_obj, waarde, when, door_account)
            # else: illegale score --> ignore
        # for

        ScoreHist.objects.bulk_create(bulk)

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Opslaan' gebruikt wordt
        """

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnreadablePostError):
            # garbage in
            raise Http404('Geen valide verzoek')

        # print('data:', repr(data))
        try:
            match_pk = str(data['wedstrijd_pk'])[:6]  # afkappen voor de veiligheid
        except KeyError:
            raise Http404('Wedstrijd niet gevonden')

        match, deelcomp, ronde = bepaal_match_en_deelcomp_of_404(match_pk, mag_database_wijzigen=True)
        uitslag = match.uitslag

        rol_nu, functie_nu = rol_get_huidige_functie(request)
        if not mag_deelcomp_wedstrijd_wijzigen(match, functie_nu, ronde.regiocompetitie):
            raise PermissionDenied('Geen toegang')

        # voorkom wijzigingen bevroren wedstrijduitslag
        if rol_nu in (Rol.ROL_HWL, Rol.ROL_WL) and uitslag.is_bevroren:
            raise Http404('Uitslag mag niet meer gewijzigd worden')

        door_account = get_account(request)
        when = timezone.now()

        self.scores_opslaan(uitslag, data, when, door_account)

        out = {'done': 1}
        return JsonResponse(out)


class WedstrijdUitslagBekijkenView(UserPassesTestMixin, TemplateView):

    """ Deze view toont de uitslag van een wedstrijd """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPSCORES_BEKIJKEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # pagina is alleen bereikbaar vanuit Beheer vereniging
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rol.ROL_HWL, Rol.ROL_WL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        match_pk = kwargs['match_pk'][:6]     # afkappen voor de veiligheid
        match, deelcomp, ronde = bepaal_match_en_deelcomp_of_404(match_pk, mag_database_wijzigen=True)

        scores = (match
                  .uitslag
                  .scores
                  .filter(type=SCORE_TYPE_SCORE)
                  .exclude(waarde=SCORE_WAARDE_VERWIJDERD)
                  .select_related('sporterboog',
                                  'sporterboog__boogtype',
                                  'sporterboog__sporter'))

        # maak een opzoektabel voor de huidige vereniging van elke sporterboog
        sporterboog_pks = [score.sporterboog.pk for score in scores]
        regioschutters = (RegiocompetitieSporterBoog
                          .objects
                          .select_related('sporterboog',
                                          'bij_vereniging')
                          .filter(sporterboog__pk__in=sporterboog_pks))

        sporterboog2vereniging = dict()
        for regioschutter in regioschutters:
            sporterboog2vereniging[regioschutter.sporterboog.pk] = regioschutter.bij_vereniging
        # for

        for score in scores:
            score.schutter_str = score.sporterboog.sporter.lid_nr_en_volledige_naam()
            score.lid_nr = score.sporterboog.sporter.lid_nr
            score.boog_str = score.sporterboog.boogtype.beschrijving
            try:
                score.vereniging_str = str(sporterboog2vereniging[score.sporterboog.pk])
            except KeyError:
                # unlikely inconsistency
                score.vereniging_str = "?"
        # for

        # vereniging kan 2 leden met dezelfde naam en boog hebben, daarom lid_nr
        te_sorteren = [(score.vereniging_str, score.schutter_str, score.boog_str, score.lid_nr, score)
                       for score in scores]
        te_sorteren.sort()
        scores = [score for _, _, _, _, score in te_sorteren]

        context['scores'] = scores
        context['wedstrijd'] = match
        context['deelcomp'] = deelcomp
        context['ronde'] = ronde

        context['aantal_regels'] = 2 + len(scores)

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (reverse('CompScores:wedstrijden'), 'Competitiewedstrijden'),
            (None, 'Uitslag'),
        )

        return context


class ScoresRegioTeamsView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de RCL de mogelijkheid om voor de teamcompetitie de juiste individuele scores
        te selecteren voor sporters die meer dan 1 score neergezet hebben (inhalen/voorschieten).
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPSCORES_TEAMS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_RCL

    @staticmethod
    def _bepaal_teams_en_scores(deelcomp, mag_database_wijzigen=False):
        alle_regels = list()
        aantal_keuzes_nodig = 0

        # sporters waarvan we de scores op moeten zoeken
        sporterboog_pks = list()

        used_score_pks = list()

        deelnemer2sporter_cache: dict[int, tuple[int, str]] = dict()    # [deelnemer_pk] = (sporterboog_pk, naam_str)
        sporterboog_cache: dict[int, SporterBoog] = dict()              # [sporterboog_pk] = SporterBoog
        for deelnemer in (RegiocompetitieSporterBoog
                          .objects
                          .select_related('sporterboog',
                                          'sporterboog__sporter')
                          .filter(regiocompetitie=deelcomp)):

            sporterboog = deelnemer.sporterboog
            sporterboog_cache[sporterboog.pk] = sporterboog

            sporter = sporterboog.sporter
            tup = (sporterboog.pk, "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam()))
            deelnemer2sporter_cache[deelnemer.pk] = tup
        # for

        alle_sporterboog_pks = list()
        afstand = deelcomp.competitie.afstand

        for poule in (RegiocompetitieTeamPoule
                      .objects
                      .prefetch_related('teams')
                      .filter(regiocompetitie=deelcomp)
                      .order_by('beschrijving')):

            team_pks = poule.teams.values_list('pk', flat=True)

            # alle al gebruikte scores
            used_scores = list(RegiocompetitieRondeTeam
                               .objects
                               .prefetch_related('scores_feitelijk')
                               .filter(team__in=team_pks)
                               .exclude(ronde_nr=deelcomp.huidige_team_ronde)
                               .values_list('scores_feitelijk__pk', flat=True))
            used_score_pks.extend(used_scores)

            ronde_teams = (RegiocompetitieRondeTeam
                           .objects
                           .select_related('team',
                                           'team__vereniging',
                                           'team__team_klasse')
                           .prefetch_related('deelnemers_feitelijk',
                                             'scores_feitelijk')
                           .filter(team__in=team_pks,
                                   ronde_nr=deelcomp.huidige_team_ronde)
                           .order_by('team__vereniging__ver_nr',
                                     'team__volg_nr'))

            # TODO: is volgende lus nog wel nodig?
            for ronde_team in ronde_teams:
                ronde_team.ronde_wp = 0
                ronde_team.team_str = "[%s] %s" % (ronde_team.team.vereniging.ver_nr,
                                                   ronde_team.team.maak_team_naam_kort())
            # for

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
        for ronde in (RegiocompetitieRonde
                      .objects
                      .filter(regiocompetitie=deelcomp)
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

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen voor de veiligheid
            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie')
                        .get(pk=deelcomp_pk))
        except (ValueError, Regiocompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        if deelcomp.functie != functie_nu:
            # niet de beheerder
            raise PermissionDenied('Niet de beheerder')

        if not deelcomp.regio_organiseert_teamcompetitie:
            raise Http404('Geen teamcompetitie in deze regio')

        context['deelcomp'] = deelcomp
        context['huidige_ronde'] = '-'

        if 1 <= deelcomp.huidige_team_ronde <= 7:
            context['huidige_ronde'] = deelcomp.huidige_team_ronde

            tup = self._bepaal_teams_en_scores(deelcomp)
            context['alle_regels'], context['aantal_keuzes_nodig'], context['anchor'] = tup
            context['url_opslaan'] = reverse('CompScores:selecteer-team-scores',
                                             kwargs={'deelcomp_pk': deelcomp.pk})

        comp = deelcomp.competitie
        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (reverse('CompLaagRegio:start-volgende-team-ronde',
                     kwargs={'deelcomp_pk': deelcomp.pk}), 'Team Ronde'),
            (None, 'Team scores')
        )

        return context

    def post(self, request, *args, **kwargs):

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen voor de veiligheid
            deelcomp = Regiocompetitie.objects.get(pk=deelcomp_pk)
        except (ValueError, Regiocompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        if deelcomp.functie != functie_nu:
            # niet de beheerder
            raise PermissionDenied('Niet de beheerder')

        if not deelcomp.regio_organiseert_teamcompetitie:
            raise Http404('Geen teamcompetitie in deze regio')

        alle_regels, _, _ = self._bepaal_teams_en_scores(deelcomp, mag_database_wijzigen=True)

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

        url = reverse('CompLaagRegio:start-volgende-team-ronde', kwargs={'deelcomp_pk': deelcomp.pk})
        return HttpResponseRedirect(url)


# end of file
