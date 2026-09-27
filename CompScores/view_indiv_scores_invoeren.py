# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from CompLaagRegio.models import RegioDeelnemer, RegioTeam, RegioRondeTeam
from CompScores.helpers import mag_deelcomp_wedstrijd_wijzigen, bepaal_match_en_deelcomp_of_404
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Score.definities import SCORE_WAARDE_VERWIJDERD, SCORE_TYPE_SCORE

TEMPLATE_COMPSCORES_INVOEREN = 'compscores/scores-invoeren.dtl'


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

        deelnemers = (RegioDeelnemer
                      .objects
                      .filter(regiocomp=deelcomp,
                              sporterboog__pk__in=sporterboog_pks))

        ronde_teams = (RegioRondeTeam
                       .objects
                       .select_related('team')
                       .prefetch_related('deelnemers_feitelijk')
                       .filter(team__regiocomp=deelcomp,
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

        match_pk = kwargs['match_pk'][:7]     # afkappen voor de veiligheid
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

        if deelcomp.regio_organiseert_teamcompetitie:
            context['team_pk2naam'] = team_pk2naam = dict()
            team_pk2naam[0] = '-'
            for team in (RegioTeam
                         .objects
                         .filter(regiocomp=deelcomp)
                         .select_related('vereniging')):
                team_pk2naam[team.pk] = team.maak_team_naam_kort()
            # for

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

        match_pk = kwargs['match_pk'][:7]     # afkappen voor de veiligheid
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


# end of file
