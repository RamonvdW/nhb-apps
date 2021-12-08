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

TEMPLATE_WEDSTRIJDEN = 'compscores/wedstrijden.dtl'
TEMPLATE_WAARSCHIJNLIJKE_DEELNEMERS = 'compscores/waarschijnlijke-deelnemers.dtl'
TEMPLATE_WAARSCHIJNLIJKE_DEELNEMERS_RK_BK = 'compscores/waarschijnlijke-deelnemers-rk-bk.dtl'


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
                    wedstrijd.url_waarschijnlijke_deelnemers = reverse('CompScores:waarschijnlijke-deelnemers-rk-bk',
                                                                       kwargs={'wedstrijd_pk': wedstrijd.pk})
                else:
                    wedstrijd.url_waarschijnlijke_deelnemers = reverse('CompScores:waarschijnlijke-deelnemers',
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
        ronde = plan.deelcompetitieronde_set.select_related('deelcompetitie', 'deelcompetitie__competitie').all()[0]
        deelcomp = ronde.deelcompetitie
        afstand = deelcomp.competitie.afstand

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

        menu_dynamics(self.request, context, actief='vereniging')       # TODO: competitie
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
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])
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


class WaarschijnlijkeDeelnemersKampioenschapView(UserPassesTestMixin, TemplateView):

    """ Toon de HWL of WL de waarschijnlijke deelnemerslijst voor een wedstrijd bij deze vereniging
    """

    # class variables shared by all instances
    template_name = TEMPLATE_WAARSCHIJNLIJKE_DEELNEMERS_RK_BK
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
                         .prefetch_related('indiv_klassen',
                                           'team_klassen')
                         .get(pk=wedstrijd_pk))
        except (ValueError, CompetitieWedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        plan = wedstrijd.competitiewedstrijdenplan_set.all()[0]
        deelcomp = plan.deelcompetitie_set.select_related('competitie').all()[0]
        comp = deelcomp.competitie

        if deelcomp.laag == LAAG_RK:
            wedstrijd.is_rk = True
            wedstrijd.beschrijving = "Rayonkampioenschap"
        else:
            wedstrijd.is_bk = True
            wedstrijd.beschrijving = "Bondskampioenschap"

        heeft_indiv = heeft_teams = False
        beschr = list()

        klasse_indiv_pks = list()
        klasse_team_pks = list()
        wedstrijd.klassen_lijst = klassen_lijst = list()
        for klasse in wedstrijd.indiv_klassen.all():
            klassen_lijst.append(str(klasse))
            klasse_indiv_pks.append(klasse.pk)
            if not heeft_indiv:
                heeft_indiv = True
                beschr.append('Individueel')
        # for
        for klasse in wedstrijd.team_klassen.all():
            klassen_lijst.append(str(klasse))
            klasse_team_pks.append(klasse.pk)
            if not heeft_teams:
                heeft_teams = True
                beschr.append('Teams')
        # for

        context['deelcomp'] = deelcomp
        context['wedstrijd'] = wedstrijd
        context['vastgesteld'] = timezone.now()
        context['heeft_indiv'] = heeft_indiv
        context['heeft_teams'] = heeft_teams
        context['beschrijving'] = "%s %s" % (wedstrijd.beschrijving, " en ".join(beschr))

        # zoek de deelnemers erbij
        if heeft_indiv:
            deelnemers = (KampioenschapSchutterBoog
                          .objects
                          .filter(deelcompetitie=deelcomp,
                                  klasse__indiv__pk__in=klasse_indiv_pks)
                          .select_related('sporterboog',
                                          'sporterboog__sporter',
                                          'bij_vereniging',
                                          'klasse')
                          .order_by('klasse',
                                    'rank'))
            context['deelnemers_indiv'] = deelnemers

            prev_klasse = None
            for deelnemer in deelnemers:
                if deelnemer.klasse != prev_klasse:
                    deelnemer.break_before = True
                    prev_klasse = deelnemer.klasse
                deelnemer.ver_nr = deelnemer.bij_vereniging.ver_nr
                deelnemer.ver_naam = deelnemer.bij_vereniging.naam
                deelnemer.lid_nr = deelnemer.sporterboog.sporter.lid_nr
                deelnemer.volledige_naam = deelnemer.sporterboog.sporter.volledige_naam()
                deelnemer.gemiddelde_str = "%.3f" % deelnemer.gemiddelde
                deelnemer.gemiddelde_str.replace('.', ',')
            # for

        if heeft_teams:
            teams = (KampioenschapTeam
                     .objects
                     .filter(deelcompetitie=deelcomp,
                             klasse__team__pk__in=klasse_team_pks)
                     .select_related('vereniging')
                     .all())
            context['deelnemers_teams'] = teams

            volg_nr = 0
            prev_klasse = None
            for team in teams:
                if team.klasse != prev_klasse:
                    team.break_before = True
                    prev_klasse = team.klasse
                volg_nr += 1
                team.volg_nr = volg_nr
                team.ver_nr = team.vereniging.ver_nr
                team.ver_naam = team.vereniging.naam
            # for

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return context


# end of file
