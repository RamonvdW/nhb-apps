# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import TemplateView, ListView, View
from Plein.menu import menu_dynamics
from BasisTypen.models import IndivWedstrijdklasse
from NhbStructuur.models import NhbRegio


TEMPLATE_COMPETITIE_INFO_COMPETITIE = 'competitie/info-competitie.dtl'


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

# end of file
