# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import WedstrijdLocatie, Wedstrijd, WedstrijdenPlan, WedstrijdUitslag


class WedstrijdAdmin(admin.ModelAdmin):             # pragma: no cover
    """ Admin configuratie voor Wedstrijd """

    search_fields = ('beschrijving', 'vereniging__ver_nr', 'vereniging__naam')

    filter_horizontal = ('indiv_klassen', 'team_klassen')

    def get_queryset(self, request):
        """ deze functie is voor prestatieverbetering
            want helaas bestaat list_prefetch_related niet
        """
        # qs = super().get_queryset(request)
        return (Wedstrijd
                .objects
                .select_related('locatie', 'vereniging')
                .prefetch_related('indiv_klassen', 'team_klassen')
                .all())


class WedstrijdLocatieAdmin(admin.ModelAdmin):      # pragma: no cover
    """ Admin configuratie voor WedstrijdLocatie """

    list_filter = ('baan_type',
                   'discipline_outdoor', 'discipline_indoor', 'discipline_veld',
                   'zichtbaar',)

    search_fields = ('adres', 'verenigingen__ver_nr')

    def get_queryset(self, request):
        """ deze functie is voor prestatieverbetering
            want helaas bestaat list_prefetch_related niet
        """
        # qs = super().get_queryset(request)
        return (WedstrijdLocatie
                .objects
                .prefetch_related('verenigingen')
                .all())


class WedstrijdenPlanAdmin(admin.ModelAdmin):      # pragma: no cover
    """ Admin configuratie voor WedstrijdenPlan"""

    search_fields = ('pk',)

    autocomplete_fields = ('wedstrijden',)


class WedstrijdUitslagAdmin(admin.ModelAdmin):      # pragma: no cover
    """ Admin configuratie voor WedstrijdenUitslag"""

    readonly_fields = ('scores',)

    #autocomplete_fields = ('wedstrijden',)
    pass


admin.site.register(WedstrijdLocatie, WedstrijdLocatieAdmin)
admin.site.register(Wedstrijd, WedstrijdAdmin)
admin.site.register(WedstrijdenPlan, WedstrijdenPlanAdmin)
admin.site.register(WedstrijdUitslag, WedstrijdUitslagAdmin)

# FUTURE: Wedstrijd admin scherm word langzaam als str(WedstrijdLocatie) een self.verenigingen.count() doet
#         nog niet op kunnen lossen met een get_queryset(). Even uitgezet.

# end of file
