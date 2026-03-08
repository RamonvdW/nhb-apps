# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from CompLaagBond.models import KampBK, TeamBK
from CompLaagRayon.models import DeelnemerRK
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie

TEMPLATE_COMPBOND_VERTEAMS = 'complaagbond/hwl-teams.dtl'


class TeamsBkView(UserPassesTestMixin, TemplateView):

    """ Laat de HWL de teams beheren die door deze vereniging opgesteld
        worden voor de rayonkampioenschappen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPBOND_VERTEAMS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_HWL

    @staticmethod
    def _get_deelkamp_bk(deelkamp_pk) -> KampBK:
        # haal de gevraagde kampioenschap op
        try:
            deelkamp_pk = int(deelkamp_pk[:6])  # afkappen voor de veiligheid
            deelkamp = (KampBK
                        .objects
                        .select_related('competitie')
                        .get(pk=deelkamp_pk,
                             is_afgesloten=False))
        except (ValueError, KampBK.DoesNotExist):
            raise Http404('Kampioenschap niet gevonden')

        comp = deelkamp.competitie
        comp.bepaal_fase()

        if not ('N' <= comp.fase_teams <= 'P'):
            raise Http404('Competitie is niet in de juiste fase')

        return deelkamp

    def _get_bk_teams(self, deelkamp: KampBK):
        bk_teams = (TeamBK
                    .objects
                    .filter(kamp=deelkamp,
                            vereniging=self.functie_nu.vereniging)
                    .select_related('vereniging',
                                    'team_type')
                    .order_by('volg_nr'))

        for team in bk_teams:
            team.leden = list()
            for lid in team.gekoppelde_leden.select_related('sporterboog__sporter').all():
                team.leden.append(lid)
            # for

        return bk_teams

    def _get_bk_team_invallers(self, deelkamp: KampBK):
        # BK team bestaat uit gerechtigde RK deelnemers
        deelnemers = (DeelnemerRK
                      .objects
                      .filter(kamp__competitie=deelkamp.competitie,
                              bij_vereniging=self.functie_nu.vereniging)
                      .select_related('sporterboog',
                                      'sporterboog__sporter',
                                      'sporterboog__boogtype')
                      .order_by('sporterboog__boogtype__volgorde',
                                '-gemiddelde'))                     # sterkste bovenaan

        return deelnemers

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['ver'] = self.functie_nu.vereniging

        # zoek de regiocompetitie waar de regio teams voor in kunnen stellen
        context['deelkamp'] = deelkamp = self._get_deelkamp_bk(kwargs['deelkamp_pk'])

        context['bk_teams'] = self._get_bk_teams(deelkamp)

        context['invallers'] = self._get_bk_team_invallers(deelkamp)

        comp = deelkamp.competitie
        url_overzicht = reverse('Vereniging:overzicht')
        anker = '#competitie_%s' % comp.pk
        context['kruimels'] = (
            (url_overzicht, 'Beheer vereniging'),
            (url_overzicht + anker, comp.beschrijving.replace(' competitie', '')),
            (None, 'Teams BK'),
        )

        return context


# end of file
