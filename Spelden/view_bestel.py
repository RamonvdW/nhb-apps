# -*- coding: utf-8 -*-
import django.http
#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView
from Account.models import get_account
from BasisTypen.definities import (ORGANISATIE_WA, BOOGTYPE_AFKORTING_RECURVE, BOOGTYPE_AFKORTING2STR,
                                   BOOGTYPE_AFKORTING2URL, BOOGTYPE_URL2AFKORTING)
from BasisTypen.models import BoogType
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Spelden.definities import (SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR, SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR,
                                SPELD_CATEGORIE_NL_GRAADSPELD_VELD, SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC,
                                SPELD_CATEGORIE_WA_ARROWHEAD)
from Spelden.models import SpeldScore
from Sporter.models import get_sporter, SporterBoog
from Wedstrijden.definities import (WEDSTRIJD_DISCIPLINES, WEDSTRIJD_DISCIPLINE_TO_STR_KHSN,
                                    WEDSTRIJD_DISCIPLINE_MAXLEN, DISCIPLINE2URL, URL2DISCIPLINE)
from types import SimpleNamespace

TEMPLATE_PRESTATIESPELDEN_BESTEL_SCORE = 'spelden/bestel_stap1.dtl'
TEMPLATE_PRESTATIESPELDEN_BESTEL_FILTER = 'spelden/bestel_stap2.dtl'

WEDSTRIJD_DISCIPLINE_DEFAULT = WEDSTRIJD_DISCIPLINES[0][0]       # eerste optie = outdoor
BOOGTYPE_AFKORTING_DEFAULT = BOOGTYPE_AFKORTING_RECURVE


class BestelStap1View(TemplateView):

    """ In deze view begint het bestelproces met de invoer van de behaalde score en de wedstrijddiscipline """

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_BESTEL_SCORE

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sporter = None
        self.discipline = WEDSTRIJD_DISCIPLINE_DEFAULT
        self.boogtype = BOOGTYPE_AFKORTING_DEFAULT
        self.score = ''
        self.sporter_bogen = list()     # afkortingen

    def _get_sporter(self):
        if rol_get_huidige(self.request) != Rol.ROL_SPORTER:
            raise PermissionError('Niet ingelogd')

        account = get_account(self.request)
        self.sporter = get_sporter(account)

        if self.sporter:
            self.sporter_bogen = list(SporterBoog
                                      .objects
                                      .filter(sporter=self.sporter,
                                              voor_wedstrijd=True,
                                              boogtype__organisatie=ORGANISATIE_WA)
                                      .order_by('boogtype__volgorde')
                                      .values_list('boogtype__afkorting', flat=True))

            # selecteer automatisch de eerste boog van de sporter
            if len(self.sporter_bogen):
                self.boogtype = self.sporter_bogen[0]

    def _prep_pagina(self, context):
        """ herbruikbare code voor get and post handlers """

        context['sporter_str'] = self.sporter.lid_nr_en_volledige_naam()

        context['menu_toon_mandje'] = True
        context['url_opslaan'] = reverse('Spelden:bestel-stap1')    # voor invoer score (form POST)

        context['discipline_opties'] = opties = list()
        for afkorting, beschrijving in WEDSTRIJD_DISCIPLINES:
            obj = SimpleNamespace(
                        afkorting=afkorting,
                        beschrijving=beschrijving,
                        actief=(self.discipline == afkorting))
            opties.append(obj)
        # for

        context['boog_opties'] = opties = list()
        for boogtype in (BoogType
                         .objects
                         .filter(organisatie=ORGANISATIE_WA,
                                 buiten_gebruik=False)
                         .order_by('volgorde')):

            boogtype.actief = (self.boogtype == boogtype.afkorting)
            opties.append(boogtype)
        # for

        context['score'] = self.score

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Spelden'),
            (None, 'Bestellen'),
        )

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        self._get_sporter()

        param = self.request.GET.get('discipline', None)
        if param:
            self.discipline = URL2DISCIPLINE.get(param, WEDSTRIJD_DISCIPLINE_DEFAULT)

        param = self.request.GET.get('boog', None)
        if param:
            self.boogtype = BOOGTYPE_URL2AFKORTING.get(param, BOOGTYPE_AFKORTING_DEFAULT)

        param = self.request.GET.get('score', None)
        if param:
            try:
                self.score = int(param)
            except (ValueError, TypeError):
                self.score = ''

        self._prep_pagina(context)

        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST ontvangen is van het invoer formulier. """

        self._get_sporter()

        afkortingen = list(DISCIPLINE2URL.keys())
        discipline = request.POST.get('discipline', '')[:WEDSTRIJD_DISCIPLINE_MAXLEN]     # afkorting
        if discipline not in afkortingen:
            discipline = WEDSTRIJD_DISCIPLINE_DEFAULT

        afkortingen = list(BOOGTYPE_AFKORTING2URL.keys())
        boogtype = request.POST.get('boogtype', '')[:2]     # afkorting
        if boogtype not in afkortingen:
            boogtype = BOOGTYPE_AFKORTING_DEFAULT

        score = request.POST.get('score', None)
        try:
            score = int(score)
        except (ValueError, TypeError):
            score = None

        if score and 1 <= score <= 2880:
            # acceptable score --> door naar het filteren
            return HttpResponseRedirect(reverse('Spelden:bestel-stap2',
                                                kwargs={
                                                    'discipline': DISCIPLINE2URL[discipline],
                                                    'boogtype': BOOGTYPE_AFKORTING2URL[boogtype],
                                                    'score': score,
                                                }))

        # het formulier opnieuw aanbieden
        context = dict()
        self._prep_pagina(context)

        return render(request, self.template_name, context)


class BestelStap2View(TemplateView):

    """ In deze view weten we de score en kan de sporter met filter knoppen nog wat extra zaken invoeren """

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_BESTEL_FILTER

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sporter = None
        self.score = 0
        self.discipline = WEDSTRIJD_DISCIPLINE_DEFAULT
        self.boogtype = BOOGTYPE_AFKORTING_DEFAULT
        self.afstand = 18
        self.pijlen = 25

    def _get_sporter(self):
        if rol_get_huidige(self.request) != Rol.ROL_SPORTER:
            raise PermissionError('Niet ingelogd')

        account = get_account(self.request)
        self.sporter = get_sporter(account)

    def _get_filters(self, kwargs: dict):

        self.score = kwargs['score']

        param = kwargs['discipline'][:11]   # langste  = "run-archery"
        self.discipline = URL2DISCIPLINE.get(param, WEDSTRIJD_DISCIPLINE_DEFAULT)

        param = kwargs['boogtype'][:11]   # langste  = "traditional"
        self.boogtype = BOOGTYPE_URL2AFKORTING.get(param, BOOGTYPE_AFKORTING_DEFAULT)

        afstand_str = str(kwargs.get('afstand', '18'))[:2]
        try:
            self.afstand = int(afstand_str)
        except (ValueError, TypeError):
            self.afstand = 18

        pijlen_str = str(kwargs.get('pijlen', '25'))
        try:
            self.pijlen = int(pijlen_str)
        except (ValueError, TypeError):
            self.pijlen = 25

    def _prep_pagina(self, context):
        """ herbruikbare code voor get and post handlers """

        context['sporter_str'] = self.sporter.lid_nr_en_volledige_naam()
        context['discipline_str'] = WEDSTRIJD_DISCIPLINE_TO_STR_KHSN[self.discipline]
        context['boogtype_str'] = BOOGTYPE_AFKORTING2STR[self.boogtype]
        context['score'] = self.score

        context['menu_toon_mandje'] = True
        query_params = '?discipline=%s&boog=%s&score=%s' % (DISCIPLINE2URL[self.discipline],
                                                            BOOGTYPE_AFKORTING2URL[self.boogtype],
                                                            self.score)
        context['url_stap1'] = reverse('Spelden:bestel-stap1') + query_params

        context['url_filter'] = reverse('Spelden:bestel-stap2b',
                                        kwargs={'score': self.score,
                                                'discipline': DISCIPLINE2URL[self.discipline],
                                                'boogtype': '?',
                                                'afstand': self.afstand,
                                                'pijlen': self.pijlen,
                                                })

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Spelden'),
            (None, 'Bestellen'),
        )

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        self._get_sporter()
        self._get_filters(kwargs)
        self._prep_pagina(context)

        return context


# end of file
