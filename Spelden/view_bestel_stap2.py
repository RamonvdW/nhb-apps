# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from Account.models import get_account
from BasisTypen.definities import BOOGTYPE_AFKORTING2STR, GESLACHT2STR
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Spelden.definities import SPELD_DISCIPLINE_VELD, SPELD_DISCIPLINE_OUTDOOR, SPELD_DISCIPLINE2STR
from Spelden.models import SpeldAanvraagPrep
from Spelden.operations import speld_discipline2wedstrijd_discplines
from Sporter.operations import get_sporter
from Wedstrijden.definities import ORGANISATIE_IFAA, WEDSTRIJD_STATUS_GEACCEPTEERD
from Wedstrijden.models import Wedstrijd

TEMPLATE_PRESTATIESPELDEN_BESTEL_STAP2 = 'spelden/bestel_stap2.dtl'


class BestelStap2View(TemplateView):

    """ In deze view tonen vragen we meer informatie over de wedstrijd: plaats en land
        en indien aanwezig kan direct een wedstrijd van de kalender gekozen worden.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_BESTEL_STAP2

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
        if not sporter:                                 # pragma: no branch
            raise Http404('Onvolledige verzoek')        # pragma: no cover

        prep = SpeldAanvraagPrep.objects.filter(voor_sporter=sporter).first()
        if prep is None:
            raise Http404('Onvolledige verzoek (1)')
        else:
            self.prep = prep

        if not self.prep.heeft_data_stap1:
            raise Http404('Onvolledige verzoek (2)')

    def _vind_wedstrijden(self):
        wed_disciplines = speld_discipline2wedstrijd_discplines(self.prep.discipline)

        self.qset_wedstrijden = (Wedstrijd
                                 .objects
                                 .exclude(toon_op_kalender=False)
                                 .exclude(organisatie=ORGANISATIE_IFAA)      # spelden zijn voor WA en KHSN
                                 .exclude(is_ter_info=True)
                                 .filter(status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                                         discipline__in=wed_disciplines,
                                         datum_begin__lte=self.prep.datum_wedstrijd,
                                         datum_einde__gte=self.prep.datum_wedstrijd)
                                 .order_by('-datum_begin',      # nieuwste bovenaan
                                           'pk'))               # consistente volgorde

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
        context['score'] = self.prep.score
        context['wedstrijd_datum'] = self.prep.datum_wedstrijd
        if self.prep.wedstrijd:
            context['wedstrijd_pk'] = self.prep.wedstrijd_id
        else:
            context['wedstrijd_pk'] = 'geen'

        if len(self.qset_wedstrijden) > 0:
            context['kalender_lijst'] = self.qset_wedstrijden

        spl = self.prep.informatie_wedstrijd.split('|')
        context['plaats'] = spl[0]
        if len(spl) > 1:
            context['land'] = spl[1]
        else:
            context['land'] = 'Nederland'

        # # verwijder spelden die niet besteld kunnen worden (met hogere score vereiste)
        # while len(mogelijke_spelden) and not mogelijke_spelden[-1].ok_score:
        #     mogelijke_spelden.pop(-1)
        # # while

        context['url_opslaan'] = reverse('Spelden:bestel-stap2')
        context['url_stap1'] = reverse('Spelden:bestel-stap1')

        context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Spelden:begin'), 'Prestatiespelden'),
            (None, 'Bestellen stap 2'),
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
            if locatie:     # pragma: no branch
                # we ondersteunen alleen wedstrijdlocaties in Nederland
                self.prep.informatie_wedstrijd = '%s|%s' % (locatie.plaats, 'Nederland')
        else:
            self.prep.wedstrijd = None

            plaats = request.POST.get('plaats', '')[:100]
            land = request.POST.get('land', '')[:100]
            combi = '%s|%s' % (plaats, land)
            self.prep.informatie_wedstrijd = combi[:128]     # limiet van het veld

        self.prep.heeft_data_stap2 = True
        self.prep.save(update_fields=['wedstrijd', 'informatie_wedstrijd', 'heeft_data_stap2'])

        url = reverse('Spelden:bestel-stap3')
        return HttpResponseRedirect(url)

# end of file
