# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.definities import DEEL_RK
from Competitie.models import CompetitieTeamKlasse, CompetitieMatch
from CompKampioenschap.operations import MaakTeamsExcel
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie


class FormulierTeamsAlsBestandView(UserPassesTestMixin, TemplateView):

    """ Geef de HWL het ingevulde wedstrijdformulier voor een RK teams wedstrijd bij deze vereniging """

    # class variables shared by all instances
    raise_exception = True  # genereer PermissionDefined als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu in (Rol.ROL_HWL, Rol.ROL_WL)

    def get(self, request, *args, **kwargs):
        """ Afhandelen van de GET request waarmee we een bestand terug geven. """

        try:
            match_pk = int(kwargs['match_pk'][:6])      # afkappen voor de veiligheid
            match = (CompetitieMatch
                     .objects
                     .select_related('vereniging',
                                     'locatie')
                     .get(pk=match_pk,
                          vereniging=self.functie_nu.vereniging))
        except (ValueError, CompetitieMatch.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        try:
            klasse_pk = int(kwargs['klasse_pk'][:6])            # afkappen voor de veiligheid
            team_klasse = (CompetitieTeamKlasse
                           .objects
                           .get(pk=klasse_pk))
        except (ValueError, CompetitieTeamKlasse.DoesNotExist):
            raise Http404('Klasse niet gevonden')

        deelkamp = match.kampioenschap_set.filter(deel=DEEL_RK).first()
        if not deelkamp:
            raise Http404('Geen kampioenschap')

        # comp = self.deelkamp.competitie
        # # TODO: check fase

        maker = MaakTeamsExcel(deelkamp, team_klasse, match)

        try:
            response = maker.vul_excel()
        except RuntimeError as exc:
            msg = exc.args[0]
            raise Http404(msg)

        return response


# end of file
