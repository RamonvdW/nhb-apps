# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Registreer.definities import REGISTRATIE_FASE2STR
from Registreer.models import GastLidNummer, GastRegistratie, GastRegistratieRateTracker


class GastRegistratieFaseFilter(admin.SimpleListFilter):

    title = "Fase"

    parameter_name = 'fase_filter'

    default_value = None

    def lookups(self, request, model_admin):
        """ Return list of tuples for the sidebar """
        return [tup for tup in REGISTRATIE_FASE2STR.items()]

    def queryset(self, request, queryset):
        selection = self.value()
        if selection:
            queryset = queryset.filter(fase=selection)
        return queryset


class GastRegistratieAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Sporter klasse """

    ordering = ('-aangemaakt',)       # nieuwste bovenaan

    search_fields = ('voornaam', 'achternaam', 'lid_nr', 'email')

    list_select_related = True

    autocomplete_fields = ('account', 'sporter')

    list_filter = (GastRegistratieFaseFilter, 'land')


class GastRegistratieRateTrackerAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Sporter klasse """

    ordering = ('teller_uur',)


admin.site.register(GastRegistratie, GastRegistratieAdmin)
admin.site.register(GastRegistratieRateTracker, GastRegistratieRateTrackerAdmin)
admin.site.register(GastLidNummer)

# end of file
