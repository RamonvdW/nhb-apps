# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.db.models import F
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.definities import DEEL_BK, DEEL_RK, DEELNAME_NEE
from Competitie.models import (Competitie,
                               RegiocompetitieSporterBoog, RegiocompetitieTeam,
                               KampioenschapSporterBoog, KampioenschapTeam)
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige
from Plein.menu import menu_dynamics
from Sporter.models import Sporter


TEMPLATE_COMPETITIE_STATISTIEK = 'compbeheer/bb-statistiek.dtl'


class CompetitieStatistiekView(UserPassesTestMixin, TemplateView):
    """ Deze view biedt statistiek over de competities """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_STATISTIEK
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL)

    @staticmethod
    def _tel_aantallen(context, actuele_comps):
        context['toon_aantal_inschrijvingen'] = True

        context['totaal_18m_indiv'] = 0
        context['aantal_18m_teams_niet_af'] = 0

        context['totaal_25m_indiv'] = 0
        context['aantal_25m_teams_niet_af'] = 0

        aantal_18m_teams = dict()
        aantal_25m_teams = dict()
        for regio_nr in range(101, 116+1):
            aantal_18m_teams[regio_nr] = 0
            aantal_25m_teams[regio_nr] = 0
        # for

        pks = list()
        for comp in actuele_comps:
            pks.append(comp.pk)
            aantal_indiv = (RegiocompetitieSporterBoog
                            .objects
                            .filter(regiocompetitie__competitie=comp)
                            .count())

            qset = (RegiocompetitieTeam
                    .objects
                    .filter(regiocompetitie__competitie=comp)
                    .select_related('vereniging__regio__rayon'))
            aantal_teams_ag_nul = qset.filter(aanvangsgemiddelde__lt=0.001).count()

            if comp.afstand == '18':
                context['totaal_18m_indiv'] = aantal_indiv
                context['aantal_18m_teams_niet_af'] = aantal_teams_ag_nul
            else:
                context['totaal_25m_indiv'] = aantal_indiv
                context['aantal_25m_teams_niet_af'] = aantal_teams_ag_nul

            for team in qset:
                regio_nr = team.vereniging.regio.regio_nr
                if comp.afstand == '18':
                    aantal_18m_teams[regio_nr] += 1
                else:
                    aantal_25m_teams[regio_nr] += 1
            # for
        # for

        context['aantal_18m_teams'] = list()
        context['aantal_25m_teams'] = list()
        context['totaal_18m_teams'] = 0
        context['totaal_25m_teams'] = 0
        for regio_nr in range(101, 116+1):
            context['aantal_18m_teams'].append(aantal_18m_teams[regio_nr])
            context['aantal_25m_teams'].append(aantal_25m_teams[regio_nr])
            context['totaal_18m_teams'] += aantal_18m_teams[regio_nr]
            context['totaal_25m_teams'] += aantal_25m_teams[regio_nr]
        # for

        aantal_18m_rayon = dict()
        aantal_25m_rayon = dict()
        aantal_18m_regio = dict()
        aantal_25m_regio = dict()
        aantal_18m_geen_rk = dict()
        aantal_25m_geen_rk = dict()
        aantal_zelfstandig_18m_regio = dict()
        aantal_zelfstandig_25m_regio = dict()
        aantal_leden_regio = dict()

        for rayon_nr in range(1, 4+1):
            aantal_18m_rayon[rayon_nr] = 0
            aantal_25m_rayon[rayon_nr] = 0
            aantal_18m_geen_rk[rayon_nr] = 0
            aantal_25m_geen_rk[rayon_nr] = 0
        # for

        for regio_nr in range(101, 116+1):
            aantal_18m_regio[regio_nr] = 0
            aantal_25m_regio[regio_nr] = 0
            aantal_zelfstandig_18m_regio[regio_nr] = 0
            aantal_zelfstandig_25m_regio[regio_nr] = 0
            aantal_leden_regio[regio_nr] = 0
        # for

        for deelnemer in (RegiocompetitieSporterBoog
                          .objects
                          .filter(regiocompetitie__competitie__pk__in=pks)
                          .select_related('sporterboog__sporter',
                                          'sporterboog__sporter__account',
                                          'bij_vereniging__regio__rayon',
                                          'aangemeld_door',
                                          'regiocompetitie__competitie')):

            rayon_nr = deelnemer.bij_vereniging.regio.rayon.rayon_nr
            regio_nr = deelnemer.bij_vereniging.regio.regio_nr
            zelfstandig = deelnemer.aangemeld_door == deelnemer.sporterboog.sporter.account

            if deelnemer.regiocompetitie.competitie.afstand == '18':
                aantal_18m_rayon[rayon_nr] += 1
                aantal_18m_regio[regio_nr] += 1
                if not deelnemer.inschrijf_voorkeur_rk_bk:
                    aantal_18m_geen_rk[rayon_nr] += 1
                if zelfstandig:
                    aantal_zelfstandig_18m_regio[regio_nr] += 1
            else:
                aantal_25m_rayon[rayon_nr] += 1
                aantal_25m_regio[regio_nr] += 1
                if not deelnemer.inschrijf_voorkeur_rk_bk:
                    aantal_25m_geen_rk[rayon_nr] += 1
                if zelfstandig:
                    aantal_zelfstandig_25m_regio[regio_nr] += 1
        # for

        context['aantal_18m_rayon'] = list()
        context['aantal_25m_rayon'] = list()
        context['aantal_18m_geen_rk'] = list()
        context['aantal_25m_geen_rk'] = list()
        for rayon_nr in range(1, 4+1):
            context['aantal_18m_rayon'].append(aantal_18m_rayon[rayon_nr])
            context['aantal_25m_rayon'].append(aantal_25m_rayon[rayon_nr])
            context['aantal_18m_geen_rk'].append(aantal_18m_geen_rk[rayon_nr])
            context['aantal_25m_geen_rk'].append(aantal_25m_geen_rk[rayon_nr])
        # for

        context['aantal_18m_regio'] = list()
        context['aantal_25m_regio'] = list()
        for regio_nr in range(101, 116+1):
            context['aantal_18m_regio'].append(aantal_18m_regio[regio_nr])
            context['aantal_25m_regio'].append(aantal_25m_regio[regio_nr])
        # for

        qset = (RegiocompetitieSporterBoog
                .objects
                .filter(regiocompetitie__competitie__pk__in=pks)
                .select_related('sporterboog',
                                'sporterboog__sporter__account')
                .distinct('sporterboog'))

        aantal_sportersboog = qset.count()
        context['aantal_sporters'] = qset.distinct('sporterboog__sporter').count()
        context['aantal_multiboog'] = aantal_sportersboog - context['aantal_sporters']
        context['aantal_zelfstandig'] = qset.filter(aangemeld_door=F('sporterboog__sporter__account')).count()

        for sporter in (Sporter
                        .objects
                        .select_related('bij_vereniging__regio')
                        .filter(is_actief_lid=True)
                        .exclude(bij_vereniging=None)):

            regio_nr = sporter.bij_vereniging.regio.regio_nr
            if regio_nr >= 101:
                aantal_leden_regio[regio_nr] += 1
        # for

        context['perc_zelfstandig_18m_regio'] = perc_zelfstandig_18m_regio = list()
        context['perc_zelfstandig_25m_regio'] = perc_zelfstandig_25m_regio = list()
        context['perc_leden_18m_regio'] = perc_leden_18m_regio = list()
        context['perc_leden_25m_regio'] = perc_leden_25m_regio = list()
        for regio_nr in range(101, 116+1):
            aantal = aantal_18m_regio[regio_nr]
            if aantal > 0:
                perc_str = '%.1f' % ((aantal_zelfstandig_18m_regio[regio_nr] / aantal) * 100.0)
            else:
                perc_str = '0.0'
            perc_zelfstandig_18m_regio.append(perc_str)

            aantal = aantal_25m_regio[regio_nr]
            if aantal > 0:
                perc_str = '%.1f' % ((aantal_zelfstandig_25m_regio[regio_nr] / aantal) * 100.0)
            else:
                perc_str = '0.0'
            perc_zelfstandig_25m_regio.append(perc_str)

            aantal = aantal_leden_regio[regio_nr]
            if aantal > 0:
                perc_str = '%.1f' % ((aantal_18m_regio[regio_nr] / aantal) * 100.0)
                perc_leden_18m_regio.append(perc_str)

                perc_str = '%.1f' % ((aantal_25m_regio[regio_nr] / aantal) * 100.0)
                perc_leden_25m_regio.append(perc_str)
            else:
                perc_str = '0.0'
                perc_leden_18m_regio.append(perc_str)
                perc_leden_25m_regio.append(perc_str)
        # for

        if aantal_sportersboog > 0:
            context['procent_zelfstandig'] = '%.1f' % ((context['aantal_zelfstandig'] / aantal_sportersboog) * 100.0)

        for afstand in (18, 25):
            context['geplaatst_rk_%sm' % afstand] = geplaatst_rk = list()
            context['deelnemers_rk_%sm' % afstand] = deelnemers_rk = list()
            context['in_uitslag_rk_%sm' % afstand] = in_uitslag_rk = list()
            context['teams_rk_%sm' % afstand] = teams_rk = list()

            qset = (KampioenschapSporterBoog
                    .objects
                    .filter(kampioenschap__competitie__afstand=afstand,
                            kampioenschap__competitie__pk__in=pks,
                            kampioenschap__deel=DEEL_RK))

            qset_teams = (KampioenschapTeam
                          .objects
                          .filter(kampioenschap__competitie__afstand=afstand,
                                  kampioenschap__competitie__pk__in=pks,
                                  kampioenschap__deel=DEEL_RK))

            totaal1 = totaal2 = totaal3 = totaal4 = 0
            for rayon_nr in range(1, 4+1):
                qset_rayon = qset.filter(kampioenschap__rayon__rayon_nr=rayon_nr)

                aantal = qset_rayon.count()
                geplaatst_rk.append(aantal)
                totaal1 += aantal

                qset_rayon = qset_rayon.exclude(deelname=DEELNAME_NEE)
                aantal = qset_rayon.count()
                deelnemers_rk.append(aantal)
                totaal2 += aantal

                aantal = qset_rayon.filter(result_rank__gte=1, result_rank__lt=100).count()
                in_uitslag_rk.append(aantal)

                totaal3 += aantal

                aantal = qset_teams.filter(kampioenschap__rayon__rayon_nr=rayon_nr).count()
                teams_rk.append(aantal)

                totaal4 += aantal
            # for

            geplaatst_rk.append(totaal1)
            deelnemers_rk.append(totaal2)
            in_uitslag_rk.append(totaal3)
            teams_rk.append(totaal4)

            qset_bk = (KampioenschapSporterBoog
                       .objects
                       .filter(kampioenschap__competitie__afstand=afstand,
                               kampioenschap__competitie__pk__in=pks,
                               kampioenschap__deel=DEEL_BK))
            context['deelnemers_bk_%sm' % afstand] = qset_bk.count()

            qset_bk = qset_bk.filter(result_rank__gte=1, result_rank__lt=100)
            context['uitslag_bk_%sm' % afstand] = qset_bk.count()

            qset_bk = (KampioenschapTeam
                       .objects
                       .filter(kampioenschap__competitie__afstand=afstand,
                               kampioenschap__competitie__pk__in=pks,
                               kampioenschap__deel=DEEL_BK))
            context['teams_bk_%sm' % afstand] = qset_bk.count()

            qset_bk = qset_bk.filter(result_rank__gte=1, result_rank__lt=100)
            context['uitslag_teams_bk_%sm' % afstand] = qset_bk.count()
        # for

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        actuele_comps = list()
        afstand_gevonden = list()       # afstand

        for comp in (Competitie
                     .objects
                     .exclude(is_afgesloten=True)
                     .order_by('afstand',
                               '-begin_jaar')):     # nieuwste eerst

            if comp.afstand not in afstand_gevonden:
                comp.bepaal_fase()
                comp.bepaal_openbaar(self.rol_nu)

                if comp.is_openbaar:
                    if comp.fase_indiv >= 'C':
                        actuele_comps.append(comp)
                        afstand_gevonden.append(comp.afstand)
                        context['seizoen'] = comp.maak_seizoen_str()
        # for

        self._tel_aantallen(context, actuele_comps)

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (None, 'Statistiek')
        )

        menu_dynamics(self.request, context)
        return context


# end of file
