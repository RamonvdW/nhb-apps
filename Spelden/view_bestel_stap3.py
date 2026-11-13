# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponseRedirect, Http404
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from Account.models import get_account
from BasisTypen.definities import BOOGTYPE_AFKORTING2STR, GESLACHT2STR
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Spelden.definities import SPELD_DISCIPLINE_VELD, SPELD_DISCIPLINE2STR
from Spelden.models import SpeldAanvraagPrep
from Sporter.operations import get_sporter
from Wedstrijden.definities import ORGANISATIE_IFAA, WEDSTRIJD_STATUS_GEACCEPTEERD
from Wedstrijden.models import Wedstrijd
import datetime

TEMPLATE_PRESTATIESPELDEN_BESTEL_STAP3 = 'spelden/bestel_stap3.dtl'


class BestelStap3View(TemplateView):

    """ In deze view tonen we de mogelijke spelden, gebaseerd op de informatie in SpeldAanvraagPrep """

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_BESTEL_STAP3

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prep: SpeldAanvraagPrep = SpeldAanvraagPrep()
        self.qset_wedstrijden = None

    def _load_prep(self):
        if rol_get_huidige(self.request) != Rol.ROL_SPORTER:
            raise PermissionDenied('Niet ingelogd')

        if not settings.TOON_SPELDEN_BESTELLEN:
            raise Http404('Bestellen is niet mogelijk')

        account = get_account(self.request)
        sporter = get_sporter(account)

        prep = SpeldAanvraagPrep.objects.filter(voor_sporter=sporter).first()
        if prep is None:
            raise Http404('Onvolledige verzoek (1)')
        else:
            self.prep = prep

        if not self.prep.heeft_data_stap2:
            raise Http404('Onvolledige verzoek (2)')

    def _vind_wedstrijden(self):
        self.qset_wedstrijden = (Wedstrijd
                                 .objects
                                 .exclude(toon_op_kalender=False)
                                 .exclude(organisatie=ORGANISATIE_IFAA)      # spelden zijn voor WA en KHSN
                                 .exclude(is_ter_info=True)
                                 .filter(status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                                         datum_begin__gte=self.prep.datum_wedstrijd,
                                         datum_einde__lte=self.prep.datum_wedstrijd)
                                 .order_by('-datum_begin',      # nieuwste bovenaan
                                           'pk'))               # consistente volgorde

        for obj in self.qset_wedstrijden:
            obj.plaats = obj.locatie.plaats if obj.locatie else ''
        # for

    def _prep_pagina(self, context):
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
            context['wedstrijd_pk'] = self.prep.wedstrijd_id
        else:
            context['wedstrijd_pk'] = 'geen'
        context['kalender_lijst'] = self.qset_wedstrijden

        spl = self.prep.informatie_wedstrijd.split('|')
        if len(spl) >= 1:
            context['plaats'] = spl[0]
        else:
            context['plaats'] = ''
        if len(spl) > 1:
            context['land'] = spl[1]
        else:
            context['land'] = 'Nederland'

        # # verwijder spelden die niet besteld kunnen worden (met hogere score vereiste)
        # while len(mogelijke_spelden) and not mogelijke_spelden[-1].ok_score:
        #     mogelijke_spelden.pop(-1)
        # # while

        context['url_opslaan'] = reverse('Spelden:bestel-stap3')
        context['url_stap2'] = reverse('Spelden:bestel-stap2')

        context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Prestatiespelden'),
            (None, 'Bestellen - Stap 3'),
        )

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        self._load_prep()
        self._vind_wedstrijden()

        self._prep_pagina(context)
        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST ontvangen is van het invoer formulier. """

        self._load_prep()

        # is de wedstrijd gekozen uit de lijst?
        wed_pk_str = request.POST.get('wedstrijd', '')[:10]     # afkappen voor de veiligheid
        if wed_pk_str.startswith('wed_'):
            self._vind_wedstrijden()

            try:
                wed_pk = int(wed_pk_str[4:4+6])
                obj = self.qset_wedstrijden.get(pk=wed_pk)
            except (ValueError, TypeError, Wedstrijd.DoesNotExist):
                raise Http404('Wedstrijd niet gevonden')

            self.prep.wedstrijd = obj

            locatie = self.prep.wedstrijd.locatie
            if locatie:
                # we ondersteunen alleen wedstrijdlocaties in Nederland
                self.prep.informatie_wedstrijd = '%s|%s' % (locatie.plaats, 'Nederland')
        else:
            self.prep.wedstrijd = None

            plaats = request.POST.get('plaats', '')[:100]
            land = request.POST.get('land', '')[:100]
            combi = '%s|%s' % (plaats, land)
            self.prep.informatie_wedstrijd = combi[:128]     # limiet van het veld

        self.prep.heeft_data_stap3 = True
        self.prep.save(update_fields=['wedstrijd', 'informatie_wedstrijd', 'heeft_data_stap3',])

        url = reverse('Spelden:bestel-stap4')
        return HttpResponseRedirect(url)

# end of file
