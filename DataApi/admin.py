# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from DataApi.models import DataApiVereniging, DataApiLidmaatschap


class VerenigingIsActiefFilter(admin.SimpleListFilter):

    title = 'Vereniging is actief'

    parameter_name = 'ver_is_actief'

    def lookups(self, request, model_admin):
        return (
            ('Ja', 'Vereniging is actief'),
            ('Nee', 'Vereniging is afgemeld'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'Ja':
            queryset = queryset.filter(afmeld_datum='')
        if self.value() == 'Nee':
            queryset = queryset.exclude(afmeld_datum='')
        return queryset


class DataApiVerenigingAdmin(admin.ModelAdmin):

    list_filter = (VerenigingIsActiefFilter, )

    search_fields = ('ver_nr', 'naam', 'straatnaam', 'plaats')


class DataApiLidmaatschapAdmin(admin.ModelAdmin):

    search_fields = ('lid_nr',)


admin.site.register(DataApiVereniging, DataApiVerenigingAdmin)
admin.site.register(DataApiLidmaatschap, DataApiLidmaatschapAdmin)

# end of file
