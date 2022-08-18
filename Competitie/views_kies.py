# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.db.models import F
from django.views.generic import TemplateView
from django.templatetags.static import static
from Competitie.models import RegioCompetitieSchutterBoog, RegiocompetitieTeam
from Competitie.operations import bepaal_startjaar_nieuwe_competitie
from Functie.rol import Rollen, rol_get_huidige, rol_get_beschrijving
from Plein.menu import menu_dynamics
from .models import Competitie


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

        context['aantal_18m_indiv'] = 0
        context['aantal_18m_teams'] = 0
        context['aantal_18m_teams_niet_af'] = 0

        context['aantal_25m_indiv'] = 0
        context['aantal_25m_teams'] = 0
        context['aantal_25m_teams_niet_af'] = 0

        pks = list()
        for comp in self.actuele_regio_comps:
            pks.append(comp.pk)
            aantal_indiv = (RegioCompetitieSchutterBoog
                            .objects
                            .filter(deelcompetitie__competitie=comp)
                            .count())

            qset = RegiocompetitieTeam.objects.filter(deelcompetitie__competitie=comp)
            aantal_teams = qset.count()
            aantal_teams_ag_nul = qset.filter(aanvangsgemiddelde__lt=0.001).count()

            if comp.afstand == '18':
                context['aantal_18m_indiv'] = aantal_indiv
                context['aantal_18m_teams'] = aantal_teams
                context['aantal_18m_teams_niet_af'] = aantal_teams_ag_nul
            else:
                context['aantal_25m_indiv'] = aantal_indiv
                context['aantal_25m_teams'] = aantal_teams
                context['aantal_25m_teams_niet_af'] = aantal_teams_ag_nul
        # for

        qset = (RegioCompetitieSchutterBoog
                .objects
                .filter(deelcompetitie__competitie__pk__in=pks)
                .select_related('sporterboog__sporter__bij_vereniging__regio__rayon'))

        context['aantal_r1'] = qset.filter(sporterboog__sporter__bij_vereniging__regio__rayon=1).count()
        context['aantal_r2'] = qset.filter(sporterboog__sporter__bij_vereniging__regio__rayon=2).count()
        context['aantal_r3'] = qset.filter(sporterboog__sporter__bij_vereniging__regio__rayon=3).count()
        context['aantal_r4'] = qset.filter(sporterboog__sporter__bij_vereniging__regio__rayon=4).count()

        qset_geen_rk = qset.filter(inschrijf_voorkeur_rk_bk=False)
        context['aantal_geen_rk1'] = qset_geen_rk.filter(sporterboog__sporter__bij_vereniging__regio__rayon=1).count()
        context['aantal_geen_rk2'] = qset_geen_rk.filter(sporterboog__sporter__bij_vereniging__regio__rayon=2).count()
        context['aantal_geen_rk3'] = qset_geen_rk.filter(sporterboog__sporter__bij_vereniging__regio__rayon=3).count()
        context['aantal_geen_rk4'] = qset_geen_rk.filter(sporterboog__sporter__bij_vereniging__regio__rayon=4).count()

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

                if 'B' <= comp.fase <= 'G':
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
