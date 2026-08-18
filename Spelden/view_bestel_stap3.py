# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from Account.models import get_account
from BasisTypen.definities import BOOGTYPE_AFKORTING2STR, GESLACHT2STR
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Spelden.definities import SPELD_DISCIPLINE_VELD, SPELD_DISCIPLINE2STR, SPELD_CATEGORIE2STR
from Spelden.models import SpeldAanvraagPrep
from Spelden.operations import get_mogelijke_spelden
from Sporter.models import get_sporter

TEMPLATE_PRESTATIESPELDEN_BESTEL_STAP3 = 'spelden/bestel_stap3.dtl'


class BestelStap3View(TemplateView):

    """ In deze view tonen we de mogelijke spelden, gebaseerd op de informatie in SpeldAanvraagPrep """

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_BESTEL_STAP3

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prep = None
        self.al_besteld = list()

    def _load_prep(self):
        if rol_get_huidige(self.request) != Rol.ROL_SPORTER:
            raise PermissionDenied('Niet ingelogd')

        account = get_account(self.request)
        sporter = get_sporter(account)

        self.prep = SpeldAanvraagPrep.objects.filter(voor_sporter=sporter).first()
        if not self.prep:
            raise Http404('Onvolledige verzoek (1)')

        if not self.prep.heeft_data_stap2:
            raise Http404('Onvolledige verzoek (2)')

    def _load_al_besteld(self):
        pass

    def _prep_pagina(self, context, opties):
        context['sporter_str'] = self.prep.voor_sporter.lid_nr_en_volledige_naam()

        # geslacht is alleen relevant voor de arrowhead spelden (andere scores), dus toon alleen voor discipline veld
        if self.prep.discipline == SPELD_DISCIPLINE_VELD:
            context['geslacht_str'] = GESLACHT2STR[self.prep.wedstrijd_geslacht]

        # informatie die verzameld is in stap 1
        context['discipline_str'] = SPELD_DISCIPLINE2STR[self.prep.discipline]
        context['boogtype_str'] = BOOGTYPE_AFKORTING2STR[self.prep.boog]
        context['score'] = self.prep.score

        mogelijke_spelden = list()

        # informatie die verzameld is in stap 2
        if self.prep.discipline == SPELD_DISCIPLINE_VELD:
            context['aantal_doelen'] = '%s doelen' % self.prep.aantal_doelen

            for optie in opties:
                if optie.aantal_doelen == self.prep.aantal_doelen:
                    mogelijke_spelden.append(optie)
            # for
        else:
            context['afstanden'] = self.prep.afstanden + ' meter'
            context['aantal_pijlen'] = '%s pijlen' % self.prep.aantal_pijlen

            for optie in opties:
                if optie.aantal_pijlen == self.prep.aantal_pijlen and optie.afstanden == self.prep.afstanden:
                    mogelijke_spelden.append(optie)
            # for

        # optie 1: geen van de spelden kan besteld worden --> toon score nodig voor eerste speld
        # optie 2: een of meerdere spelden kan besteld worden, maar sporter heeft ze allemaal al
        # optie 3: een of meerdere spelden kan besteld worden

        for optie in mogelijke_spelden:
            optie.speld.categorie_str = SPELD_CATEGORIE2STR[optie.speld.categorie]

            # controleer dat de score hoog genoeg is
            optie.ok_score = self.prep.score >= optie.benodigde_score

            # TODO: controleer dat de speld niet al besteld is
            optie.al_besteld = False
        # for

        # verwijder spelden die niet besteld kunnen worden (met hogere score vereiste)
        while len(mogelijke_spelden) and not mogelijke_spelden[-1].ok_score:
            mogelijke_spelden.pop(-1)
        # while

        context['mogelijke_spelden'] = mogelijke_spelden

        context['url_opslaan'] = reverse('Spelden:bestel-stap3')    # voor doorgave keuzes (form POST)
        context['url_stap2'] = reverse('Spelden:bestel-stap2')

        context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Spelden'),
            (None, 'Bestellen - Stap 3'),
        )

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        self._load_prep()
        self._load_al_besteld()

        opties = get_mogelijke_spelden(self.prep.discipline,
                                       self.prep.boog,
                                       self.prep.score,
                                       self.prep.wedstrijd_geslacht,
                                       self.prep.voor_sporter.geboorte_datum.year)

        self._prep_pagina(context, opties)

        return context


# end of file
