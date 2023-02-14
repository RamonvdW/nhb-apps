# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from django.templatetags.static import static
from Competitie.models import Competitie
from Competitie.operations import bepaal_startjaar_nieuwe_competitie
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige, rol_get_beschrijving
from Plein.menu import menu_dynamics


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

        link_naar_beheer = rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL)

        context['competities'] = comps = list()

        begin_jaar = bepaal_startjaar_nieuwe_competitie()
        eerdere_comp = dict()
        seizoen_afsluiten = 0

        for comp in (Competitie
                     .objects
                     .exclude(is_afgesloten=True)
                     .order_by('afstand',
                               'begin_jaar')):

            comp.bepaal_fase()
            if comp.fase_indiv == comp.fase_teams == 'Q':
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

                if link_naar_beheer:
                    comp.card_url = reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk})
                else:
                    comp.card_url = reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk})

                if comp.fase_indiv < 'C':
                    comp.text = "Hier worden de voorbereidingen voor getroffen voor de volgende bondscompetitie."
                else:
                    comp.text = "Alle informatie en uitslagen van de actuele bondscompetitie."

                if comp.fase_indiv == 'C' and rol_nu == Rollen.ROL_SPORTER:
                    context['toon_inschrijven'] = True

                if comp.fase_indiv >= 'C':
                    self.actuele_regio_comps.append(comp)

            try:
                if comp.afstand in eerdere_comp:
                    comp.is_volgend_seizoen = True
            except KeyError:
                pass
            eerdere_comp[comp.afstand] = True
        # for

        if rol_nu == Rollen.ROL_BB:
            context['toon_management'] = True

            # als er nog geen competitie is voor het huidige jaar, geeft de BB dan de optie om deze op te starten
            if begin_jaar is not None:
                context['nieuwe_seizoen'] = "%s/%s" % (begin_jaar, begin_jaar+1)
                context['url_seizoen_opstarten'] = reverse('CompBeheer:instellingen-volgende-competitie')

            if seizoen_afsluiten > 0:
                context['url_seizoen_afsluiten'] = reverse('CompBeheer:bb-seizoen-afsluiten')

            context['url_statistiek'] = reverse('CompBeheer:statistiek')

        if rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL):
            context['toon_beheerders'] = True
            context['huidige_rol'] = rol_get_beschrijving(self.request)

        context['kruimels'] = (
            (None, 'Bondscompetities'),
        )

        menu_dynamics(self.request, context)
        return context


# end of file
