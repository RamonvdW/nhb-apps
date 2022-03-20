# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404, HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import RegiocompetitieTeam, CompetitieMatch
from Competitie.operations.wedstrijdcapaciteit import bepaal_waarschijnlijke_deelnemers, bepaal_blazoen_behoefte
from Functie.rol import Rollen, rol_get_huidige_functie
from Plein.menu import menu_dynamics
import csv

TEMPLATE_WAARSCHIJNLIJKE_DEELNEMERS = 'complaagregio/waarschijnlijke-deelnemers-regio.dtl'


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
            match_pk = int(kwargs['wedstrijd_pk'][:6])      # afkappen voor de veiligheid
            match = (CompetitieMatch
                     .objects
                     .select_related('vereniging')
                     .get(pk=match_pk))
        except (ValueError, CompetitieMatch.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        msg = match.beschrijving
        pos = msg.find(' - ')
        if pos > 0:
            match.beschrijving1 = msg[:pos].strip()
            match.beschrijving2 = msg[pos+3:].strip()
        else:
            match.beschrijving1 = msg
            match.beschrijving2 = ''

        ronde = match.deelcompetitieronde_set.select_related('deelcompetitie', 'deelcompetitie__competitie').all()[0]
        deelcomp = ronde.deelcompetitie
        comp = deelcomp.competitie
        afstand = comp.afstand

        context['deelcomp'] = deelcomp
        context['wedstrijd'] = match
        context['vastgesteld'] = timezone.now()
        context['is_25m1p'] = (afstand == '25')

        team_pk2naam = dict()
        team_pk2naam[0] = '-'
        for team in RegiocompetitieTeam.objects.filter(deelcompetitie=deelcomp):
            team_pk2naam[team.pk] = team.maak_team_naam_kort()
        # for

        sporters, teams = bepaal_waarschijnlijke_deelnemers(afstand, deelcomp, match)
        context['sporters'] = sporters
        context['aantal_regels'] = 2 + len(sporters) + len(team_pk2naam.keys())

        for sporter in sporters:
            sporter.in_team_naam = team_pk2naam[sporter.team_pk]
        # for

        context['blazoenen'] = bepaal_blazoen_behoefte(afstand, sporters, teams)

        context['url_download'] = reverse('CompLaagRegio:waarschijnlijke-deelnemers-als-bestand',
                                          kwargs={'wedstrijd_pk': match.pk})

        # prep de view
        nr = 1
        for sporter in sporters:
            sporter.volg_nr = nr
            nr += 1
        # for

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (reverse('CompScores:wedstrijden'), 'Competitie wedstrijden'),
            (None, 'Deelnemers')
        )

        menu_dynamics(self.request, context)
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
            match_pk = int(kwargs['wedstrijd_pk'][:6])      # afkappen voor de veiligheid
            match = (CompetitieMatch
                     .objects
                     .select_related('vereniging')
                     .get(pk=match_pk))
        except (ValueError, CompetitieMatch.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        rondes = match.deelcompetitieronde_set.select_related('deelcompetitie', 'deelcompetitie__competitie').all()
        if len(rondes) == 0:
            raise Http404('Verkeerde competitie')
        ronde = rondes[0]
        deelcomp = ronde.deelcompetitie
        afstand = deelcomp.competitie.afstand

        team_pk2naam = dict()
        team_pk2naam[0] = '-'
        for team in RegiocompetitieTeam.objects.filter(deelcompetitie=deelcomp):
            team_pk2naam[team.pk] = team.maak_team_naam_kort()
        # for

        vastgesteld = timezone.now()

        sporters, teams = bepaal_waarschijnlijke_deelnemers(afstand, deelcomp, match)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="waarschijnlijke-deelnemers-%s.csv"' % match.pk

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
