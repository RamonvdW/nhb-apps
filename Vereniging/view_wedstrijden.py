# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import (DeelcompetitieRonde, RegioCompetitieSchutterBoog, RegiocompetitieTeam,
                               INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_2, INSCHRIJF_METHODE_3)
from Competitie.operations.wedstrijdcapaciteit import bepaal_waarschijnlijke_deelnemers, bepaal_blazoen_behoefte
from Functie.rol import Rollen, rol_get_huidige_functie, rol_get_beschrijving
from Plein.menu import menu_dynamics
from Wedstrijden.models import CompetitieWedstrijd

TEMPLATE_WEDSTRIJDEN = 'vereniging/wedstrijden.dtl'
TEMPLATE_WAARSCHIJNLIJKE_DEELNEMERS = 'vereniging/waarschijnlijke-deelnemers.dtl'


class WedstrijdenView(UserPassesTestMixin, TemplateView):

    """ Toon de SEC, HWL, WL de wedstrijden die aan deze vereniging toegekend zijn
        of door deze vereniging georganiseerd worden.
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

        pks = (DeelcompetitieRonde
               .objects
               .filter(deelcompetitie__is_afgesloten=False,
                       plan__wedstrijden__vereniging=self.functie_nu.nhb_ver)
               .values_list('plan__wedstrijden', flat=True))

        wedstrijden = (CompetitieWedstrijd
                       .objects
                       .filter(pk__in=pks)
                       .order_by('datum_wanneer', 'tijd_begin_wedstrijd'))

        context['geen_wedstrijden'] = True
        for wedstrijd in wedstrijden:
            # voor competitiewedstrijden wordt de beschrijving ingevuld
            # als de instellingen van de ronde opgeslagen worden
            # dit is slechts fall-back
            if wedstrijd.beschrijving == "":
                # als deze wedstrijd bij een competitieronde hoort,
                # maak er dan een passende beschrijving voor

                # CompetitieWedstrijd --> CompetitieWedstrijdenPlan --> DeelcompetitieRonde
                plan = wedstrijd.competitiewedstrijdenplan_set.all()[0]
                ronde = plan.deelcompetitieronde_set.all()[0]
                wedstrijd.beschrijving = "%s - %s" % (ronde.deelcompetitie.competitie.beschrijving, ronde.beschrijving)

            msg = wedstrijd.beschrijving
            pos = msg.find(' - ')
            if pos > 0:
                wedstrijd.beschrijving1 = msg[:pos].strip()
                wedstrijd.beschrijving2 = msg[pos+3:].strip()
            else:
                wedstrijd.beschrijving1 = msg
                wedstrijd.beschrijving2 = ''

            wedstrijd.toon_geen_uitslag = True
            heeft_uitslag = (wedstrijd.uitslag and wedstrijd.uitslag.scores.count() > 0)
            mag_wijzigen = self.uitslag_invoeren and not (wedstrijd.uitslag and wedstrijd.uitslag.is_bevroren)
            if self.rol_nu in (Rollen.ROL_HWL, Rollen.ROL_WL) and mag_wijzigen:
                # mag uitslag wijzigen
                url = reverse('Competitie:wedstrijd-uitslag-invoeren',
                              kwargs={'wedstrijd_pk': wedstrijd.pk})
                if heeft_uitslag:
                    wedstrijd.url_uitslag_aanpassen = url
                else:
                    wedstrijd.url_score_invoeren = url
                wedstrijd.toon_geen_uitslag = False

                wedstrijd.url_team_samenstelling = reverse('Competitie:wedstrijd-team-samenstelling',
                                                           kwargs={'wedstrijd_pk': wedstrijd.pk})
            else:
                if heeft_uitslag:
                    wedstrijd.url_uitslag_bekijken = reverse('Competitie:wedstrijd-bekijk-uitslag',
                                                             kwargs={'wedstrijd_pk': wedstrijd.pk})
                    wedstrijd.toon_geen_uitslag = False

            # link naar de waarschijnlijke deelnemerslijst
            if self.rol_nu in (Rollen.ROL_HWL, Rollen.ROL_WL) and not (wedstrijd.uitslag and wedstrijd.uitslag.is_bevroren):
                wedstrijd.url_waarschijnlijke_deelnemers = reverse('Vereniging:waarschijnlijke-deelnemers',
                                                                   kwargs={'wedstrijd_pk': wedstrijd.pk})

            context['geen_wedstrijden'] = False
        # for

        context['vereniging'] = self.functie_nu.nhb_ver
        context['huidige_rol'] = rol_get_beschrijving(self.request)
        context['wedstrijden'] = wedstrijden
        context['uitslag_invoeren'] = self.uitslag_invoeren

        menu_dynamics(self.request, context, actief='vereniging')
        return context


class WedstrijdenUitslagInvoerenView(WedstrijdenView):

    uitslag_invoeren = True


class WaarschijnlijkeDeelnemersView(UserPassesTestMixin, TemplateView):

    """ Toon de HWL of WL de waarschijnlijke deelnemerslijst voor een wedstrijd bij deze vereniging
    """

    # class variables shared by all instances
    template_name = TEMPLATE_WAARSCHIJNLIJKE_DEELNEMERS
    uitslag_invoeren = False
    raise_exception = True  # genereer PermissionDefined als test_func False terug geeft

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

        try:
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])
            wedstrijd = (CompetitieWedstrijd
                         .objects
                         .select_related('vereniging')
                         .get(pk=wedstrijd_pk))
        except (ValueError, CompetitieWedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        msg = wedstrijd.beschrijving
        pos = msg.find(' - ')
        if pos > 0:
            wedstrijd.beschrijving1 = msg[:pos].strip()
            wedstrijd.beschrijving2 = msg[pos+3:].strip()
        else:
            wedstrijd.beschrijving1 = msg
            wedstrijd.beschrijving2 = ''

        plan = wedstrijd.competitiewedstrijdenplan_set.all()[0]
        ronde = plan.deelcompetitieronde_set.all()[0]
        deelcomp = ronde.deelcompetitie
        afstand = deelcomp.competitie.afstand

        context['deelcomp'] = deelcomp
        context['wedstrijd'] = wedstrijd
        context['vastgesteld'] = timezone.now()
        context['is_25m1p'] = (afstand == '25')

        sporters, teams = bepaal_waarschijnlijke_deelnemers(afstand, deelcomp, wedstrijd)
        context['sporters'] = sporters

        context['blazoenen'] = bepaal_blazoen_behoefte(afstand, sporters, teams)

        # prep de view
        nr = 1
        for sporter in sporters:
            sporter.volg_nr = nr
            nr += 1
        # for

        menu_dynamics(self.request, context, actief='vereniging')
        return context


# end of file
