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
from Bestelling.operations import mandje_tel_inhoud, bestel_mutatieverzoek_aanvraag_spelden
from Betaal.format import format_bedrag_euro
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Spelden.definities import (SPELD_DISCIPLINE_VELD, SPELD_DISCIPLINE_OUTDOOR,
                                SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC,
                                SPELD_DISCIPLINE2STR, SPELD_CATEGORIE2STR)
from Spelden.models import SpeldAanvraagPrep, SpeldVoorwaarden, SpeldToegekend, SpeldAanvraag, SpeldBestelling
from Spelden.operations import get_mogelijke_spelden_wa, get_mogelijke_graadspelden_khsn
from Sporter.operations import get_sporter
from decimal import Decimal

TEMPLATE_PRESTATIESPELDEN_BESTEL_STAP4 = 'spelden/bestel_stap4.dtl'
TEMPLATE_PRESTATIESPELDEN_BESTEL_TOEGEVOEGD = 'spelden/bestel_toegevoegd-aan-mandje.dtl'


class BestelStap4View(TemplateView):

    """ In deze view tonen kan sporter de beschikbare spelden in het mandje leggen """

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_BESTEL_STAP4

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account = None
        self.sporter = None
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

        self.account = get_account(self.request)
        self.sporter = get_sporter(self.account)

        self.prep = SpeldAanvraagPrep.objects.filter(voor_sporter=self.sporter).first()
        if not self.prep:
            raise Http404('Onvolledige verzoek (1)')

        if not self.prep.heeft_data_stap3:
            raise Http404('Onvolledige verzoek (2)')

    def _load_al_toegekend(self):
        pks = list(SpeldToegekend.objects.filter(sporter=self.sporter).values_list('speld__pk', flat=True))
        self.al_toegekende_speld_pks = pks

    def _analyseer_opties_wa(self, opties: list[SpeldVoorwaarden]):
        """ Analyseer elk van de opties en bepaal of deze speld besteld mag worden
            aan de hand van de spelden die sporter al heeft en de behaalde score.

            vult self.mogelijke_spelden
        """

        speld_prijs_wa = Decimal(settings.SPELD_PRIJS_WA)
        speld_prijs_wa_str = format_bedrag_euro(speld_prijs_wa, gratis=True)

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
            optie.mag_besteld_worden = False

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
                    optie.mag_besteld_worden = True
                    optie.prijs_str = speld_prijs_wa_str
                    self.totale_prijs += speld_prijs_wa
                else:
                    optie.opmerking = "Score niet hoog genoeg"
        # for

    def _analyseer_opties_khsn(self, opties: list[SpeldVoorwaarden]):

        speld_prijs_khsn = Decimal(settings.SPELD_PRIJS_KHSN)
        speld_prijs_khsn_str = format_bedrag_euro(speld_prijs_khsn, gratis=True)

        for optie in opties:
            print('{optie khsn} %s' % optie)
            optie.opmerking = '?'

            optie.speld.categorie_str = SPELD_CATEGORIE2STR[optie.speld.categorie]
            optie.mag_besteld_worden = False

            if optie.speld.pk in self.al_toegekende_speld_pks:
                optie.opmerking = "Deze speld heb je al"
                optie.ok_score = optie.nok_score = False  # niet in groen of rood tonen
            else:
                # controleer of de behaalde score hoog genoeg is
                if optie.speld.categorie == SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC:
                    score = self.prep.score_sm
                else:
                    score = self.prep.score
                optie.nok_score = score < optie.benodigde_score  # toon in rood
                optie.ok_score = score >= optie.benodigde_score  # toon in groen
                if optie.ok_score:
                    self.aantal_bestelbaar += 1
                    optie.opmerking = "Deze speld kan je bestellen"
                    optie.mag_besteld_worden = True
                    optie.prijs_str = speld_prijs_khsn_str
                    self.totale_prijs += speld_prijs_khsn
                else:
                    optie.opmerking = "Score niet hoog genoeg"

            self.mogelijke_spelden.append(optie)
        # for

    def _prep_pagina(self, context):
        context['sporter_str'] = self.prep.voor_sporter.lid_nr_en_volledige_naam()

        # geslacht is relevant voor de arrowhead spelden (andere scores M/V)
        # geslacht is relevant voor de ster spelden (andere scores M/V)
        # dus toon voor veld en outdoor
        if self.prep.discipline in (SPELD_DISCIPLINE_VELD, SPELD_DISCIPLINE_OUTDOOR):
            context['geslacht_str'] = GESLACHT2STR[self.prep.wedstrijd_geslacht]

        # informatie die verzameld is in stap 1
        context['discipline_str'] = SPELD_DISCIPLINE2STR[self.prep.discipline]
        context['boogtype_str'] = BOOGTYPE_AFKORTING2STR[self.prep.boog]

        if self.prep.discipline == SPELD_DISCIPLINE_VELD:
            context['aantal_doelen'] = self.prep.aantal_doelen
        else:
            context['aantal_pijlen'] = self.prep.aantal_pijlen

        context['score'] = self.prep.score
        if self.prep.score_sm > 0:
            context['score_sm'] = self.prep.score_sm

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
            (reverse('Spelden:begin'), 'Prestatiespelden'),
            (None, 'Bestellen stap 4'),
        )

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        self._load_prep()
        self._load_al_toegekend()

        opties1 = get_mogelijke_spelden_wa(self.prep.discipline,
                                           self.prep.boog,
                                           self.prep.score,
                                           self.prep.wedstrijd_geslacht,
                                           self.prep.voor_sporter.geboorte_datum.year)
        self._analyseer_opties_wa(opties1)

        opties2 = get_mogelijke_graadspelden_khsn(self.prep.discipline,
                                                  self.prep.afstanden,
                                                  self.prep.aantal_doelen,
                                                  self.prep.aantal_pijlen,
                                                  self.prep.wedstrijd_geslacht,
                                                  self.prep.score,
                                                  self.prep.score_sm)
        self._analyseer_opties_khsn(opties2)

        self._prep_pagina(context)
        return context

    def post(self, request, *args, **kwargs):
        self._load_prep()
        self._load_al_toegekend()

        opties1 = get_mogelijke_spelden_wa(self.prep.discipline,
                                           self.prep.boog,
                                           self.prep.score,
                                           self.prep.wedstrijd_geslacht,
                                           self.prep.voor_sporter.geboorte_datum.year)
        self._analyseer_opties_wa(opties1)

        opties2 = get_mogelijke_graadspelden_khsn(self.prep.discipline,
                                                  self.prep.afstanden,
                                                  self.prep.aantal_doelen,
                                                  self.prep.aantal_pijlen,
                                                  self.prep.wedstrijd_geslacht,
                                                  self.prep.score,
                                                  self.prep.score_sm)
        self._analyseer_opties_khsn(opties2)

        del opties1
        del opties2

        spelden = [optie.speld
                   for optie in self.mogelijke_spelden
                   if optie.mag_besteld_worden]

        if len(spelden) == 0:
            raise Http404('Slecht verzoek')

        # informatie over de wedstrijd
        aanvraag = SpeldAanvraag.objects.create(
                        voor_sporter=self.sporter,
                        wedstrijd_geslacht=self.prep.wedstrijd_geslacht,
                        discipline=self.prep.discipline,
                        boog=self.prep.boog,
                        score=self.prep.score,
                        datum_wedstrijd=self.prep.datum_wedstrijd,
                        wedstrijd=self.prep.wedstrijd,
                        informatie_wedstrijd=self.prep.informatie_wedstrijd)

        # leg elke speld afzonderlijk in het mandje
        bestelling = None
        for speld in spelden:
            if bestelling:
                # zet door naar de achtergrondtaak, maar wacht niet op het antwoord
                bestel_mutatieverzoek_aanvraag_spelden(self.account, bestelling, snel=True)

            bestelling = SpeldBestelling.objects.create(
                            door_account=self.account,
                            is_nieuwe_aanvraag=True,
                            speld=speld,
                            aanvraag=aanvraag)
        # for

        # zet de laatste aanvraag door naar de achtergrondtaak + wacht op verwerken
        if bestelling:
            snel = str(request.POST.get('snel', ''))[:1]
            bestel_mutatieverzoek_aanvraag_spelden(self.account, bestelling, snel == '1')

        mandje_tel_inhoud(self.request, self.account)

        context = dict()

        context['url_naar_spelden'] = reverse('Spelden:begin')
        context['url_naar_webwinkel'] = reverse('Webwinkel:overzicht')
        context['url_mandje'] = reverse('Bestelling:toon-inhoud-mandje')
        context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Spelden:begin'), 'Prestatiespelden'),
            (None, 'Bestellen - Toegevoegd aan mandje'),
        )

        return render(request, TEMPLATE_PRESTATIESPELDEN_BESTEL_TOEGEVOEGD, context)


# end of file
