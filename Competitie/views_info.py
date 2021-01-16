# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import TemplateView, ListView, View
from django.utils import timezone
from BasisTypen.models import LeeftijdsKlasse, MAXIMALE_LEEFTIJD_JEUGD, GESLACHT
from Plein.menu import menu_dynamics
from BasisTypen.models import IndivWedstrijdklasse
from NhbStructuur.models import NhbRegio
from Schutter.leeftijdsklassen import get_sessionvars_leeftijdsklassen
from types import SimpleNamespace


TEMPLATE_COMPETITIE_INFO_COMPETITIE = 'competitie/info-competitie.dtl'
TEMPLATE_COMPETITIE_INFO_LEEFTIJDEN = 'competitie/info-leeftijden.dtl'


class InfoCompetitieView(TemplateView):

    """ Django class-based view voor de Competitie Info """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_INFO_COMPETITIE

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['regios'] = (NhbRegio
                             .objects
                             .filter(is_administratief=False)
                             .select_related('rayon')
                             .order_by('regio_nr'))

        account = self.request.user
        if account and account.is_authenticated:
            if account.nhblid_set.count() > 0:
                nhblid = account.nhblid_set.all()[0]
                nhb_ver = nhblid.bij_vereniging
                if nhb_ver:
                    context['mijn_vereniging'] = nhb_ver
                    for obj in context['regios']:
                        if obj == nhb_ver.regio:
                            obj.mijn_regio = True
                    # for

        context['klassen_count'] = IndivWedstrijdklasse.objects.exclude(is_onbekend=True).count()

        menu_dynamics(self.request, context, actief='competitie')
        return context


class InfoLeeftijdenView(TemplateView):

    """ Django class-based view voor de Competitie Info """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_INFO_LEEFTIJDEN

    @staticmethod
    def _maak_jaren(jaar, begin_leeftijd, aantal):
        print('jaar=%s, begin_leeftijd=%s, aantal=%s' % (jaar, begin_leeftijd, aantal))
        jaar -= begin_leeftijd
        jaren = list()
        while aantal > 0:
            jaren.append(str(jaar))
            jaar -= 1
            aantal -= 1
        # while
        return ", ".join(jaren)

    def _comp_info(self, jaar):
        comp = SimpleNamespace()
        comp.seizoen = '%s/%s' % (jaar, jaar+1)
        comp.klassen = dict()       # ['klasse'] = list(jaartal, jaartal, ..)

        jaar += 1       # informatie voor het tweede jaar produceren
        comp.asp = self._maak_jaren(jaar, 13, 1)        # (10, 11, 12,) 13
        comp.cadet = self._maak_jaren(jaar, 14, 4)      # 14, 15, 16, 17
        comp.junior = self._maak_jaren(jaar, 18, 3)     # 18, 19, 20
        comp.senior = str(jaar - 21)
        return comp

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        huidige_jaar = timezone.now().year

        context['comp_1'] = self._comp_info(huidige_jaar - 1)
        context['comp_2'] = self._comp_info(huidige_jaar)

        _, _, is_jong, _, _ = get_sessionvars_leeftijdsklassen(self.request)
        if is_jong:
            context['is_jong'] = True

        menu_dynamics(self.request, context, actief='competitie')
        return context


# end of file
