# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Bestelling.models import Bestelling
from Betaal.definities import TRANSACTIE_TYPE_CHOICES
from Betaal.models import BetaalInstellingenVereniging, BetaalActief, BetaalTransactie, BetaalMutatie


class HeeftRestitutieFilter(admin.SimpleListFilter):
    title = 'Heeft restitutie'
    parameter_name = 'heeft_restitutie'

    def lookups(self, request, model_admin):
        return [('ja', 'Ja')]

    def queryset(self, request, queryset):
        if self.value() == 'ja':
            queryset = queryset.filter(bedrag_terugbetaald__gt=0.0)
        return queryset


class HeeftTerugvorderingFilter(admin.SimpleListFilter):
    title = 'Heeft terugvordering'
    parameter_name = 'heeft_terugvordering'

    def lookups(self, request, model_admin):
        return [('ja', 'Ja')]

    def queryset(self, request, queryset):
        if self.value() == 'ja':
            queryset = queryset.filter(bedrag_teruggevorderd__gt=0.0)
        return queryset


class TransactieTypeFilter(admin.SimpleListFilter):
    title = 'Transactie type'
    parameter_name = 'transactietype'

    def lookups(self, request, model_admin):
        return TRANSACTIE_TYPE_CHOICES

    def queryset(self, request, queryset):
        value = self.value()
        print('value: %s' % repr(value))
        if value:
            queryset = queryset.filter(transactie_type=self.value())
        return queryset


class BetaalTransactieAdmin(admin.ModelAdmin):

    ordering = ('-when',)

    list_filter = (TransactieTypeFilter, 'payment_status', HeeftRestitutieFilter, HeeftTerugvorderingFilter)

    search_fields = ('payment_id', 'refund_id', 'beschrijving')

    fieldsets = (
        ('Basics',
            {'fields': ('when',
                        'transactie_type',
                        'beschrijving',
                        'bedrag_handmatig'),
             }),
        ('Mollie',
            {'fields': ('payment_id',
                        'payment_status',
                        'bedrag_te_ontvangen',
                        'klant_naam',
                        'klant_account',
                        'bedrag_terugbetaald',
                        'bedrag_teruggevorderd',
                        'bedrag_beschikbaar')
             }),
        ('Mollie restitutie',
            {'fields': ('refund_id',
                        'refund_status',
                        'bedrag_refund'),
             }),
    )


class OntvangerFilter(admin.SimpleListFilter):

    title = 'Ontvanger'

    parameter_name = 'ontvanger'

    def lookups(self, request, model_admin):
        lijst = [
            (actief.ontvanger.vereniging.ver_nr, actief.ontvanger.vereniging.ver_nr_en_naam())
            for actief in BetaalActief.objects.distinct('ontvanger').select_related('ontvanger__vereniging')
        ]
        return lijst

    def queryset(self, request, queryset):
        ver_nr = self.value()
        if ver_nr:
            queryset = queryset.filter(ontvanger__vereniging__ver_nr=ver_nr)
        return queryset


class BetaalActiefAdmin(admin.ModelAdmin):

    ordering = ('-when',)

    list_filter = ('payment_status', OntvangerFilter)

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

    ordering = ('-when',)

    search_fields = ('payment_id', 'beschrijving')

    list_filter = ('is_verwerkt', 'pogingen', 'code')


admin.site.register(BetaalInstellingenVereniging, BetaalInstellingenVerenigingAdmin)
admin.site.register(BetaalActief, BetaalActiefAdmin)
admin.site.register(BetaalTransactie, BetaalTransactieAdmin)
admin.site.register(BetaalMutatie, BetaalMutatieAdmin)

# end of file
