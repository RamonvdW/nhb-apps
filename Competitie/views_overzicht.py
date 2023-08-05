# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.views.generic import TemplateView
from Competitie.models import Competitie, get_competitie_boog_typen
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige
from Plein.menu import menu_dynamics
from Sporter.models import SporterBoog


TEMPLATE_COMPETITIE_OVERZICHT = 'competitie/overzicht.dtl'


class CompetitieOverzichtView(TemplateView):
    """ Deze view biedt de landing page vanuit het menu aan """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_OVERZICHT

    def _get_uitslagen(self, context, comp):

        # kijk of de uitslagen klaar zijn om te tonen
        context['toon_uitslagen'] = (comp.fase_indiv >= 'C')      # inschrijving is open

        wed_boog = 'r'

        if self.request.user.is_authenticated:
            account = self.request.user

            # als deze sporter ingeschreven is voor de competitie, pak dan het boogtype waarmee hij ingeschreven is

            # kies de eerste wedstrijdboog uit de voorkeuren van sporter
            comp_boogtypen = get_competitie_boog_typen(comp)
            boog_pks = [boogtype.pk for boogtype in comp_boogtypen]

            all_bogen = (SporterBoog
                         .objects
                         .filter(sporter__account=account,
                                 voor_wedstrijd=True,
                                 boogtype__pk__in=boog_pks)
                         .order_by('boogtype__volgorde'))

            if all_bogen.count():
                wed_boog = all_bogen[0].boogtype.afkorting.lower()

            # TODO: zoek ook het team type van het team waarin hij geplaatst is
            # team_type = wed_boog

        team_type = list(comp.teamtypen.order_by('volgorde').values_list('afkorting', flat=True))[0].lower()    # r/r2

        context['url_regio_indiv'] = reverse('CompUitslagen:uitslagen-regio-indiv',
                                             kwargs={'comp_pk': comp.pk,
                                                     'comp_boog': wed_boog})
        context['url_regio_teams'] = reverse('CompUitslagen:uitslagen-regio-teams',
                                             kwargs={'comp_pk': comp.pk,
                                                     'team_type': team_type})

        context['url_rayon_indiv'] = reverse('CompUitslagen:uitslagen-rk-indiv',
                                             kwargs={'comp_pk': comp.pk,
                                                     'comp_boog': wed_boog})
        context['url_rayon_teams'] = reverse('CompUitslagen:uitslagen-rk-teams',
                                             kwargs={'comp_pk': comp.pk,
                                                     'team_type': team_type})

        context['url_bond_indiv'] = reverse('CompUitslagen:uitslagen-bk-indiv',
                                            kwargs={'comp_pk': comp.pk,
                                                    'comp_boog': wed_boog})
        context['url_bond_teams'] = reverse('CompUitslagen:uitslagen-bk-teams',
                                            kwargs={'comp_pk': comp.pk,
                                                    'team_type': team_type})

        tussen_eind = "Tussen" if comp.fase_indiv <= 'G' else "Eind"
        context['text_regio_indiv'] = tussen_eind + 'stand voor de regiocompetitie individueel'
        context['text_regio_teams'] = tussen_eind + 'stand voor de regiocompetitie teams'

        # TODO: ook melden dat dit de tijdelijke deelnemerslijst is (tijdens regiocompetitie)
        if comp.fase_indiv <= 'G':
            tussen_eind = 'Preliminaire lijst'
        elif comp.fase_indiv <= 'L':
            tussen_eind = "Tussenstand"
        else:
            tussen_eind = "Eindstand"
        context['text_rayon_indiv'] = tussen_eind + ' voor de rayonkampioenschappen individueel'

        tussen_eind = "Tussen" if comp.fase_teams <= 'N' else "Eind"
        context['text_rayon_teams'] = tussen_eind + 'stand voor de rayonkampioenschappen teams'

        tussen_eind = "Tussen" if comp.fase_indiv <= 'P' else "Eind"
        context['text_bond_indiv'] = tussen_eind + 'stand voor de landelijke bondskampioenschappen individueel'

        tussen_eind = "Tussen" if comp.fase_teams <= 'P' else "Eind"
        context['text_bond_teams'] = tussen_eind + 'stand voor de landelijke bondskampioenschappen teams'

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            # TODO: externe links naar een oude competitie komen hier --> stuur ze door naar de kies pagina
            raise Http404('Competitie niet gevonden')

        context['comp'] = comp

        comp.bepaal_fase()                     # zet comp.fase
        comp.bepaal_openbaar(Rollen.ROL_NONE)  # zet comp.is_openbaar

        if comp.fase_indiv >= 'C':
            context['toon_uitslagen'] = True
            self._get_uitslagen(context, comp)

        if comp.is_open_voor_inschrijven():
            comp.url_inschrijvingen = reverse('CompInschrijven:lijst-regiocomp-alles',
                                              kwargs={'comp_pk': comp.pk})

        if rol_get_huidige(self.request) in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL):
            context['url_beheer'] = reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk})

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (None, comp.beschrijving.replace(' competitie', ''))
        )

        menu_dynamics(self.request, context)
        return context


# end of file
