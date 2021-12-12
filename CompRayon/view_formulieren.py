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

TEMPLATE_WAARSCHIJNLIJKE_DEELNEMERS_RK_BK = 'comprayon/waarschijnlijke-deelnemers-rk-bk.dtl'


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
        if comp.afstand == '18':
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

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
                deelnemer.gemiddelde_str = deelnemer.gemiddelde_str.replace('.', ',')
            # for

        if heeft_teams:
            teams = (KampioenschapTeam
                     .objects
                     .filter(deelcompetitie=deelcomp,
                             klasse__team__pk__in=klasse_team_pks)
                     .select_related('vereniging')
                     .prefetch_related('gekoppelde_schutters')
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
                team.sterkte_str = "%.1f" % (team.aanvangsgemiddelde * aantal_pijlen)
                team.sterkte_str = team.sterkte_str.replace('.', ',')

                for lid in team.gekoppelde_schutters.all():
                    sporter = lid.sporterboog.sporter
                    lid.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())
                    lid.gem_str = lid.gemiddelde
                # for
            # for

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return context


# end of file
