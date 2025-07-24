# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from Account.models import get_account
from CompBeheer.operations.toegang import is_competitie_openbaar_voor_rol
from Competitie.models import Competitie, get_competitie_boog_typen
from Competitie.seizoenen import get_comp_pk
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Sporter.models import SporterBoog


TEMPLATE_COMPETITIE_OVERZICHT = 'competitie/overzicht.dtl'
TEMPLATE_COMPETITIE_BESTAAT_NIET = 'competitie/bestaat-niet.dtl'


class CompetitieOverzichtView(TemplateView):
    """ Deze view biedt de landing page vanuit het menu aan """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_OVERZICHT

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comp = None

    def _get_uitslagen(self, context):

        wed_boog = 'r'

        if self.request.user.is_authenticated:

            account = get_account(self.request)

            # als deze sporter ingeschreven is voor de competitie, pak dan het boogtype waarmee hij ingeschreven is

            # kies de eerste wedstrijdboog uit de voorkeuren van sporter
            comp_boogtypen = get_competitie_boog_typen(self.comp)
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

        team_type = list(self.comp
                         .teamtypen
                         .order_by('volgorde')
                         .values_list('afkorting', flat=True))[0].lower()    # r/r2

        context['url_regio_indiv'] = reverse('CompUitslagen:uitslagen-regio-indiv',
                                             kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url(),
                                                     'comp_boog': wed_boog})
        context['url_regio_teams'] = reverse('CompUitslagen:uitslagen-regio-teams',
                                             kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url(),
                                                     'team_type': team_type})

        context['url_rayon_indiv'] = reverse('CompUitslagen:uitslagen-rk-indiv',
                                             kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url(),
                                                     'comp_boog': wed_boog})
        context['url_rayon_teams'] = reverse('CompUitslagen:uitslagen-rk-teams',
                                             kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url(),
                                                     'team_type': team_type})

        context['url_bond_indiv'] = reverse('CompUitslagen:uitslagen-bk-indiv',
                                            kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url(),
                                                    'comp_boog': wed_boog})
        context['url_bond_teams'] = reverse('CompUitslagen:uitslagen-bk-teams',
                                            kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url(),
                                                    'team_type': team_type})

        tussen_eind = "Tussen" if self.comp.fase_indiv <= 'G' else "Eind"
        context['text_regio_indiv'] = tussen_eind + 'stand voor de regiocompetitie individueel'
        context['text_regio_teams'] = tussen_eind + 'stand voor de regiocompetitie teams'

        # TODO: ook melden dat dit de tijdelijke deelnemerslijst is (tijdens regiocompetitie)
        if self.comp.fase_indiv <= 'G':
            tussen_eind = 'Preliminaire lijst'
        elif self.comp.fase_indiv <= 'L':
            tussen_eind = "Tussenstand"
        else:
            tussen_eind = "Eindstand"
        context['text_rayon_indiv'] = tussen_eind + ' voor de rayonkampioenschappen individueel'

        tussen_eind = "Tussen" if self.comp.fase_teams <= 'N' else "Eind"
        context['text_rayon_teams'] = tussen_eind + 'stand voor de rayonkampioenschappen teams'

        tussen_eind = "Tussen" if self.comp.fase_indiv <= 'P' else "Eind"
        context['text_bond_indiv'] = tussen_eind + 'stand voor de landelijke bondskampioenschappen individueel'

        tussen_eind = "Tussen" if self.comp.fase_teams <= 'P' else "Eind"
        context['text_bond_teams'] = tussen_eind + 'stand voor de landelijke bondskampioenschappen teams'

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = get_comp_pk(kwargs['comp_pk_of_seizoen'])
            self.comp = (Competitie
                         .objects
                         .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            # externe links naar een oude competitie komen hier --> geef ze een noindex foutmelding pagina
            self.template_name = TEMPLATE_COMPETITIE_BESTAAT_NIET
            context['robots'] = 'noindex'   # prevent indexing this outdated page
            context['bad_seizoen'] = kwargs['comp_pk_of_seizoen']
        else:
            context['comp'] = self.comp

            self.comp.bepaal_fase()                     # zet comp.fase
            self.comp.is_openbaar = is_competitie_openbaar_voor_rol(self.comp, Rol.ROL_NONE)

            if self.comp.fase_indiv >= 'C':
                context['toon_uitslagen'] = True
                self._get_uitslagen(context)

            if self.comp.is_open_voor_inschrijven():
                self.comp.url_inschrijvingen = reverse('CompInschrijven:lijst-regiocomp-alles',
                                                       kwargs={'comp_pk': self.comp.pk})

            if rol_get_huidige(self.request) in (Rol.ROL_BB, Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL):
                context['url_beheer'] = reverse('CompBeheer:overzicht', kwargs={'comp_pk': self.comp.pk})

            # verwijs de url met comp.pk naar de url met het seizoen
            context['canonical'] = reverse('Competitie:overzicht',
                                           kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url()})

            context['kruimels'] = (
                (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
                (None, self.comp.beschrijving.replace(' competitie', ''))
            )

        return context


# end of file
