# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.definities import DEEL_RK, DEEL_BK
from Competitie.models_competitie import CompetitieMatch
from Competitie.models_laag_regio import RegiocompetitieRonde
from Competitie.models_laag_kamp import Kampioenschap
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving

TEMPLATE_WEDSTRIJDEN = 'compscores/wedstrijden.dtl'


class WedstrijdenView(UserPassesTestMixin, TemplateView):

    """ Toon de SEC, HWL, WL de competitiewedstrijden die aan deze vereniging toegekend zijn.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN
    uitslag_invoeren = False
    toon_rk_bk = True
    raise_exception = True      # genereer PermissionDefined als test_func False terug geeft
    permission_denied_message = 'Geen toegang'
    kruimel = 'Competitie wedstrijden'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_WL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['geen_wedstrijden'] = True

        pks1 = list(RegiocompetitieRonde
                    .objects
                    .filter(regiocompetitie__is_afgesloten=False,
                            matches__vereniging=self.functie_nu.vereniging)
                    .values_list('matches', flat=True))

        if self.toon_rk_bk:
            pks2 = list(Kampioenschap
                        .objects
                        .filter(is_afgesloten=False,
                                rk_bk_matches__vereniging=self.functie_nu.vereniging)
                        .exclude(rk_bk_matches=None)                # excludes when ManyToMany is empty
                        .values_list('rk_bk_matches', flat=True))
        else:
            pks2 = list()

        pks = list(pks1) + list(pks2)

        is_mix = len(pks1) > 0 and len(pks2) > 0

        matches = (CompetitieMatch
                   .objects
                   .filter(pk__in=pks)
                   .prefetch_related('kampioenschap_set',
                                     'regiocompetitieronde_set')
                   .order_by('datum_wanneer',
                             'tijd_begin_wedstrijd'))

        for match in matches:

            rondes = match.regiocompetitieronde_set.all()

            deelkamps = match.kampioenschap_set.all()
            if len(deelkamps) > 0:
                match.deelkamp = deelkamps[0]
            else:
                match.deelkamp = None

            # voor competitiewedstrijden wordt de beschrijving ingevuld
            # als de instellingen van de ronde opgeslagen worden
            # dit is slechts fall-back
            if match.beschrijving == "":
                # maak een passende beschrijving voor deze wedstrijd
                if len(rondes) > 0:
                    ronde = rondes[0]
                    match.beschrijving1 = ronde.regiocompetitie.competitie.beschrijving
                    match.beschrijving2 = ronde.beschrijving
                else:
                    if match.deelkamp:          # pragma: no branch
                        match.beschrijving1 = match.deelkamp.competitie.beschrijving
                        if match.deelkamp.deel == DEEL_RK:
                            match.beschrijving2 = "Rayonkampioenschappen"
                        else:
                            match.beschrijving2 = "Bondskampioenschappen"
            else:
                msg = match.beschrijving
                pos = msg.find(' - ')           # TODO: is dit nog actueel?
                if pos > 0:
                    match.beschrijving1 = msg[:pos].strip()
                    match.beschrijving2 = msg[pos+3:].strip()
                else:
                    match.beschrijving1 = msg
                    match.beschrijving2 = ''

            match.is_rk = (match.deelkamp and match.deelkamp.deel == DEEL_RK)
            match.is_bk = (match.deelkamp and match.deelkamp.deel == DEEL_BK)
            match.opvallen = (match.is_rk or match.is_bk) and is_mix

            match.toon_geen_uitslag = True

            if match.is_rk or match.is_bk:
                # geen knop nodig om de uitslag in te voeren
                match.toon_nvt = True
            else:
                match.toon_nvt = False
                heeft_uitslag = (match.uitslag and match.uitslag.scores.count() > 0)
                mag_wijzigen = self.uitslag_invoeren and not (match.uitslag and match.uitslag.is_bevroren)
                if self.rol_nu in (Rollen.ROL_HWL, Rollen.ROL_WL) and mag_wijzigen:
                    # mag uitslag wijzigen
                    url = reverse('CompScores:uitslag-invoeren',
                                  kwargs={'match_pk': match.pk})
                    if heeft_uitslag:
                        match.url_uitslag_aanpassen = url
                    else:
                        match.url_score_invoeren = url
                    match.toon_geen_uitslag = False
                else:
                    if heeft_uitslag:
                        match.url_uitslag_bekijken = reverse('CompScores:uitslag-bekijken',
                                                             kwargs={'match_pk': match.pk})
                        match.toon_geen_uitslag = False

            # link naar de waarschijnlijke deelnemerslijst
            if self.rol_nu in (Rollen.ROL_HWL, Rollen.ROL_WL) and not (match.uitslag and match.uitslag.is_bevroren):
                if match.is_rk:
                    match.url_lijst = reverse('CompLaagRayon:download-formulier',
                                              kwargs={'match_pk': match.pk})
                elif match.is_bk:
                    match.url_lijst = reverse('CompLaagBond:bk-match-informatie',
                                              kwargs={'match_pk': match.pk})
                    # geen knoppen - formulier wordt door BKO opgestuurd
                    pass

                else:
                    match.url_lijst = reverse('CompLaagRegio:waarschijnlijke-deelnemers',
                                              kwargs={'match_pk': match.pk})

            context['geen_wedstrijden'] = False
        # for

        context['vereniging'] = self.functie_nu.vereniging
        context['huidige_rol'] = rol_get_beschrijving(self.request)
        context['wedstrijden'] = matches
        context['uitslag_invoeren'] = self.uitslag_invoeren

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (None, self.kruimel)
        )

        return context


class WedstrijdenScoresView(WedstrijdenView):

    uitslag_invoeren = True
    toon_rk_bk = False
    kruimel = 'Scores invoeren'


# end of file
