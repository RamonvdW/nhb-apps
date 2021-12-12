# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404, HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import (DeelcompetitieRonde, RegiocompetitieTeam, DeelCompetitie,
                               KampioenschapSchutterBoog, KampioenschapTeam,
                               LAAG_REGIO, LAAG_RK, LAAG_BK)
from Competitie.operations.wedstrijdcapaciteit import bepaal_waarschijnlijke_deelnemers, bepaal_blazoen_behoefte
from Competitie.menu import menu_dynamics_competitie
from Functie.rol import Rollen, rol_get_huidige_functie, rol_get_beschrijving
from Plein.menu import menu_dynamics
from Wedstrijden.models import CompetitieWedstrijd
import csv

TEMPLATE_WAARSCHIJNLIJKE_DEELNEMERS = 'compscores/waarschijnlijke-deelnemers-regio.dtl'


class WaarschijnlijkeDeelnemersView(UserPassesTestMixin, TemplateView):

    """ Toon de HWL of WL de waarschijnlijke deelnemerslijst voor een wedstrijd bij deze vereniging
    """

    # class variables shared by all instances
    template_name = TEMPLATE_WAARSCHIJNLIJKE_DEELNEMERS
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
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])      # afkappen voor de veiligheid
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
        ronde = plan.deelcompetitieronde_set.select_related('deelcompetitie', 'deelcompetitie__competitie').all()[0]
        deelcomp = ronde.deelcompetitie
        comp = deelcomp.competitie
        afstand = comp.afstand

        context['deelcomp'] = deelcomp
        context['wedstrijd'] = wedstrijd
        context['vastgesteld'] = timezone.now()
        context['is_25m1p'] = (afstand == '25')

        team_pk2naam = dict()
        team_pk2naam[0] = '-'
        for team in RegiocompetitieTeam.objects.filter(deelcompetitie=deelcomp):
            team_pk2naam[team.pk] = team.maak_team_naam_kort()
        # for

        sporters, teams = bepaal_waarschijnlijke_deelnemers(afstand, deelcomp, wedstrijd)
        context['sporters'] = sporters

        for sporter in sporters:
            sporter.in_team_naam = team_pk2naam[sporter.team_pk]
        # for

        context['blazoenen'] = bepaal_blazoen_behoefte(afstand, sporters, teams)

        context['url_download'] = reverse('CompScores:waarschijnlijke-deelnemers-als-bestand',
                                          kwargs={'wedstrijd_pk': wedstrijd.pk})

        # prep de view
        nr = 1
        for sporter in sporters:
            sporter.volg_nr = nr
            nr += 1
        # for

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return context


class WaarschijnlijkeDeelnemersAlsBestandView(UserPassesTestMixin, TemplateView):

    """ Geef de HWL of WL de waarschijnlijke deelnemerslijst voor een wedstrijd bij deze vereniging als bestand
    """

    # class variables shared by all instances
    raise_exception = True  # genereer PermissionDefined als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_WL)

    def get(self, request, *args, **kwargs):
        """ Afhandelen van de GET request waarmee we een bestand terug geven. """

        try:
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])      # afkappen voor de veiligheid
            wedstrijd = (CompetitieWedstrijd
                         .objects
                         .select_related('vereniging')
                         .get(pk=wedstrijd_pk))
        except (ValueError, CompetitieWedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        plan = wedstrijd.competitiewedstrijdenplan_set.all()[0]
        ronde = plan.deelcompetitieronde_set.select_related('deelcompetitie', 'deelcompetitie__competitie').all()[0]
        deelcomp = ronde.deelcompetitie
        afstand = deelcomp.competitie.afstand

        team_pk2naam = dict()
        team_pk2naam[0] = '-'
        for team in RegiocompetitieTeam.objects.filter(deelcompetitie=deelcomp):
            team_pk2naam[team.pk] = team.maak_team_naam_kort()
        # for

        vastgesteld = timezone.now()

        sporters, teams = bepaal_waarschijnlijke_deelnemers(afstand, deelcomp, wedstrijd)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="waarschijnlijke-deelnemers-%s.csv"' % wedstrijd.pk

        writer = csv.writer(response, delimiter=";")      # ; is good for import with dutch regional settings

        toon_teams = deelcomp.regio_organiseert_teamcompetitie

        # voorkeur dagdelen per vereniging
        cols = ['VerNr', 'Vereniging', 'Bondsnummer', 'Naam', 'Boog']
        if toon_teams:
            cols.append('Team gem.')
        cols.append('Blazoen indiv.')
        if toon_teams:
            cols.append('In team')
        cols.append('Notitie')
        writer.writerow(cols)

        for sporter in sporters:
            if hasattr(sporter, 'vereniging_teams'):
                row = ['-', '(' + sporter.ver_naam + ' heeft ' + sporter.vereniging_teams + ')']
                writer.writerow(row)

            row = [sporter.ver_nr, sporter.ver_naam, sporter.lid_nr, sporter.volledige_naam, sporter.boog]

            if toon_teams:
                row.append(sporter.team_gem)

            blazoenen = ' of '.join(sporter.blazoen_str_lijst)
            row.append(blazoenen)

            if toon_teams:
                row.append(team_pk2naam[sporter.team_pk])

            row.append(sporter.notitie)
            writer.writerow(row)
        # for

        return response


# end of file
