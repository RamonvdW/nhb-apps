# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import ListView
from Plein.menu import menu_dynamics
from .models import IndivRecord


TEMPLATE_RECORDS_SPECIAL_ER = 'records/records_special_er.dtl'
TEMPLATE_RECORDS_SPECIAL_WR = 'records/records_special_wr.dtl'

makl2str = {'R': 'Recurve',
            'C': 'Compound',
            'BB': 'Barebow',
            'IB': 'Instinctive bow',
            'LB': 'Longbow'}

lcat2str = {'M': 'Masters (50+)',
            'S': 'Senioren',
            'J': 'Junioren (t/m 20 jaar)',
            'C': 'Cadetten (t/m 17 jaar)',
            'U': 'Gecombineerd (bij para)'}


class RecordsSpecialView(ListView):
    """ Toon lijst met 'speciale' records: ER of WR """

    # class variables shared by all instances
    template_name = None

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        for obj in context['object_list']:
            obj.materiaalklasse_str = makl2str[obj.materiaalklasse]
            # obj.leeftijdscategorie_str = lcat2str[obj.leeftijdscategorie]

            obj.url_details = reverse('Records:specifiek', kwargs={'discipline': obj.discipline,
                                                                   'nummer': obj.volg_nr})
        # for

        context['kruimels'] = (
            (reverse('Records:overzicht'), 'Records'),
            (None, self.kruimel)
        )

        menu_dynamics(self.request, context, actief='records')
        return context


class RecordsSpecialERView(RecordsSpecialView):
    """ Toon alle ER records """

    template_name = TEMPLATE_RECORDS_SPECIAL_ER
    kruimel = 'Europesche Records'

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        return (IndivRecord
                .objects
                .filter(is_european_record=True)
                .order_by('-datum'))


class RecordsSpecialWRView(RecordsSpecialView):
    """ Toon alle WR records """

    template_name = TEMPLATE_RECORDS_SPECIAL_WR
    kruimel = 'Wereld Records'

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        return (IndivRecord
                .objects
                .filter(is_world_record=True)
                .order_by('-datum'))


# end of file
