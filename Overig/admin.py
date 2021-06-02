# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import SiteFeedback, SiteTijdelijkeUrl


class IsAfgehandeldListFilter(admin.SimpleListFilter):      # pragma: no cover
    """ speciaal filter voor is_afgehandeld met default=No """

    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'is afgehandeld'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'is_afgehandeld'

    def lookups(self, request, model_admin):
        """ geeft de filter mogelijkheden terug """
        return ((0, 'Nog niet'), (1, 'Ja'), (-1, 'Alles'))

    def queryset(self, request, queryset):
        """ geef een gefilterde lijst met records terug """
        val = self.value()
        if val == '-1':
            return queryset
        if val == '0':
            val = False
        elif val == '1':
            val = True
        else:
            val = False     # also default
        return queryset.filter(is_afgehandeld=val)

    def choices(self, cl):
        """ Produceer de opties die in het filter getoond worden
            zorgt ook voor extra informatie voor highlighten
        """
        # filter de All optie eruit
        val = self.value()
        for opt in super().choices(cl):
            # zorg voor highlight op 'Nog niet' als initiële waarde
            if not val:
                if opt['display'] == 'Nog niet':
                    opt['selected'] = True
            # mik de All optie eruit
            if opt['display'] != 'All':
                yield opt
        # for


class SiteFeedbackAdmin(admin.ModelAdmin):
    # filter mogelijkheid
    list_filter = (IsAfgehandeldListFilter,)

    readonly_fields = ('toegevoegd_op', 'op_pagina', 'site_versie', )

    # volgorde van de velden
    fields = ('toegevoegd_op', 'bevinding', 'is_afgehandeld', 'feedback', 'gebruiker', 'op_pagina', 'site_versie')


class SiteTijdelijkeUrlAdmin(admin.ModelAdmin):

    # readonly voorkomt inladen van lange lijst met mogelijkheden
    # dit is ook meteen de volgorde waarin ze getoond worden
    readonly_fields = ('hoortbij_accountemail',
                       'hoortbij_functie')

    list_select_related = ('hoortbij_functie',
                           'hoortbij_accountemail',
                           'hoortbij_accountemail__account')


admin.site.register(SiteFeedback, SiteFeedbackAdmin)
admin.site.register(SiteTijdelijkeUrl, SiteTijdelijkeUrlAdmin)

# end of file
