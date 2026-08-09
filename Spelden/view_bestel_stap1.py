# -*- coding: utf-8 -*-
import django.http
#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
from django.views.generic import TemplateView
from Account.models import get_account
from BasisTypen.definities import ORGANISATIE_WA, GESLACHT_MAN
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Spelden.definities import SPELD_DISCIPLINE_CHOICES, SPELD_DISCIPLINE_NVT, SPELD_BOOGTYPE_CHOICES
from Spelden.models import SpeldAanvraagPrep
from Sporter.models import get_sporter, SporterBoog
from Sporter.operations import get_sporter_voorkeuren
from Wedstrijden.definities import WEDSTRIJD_DISCIPLINE_MAXLEN
from types import SimpleNamespace

TEMPLATE_PRESTATIESPELDEN_BESTEL_STAP1 = 'spelden/bestel_stap1.dtl'

DEFAULT_DISCIPLINE = SPELD_DISCIPLINE_CHOICES[0][0]       # eerste optie = outdoor
DEFAULT_BOOGTYPE = SPELD_BOOGTYPE_CHOICES[0][0]           # eerste optie = recurve


class BestelStap1View(TemplateView):

    """ In deze view begint het bestelproces met de invoer van de behaalde score en de wedstrijddiscipline """

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_BESTEL_STAP1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prep = None
        self.sporter_bogen = list()     # afkortingen

    def _load_prep(self):
        if rol_get_huidige(self.request) != Rol.ROL_SPORTER:
            raise PermissionError('Niet ingelogd')

        account = get_account(self.request)
        sporter = get_sporter(account)

        self.prep, _ = SpeldAanvraagPrep.objects.get_or_create(voor_sporter=sporter)

    def _load_boogtypen(self):
        sporter = self.prep.voor_sporter

        if sporter:
            self.sporter_bogen = list(SporterBoog
                                      .objects
                                      .filter(sporter=sporter,
                                              voor_wedstrijd=True,
                                              boogtype__organisatie=ORGANISATIE_WA)
                                      .order_by('boogtype__volgorde')
                                      .values_list('boogtype__afkorting', flat=True))

            # selecteer automatisch de eerste boog van de sporter
            if len(self.sporter_bogen):
                self.sel_boogtype = self.sporter_bogen[0]

    def _prep_pagina(self, context):
        """ herbruikbare code voor get and post handlers """

        # informatie die verzameld is
        context['sporter_str'] = self.prep.voor_sporter.lid_nr_en_volledige_naam()

        # keuze opties
        context['discipline_opties'] = opties = list()
        for afkorting, beschrijving in SPELD_DISCIPLINE_CHOICES:
            if afkorting != SPELD_DISCIPLINE_NVT:
                obj = SimpleNamespace(
                            afkorting=afkorting,
                            beschrijving=beschrijving,
                            actief=(self.prep.discipline == afkorting))
                opties.append(obj)
        # for

        context['boog_opties'] = opties = list()
        for afkorting, beschrijving in SPELD_BOOGTYPE_CHOICES:
            obj = SimpleNamespace(
                        afkorting=afkorting,
                        beschrijving=beschrijving,
                        actief=(self.prep.boog == afkorting))
            opties.append(obj)
        # for

        context['score'] = self.prep.score

        context['url_opslaan'] = reverse('Spelden:bestel-stap1')    # voor doorgave keuzes (form POST)

        context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Spelden'),
            (None, 'Bestellen - Stap 1'),
        )

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        self._load_prep()
        self._load_boogtypen()

        self._prep_pagina(context)

        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST ontvangen is van het invoer formulier. """

        self._load_prep()

        voorkeuren = get_sporter_voorkeuren(self.prep.voor_sporter, mag_database_wijzigen=True)
        if voorkeuren.wedstrijd_geslacht_gekozen:
            self.prep.wedstrijd_geslacht = voorkeuren.wedstrijd_geslacht
        else:
            # niet gekozen: gebruik 'man' (maakt alleen voor de Arrowhead spelden wat uit)
            self.prep.wedstrijd_geslacht = GESLACHT_MAN

        afkortingen = [afkorting
                       for afkorting, beschrijving in SPELD_DISCIPLINE_CHOICES]
        discipline = request.POST.get('discipline', '')[:WEDSTRIJD_DISCIPLINE_MAXLEN]     # afkorting
        if discipline not in afkortingen:
            raise Http404('Onbekende discipline')
        self.prep.discipline = discipline

        afkortingen = [afkorting
                       for afkorting, beschrijving in SPELD_BOOGTYPE_CHOICES]
        boogtype = request.POST.get('boogtype', '')[:2]     # afkorting
        if boogtype not in afkortingen:
            raise Http404('Onbekende boog')
        self.prep.boog = boogtype

        score = request.POST.get('score', None)
        try:
            score = int(score)
        except (ValueError, TypeError):
            raise Http404('Slechte score')

        if score and 1 <= score <= 2880:
            # acceptable score --> opslaan en door naar stap 2

            self.prep.score = score
            self.prep.heeft_data_stap1 = True
            self.prep.save(update_fields=['heeft_data_stap1', 'discipline', 'boog', 'score'])

            url = reverse('Spelden:bestel-stap2')
            return HttpResponseRedirect(url)

        # het formulier opnieuw aanbieden
        context = dict()
        self._prep_pagina(context)

        return render(request, self.template_name, context)


# end of file
