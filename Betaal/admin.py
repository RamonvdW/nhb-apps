# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Betaal.models import BetaalInstellingenVereniging, BetaalActief, BetaalTransactie, BetaalMutatie


class BetaalTransactieAdmin(admin.ModelAdmin):

    search_fields = ('payment_id', 'beschrijving')


class BetaalActiefAdmin(admin.ModelAdmin):

    search_fields = ('payment_id',)


class HeeftMollieKeyFilter(admin.SimpleListFilter):

    title = 'Heeft Mollie koppeling'

    parameter_name = 'Mollie'

    def lookups(self, request, model_admin):
        return (('0', 'Ja'),
                ('1', 'Nee'))

    def queryset(self, request, queryset):
        keuze = self.value()
        if keuze is not None:
            # print('keuze: %s' % repr(keuze))
            if keuze == '0':
                # moet een mollie key hebben
                queryset = queryset.exclude(mollie_api_key='')

            else:
                # moet juist geen mollie key hebben
                queryset = queryset.filter(mollie_api_key='')

        return queryset


class BetaalInstellingenVerenigingAdmin(admin.ModelAdmin):

    search_fields = ('vereniging__ver_nr', 'vereniging__naam')

    list_filter = (HeeftMollieKeyFilter, 'akkoord_via_bond')


class BetaalMutatieAdmin(admin.ModelAdmin):

    search_fields = ('payment_id', 'beschrijving')

    list_filter = ('is_verwerkt', 'pogingen', 'code')


admin.site.register(BetaalInstellingenVereniging, BetaalInstellingenVerenigingAdmin)
admin.site.register(BetaalActief, BetaalActiefAdmin)
admin.site.register(BetaalTransactie, BetaalTransactieAdmin)
admin.site.register(BetaalMutatie, BetaalMutatieAdmin)

# end of file
