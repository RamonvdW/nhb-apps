# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from CompLaagRegio.models import RegioDeelnemer
from CompScores.helpers import bepaal_match_en_deelcomp_of_404
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Score.definities import SCORE_WAARDE_VERWIJDERD, SCORE_TYPE_SCORE

TEMPLATE_COMPSCORES_BEKIJKEN = 'compscores/scores-bekijken.dtl'


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

        match_pk = kwargs['match_pk'][:7]     # afkappen voor de veiligheid
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
        regioschutters = (RegioDeelnemer
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


# end of file
