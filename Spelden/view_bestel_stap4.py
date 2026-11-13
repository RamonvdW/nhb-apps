# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from Account.models import get_account
from BasisTypen.definities import BOOGTYPE_AFKORTING2STR, GESLACHT2STR
from Betaal.format import format_bedrag_euro
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Spelden.definities import SPELD_DISCIPLINE_VELD, SPELD_DISCIPLINE2STR, SPELD_CATEGORIE2STR
from Spelden.models import SpeldAanvraagPrep, SpeldVoorwaarden, SpeldToegekend
from Spelden.operations import get_mogelijke_spelden
from Sporter.operations import get_sporter
from decimal import Decimal

TEMPLATE_PRESTATIESPELDEN_BESTEL_STAP4 = 'spelden/bestel_stap4.dtl'
TEMPLATE_PRESTATIESPELDEN_BESTEL_TOEGEVOEGD = 'spelden/bestel_toegevoegd-aan-mandje.dtl'


class BestelStap4View(TemplateView):

    """ In deze view tonen we de mogelijke spelden, gebaseerd op de informatie in SpeldAanvraagPrep """

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_BESTEL_STAP4

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prep = None
        self.al_toegekende_speld_pks = list()
        self.mogelijke_spelden = list()
        self.aantal_bestelbaar = 0
        self.totale_prijs = Decimal("0.00")

    def _load_prep(self):
        if rol_get_huidige(self.request) != Rol.ROL_SPORTER:
            raise PermissionDenied('Niet ingelogd')

        if not settings.TOON_SPELDEN_BESTELLEN:
            raise Http404('Bestellen is niet mogelijk')

        account = get_account(self.request)
        sporter = get_sporter(account)

        self.prep = SpeldAanvraagPrep.objects.filter(voor_sporter=sporter).first()
        if not self.prep:
            raise Http404('Onvolledige verzoek (1)')

        if not self.prep.heeft_data_stap3:
            raise Http404('Onvolledige verzoek (2)')

    def _load_al_toegekend(self):
        account = get_account(self.request)
        sporter = get_sporter(account)

        pks = list(SpeldToegekend.objects.filter(sporter=sporter).values_list('speld__pk', flat=True))
        self.al_toegekende_speld_pks = pks

    def _analyseer_opties(self, opties: list[SpeldVoorwaarden]):
        self.mogelijke_spelden = list()

        # informatie die verzameld is in stap 2
        for optie in opties:
            optie.opmerking = '?'

            if self.prep.discipline == SPELD_DISCIPLINE_VELD:
                if optie.aantal_doelen == self.prep.aantal_doelen:
                    self.mogelijke_spelden.append(optie)
            else:
                # indoor/outdoor
                if optie.aantal_pijlen == self.prep.aantal_pijlen and optie.afstanden == self.prep.afstanden:
                    self.mogelijke_spelden.append(optie)
        # for

        # doorloop alle spelden die passen bij de gemaakte keuzes
        # vergelijk de ingevoerde score met de benodigde score

        self.aantal_bestelbaar = 0
        for optie in self.mogelijke_spelden:
            optie.speld.categorie_str = SPELD_CATEGORIE2STR[optie.speld.categorie]

            if optie.speld.pk in self.al_toegekende_speld_pks:
                optie.opmerking = "Deze speld heb je al"
                optie.ok_score = optie.nok_score = False  # niet in groen of rood tonen
            else:
                # controleer of de behaalde score hoog genoeg is
                optie.nok_score = self.prep.score < optie.benodigde_score  # toon in rood
                optie.ok_score = self.prep.score >= optie.benodigde_score  # toon in groen
                if optie.ok_score:
                    self.aantal_bestelbaar += 1
                    optie.opmerking = "Deze speld kan je bestellen"
                    if optie.speld.prijs_euro < 0.001:
                        optie.prijs_str = "Gratis"
                    else:
                        optie.prijs_str = format_bedrag_euro(optie.speld.prijs_euro)
                        self.totale_prijs += optie.speld.prijs_euro
                else:
                    optie.opmerking = "Score niet hoog genoeg"
        # for

    def _prep_pagina(self, context, opties: list[SpeldVoorwaarden]):
        context['sporter_str'] = self.prep.voor_sporter.lid_nr_en_volledige_naam()

        # geslacht is alleen relevant voor de arrowhead spelden (andere scores), dus toon alleen voor discipline veld
        if self.prep.discipline == SPELD_DISCIPLINE_VELD:
            context['geslacht_str'] = GESLACHT2STR[self.prep.wedstrijd_geslacht]

        # informatie die verzameld is in stap 1
        context['discipline_str'] = SPELD_DISCIPLINE2STR[self.prep.discipline]
        context['boogtype_str'] = BOOGTYPE_AFKORTING2STR[self.prep.boog]
        context['score'] = self.prep.score
        context['wedstrijd_datum'] = self.prep.datum_wedstrijd

        if self.prep.wedstrijd:
            context['wedstrijd_titel'] = self.prep.wedstrijd.titel
            locatie = self.prep.wedstrijd.locatie
            if locatie:
                context['wedstrijd_titel'] += ' (%s)' % locatie.plaats
        else:
            spl = self.prep.informatie_wedstrijd.split('|')
            context['wedstrijd_plaats_land'] = ", ".join(spl[:2])

        context['mogelijke_spelden'] = self.mogelijke_spelden

        # zoek uit of er 1 wedstrijd soort is die we kunnen tonen
        alle_soorten_wedstrijd = []
        for optie in self.mogelijke_spelden:
            if optie.wedstrijd_soort not in alle_soorten_wedstrijd:
                alle_soorten_wedstrijd.append(optie.wedstrijd_soort)
        # for
        if len(alle_soorten_wedstrijd) == 1:
            context['wedstrijd_soort'] = alle_soorten_wedstrijd[0]

        if self.aantal_bestelbaar > 0:
            context['aantal_bestelbaar'] = self.aantal_bestelbaar
            context['totale_prijs_str'] = format_bedrag_euro(self.totale_prijs)
            context['url_leg_in_mandje'] = reverse('Spelden:bestel-stap4')      # voor doorgave keuzes (form POST)

        # # verwijder spelden die niet besteld kunnen worden (met hogere score vereiste)
        # while len(mogelijke_spelden) and not mogelijke_spelden[-1].ok_score:
        #     mogelijke_spelden.pop(-1)
        # # while

        context['url_stap3'] = reverse('Spelden:bestel-stap3')

        context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Prestatiespelden'),
            (None, 'Bestellen - Stap 4'),
        )

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        print('HI!!')
        self._load_prep()
        self._load_al_toegekend()

        opties = get_mogelijke_spelden(self.prep.discipline,
                                       self.prep.boog,
                                       self.prep.score,
                                       self.prep.wedstrijd_geslacht,
                                       self.prep.voor_sporter.geboorte_datum.year)
        self._analyseer_opties(opties)
        self._prep_pagina(context, opties)
        return context

    def post(self, request, *args, **kwargs):
        self._load_prep()
        self._load_al_toegekend()

        opties = get_mogelijke_spelden(self.prep.discipline,
                                       self.prep.boog,
                                       self.prep.score,
                                       self.prep.wedstrijd_geslacht,
                                       self.prep.voor_sporter.geboorte_datum.year)
        self._analyseer_opties(opties)

        context = dict()

        context['url_naar_spelden'] = reverse('Spelden:begin')
        context['url_naar_webwinkel'] = reverse('Webwinkel:overzicht')
        context['url_mandje'] = reverse('Bestelling:toon-inhoud-mandje')
        context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Prestatiespelden'),
            (None, 'Bestellen - Toegevoegd aan mandje'),
        )

        return render(request, TEMPLATE_PRESTATIESPELDEN_BESTEL_TOEGEVOEGD, context)


# end of file
