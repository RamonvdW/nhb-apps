# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
from django.views.generic import TemplateView
from Account.models import get_account
from BasisTypen.definities import BOOGTYPE_AFKORTING2STR, GESLACHT2STR
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Spelden.definities import SPELD_DISCIPLINE_VELD, SPELD_DISCIPLINE_INDOOR, SPELD_DISCIPLINE2STR
from Spelden.models import SpeldAanvraagPrep
from Spelden.operations import get_mogelijke_spelden
from Sporter.models import get_sporter
from types import SimpleNamespace

TEMPLATE_PRESTATIESPELDEN_BESTEL_STAP2 = 'spelden/bestel_stap2.dtl'


class BestelStap2View(TemplateView):

    """ In deze view weten we de score en kan de sporter met filter knoppen nog wat extra zaken invoeren """

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_BESTEL_STAP2

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prep = None

    def _load_prep(self):
        if rol_get_huidige(self.request) != Rol.ROL_SPORTER:
            raise PermissionError('Niet ingelogd')

        account = get_account(self.request)
        sporter = get_sporter(account)

        self.prep, _ = SpeldAanvraagPrep.objects.get_or_create(voor_sporter=sporter)

        if not self.prep.heeft_data_stap1:
            raise Http404('Onvolledige verzoek')

    def _prep_pagina(self, context, opties):
        """ herbruikbare code voor get and post handlers """

        # informatie die verzameld is in stap 1
        context['sporter_str'] = self.prep.voor_sporter.lid_nr_en_volledige_naam()
        context['discipline_str'] = SPELD_DISCIPLINE2STR[self.prep.discipline]
        context['boogtype_str'] = BOOGTYPE_AFKORTING2STR[self.prep.boog]
        context['score'] = self.prep.score

        # geslacht is alleen relevant voor de arrowhead spelden (andere scores), dus toon alleen voor discipline veld
        if self.prep.discipline == SPELD_DISCIPLINE_VELD:
            context['geslacht_str'] = GESLACHT2STR[self.prep.wedstrijd_geslacht]

        for optie in opties:
            print('{optie} %s' % repr(optie))

        # filter opties
        if self.prep.discipline == SPELD_DISCIPLINE_VELD:
            aantal_doelen = [str(optie.aantal_doelen)
                             for optie in opties]
            aantal_doelen = list(set(aantal_doelen))
            aantal_doelen.sort()

            context['doelen_opties'] = filter_opties = list()
            for aantal in aantal_doelen:
                obj = SimpleNamespace(
                            afkorting=aantal,
                            beschrijving=aantal + ' doelen',
                            actief=(self.prep.aantal_doelen == aantal))
                filter_opties.append(obj)
            # for
        else:
            afstanden = [(len(optie.afstanden), optie.afstanden)
                         for optie in opties]
            afstanden = list(set(afstanden))

            if self.prep.discipline == SPELD_DISCIPLINE_INDOOR:
                afstanden.sort()                    # laagste eerst: 18m, 25m
            else:
                afstanden.sort(reverse=True)        # langste string eerst; langste afstand eerst

            context['afstanden_titel'] = 'Geschoten afstand'
            context['afstanden_opties'] = filter_opties = list()
            for _, afstand_str in afstanden:
                if ", " in afstand_str:
                    context['afstanden_titel'] = 'Geschoten afstand(en)'

                obj = SimpleNamespace(
                            afkorting=afstand_str,
                            beschrijving=afstand_str + ' meter',
                            actief=(self.prep.afstanden == afstand_str))
                filter_opties.append(obj)
            # for

        context['url_opslaan'] = reverse('Spelden:bestel-stap2')    # voor doorgave keuzes (form POST)
        context['url_stap1'] = reverse('Spelden:bestel-stap1')

        context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Spelden'),
            (None, 'Bestellen - Stap 2'),
        )

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        self._load_prep()

        opties = get_mogelijke_spelden(self.prep.discipline,
                                       self.prep.boog,
                                       self.prep.score,
                                       self.prep.wedstrijd_geslacht,
                                       self.prep.voor_sporter.geboorte_datum.year)

        self._prep_pagina(context, opties)

        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST ontvangen is van het invoer formulier. """

        self._load_prep()

        opties = get_mogelijke_spelden(self.prep.discipline,
                                       self.prep.boog,
                                       self.prep.score,
                                       self.prep.wedstrijd_geslacht,
                                       self.prep.voor_sporter.geboorte_datum.year)

        if self.prep.discipline == SPELD_DISCIPLINE_VELD:

            aantal_doelen = [str(optie.aantal_doelen)
                             for optie in opties]

            doelen = request.POST.get('doelen', '')[:2]          # "24" of "48"

            if doelen not in aantal_doelen:
                raise Http404('Onbekend aantal doelen')

            self.prep.aantal_doelen = doelen
            self.prep.heeft_data_stap2 = True
            self.prep.save(update_fields=['heeft_data_stap2', 'aantal_doelen'])
            # note: aantal_pijlen wordt niet gebruikt voor veld

        else:
            afstanden = [optie.afstanden
                         for optie in opties]
            afstanden = list(set(afstanden))

            afstand = request.POST.get('afstand', '')[:15]      # "90, 70, 50, 30" = 14
            if afstand not in afstanden:
                raise Http404('Onbekende afstand')

            self.prep.afstanden = afstand

            # zet ook meteen het aantal pijlen
            aantal_pijlen = [optie.aantal_pijlen
                             for optie in opties
                             if optie.afstanden == afstand]
            aantal_pijlen = list(set(aantal_pijlen))
            if len(aantal_pijlen) != 1:
                raise Http404('Kan aantal pijlen niet vaststellen')

            self.prep.aantal_pijlen = aantal_pijlen[0]

            self.prep.heeft_data_stap2 = True
            self.prep.save(update_fields=['heeft_data_stap2', 'afstanden', 'aantal_pijlen'])

        url = reverse('Spelden:bestel-stap3')
        return HttpResponseRedirect(url)


# end of file
