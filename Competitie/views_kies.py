# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from django.templatetags.static import static
from CompBeheer.operations import is_competitie_openbaar_voor_rol
from Competitie.models import Competitie
from Competitie.operations import bepaal_startjaar_nieuwe_competitie
from Functie.definities import Rol
from Functie.rol import rol_get_huidige, rol_get_beschrijving


TEMPLATE_COMPETITIE_KIES_SEIZOEN = 'competitie/kies.dtl'


class CompetitieKiesView(TemplateView):

    """ deze view wordt gebruik om een keuze te laten maken uit de beschikbare bondscompetities. """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_KIES_SEIZOEN

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.actuele_regio_comps = list()

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        rol_nu = rol_get_huidige(self.request)

        link_naar_beheer = rol_nu in (Rol.ROL_BB, Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL)

        context['competities'] = comps = list()

        begin_jaar = bepaal_startjaar_nieuwe_competitie()
        eerdere_comp = dict()
        seizoen_afsluiten = 0
        vorig_jaar = None

        for comp in (Competitie
                     .objects
                     .exclude(is_afgesloten=True)
                     .order_by('begin_jaar',
                               'afstand')):

            comp.bepaal_fase()
            if comp.fase_indiv == comp.fase_teams == 'Q':
                seizoen_afsluiten += 1

            if comp.begin_jaar == begin_jaar:
                begin_jaar = None           # geen nieuwe competitie nodig

            comp.break_row = False
            if comp.begin_jaar != vorig_jaar:
                if vorig_jaar is not None:
                    comp.break_row = True
                vorig_jaar = comp.begin_jaar

            comp.is_openbaar = is_competitie_openbaar_voor_rol(comp, rol_nu)

            if comp.is_openbaar:
                comps.append(comp)

                if comp.is_indoor():
                    comp.img_src = static('plein/badge_discipline_indoor.png')
                else:
                    comp.img_src = static('plein/badge_discipline_25m1p.png')

                if link_naar_beheer:
                    comp.card_url = reverse('CompBeheer:overzicht',
                                            kwargs={'comp_pk': comp.pk})
                else:
                    comp.card_url = reverse('Competitie:overzicht',
                                            kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url()})

                if comp.fase_indiv < 'C':
                    comp.text = "Hier worden de voorbereidingen voor getroffen voor de volgende bondscompetitie."
                else:
                    comp.text = "Alle informatie en uitslagen van de actuele bondscompetitie."

                if comp.fase_indiv == 'C' and rol_nu == Rol.ROL_SPORTER:
                    context['toon_inschrijven'] = True

                if comp.fase_indiv >= 'C':
                    self.actuele_regio_comps.append(comp)

            if comp.afstand in eerdere_comp:
                comp.is_volgend_seizoen = True
            eerdere_comp[comp.afstand] = True
        # for

        if rol_nu in (Rol.ROL_BB, Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL, Rol.ROL_HWL):
            context['toon_rol'] = True
            context['huidige_rol'] = rol_get_beschrijving(self.request)

            # Verenigingen
            if rol_nu in (Rol.ROL_RCL, Rol.ROL_HWL):
                tekst = "Overzicht van de verenigingen in jouw regio"
            elif rol_nu == Rol.ROL_RKO:
                tekst = "Overzicht van de verenigingen, accommodaties en indeling in clusters in jouw rayon."
            else:
                tekst = "Landelijk overzicht van de verenigingen, accommodaties en indeling in clusters."
            context['tekst_verenigingen'] = tekst

            if rol_nu == Rol.ROL_BB:
                context['toon_management'] = True

                # als er nog geen competitie is voor het huidige jaar, geeft de BB dan de optie om deze op te starten
                if begin_jaar is not None:
                    context['nieuwe_seizoen'] = "%s/%s" % (begin_jaar, begin_jaar+1)
                    context['url_seizoen_opstarten'] = reverse('CompBeheer:instellingen-volgende-competitie')

                if seizoen_afsluiten > 0:
                    context['url_seizoen_afsluiten'] = reverse('CompBeheer:bb-seizoen-afsluiten')

            context['toon_beheerders_algemeen'] = (rol_nu == Rol.ROL_HWL)

            if rol_nu in (Rol.ROL_BB, Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL):
                context['toon_management'] = True
                context['url_statistiek'] = reverse('CompBeheer:statistiek')
            else:
                context['toon_management'] = False

        context['kruimels'] = (
            (None, 'Bondscompetities'),
        )

        return context


# end of file
