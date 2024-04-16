# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Locatie.models import Locatie, Reistijd


class LocatieAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Locatie """

    list_filter = ('baan_type',
                   'discipline_outdoor', 'discipline_indoor', 'discipline_veld', 'discipline_25m1pijl',
                   'zichtbaar', 'adres_uit_crm')

    search_fields = ('adres', 'verenigingen__ver_nr')

    def get_queryset(self, request):
        """ deze functie is voor prestatieverbetering
            want helaas bestaat list_prefetch_related niet
        """
        # qs = super().get_queryset(request)
        return (Locatie
                .objects
                .prefetch_related('verenigingen')
                .all())


class GeenReistijdFilter(admin.SimpleListFilter):

    title = 'Reistijd vastgesteld?'
    parameter_name = 'reistijd_vastgesteld'

    def lookups(self, request, model_admin):
        return [
            ('nul', 'Reistijd nog niet vastgesteld'),
        ]

    def queryset(self, request, qset):
        if self.value() == 'nul':
            qset = qset.filter(reistijd_min=0)
        return qset


class ReistijdAdmin(admin.ModelAdmin):

    list_filter = (GeenReistijdFilter,)


admin.site.register(Locatie, LocatieAdmin)
admin.site.register(Reistijd, ReistijdAdmin)

# end of file
