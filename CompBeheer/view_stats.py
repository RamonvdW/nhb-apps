# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
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

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL)

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

        for values in (RegiocompetitieSporterBoog       # 14ms
                       .objects
                       .filter(regiocompetitie__competitie__pk__in=pks)
                       .values_list('bij_vereniging__regio__rayon_nr',
                                    'bij_vereniging__regio__regio_nr',
                                    'aangemeld_door',
                                    'sporterboog__sporter__account',
                                    'regiocompetitie__competitie__afstand',
                                    'inschrijf_voorkeur_rk_bk')):

            rayon_nr, regio_nr, aangemeld_door, account, afstand, voorkeur_rk_bk = values
            zelfstandig = (aangemeld_door == account)

            if afstand == '18':
                aantal_18m_rayon[rayon_nr] += 1
                aantal_18m_regio[regio_nr] += 1
                if not voorkeur_rk_bk:
                    aantal_18m_geen_rk[rayon_nr] += 1
                if zelfstandig:
                    aantal_zelfstandig_18m_regio[regio_nr] += 1
            else:
                aantal_25m_rayon[rayon_nr] += 1
                aantal_25m_regio[regio_nr] += 1
                if not voorkeur_rk_bk:
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

        if True:
            pks1 = list()
            pks2 = list()
            zelfstandig = 0
            for values in (RegiocompetitieSporterBoog       # 10,5ms
                           .objects
                           .filter(regiocompetitie__competitie__pk__in=pks)
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
                if comp.fase_indiv >= 'C':
                    actuele_comps.append(comp)
                    afstand_gevonden.append(comp.afstand)
                    context['seizoen'] = comp.maak_seizoen_str()
        # for

        context['heeft_data'] = len(actuele_comps) > 0

        if len(actuele_comps):
            self._tel_aantallen(context, actuele_comps)

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (None, 'Statistiek')
        )

        return context


# end of file
