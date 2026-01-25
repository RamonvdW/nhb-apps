# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.utils import timezone
from django.db.models import Count
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.definities import DEEL_BK, DEEL_RK, DEELNAME_NEE
from Competitie.models import (Competitie, Regiocompetitie, RegiocompetitieSporterBoog, RegiocompetitieTeam,
                               KampioenschapSporterBoog, KampioenschapTeam)
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Sporter.models import Sporter
from decimal import Decimal

TEMPLATE_COMPETITIE_STATISTIEK = 'compbeheer/statistiek.dtl'


class CompetitieStatistiekView(UserPassesTestMixin, TemplateView):
    """ Deze view biedt statistiek over de competities """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_STATISTIEK
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None
        self.comp_pks = list()
        self.huidig_jaar = timezone.now().year
        self.age_group_counts_18m_indiv_rk = dict()
        self.age_group_counts_25m_indiv_rk = dict()
        self.age_group_counts_18m_teams_rk = dict()
        self.age_group_counts_25m_teams_rk = dict()

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL)

    def _add_to_age_group(self, age_group_counts: dict, geboorte_jaar: int):
        leeftijd = self.huidig_jaar - geboorte_jaar
        leeftijd = min(leeftijd, 89)  # groep "80 en ouder"
        group = leeftijd // 10
        age_group_counts[group] += 1

    @staticmethod
    def _make_age_groups(age_group_counts: dict, titel) -> tuple[str, int, list]:
        total = sum(age_group_counts.values())
        divider = max(1, total)   # prevent div by zero

        age_groups = [((age * 10),
                       (age * 10)+9,
                       count,
                       int((count * 100) / divider),
                      )
                      for age, count in age_group_counts.items()]
        age_groups.sort()

        return titel, total, age_groups

    def _tel_totalen(self, context, actuele_comps):
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

        self.comp_pks = list()
        for comp in actuele_comps:
            self.comp_pks.append(comp.pk)

            aantal_indiv = (RegiocompetitieSporterBoog
                            .objects
                            .filter(regiocompetitie__competitie=comp)
                            .count())

            floor = Decimal(0.001)
            aantal_teams_ag_nul = 0

            for values in (RegiocompetitieTeam
                           .objects
                           .filter(regiocompetitie__competitie=comp)
                           .values_list('vereniging__regio__regio_nr',
                                        'aanvangsgemiddelde')):

                regio_nr, ag = values

                if ag < floor:                  # pragma: no branch
                    aantal_teams_ag_nul += 1

                if comp.is_indoor():
                    aantal_18m_teams[regio_nr] += 1
                else:
                    aantal_25m_teams[regio_nr] += 1
            # for

            if comp.is_indoor():
                context['totaal_18m_indiv'] = aantal_indiv
                context['aantal_18m_teams_niet_af'] = aantal_teams_ag_nul
            else:
                context['totaal_25m_indiv'] = aantal_indiv
                context['aantal_25m_teams_niet_af'] = aantal_teams_ag_nul
        # for

        context['aantal_18m_teams'] = list()
        context['aantal_25m_teams'] = list()
        context['totaal_18m_teams'] = 0
        context['totaal_25m_teams'] = 0

        regio_organiseert_teamcompetitie = dict()     # ["afstand", regio_nr] = True/False
        for regio_nr in range(101, 116+1):
            regio_organiseert_teamcompetitie[('18', regio_nr)] = False
            regio_organiseert_teamcompetitie[('25', regio_nr)] = False
        # for
        for values in (Regiocompetitie
                       .objects
                       .filter(competitie__in=actuele_comps)
                       .values_list('competitie__afstand',
                                    'regio__regio_nr',
                                    'regio_organiseert_teamcompetitie')):
            afstand, regio_nr, do_teamcompetitie = values
            tup = (afstand, regio_nr)
            regio_organiseert_teamcompetitie[tup] = do_teamcompetitie
        # for

        for regio_nr in range(101, 116+1):
            if regio_organiseert_teamcompetitie['18', regio_nr]:
                context['aantal_18m_teams'].append(aantal_18m_teams[regio_nr])
                context['totaal_18m_teams'] += aantal_18m_teams[regio_nr]
            else:
                context['aantal_18m_teams'].append('-')

            if regio_organiseert_teamcompetitie['25', regio_nr]:
                context['aantal_25m_teams'].append(aantal_25m_teams[regio_nr])
                context['totaal_25m_teams'] += aantal_25m_teams[regio_nr]
            else:
                context['aantal_25m_teams'].append('-')
        # for

    def _tel_regio(self, context):
        aantal_18m_rayon = dict()
        aantal_25m_rayon = dict()
        aantal_18m_regio = dict()
        aantal_25m_regio = dict()
        aantal_18m_geen_rk = dict()
        aantal_25m_geen_rk = dict()
        aantal_zelfstandig_18m_regio = dict()
        aantal_zelfstandig_25m_regio = dict()
        aantal_geen_scores_18m_regio = dict()
        aantal_geen_scores_25m_regio = dict()
        aantal_leden_regio = dict()

        age_group_counts_18m_indiv_regio = dict()       # [groep] = aantal
        age_group_counts_25m_indiv_regio = dict()
        age_group_counts_18m_teams_regio = dict()
        age_group_counts_25m_teams_regio = dict()
        for leeftijd in (1, 10, 20, 30, 40, 50, 60, 70, 80):
            group = leeftijd // 10
            age_group_counts_18m_indiv_regio[group] = 0
            age_group_counts_25m_indiv_regio[group] = 0
            age_group_counts_18m_teams_regio[group] = 0
            age_group_counts_25m_teams_regio[group] = 0
        # for

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
            aantal_geen_scores_18m_regio[regio_nr] = 0
            aantal_geen_scores_25m_regio[regio_nr] = 0
        # for

        hoogste_aantal_scores = 0
        for values in (RegiocompetitieSporterBoog       # 14ms
                       .objects
                       .filter(regiocompetitie__competitie__pk__in=self.comp_pks)
                       .values_list('bij_vereniging__regio__rayon_nr',
                                    'bij_vereniging__regio__regio_nr',
                                    'aangemeld_door',
                                    'sporterboog__sporter__geboorte_datum',
                                    'sporterboog__sporter__account',
                                    'regiocompetitie__competitie__afstand',
                                    'inschrijf_voorkeur_rk_bk',
                                    'aantal_scores')):

            rayon_nr, regio_nr, aangemeld_door, geboorte_datum, account, afstand, voorkeur_rk_bk, aantal_scores = values
            zelfstandig = (aangemeld_door == account)

            if afstand == '18':
                aantal_18m_rayon[rayon_nr] += 1
                aantal_18m_regio[regio_nr] += 1
                if not voorkeur_rk_bk:
                    aantal_18m_geen_rk[rayon_nr] += 1
                if zelfstandig:
                    aantal_zelfstandig_18m_regio[regio_nr] += 1
                if aantal_scores == 0:
                    aantal_geen_scores_18m_regio[regio_nr] += 1

                self._add_to_age_group(age_group_counts_18m_indiv_regio, geboorte_datum.year)
            else:
                aantal_25m_rayon[rayon_nr] += 1
                aantal_25m_regio[regio_nr] += 1
                if not voorkeur_rk_bk:
                    aantal_25m_geen_rk[rayon_nr] += 1
                if zelfstandig:
                    aantal_zelfstandig_25m_regio[regio_nr] += 1
                if aantal_scores == 0:
                    aantal_geen_scores_25m_regio[regio_nr] += 1

                self._add_to_age_group(age_group_counts_25m_indiv_regio, geboorte_datum.year)

            if aantal_scores > hoogste_aantal_scores:
                hoogste_aantal_scores = aantal_scores
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

        if hoogste_aantal_scores > 5:
            context['toon_geen_scores'] = True
            context['aantal_18m_geen_scores'] = list()
            context['aantal_25m_geen_scores'] = list()
            for regio_nr in range(101, 116+1):
                context['aantal_18m_geen_scores'].append(aantal_geen_scores_18m_regio[regio_nr])
                context['aantal_25m_geen_scores'].append(aantal_geen_scores_25m_regio[regio_nr])
            # for

        pks1 = list()
        pks2 = list()
        zelfstandig = 0
        for values in (RegiocompetitieSporterBoog       # 10,5ms
                       .objects
                       .filter(regiocompetitie__competitie__pk__in=self.comp_pks)
                       .values_list('sporterboog__pk',
                                    'sporterboog__sporter__lid_nr',
                                    'sporterboog__sporter__account',
                                    'aangemeld_door')):
            sporterboog_pk, lid_nr, account, aangemeld_door = values
            pks1.append(sporterboog_pk)
            pks2.append(lid_nr)
            if account == aangemeld_door:
                zelfstandig += 1
        # for

        aantal_sportersboog = len(set(pks1))
        context['aantal_sporters'] = len(set(pks2))
        context['aantal_multiboog'] = aantal_sportersboog - context['aantal_sporters']
        context['aantal_zelfstandig'] = zelfstandig

        for regio_nr in (Sporter        # 3,8ms
                         .objects
                         .select_related('bij_vereniging__regio')
                         .filter(is_actief_lid=True)
                         .exclude(bij_vereniging=None)
                         .values_list('bij_vereniging__regio__regio_nr', flat=True)):
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

        for values in (RegiocompetitieSporterBoog
                       .objects
                       .annotate(c=Count('regiocompetitieteam'))
                       .exclude(c=0)
                       .values_list('sporterboog__sporter__geboorte_datum',
                                    'regiocompetitie__competitie__afstand')):
            geboorte_datum, afstand = values

            if afstand == '18':
                self._add_to_age_group(age_group_counts_18m_teams_regio, geboorte_datum.year)
            else:
                self._add_to_age_group(age_group_counts_25m_teams_regio, geboorte_datum.year)
        # for

        context['age_groups_regio'] = (
            self._make_age_groups(age_group_counts_18m_indiv_regio, 'Indoor individueel'),
            self._make_age_groups(age_group_counts_25m_indiv_regio, '25m 1pijl individueel'),
            self._make_age_groups(age_group_counts_18m_teams_regio, 'Indoor teams'),
            self._make_age_groups(age_group_counts_25m_teams_regio, '25m 1pijl teams') )

    def _tel_rk_bk(self, context):
        age_group_counts_18m_indiv_rk = dict()
        age_group_counts_25m_indiv_rk = dict()
        age_group_counts_18m_teams_rk = dict()
        age_group_counts_25m_teams_rk = dict()
        for leeftijd in (1, 10, 20, 30, 40, 50, 60, 70, 80):
            group = leeftijd // 10
            age_group_counts_18m_indiv_rk[group] = 0
            age_group_counts_25m_indiv_rk[group] = 0
            age_group_counts_18m_teams_rk[group] = 0
            age_group_counts_25m_teams_rk[group] = 0
        # for

        for afstand in (18, 25):
            context['geplaatst_rk_%sm' % afstand] = geplaatst_rk = list()
            context['deelnemers_rk_%sm' % afstand] = deelnemers_rk = list()
            context['in_uitslag_rk_%sm' % afstand] = in_uitslag_rk = list()
            context['teams_rk_%sm' % afstand] = teams_rk = list()

            qset = (KampioenschapSporterBoog
                    .objects
                    .filter(kampioenschap__competitie__afstand=afstand,
                            kampioenschap__competitie__pk__in=self.comp_pks,
                            kampioenschap__deel=DEEL_RK)
                    .select_related('sporterboog__sporter')
                    .prefetch_related('kampioenschapteam'))

            qset_teams = (KampioenschapTeam
                          .objects
                          .filter(kampioenschap__competitie__afstand=afstand,
                                  kampioenschap__competitie__pk__in=self.comp_pks,
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

            if afstand == 18:
                age_group_counts = age_group_counts_18m_indiv_rk
            else:
                age_group_counts = age_group_counts_25m_indiv_rk

            for values in qset.values_list('sporterboog__sporter__geboorte_datum'):
                geboorte_datum = values[0]
                self._add_to_age_group(age_group_counts, geboorte_datum.year)
            # for

            if afstand == 18:
                age_group_counts = age_group_counts_18m_teams_rk
            else:
                age_group_counts = age_group_counts_25m_teams_rk

            for values in (qset
                           .annotate(c=Count('kampioenschapteam_gekoppelde_leden'))
                           .exclude(c=0)
                           .values_list('sporterboog__sporter__geboorte_datum')):
                geboorte_datum = values[0]
                self._add_to_age_group(age_group_counts, geboorte_datum.year)
            # for

            qset_bk = (KampioenschapSporterBoog
                       .objects
                       .filter(kampioenschap__competitie__afstand=afstand,
                               kampioenschap__competitie__pk__in=self.comp_pks,
                               kampioenschap__deel=DEEL_BK))
            context['deelnemers_bk_%sm' % afstand] = qset_bk.count()

            qset_bk = qset_bk.filter(result_rank__gte=1, result_rank__lt=100)
            context['uitslag_bk_%sm' % afstand] = qset_bk.count()

            qset_bk = (KampioenschapTeam
                       .objects
                       .filter(kampioenschap__competitie__afstand=afstand,
                               kampioenschap__competitie__pk__in=self.comp_pks,
                               kampioenschap__deel=DEEL_BK))
            context['teams_bk_%sm' % afstand] = qset_bk.count()

            qset_bk = qset_bk.filter(result_rank__gte=1, result_rank__lt=100)
            context['uitslag_teams_bk_%sm' % afstand] = qset_bk.count()
        # for

        context['age_groups_rk'] = (
            self._make_age_groups(age_group_counts_18m_indiv_rk, 'RK Indoor individueel'),
            self._make_age_groups(age_group_counts_25m_indiv_rk, 'RK 25m 1pijl individueel'),
            self._make_age_groups(age_group_counts_18m_teams_rk, 'RK Indoor teams'),
            self._make_age_groups(age_group_counts_25m_teams_rk, 'RK 25m 1pijl teams') )

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        actuele_comps = list()
        afstand_gevonden = list()       # afstand

        # selecteer 1x  18m en 1x 25m competitie
        # begin met de oudste die in de database staat, anders is de eind-statistiek nooit te zijn
        for comp in (Competitie
                     .objects
                     .exclude(is_afgesloten=True)
                     .order_by('afstand',
                               'begin_jaar')):     # oudste eerst

            if comp.afstand not in afstand_gevonden:
                comp.bepaal_fase()
                if comp.fase_indiv >= 'C':
                    actuele_comps.append(comp)
                    afstand_gevonden.append(comp.afstand)
                    context['seizoen'] = comp.maak_seizoen_str()
        # for

        context['heeft_data'] = len(actuele_comps) > 0

        if len(actuele_comps):
            context['toon_aantal_inschrijvingen'] = True
            self._tel_totalen(context, actuele_comps)
            self._tel_regio(context)
            self._tel_rk_bk(context)

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (None, 'Statistiek')
        )

        return context


# end of file
