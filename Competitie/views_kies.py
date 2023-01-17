# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.db.models import F
from django.views.generic import TemplateView
from django.templatetags.static import static
from Competitie.models import Competitie, RegioCompetitieSchutterBoog, RegiocompetitieTeam
from Competitie.operations import bepaal_startjaar_nieuwe_competitie
from Functie.rol import Rollen, rol_get_huidige, rol_get_beschrijving
from Plein.menu import menu_dynamics
from Sporter.models import Sporter


TEMPLATE_COMPETITIE_KIES_SEIZOEN = 'competitie/kies.dtl'


class CompetitieKiesView(TemplateView):

    """ deze view wordt gebruik om een keuze te laten maken uit de beschikbare bondscompetities. """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_KIES_SEIZOEN

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.actuele_regio_comps = list()

    def _tel_aantallen(self, context):
        context['toon_aantal_inschrijvingen'] = True

        context['totaal_18m_indiv'] = 0
        context['aantal_18m_teams_niet_af'] = 0

        context['totaal_25m_indiv'] = 0
        context['aantal_25m_teams_niet_af'] = 0

        aantal_18m_teams = dict()
        aantal_25m_teams = dict()
        for rayon_nr in range(1, 4+1):
            aantal_18m_teams[rayon_nr] = 0
            aantal_25m_teams[rayon_nr] = 0
        # for

        pks = list()
        for comp in self.actuele_regio_comps:
            pks.append(comp.pk)
            aantal_indiv = (RegioCompetitieSchutterBoog
                            .objects
                            .filter(deelcompetitie__competitie=comp)
                            .count())

            qset = RegiocompetitieTeam.objects.filter(deelcompetitie__competitie=comp).select_related('vereniging__regio__rayon')
            aantal_teams_ag_nul = qset.filter(aanvangsgemiddelde__lt=0.001).count()

            if comp.afstand == '18':
                context['totaal_18m_indiv'] = aantal_indiv
                context['aantal_18m_teams_niet_af'] = aantal_teams_ag_nul
            else:
                context['totaal_25m_indiv'] = aantal_indiv
                context['aantal_25m_teams_niet_af'] = aantal_teams_ag_nul

            for team in qset:
                rayon_nr = team.vereniging.regio.rayon.rayon_nr
                if comp.afstand == '18':
                    aantal_18m_teams[rayon_nr] += 1
                else:
                    aantal_25m_teams[rayon_nr] += 1
            # for
        # for

        context['aantal_18m_teams'] = list()
        context['aantal_25m_teams'] = list()
        context['totaal_18m_teams'] = 0
        context['totaal_25m_teams'] = 0
        for rayon_nr in range(1, 4+1):
            context['aantal_18m_teams'].append(aantal_18m_teams[rayon_nr])
            context['aantal_25m_teams'].append(aantal_25m_teams[rayon_nr])
            context['totaal_18m_teams'] += aantal_18m_teams[rayon_nr]
            context['totaal_25m_teams'] += aantal_25m_teams[rayon_nr]
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

        for deelnemer in (RegioCompetitieSchutterBoog
                          .objects
                          .filter(deelcompetitie__competitie__pk__in=pks)
                          .select_related('sporterboog__sporter',
                                          'sporterboog__sporter__account',
                                          'bij_vereniging__regio__rayon',
                                          'aangemeld_door',
                                          'deelcompetitie__competitie')):

            rayon_nr = deelnemer.bij_vereniging.regio.rayon.rayon_nr
            regio_nr = deelnemer.bij_vereniging.regio.regio_nr
            zelfstandig = deelnemer.aangemeld_door == deelnemer.sporterboog.sporter.account

            if deelnemer.deelcompetitie.competitie.afstand == '18':
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

        qset = (RegioCompetitieSchutterBoog
                .objects
                .filter(deelcompetitie__competitie__pk__in=pks)
                .select_related('sporterboog',
                                'sporterboog__sporter__account')
                .distinct('sporterboog'))

        aantal_sportersboog = qset.count()
        context['aantal_sporters'] = qset.distinct('sporterboog__sporter').count()
        context['aantal_multiboog'] = aantal_sportersboog - context['aantal_sporters']
        context['aantal_zelfstandig'] = qset.filter(aangemeld_door=F('sporterboog__sporter__account')).count()

        for sporter in Sporter.objects.select_related('bij_vereniging__regio').filter(is_actief_lid=True).exclude(bij_vereniging=None):
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

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        rol_nu = rol_get_huidige(self.request)

        context['competities'] = comps = list()

        begin_jaar = bepaal_startjaar_nieuwe_competitie()
        eerdere_comp = dict()
        seizoen_afsluiten = 0

        for comp in (Competitie
                     .objects
                     .exclude(is_afgesloten=True)
                     .order_by('afstand', 'begin_jaar')):

            comp.bepaal_fase()
            if comp.fase == 'S':
                seizoen_afsluiten += 1

            if comp.begin_jaar == begin_jaar:
                begin_jaar = None

            comp.bepaal_openbaar(rol_nu)

            if comp.is_openbaar:
                comps.append(comp)

                if comp.afstand == '18':
                    comp.img_src = static('plein/badge_nhb_indoor.png')
                else:
                    comp.img_src = static('plein/badge_nhb_25m1p.png')

                comp.card_url = reverse('Competitie:overzicht',
                                        kwargs={'comp_pk': comp.pk})
                if comp.fase < 'B':
                    comp.text = "Hier worden de voorbereidingen voor getroffen voor de volgende bondscompetitie."
                else:
                    comp.text = "Alle informatie en uitslagen van de actuele bondscompetitie."

                if comp.fase == 'B' and rol_nu == Rollen.ROL_SPORTER:
                    context['toon_inschrijven'] = True

                if comp.fase >= 'B':
                    self.actuele_regio_comps.append(comp)

            try:
                if comp.afstand in eerdere_comp:
                    comp.is_volgend_seizoen = True
            except KeyError:
                pass
            eerdere_comp[comp.afstand] = True
        # for

        if rol_nu == Rollen.ROL_BB:
            # als er nog geen competitie is voor het huidige jaar, geeft de BB dan de optie om deze op te starten
            if begin_jaar is not None:
                context['nieuwe_seizoen'] = "%s/%s" % (begin_jaar, begin_jaar+1)
                context['url_seizoen_opstarten'] = reverse('Competitie:instellingen-volgende-competitie')
                context['toon_management_competitie'] = True

            if seizoen_afsluiten > 0:
                context['url_seizoen_afsluiten'] = reverse('Competitie:bb-seizoen-afsluiten')
                context['toon_management_competitie'] = True

            self._tel_aantallen(context)

        if rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL):
            context['toon_beheerders'] = True
            context['huidige_rol'] = rol_get_beschrijving(self.request)

        context['kruimels'] = (
            (None, 'Bondscompetities'),
        )

        menu_dynamics(self.request, context)
        return context


# end of file
