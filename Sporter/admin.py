# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Sporter.models import Sporter, SporterVoorkeuren, SporterBoog, Speelsterkte


class HeeftWaIdListFilter(admin.SimpleListFilter):

    title = 'Heeft WA Id'

    parameter_name = 'heeft_wa_id'

    def lookups(self, request, model_admin):
        return (
            ('Ja', 'Heeft een WA id'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'Ja':
            queryset = queryset.exclude(wa_id='')
        return queryset


class SporterAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Sporter klasse """

    ordering = ('lid_nr',)

    search_fields = ('unaccented_naam', 'lid_nr')

    # filter mogelijkheid
    list_filter = ('geslacht', 'para_classificatie', 'is_actief_lid', HeeftWaIdListFilter)

    list_select_related = True


class SporterBoogAdmin(admin.ModelAdmin):
    """ Admin configuratie voor SporterBoog klasse """

    search_fields = ('sporter__lid_nr', 'sporter__unaccented_naam')

    list_select_related = ('sporter', 'boogtype')

    autocomplete_fields = ('sporter',)


class SporterVoorkeurenAdmin(admin.ModelAdmin):
    """ Admin configuratie voor SporterVoorkeuren klasse """

    search_fields = ('sporter__lid_nr', 'sporter__unaccented_naam')

    list_select_related = True

    readonly_fields = ('sporter',)

    fieldsets = (
        ('Wie',
            {'fields': ('sporter',)
             }),
        ('Disciplines',
            {'fields': ('voorkeur_discipline_25m1pijl',
                        'voorkeur_discipline_outdoor',
                        'voorkeur_discipline_indoor',
                        'voorkeur_discipline_clout',
                        'voorkeur_discipline_veld',
                        'voorkeur_discipline_run',
                        'voorkeur_discipline_3d'),
             }),
        ('Wedstrijdgeslacht',
            {'fields': ('wedstrijd_geslacht_gekozen',
                        'wedstrijd_geslacht'),
             }),
        ('Para',
            {'fields': ('para_met_rolstoel',
                        'opmerking_para_sporter',)
             }),
        ('Overig',
            {'fields': ('voorkeur_eigen_blazoen',
                        'voorkeur_meedoen_competitie')
             }),
    )


class SpeelsterkteAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Speelsterkte klasse """

    search_fields = ('beschrijving', 'category', 'discipline', 'sporter__unaccented_naam')

    list_filter = ('discipline', 'beschrijving', 'category')

    readonly_fields = ('sporter',)

    list_select_related = True


admin.site.register(Sporter, SporterAdmin)
admin.site.register(SporterBoog, SporterBoogAdmin)
admin.site.register(SporterVoorkeuren, SporterVoorkeurenAdmin)
admin.site.register(Speelsterkte, SpeelsterkteAdmin)

# end of file
