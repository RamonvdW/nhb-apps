# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import DeelcompetitieRonde, DeelCompetitie, LAAG_REGIO, LAAG_RK, LAAG_BK
from Functie.rol import Rollen, rol_get_huidige_functie, rol_get_beschrijving
from Plein.menu import menu_dynamics
from Wedstrijden.models import CompetitieWedstrijd

TEMPLATE_WEDSTRIJDEN = 'compscores/wedstrijden.dtl'


class WedstrijdenView(UserPassesTestMixin, TemplateView):

    """ Toon de SEC, HWL, WL de competitiewedstrijden die aan deze vereniging toegekend zijn.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN
    uitslag_invoeren = False
    raise_exception = True      # genereer PermissionDefined als test_func False terug geeft

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

        pks1 = list(DeelcompetitieRonde
                    .objects
                    .filter(deelcompetitie__is_afgesloten=False,
                            plan__wedstrijden__vereniging=self.functie_nu.nhb_ver,
                            deelcompetitie__laag=LAAG_REGIO)
                    .values_list('plan__wedstrijden', flat=True))

        pks2 = list(DeelCompetitie
                    .objects
                    .filter(is_afgesloten=False,
                            plan__wedstrijden__vereniging=self.functie_nu.nhb_ver,
                            laag__in=(LAAG_RK, LAAG_BK))
                    .exclude(plan__wedstrijden=None)                # excludes when ManyToMany is empty
                    .values_list('plan__wedstrijden', flat=True))

        pks = list(pks1) + list(pks2)

        is_mix = (1 <= len(pks2) < len(pks1))

        wedstrijden = (CompetitieWedstrijd
                       .objects
                       .filter(pk__in=pks)
                       .order_by('datum_wanneer', 'tijd_begin_wedstrijd'))

        for wedstrijd in wedstrijden:
            # voor competitiewedstrijden wordt de beschrijving ingevuld
            # als de instellingen van de ronde opgeslagen worden
            # dit is slechts fall-back
            if wedstrijd.beschrijving == "":
                # als deze wedstrijd bij een competitieronde hoort,
                # maak een passende beschrijving voor

                # CompetitieWedstrijd --> CompetitieWedstrijdenPlan --> DeelcompetitieRonde / DeelCompetitie
                plan = wedstrijd.competitiewedstrijdenplan_set.all()[0]
                if plan.deelcompetitieronde_set.count() > 0:
                    ronde = plan.deelcompetitieronde_set.select_related('deelcompetitie', 'deelcompetitie__competitie').all()[0]
                    wedstrijd.beschrijving1 = ronde.deelcompetitie.competitie.beschrijving
                    wedstrijd.beschrijving2 = ronde.beschrijving
                else:
                    deelcomp = plan.deelcompetitie_set.select_related('competitie').all()[0]
                    wedstrijd.beschrijving1 = deelcomp.competitie.beschrijving
                    if deelcomp.laag == LAAG_RK:
                        wedstrijd.beschrijving2 = "Rayonkampioenschappen"
                    else:
                        wedstrijd.beschrijving2 = "Bondskampioenschappen"
            else:
                msg = wedstrijd.beschrijving
                pos = msg.find(' - ')
                if pos > 0:
                    wedstrijd.beschrijving1 = msg[:pos].strip()
                    wedstrijd.beschrijving2 = msg[pos+3:].strip()
                else:
                    wedstrijd.beschrijving1 = msg
                    wedstrijd.beschrijving2 = ''

            wedstrijd.is_rk = (wedstrijd.beschrijving2 == 'Rayonkampioenschappen')
            wedstrijd.is_bk = (wedstrijd.beschrijving2 == 'Bondskampioenschappen')
            wedstrijd.opvallen = (wedstrijd.is_rk or wedstrijd.is_bk) and is_mix

            wedstrijd.toon_geen_uitslag = True
            heeft_uitslag = (wedstrijd.uitslag and wedstrijd.uitslag.scores.count() > 0)
            mag_wijzigen = self.uitslag_invoeren and not (wedstrijd.uitslag and wedstrijd.uitslag.is_bevroren)
            if self.rol_nu in (Rollen.ROL_HWL, Rollen.ROL_WL) and mag_wijzigen:
                # mag uitslag wijzigen
                url = reverse('CompScores:uitslag-invoeren',
                              kwargs={'wedstrijd_pk': wedstrijd.pk})
                if heeft_uitslag:
                    wedstrijd.url_uitslag_aanpassen = url
                else:
                    wedstrijd.url_score_invoeren = url
                wedstrijd.toon_geen_uitslag = False
            else:
                if heeft_uitslag:
                    wedstrijd.url_uitslag_bekijken = reverse('CompScores:uitslag-bekijken',
                                                             kwargs={'wedstrijd_pk': wedstrijd.pk})
                    wedstrijd.toon_geen_uitslag = False

            # link naar de waarschijnlijke deelnemerslijst
            if self.rol_nu in (Rollen.ROL_HWL, Rollen.ROL_WL) and not (wedstrijd.uitslag and wedstrijd.uitslag.is_bevroren):
                if wedstrijd.is_rk or wedstrijd.is_bk:
                    wedstrijd.url_waarschijnlijke_deelnemers = reverse('CompRayon:download-formulier',
                                                                       kwargs={'wedstrijd_pk': wedstrijd.pk})
                else:
                    wedstrijd.url_waarschijnlijke_deelnemers = reverse('CompRegio:waarschijnlijke-deelnemers',
                                                                       kwargs={'wedstrijd_pk': wedstrijd.pk})

            context['geen_wedstrijden'] = False
        # for

        context['vereniging'] = self.functie_nu.nhb_ver
        context['huidige_rol'] = rol_get_beschrijving(self.request)
        context['wedstrijden'] = wedstrijden
        context['uitslag_invoeren'] = self.uitslag_invoeren

        menu_dynamics(self.request, context, actief='vereniging')
        return context


class WedstrijdenScoresView(WedstrijdenView):

    uitslag_invoeren = True


# end of file
