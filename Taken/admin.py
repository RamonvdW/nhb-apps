# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.contrib import admin
from Functie.models import Functie
from Taken.models import Taak


class ToegekendAanFunctieListFilter(admin.SimpleListFilter):

    title = 'toegekend aan functie'

    parameter_name = 'ToegekendAanFunctie'

    def lookups(self, request, model_admin):

        functie_pks = list(Taak
                           .objects
                           .exclude(toegekend_aan_functie=None)
                           .distinct('toegekend_aan_functie')
                           .values_list('toegekend_aan_functie__pk', flat=True))

        lijstje_main = list()
        lijstje_comp = list()
        lijstje_ver = list()
        for functie in (Functie
                        .objects
                        .filter(pk__in=functie_pks)
                        .order_by('rol',
                                  'vereniging__ver_nr',
                                  'comp_type',
                                  'rayon__rayon_nr',
                                  'regio__regio_nr')):     # pragma: no cover
            tup = (functie.pk, functie.beschrijving)

            if functie.comp_type:
                lijstje_comp.append(tup)
            elif functie.vereniging and functie.vereniging.ver_nr not in (settings.WEBWINKEL_VERKOPER_VER_NR,
                                                                          settings.EXTERN_VER_NR):
                lijstje_ver.append(tup)
            else:
                lijstje_main.append(tup)
        # for
        return lijstje_main + lijstje_comp + lijstje_ver

    def queryset(self, request, queryset):                  # pragma: no cover
        pk = self.value()
        if pk:
            queryset = queryset.filter(toegekend_aan_functie__pk=pk)
        return queryset


class TaakAdmin(admin.ModelAdmin):

    """ Admin configuratie voor Taak klasse """

    list_filter = ('is_afgerond',
                   ToegekendAanFunctieListFilter)

    list_select_related = ('toegekend_aan_functie',
                           'aangemaakt_door')

    autocomplete_fields = ('toegekend_aan_functie',
                           'aangemaakt_door')


admin.site.register(Taak, TaakAdmin)

# end of file
