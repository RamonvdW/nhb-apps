# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Spelden.models import Speld, SpeldVoorwaarden, SpeldAanvraagPrep, SpeldAanvraag, SpeldBijlage


class SpeldAdmin(admin.ModelAdmin):

    list_filter = ('categorie', 'boog_type', 'volgorde')


class BoogFilter(admin.SimpleListFilter):

    title = 'boog'

    parameter_name = 'boog'

    def lookups(self, request, model_admin):
        return (
            ('R', 'Recurve'),
            ('C', 'Compound'),
            ('BB', 'Barebow'),
            ('LB', 'Longbow'),
            ('TR', 'Traditional'),
        )

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(boog_type__afkorting=self.value())
        return queryset


class LeeftijdsklasseFilter(admin.SimpleListFilter):

    title = 'leeftijdsklasse'

    parameter_name = 'lkl'

    def lookups(self, request, model_admin):
        tups = list()
        for voorwaarde in SpeldVoorwaarden.objects.distinct('leeftijdsklasse'):
            lkl = voorwaarde.leeftijdsklasse
            tups.append((lkl.afkorting, lkl.afkorting + ' ' + lkl.beschrijving))
        # for
        return tups

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(leeftijdsklasse__afkorting=self.value())
        return queryset


class SpeldVoorwaardenAdmin(admin.ModelAdmin):

    list_select_related = ('boog_type', 'leeftijdsklasse',)

    list_filter = ('discipline', 'wedstrijd_soort', BoogFilter,
                   'leeftijdsklasse__wedstrijd_geslacht', LeeftijdsklasseFilter,
                   'afstanden', 'aantal_pijlen', 'aantal_doelen', 'speld')


class SpeldAanvraagAdmin(admin.ModelAdmin):

    autocomplete_fields = ('door_account', 'voor_sporter', 'wedstrijd')


class SpeldAanvraagPrepAdmin(admin.ModelAdmin):

    readonly_fields = ('voor_sporter',)


admin.site.register(Speld, SpeldAdmin)
admin.site.register(SpeldVoorwaarden, SpeldVoorwaardenAdmin)
admin.site.register(SpeldAanvraag, SpeldAanvraagAdmin)
admin.site.register(SpeldAanvraagPrep, SpeldAanvraagPrepAdmin)
admin.site.register(SpeldBijlage)

# end of file
