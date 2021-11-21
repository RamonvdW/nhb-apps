# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.operations.wedstrijdcapaciteit import bepaal_waarschijnlijke_deelnemers
from Competitie.models import (LAAG_REGIO, DeelCompetitie, DeelcompetitieRonde, RegioCompetitieSchutterBoog,
                               RegiocompetitieTeam, RegiocompetitieRondeTeam, RegiocompetitieTeamPoule,
                               update_uitslag_teamcompetitie)
from Competitie.menu import menu_dynamics_competitie
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie
from Score.models import Score, ScoreHist, SCORE_WAARDE_VERWIJDERD, SCORE_TYPE_SCORE
from Sporter.models import SporterBoog
from Wedstrijden.models import CompetitieWedstrijd, CompetitieWedstrijdUitslag
from types import SimpleNamespace
import datetime
import json


TEMPLATE_COMPSCORES_REGIO = 'compscores/scores-regio.dtl'
TEMPLATE_COMPSCORES_INVOEREN = 'compscores/scores-invoeren.dtl'
TEMPLATE_COMPSCORES_BEKIJKEN = 'compscores/scores-bekijken.dtl'
TEMPLATE_COMPSCORES_TEAMS = 'compscores/scores-regio-teams.dtl'


class ScoresRegioView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de planning voor een competitie in een regio """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPSCORES_REGIO
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_RCL

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen geeft beveiliging
            deelcomp = DeelCompetitie.objects.get(pk=deelcomp_pk,
                                                  laag=LAAG_REGIO)
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        if deelcomp.functie != functie_nu:
            # niet de beheerder
            raise PermissionDenied()

        context['deelcomp'] = deelcomp

        if deelcomp.regio_organiseert_teamcompetitie:
            context['url_team_scores'] = reverse('CompScores:selecteer-team-scores',
                                                 kwargs={'deelcomp_pk': deelcomp.pk})

        # deelcompetitie bestaat uit rondes
        # elke ronde heeft een plan met wedstrijden

        wedstrijd_pks = list()
        wedstrijd2beschrijving = dict()
        comp_str = deelcomp.competitie.beschrijving

        for ronde in (DeelcompetitieRonde
                      .objects
                      .select_related('plan')
                      .prefetch_related('plan__wedstrijden')
                      .filter(deelcompetitie=deelcomp)):
            for wedstrijd in ronde.plan.wedstrijden.all():
                wedstrijd_pks.append(wedstrijd.pk)
                beschrijving = ronde.beschrijving
                if not beschrijving and ronde.cluster:
                    beschrijving = ronde.cluster.naam
                if not beschrijving:
                    beschrijving = "?? (ronde)"
                wedstrijd2beschrijving[wedstrijd.pk] = "%s - %s" % (comp_str, beschrijving)
            # for
        # for

        wedstrijden = (CompetitieWedstrijd
                       .objects
                       .select_related('uitslag')
                       .filter(pk__in=wedstrijd_pks)
                       .order_by('datum_wanneer', 'tijd_begin_wedstrijd',
                                 'pk'))     # vaste sortering bij gelijke datum/tijd

        for wedstrijd in wedstrijden:
            heeft_uitslag = (wedstrijd.uitslag and wedstrijd.uitslag.scores.count() > 0)

            beschrijving = wedstrijd2beschrijving[wedstrijd.pk]
            if wedstrijd.beschrijving != beschrijving:
                wedstrijd.beschrijving = beschrijving
                wedstrijd.save()

            # geef RCL de mogelijkheid om te scores aan te passen
            # de HWL/WL krijgen deze link vanuit Vereniging::Wedstrijden
            if heeft_uitslag:
                wedstrijd.url_uitslag_controleren = reverse('CompScores:uitslag-controleren',
                                                            kwargs={'wedstrijd_pk': wedstrijd.pk})
            else:
                # TODO: knop pas beschikbaar maken op wedstrijddatum tot datum+N
                wedstrijd.url_uitslag_invoeren = reverse('CompScores:uitslag-invoeren',
                                                         kwargs={'wedstrijd_pk': wedstrijd.pk})
        # for

        context['wedstrijden'] = wedstrijden

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp.competitie.pk)
        return context


def mag_deelcomp_wedstrijd_wijzigen(wedstrijd, functie_nu, deelcomp):
    """ controleer toestemming om scoreverwerking te doen voor deze wedstrijd """
    if (functie_nu.rol == 'RCL'
            and functie_nu.nhb_regio == deelcomp.nhb_regio
            and functie_nu.comp_type == deelcomp.competitie.afstand):
        # RCL van deze deelcompetitie
        return True

    if functie_nu.rol in ('HWL', 'WL') and functie_nu.nhb_ver == wedstrijd.vereniging:
        # (H)WL van de organiserende vereniging
        return True

    return False


def bepaal_wedstrijd_en_deelcomp_of_404(wedstrijd_pk):
    try:
        wedstrijd_pk = int(wedstrijd_pk)
        wedstrijd = (CompetitieWedstrijd
                     .objects
                     .select_related('uitslag')
                     .prefetch_related('uitslag__scores')
                     .get(pk=wedstrijd_pk))
    except (ValueError, CompetitieWedstrijd.DoesNotExist):
        raise Http404('Wedstrijd niet gevonden')

    plan = wedstrijd.competitiewedstrijdenplan_set.all()[0]

    # zoek de ronde erbij
    # deze hoort al bij een competitie type (indoor / 25m1pijl)
    ronde = (DeelcompetitieRonde
             .objects
             .select_related('deelcompetitie',
                             'deelcompetitie__nhb_regio',
                             'deelcompetitie__competitie')
             .get(plan=plan))

    deelcomp = ronde.deelcompetitie

    # maak de WedstrijdUitslag aan indien nog niet gedaan
    if not wedstrijd.uitslag:
        uitslag = CompetitieWedstrijdUitslag()
        if deelcomp.competitie.afstand == '18':
            uitslag.max_score = 300
            uitslag.afstand_meter = 18
        else:
            uitslag.max_score = 250
            uitslag.afstand_meter = 25
        uitslag.save()
        wedstrijd.uitslag = uitslag
        wedstrijd.save()

    return wedstrijd, deelcomp, ronde


class WedstrijdUitslagInvoerenView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de RCL, HWL en WL de uitslag van een wedstrijd invoeren """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPSCORES_INVOEREN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    is_controle = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_RCL, Rollen.ROL_HWL, Rollen.ROL_WL)

    @staticmethod
    def _team_naam_toevoegen(scores, deelcomp):
        """ aan elke score de team naam en vsg toevoegen """

        sporterboog_pks = scores.values_list('sporterboog__pk', flat=True)

        deelnemers = (RegioCompetitieSchutterBoog
                      .objects
                      .filter(deelcompetitie=deelcomp,
                              sporterboog__pk__in=sporterboog_pks))

        ronde_teams = (RegiocompetitieRondeTeam
                       .objects
                       .select_related('team')
                       .prefetch_related('deelnemers_feitelijk')
                       .filter(team__deelcompetitie=deelcomp,
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

        wedstrijd_pk = kwargs['wedstrijd_pk'][:6]     # afkappen geeft beveiliging
        wedstrijd, deelcomp, ronde = bepaal_wedstrijd_en_deelcomp_of_404(wedstrijd_pk)

        context['wedstrijd'] = wedstrijd
        context['deelcomp'] = deelcomp

        if not mag_deelcomp_wedstrijd_wijzigen(wedstrijd, self.functie_nu, deelcomp):
            raise PermissionDenied()

        context['is_controle'] = self.is_controle
        context['is_akkoord'] = wedstrijd.uitslag.is_bevroren

        if self.is_controle:
            context['url_geef_akkoord'] = reverse('CompScores:uitslag-accorderen',
                                                  kwargs={'wedstrijd_pk': wedstrijd.pk})

        scores = (wedstrijd
                  .uitslag
                  .scores
                  .filter(type=SCORE_TYPE_SCORE)
                  .exclude(waarde=SCORE_WAARDE_VERWIJDERD)
                  .select_related('sporterboog',
                                  'sporterboog__boogtype',
                                  'sporterboog__sporter',
                                  'sporterboog__sporter__bij_vereniging')
                  .order_by('sporterboog__sporter__lid_nr',
                            'sporterboog__pk'))                 # belangrijk ivm zelfde volgorde by dynamisch toevoegen
        context['scores'] = scores

        self._team_naam_toevoegen(scores, deelcomp)

        context['url_check_nhbnr'] = reverse('CompScores:dynamic-check-nhbnr')
        context['url_opslaan'] = reverse('CompScores:dynamic-scores-opslaan')
        context['url_deelnemers_ophalen'] = reverse('CompScores:dynamic-deelnemers-ophalen')

        teams = (RegiocompetitieTeam
                 .objects
                 .filter(deelcompetitie=deelcomp)
                 .select_related('vereniging'))
        for team in teams:
            team.naam_str = team.maak_team_naam_kort()
        context['teams'] = teams

        # plan = wedstrijd.competitiewedstrijdenplan_set.all()[0]
        # ronde = DeelcompetitieRonde.objects.get(plan=plan)

        if self.rol_nu == Rollen.ROL_RCL:
            context['url_terug'] = reverse('CompScores:scores-rcl',
                                           kwargs={'deelcomp_pk': deelcomp.pk})
        else:
            context['url_terug'] = reverse('CompScores:wedstrijden-scores')

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp.competitie.pk)
        return context


class WedstrijdUitslagControlerenView(WedstrijdUitslagInvoerenView):

    """ Deze view laat de RCL de uitslag van een wedstrijd aanpassen en accorderen """

    is_controle = True

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'ik geef akkoord voor deze uitslag'
            gebruikt wordt door de RCL.
        """

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        wedstrijd_pk = kwargs['wedstrijd_pk'][:6]     # afkappen geeft beveiliging
        wedstrijd, deelcomp, _ = bepaal_wedstrijd_en_deelcomp_of_404(wedstrijd_pk)

        if not mag_deelcomp_wedstrijd_wijzigen(wedstrijd, functie_nu, deelcomp):
            raise PermissionDenied()

        uitslag = wedstrijd.uitslag
        if not uitslag.is_bevroren:
            uitslag.is_bevroren = True
            uitslag.save()

        url = reverse('CompScores:uitslag-controleren',
                      kwargs={'wedstrijd_pk': wedstrijd.pk})

        return HttpResponseRedirect(url)


class DynamicDeelnemersOphalenView(UserPassesTestMixin, View):

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_RCL, Rollen.ROL_HWL, Rollen.ROL_WL)

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'waarschijnlijke deelnemers ophalen' gebruikt wordt

            Dit is een POST by design, om caching te voorkomen.
        """

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            # garbage in
            raise Http404('Geen valide verzoek')

        try:
            deelcomp_pk = int(str(data['deelcomp_pk'])[:6])   # afkappen voor extra veiligheid
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(laag=LAAG_REGIO,
                             pk=deelcomp_pk))
        except (KeyError, ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        try:
            wedstrijd_pk = int(str(data['wedstrijd_pk'])[:6])   # afkappen voor extra veiligheid
            wedstrijd = (CompetitieWedstrijd
                         .objects
                         .get(pk=wedstrijd_pk))
        except (KeyError, ValueError, CompetitieWedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        sporters, teams = bepaal_waarschijnlijke_deelnemers(deelcomp.competitie.afstand, deelcomp, wedstrijd)

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

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_RCL, Rollen.ROL_HWL, Rollen.ROL_WL)

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Zoek' gebruikt wordt
        """

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            # garbage in
            raise Http404('Geen valide verzoek')

        # zoek een
        # print('data: %s' % repr(data))

        try:
            lid_nr = int(str(data['lid_nr'])[:6])               # afkappen voor extra veiligheid
            wedstrijd_pk = int(str(data['wedstrijd_pk'])[:6])   # afkappen voor extra veiligheid
            wedstrijd = CompetitieWedstrijd.objects.get(pk=wedstrijd_pk)
        except (KeyError, ValueError, CompetitieWedstrijd.DoesNotExist):
            # garbage in
            raise Http404('Geen valide verzoek')

        plan = wedstrijd.competitiewedstrijdenplan_set.all()[0]

        # zoek de ronde erbij
        # deze hoort al bij een competitie type (indoor / 25m1pijl)
        ronde = (DeelcompetitieRonde
                 .objects
                 .select_related('deelcompetitie',
                                 'deelcompetitie__nhb_regio',
                                 'deelcompetitie__competitie')
                 .get(plan=plan))

        # zoek schuttersboog die ingeschreven zijn voor deze competitie
        competitie = ronde.deelcompetitie.competitie

        out = dict()

        deelnemers = (RegioCompetitieSchutterBoog
                      .objects
                      .select_related('sporterboog',
                                      'sporterboog__boogtype',
                                      'sporterboog__sporter',
                                      'sporterboog__sporter__bij_vereniging')
                      .filter(deelcompetitie__competitie=competitie,
                              sporterboog__sporter__lid_nr=lid_nr))

        if len(deelnemers) == 0:
            out['fail'] = 1         # is niet ingeschreven voor deze competitie
        else:

            out['deelnemers'] = list()

            for deelnemer in deelnemers:
                sporterboog = deelnemer.sporterboog
                sporter = sporterboog.sporter
                boog = sporterboog.boogtype

                # volgende blok wordt een paar keer uitgevoerd, maar dat maak niet uit
                out['vereniging'] = str(sporter.bij_vereniging)
                out['regio'] = str(sporter.bij_vereniging.regio)
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
                    if not ronde.deelcompetitie.regio_heeft_vaste_teams:
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

        return JsonResponse(out)


class DynamicScoresOpslaanView(UserPassesTestMixin, View):

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_RCL, Rollen.ROL_HWL, Rollen.ROL_WL)

    @staticmethod
    def laad_wedstrijd_of_404(data):
        try:
            wedstrijd_pk = int(str(data['wedstrijd_pk'])[:6])   # afkappen geeft beveiliging
            wedstrijd = (CompetitieWedstrijd
                         .objects
                         .select_related('uitslag')
                         .prefetch_related('uitslag__scores')
                         .get(pk=wedstrijd_pk))
        except (KeyError, ValueError, CompetitieWedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        return wedstrijd

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
                          afstand_meter=uitslag.afstand_meter)
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
                pk = int(str(key)[:6])     # afkappen geeft beveiliging
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
                waarde = int(str(value)[:4])   # afkappen geeft beveiliging
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
        except json.JSONDecodeError:
            # garbage in
            raise Http404('Geen valide verzoek')

        # print('data:', repr(data))

        wedstrijd = self.laad_wedstrijd_of_404(data)
        uitslag = wedstrijd.uitslag
        if not uitslag:
            raise Http404('Geen wedstrijduitslag')

        # controleer toestemming om scores op te slaan voor deze wedstrijd

        plannen = wedstrijd.competitiewedstrijdenplan_set.all()
        if plannen.count() < 1:
            # wedstrijd met andere bedoeling
            raise Http404('Geen wedstrijdenplan')

        ronde = DeelcompetitieRonde.objects.get(plan=plannen[0])

        rol_nu, functie_nu = rol_get_huidige_functie(request)
        if not mag_deelcomp_wedstrijd_wijzigen(wedstrijd, functie_nu, ronde.deelcompetitie):
            raise PermissionDenied('Geen toegang')

        # voorkom wijzigingen bevroren wedstrijduitslag
        if rol_nu in (Rollen.ROL_HWL, Rollen.ROL_WL) and uitslag.is_bevroren:
            raise Http404('Uitslag mag niet meer gewijzigd worden')

        door_account = request.user
        when = timezone.now()

        self.scores_opslaan(uitslag, data, when, door_account)

        out = {'done': 1}
        return JsonResponse(out)


class WedstrijdUitslagBekijkenView(TemplateView):

    """ Deze view toont de uitslag van een wedstrijd """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPSCORES_BEKIJKEN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        wedstrijd_pk = kwargs['wedstrijd_pk'][:6]     # afkappen geeft beveiliging
        wedstrijd, deelcomp, ronde = bepaal_wedstrijd_en_deelcomp_of_404(wedstrijd_pk)

        scores = (wedstrijd
                  .uitslag
                  .scores
                  .filter(type=SCORE_TYPE_SCORE)
                  .exclude(waarde=SCORE_WAARDE_VERWIJDERD)
                  .select_related('sporterboog',
                                  'sporterboog__boogtype',
                                  'sporterboog__sporter'))

        # maak een opzoek tabel voor de huidige vereniging van elke sporterboog
        sporterboog_pks = [score.sporterboog.pk for score in scores]
        regioschutters = (RegioCompetitieSchutterBoog
                          .objects
                          .select_related('sporterboog',
                                          'bij_vereniging')
                          .filter(sporterboog__pk__in=sporterboog_pks))

        sporterboog2vereniging = dict()
        for regioschutter in regioschutters:
            sporterboog2vereniging[regioschutter.sporterboog.pk] = regioschutter.bij_vereniging
        # for

        for score in scores:
            score.schutter_str = score.sporterboog.sporter.volledige_naam()
            score.boog_str = score.sporterboog.boogtype.beschrijving
            try:
                score.vereniging_str = str(sporterboog2vereniging[score.sporterboog.pk])
            except KeyError:
                # unlikely inconsistency
                score.vereniging_str = "?"
        # for

        te_sorteren = [(score.vereniging_str, score.schutter_str, score.boog_str, score) for score in scores]
        te_sorteren.sort()
        scores = [score for _, _, _, score in te_sorteren]

        context['scores'] = scores
        context['wedstrijd'] = wedstrijd
        context['deelcomp'] = deelcomp
        context['ronde'] = ronde

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp.competitie.pk)
        return context


class ScoresRegioTeamsView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de RCL de mogelijkheid om voor de teamcompetitie de juiste individuele scores
        te selecteren voor sporters die meer dan 1 score neergezet hebben (inhalen/voorschieten).
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPSCORES_TEAMS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_RCL

    @staticmethod
    def _bepaal_teams_en_scores(deelcomp):
        alle_regels = list()

        # sporters waarvan we de scores op moeten zoeken
        sporterboog_pks = list()

        used_score_pks = list()

        deelnemer2sporter_cache = dict()        # [deelnemer_pk] = (sporterboog_pk, naam_str)
        for deelnemer in (RegioCompetitieSchutterBoog
                          .objects
                          .select_related('sporterboog', 'sporterboog__sporter')
                          .filter(deelcompetitie=deelcomp)):

            sporter = deelnemer.sporterboog.sporter
            tup = (deelnemer.sporterboog.pk, "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam()))
            deelnemer2sporter_cache[deelnemer.pk] = tup
        # for

        for poule in (RegiocompetitieTeamPoule
                      .objects
                      .prefetch_related('teams')
                      .filter(deelcompetitie=deelcomp)
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
                                           'team__klasse__team')
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

                klasse_str = ronde_team.team.klasse.team.beschrijving
                if klasse_str != prev_klasse:
                    regel.klasse_str = klasse_str
                    prev_klasse = klasse_str

                regel.deelnemers = deelnemers = list()
                for deelnemer in (ronde_team
                                  .deelnemers_feitelijk
                                  .all()):

                    sporterboog_pk, naam_str = deelnemer2sporter_cache[deelnemer.pk]
                    sporterboog_pks.append(sporterboog_pk)

                    deelnemer.naam_str = naam_str
                    deelnemer.sporterboog_pk = sporterboog_pk
                    deelnemer.gevonden_scores = None
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
        score2wedstrijd = dict()

        # haal alle wedstrijdplannen van deze deelcompetitie op
        plan_pks = (DeelcompetitieRonde
                    .objects
                    .filter(deelcompetitie=deelcomp)
                    .values_list('plan__pk', flat=True))

        # doorloop alle wedstrijden van deze plannen
        # de wedstrijd heeft een datum en uitslag met scores
        for wedstrijd in (CompetitieWedstrijd
                          .objects
                          .select_related('uitslag')
                          .prefetch_related('uitslag__scores')
                          .exclude(uitslag=None)
                          .filter(competitiewedstrijdenplan__in=plan_pks)):

            # noteer welke scores interessant zijn
            # en de koppeling naar de wedstrijd, voor de datum
            for score in wedstrijd.uitslag.scores.all():
                score2wedstrijd[score.pk] = wedstrijd
            # for
        # for

        sporterboog2wedstrijdscores = dict()        # [sporterboog_pk] = [(score, wedstrijd), ...]
        early_date = datetime.date(year=2000, month=1, day=1)

        # doorloop alle scores van de relevante sporters
        for score in (Score
                      .objects
                      .select_related('sporterboog')
                      .exclude(waarde=SCORE_WAARDE_VERWIJDERD)
                      .filter(sporterboog__pk__in=sporterboog_pks)):

            score.block_selection = (score.pk in used_score_pks)

            try:
                wedstrijd = score2wedstrijd[score.pk]
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
                tup = (1, wedstrijd.datum_wanneer, wedstrijd.tijd_begin_wedstrijd, wedstrijd.pk, wedstrijd, score)

                pk = score.sporterboog.pk
                try:
                    sporterboog2wedstrijdscores[pk].append(tup)
                except KeyError:
                    # voeg een "niet geschoten" optie toe
                    nul_score = Score(waarde=0, pk='geen')
                    nul_score.block_selection = False
                    sporterboog2wedstrijdscores[pk] = [(3, early_date, 0, 0, None, nul_score)]     # 0-score

                    sporterboog2wedstrijdscores[pk].append(tup)
        # for

        fake_score_pk = 0
        for regel in alle_regels:
            for deelnemer in regel.deelnemers:
                try:
                    tups = sporterboog2wedstrijdscores[deelnemer.sporterboog_pk]
                except KeyError:
                    # geen score voor deze sporter
                    deelnemer.gevonden_scores = list()
                    pass
                else:
                    # sorteer de gevonden scores op wedstrijddatum
                    tups.sort()
                    deelnemer.gevonden_scores = [(wedstrijd, score) for _, _, _, _, wedstrijd, score in tups]
                    aantal = len(tups)
                    for _, score in deelnemer.gevonden_scores:
                        if score.block_selection:
                            aantal -= 1
                    # for
                    deelnemer.keuze_nodig = (aantal > 1)
                    if deelnemer.keuze_nodig:
                        deelnemer.id_radio = "id_score_%s" % deelnemer.sporterboog_pk
                        first_score = None
                        first_select = True
                        for wedstrijd, score in deelnemer.gevonden_scores:
                            if not score.block_selection:
                                if not first_score:
                                    first_score = score
                                if wedstrijd:
                                    score.id_radio = "id_score_%s" % score.pk
                                else:
                                    fake_score_pk += 1
                                    score.id_radio = "id_fake_%s" % fake_score_pk
                                score.is_selected = (score.pk in regel.score_pks_feitelijk)
                                if score.is_selected:
                                    first_select = False
                        # for

                        # als er geen score gekozen was, kies dan de 'Niet geschoten' optie
                        if first_select and first_score:
                            first_score.is_selected = True
            # for
        # for

        return alle_regels

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen geeft beveiliging
            deelcomp = DeelCompetitie.objects.get(pk=deelcomp_pk,
                                                  laag=LAAG_REGIO)
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        if deelcomp.functie != functie_nu:
            # niet de beheerder
            raise PermissionDenied()

        if not deelcomp.regio_organiseert_teamcompetitie:
            raise Http404('Geen teamcompetitie in deze regio')

        context['deelcomp'] = deelcomp

        if 1 <= deelcomp.huidige_team_ronde <= 7:
            context['alle_regels'] = self._bepaal_teams_en_scores(deelcomp)
            context['url_opslaan'] = reverse('CompScores:selecteer-team-scores',
                                             kwargs={'deelcomp_pk': deelcomp.pk})

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp.competitie.pk)
        return context

    def post(self, request, *args, **kwargs):

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen geeft beveiliging
            deelcomp = DeelCompetitie.objects.get(pk=deelcomp_pk,
                                                  laag=LAAG_REGIO)
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        if deelcomp.functie != functie_nu:
            # niet de beheerder
            raise PermissionDenied()

        if not deelcomp.regio_organiseert_teamcompetitie:
            raise Http404('Geen teamcompetitie in deze regio')

        alle_regels = self._bepaal_teams_en_scores(deelcomp)

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
                if deelnemer.keuze_nodig:
                    score_pk_str = request.POST.get(deelnemer.id_radio, '')[:10]       # afkappen voor de veiligheid
                    if score_pk_str and score_pk_str != 'geen':
                        try:
                            score_pk = int(score_pk_str)
                        except (ValueError, TypeError):
                            raise Http404('Verkeerde parameter')

                        for wedstrijd, score in deelnemer.gevonden_scores:
                            if wedstrijd and score.pk == score_pk:
                                # gevonden!
                                team_scores.append(score.pk)
                                break
                        # for
                else:
                    for wedstrijd, score in deelnemer.gevonden_scores:
                        if wedstrijd and not score.block_selection:
                            team_scores.append(score.pk)
            # for
        # for

        for ronde_team, score_pks in ronde_teams.values():
            ronde_team.scores_feitelijk.set(score_pks)
        # for

        # trigger de achtergrondtaak om de team scores opnieuw te berekenen
        update_uitslag_teamcompetitie()

        url = reverse('CompScores:scores-rcl', kwargs={'deelcomp_pk': deelcomp.pk})
        return HttpResponseRedirect(url)


# end of file
