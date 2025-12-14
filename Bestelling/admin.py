# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from django.db.models import Count
from Bestelling.definities import BESTELLING_MUTATIE_TO_STR
from Bestelling.models import BestellingRegel, BestellingMandje, Bestelling, BestellingMutatie
from Vereniging.models import Vereniging


class BtwFilter(admin.SimpleListFilter):

    title = 'btw'

    parameter_name = 'btw'

    def lookups(self, request, model_admin):
        return (
            ('Ja', 'Heeft BTW'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'Ja':
            queryset = queryset.exclude(btw_percentage='')
        return queryset


class OrphanFilter(admin.SimpleListFilter):

    title = 'orphan'

    parameter_name = 'orphan'

    def lookups(self, request, model_admin):
        return (
            ('Ja', 'Geen bestelling'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'Ja':
            queryset = queryset.annotate(c=Count('bestelling')).filter(c=0)
        return queryset


class BestellingRegelAdmin(admin.ModelAdmin):

    list_filter = ('code', BtwFilter, OrphanFilter)

    search_fields = ('korte_beschrijving', )


class MandjeLeegFilter(admin.SimpleListFilter):

    title = 'Mandje is leeg'

    parameter_name = 'is_leeg'

    def lookups(self, request, model_admin):
        return [('0', 'Leeg'),
                ('1', 'Niet leeg')]

    def queryset(self, request, qs):
        qs = qs.annotate(num_prod=Count("regels"))
        if self.value() == '0':
            # leeg
            qs = qs.filter(num_prod=0)
        elif self.value() == '1':
            # niet leeg
            qs = qs.exclude(num_prod=0)
        # else: alle
        return qs


class BestellingMandjeAdmin(admin.ModelAdmin):

    readonly_fields = ('account', 'regels_in_mandje')
    exclude = ('regels',)

    search_fields = ('account__username', 'account__unaccented_naam')

    list_filter = (MandjeLeegFilter,)

    @staticmethod
    def regels_in_mandje(obj):        # pragma: no cover
        return "\n".join([str(regel) for regel in obj.regels.all()])


class BestellingTransactions(admin.TabularInline):
    from Betaal.models import BetaalTransactie
    model = BetaalTransactie


class OntvangerFilter(admin.SimpleListFilter):
    title = 'Ontvanger'
    parameter_name = 'ontvanger'

    def lookups(self, request, model_admin):
        actieve_ver_nrs = (Bestelling
                           .objects
                           .distinct('ontvanger')
                           .values_list('ontvanger__vereniging__ver_nr', flat=True))
        # print('actieve ontvangers: %s' % actieve_ver_nrs)
        return [(ver.ver_nr, ver.ver_nr_en_naam())
                for ver in Vereniging.objects.filter(ver_nr__in=actieve_ver_nrs).order_by('ver_nr')]

    def queryset(self, request, queryset):          # pragma: no cover
        ver_nr = self.value()
        # print('ver_nr: %s' % repr(ver_nr))
        if ver_nr:
            queryset = queryset.filter(ontvanger__vereniging__ver_nr=ver_nr)
        return queryset


class BestellingAdmin(admin.ModelAdmin):

    readonly_fields = ('account', 'bestel_nr', 'aangemaakt', 'regels_in_mandje',
                       'ontvanger', 'betaal_mutatie', 'betaal_actief')

    filter_vertical = ('transacties',)

    search_fields = ('bestel_nr', 'account__username', 'account__unaccented_naam', 'betaal_mutatie__payment_id')

    ordering = ('-aangemaakt',)     # nieuwste bovenaan

    auto_complete = ('account', 'ontvanger')

    list_filter = ('status', 'transport', OntvangerFilter)

    fieldsets = (
        ('Inhoud',
            {'fields': ('aangemaakt',
                        'regels_in_mandje')
            }),
        ('Koper',
            {'fields': ('bestel_nr',
                        'account',
                        'afleveradres_regel_1', 'afleveradres_regel_2', 'afleveradres_regel_3',
                        'afleveradres_regel_4', 'afleveradres_regel_5')
             }),
        ('Kosten',
            {'fields': ('btw_percentage_cat1',
                        'btw_percentage_cat2',
                        'btw_percentage_cat3',
                        'btw_euro_cat1',
                        'btw_euro_cat2',
                        'btw_euro_cat3',
                        'totaal_euro')
             }),
        ('Verkoper',
            {'fields': ('verkoper_naam',
                        'verkoper_adres1',
                        'verkoper_adres2',
                        'verkoper_kvk',
                        'verkoper_email',
                        'verkoper_telefoon',
                        'verkoper_iban',
                        'verkoper_bic',
                        'verkoper_btw_nr')
             }),
        ('Transactie',
            {'fields': ('status',
                        'ontvanger',
                        'betaal_mutatie',       # BetaalMutatie
                        'betaal_actief',        # BetaalActief
                        'transacties',
                        'log')
             }),
    )

    @staticmethod
    def regels_in_mandje(obj):        # pragma: no cover
        return "\n".join([str(regel) for regel in obj.regels.all()])


class BestellingMutatieAdmin(admin.ModelAdmin):

    readonly_fields = ('when', 'account', 'code_plus', 'regel', 'bestelling')

    list_filter = ('is_verwerkt', 'code')

    fieldsets = (
        ('BestellingMutatie',
         {'fields': ('when', 'code_plus', 'product_pk', 'is_verwerkt',
                     'account',
                     'regel', 'korting', 'bestelling', 'betaling_is_gelukt', 'bedrag_euro')
          }),
    )

    search_fields = ('account__username',)

    @staticmethod
    def code_plus(obj):     # pragma: no cover
        try:
            msg = "%s: %s" % (obj.code, BESTELLING_MUTATIE_TO_STR[obj.code])
        except KeyError:
            msg = "%s: (onbekend)" % obj.code
        return msg


admin.site.register(BestellingMandje, BestellingMandjeAdmin)
admin.site.register(Bestelling, BestellingAdmin)
admin.site.register(BestellingRegel, BestellingRegelAdmin)
admin.site.register(BestellingMutatie, BestellingMutatieAdmin)

# end of file
