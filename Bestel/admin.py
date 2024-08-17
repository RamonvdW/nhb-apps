# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from django.db.models import Count
from Bestel.models import BestelProduct, BestelMandje, Bestelling, BestelMutatie, BESTEL_MUTATIE_TO_STR


class BestelProductAdmin(admin.ModelAdmin):

    readonly_fields = ('wedstrijd_inschrijving',)


class MandjeLeegFilter(admin.SimpleListFilter):

    title = 'Mandje is leeg'

    parameter_name = 'is_leeg'

    def lookups(self, request, model_admin):
        return [('0', 'Leeg'),
                ('1', 'Niet leeg')]

    def queryset(self, request, qs):
        qs = qs.annotate(num_prod=Count("producten"))
        if self.value() == '0':
            # leeg
            qs = qs.filter(num_prod=0)
        elif self.value() == '1':
            # niet leeg
            qs = qs.exclude(num_prod=0)
        # else: alle
        return qs


class BestelMandjeAdmin(admin.ModelAdmin):

    readonly_fields = ('account', 'producten_in_mandje')
    exclude = ('producten',)

    search_fields = ('account__username', 'account__unaccented_naam')

    list_filter = (MandjeLeegFilter,)

    @staticmethod
    def producten_in_mandje(obj):     # pragma: no cover
        return "\n".join(['(pk %s) %s' % (product.pk, product)
                          for product in obj.producten.select_related('wedstrijd_inschrijving').all()])


class BestellingAdmin(admin.ModelAdmin):

    readonly_fields = ('account', 'bestel_nr', 'aangemaakt', 'producten', 'transacties', 'ontvanger')

    search_fields = ('bestel_nr', 'account__username', 'account__unaccented_naam')

    ordering = ('-aangemaakt',)     # nieuwste bovenaan

    auto_complete = ('account', 'ontvanger', 'betaal_mutatie', 'betaal_actief')

    # filter_horizontal = ('producten', 'transacties')

    list_filter = ('status',)

    fieldsets = (
        ('Inhoud',
            {'fields': ('aangemaakt',
                        'producten')
            }),
        ('Koper',
            {'fields': ('bestel_nr',
                        'account',
                        'afleveradres_regel_1', 'afleveradres_regel_2', 'afleveradres_regel_3',
                        'afleveradres_regel_4', 'afleveradres_regel_5')
             }),
        ('Kosten',
            {'fields': ('verzendkosten_euro',
                        'btw_percentage_cat1',
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


class BestelMutatieAdmin(admin.ModelAdmin):

    readonly_fields = ('when', 'account', 'code_plus')

    auto_complete = ('wedstrijd_inschrijving', 'evenement_inschrijving', 'product', 'bestelling')

    list_filter = ('is_verwerkt', 'code')

    fieldsets = (
        ('BestelMutatie',
         {'fields': ('when', 'code_plus', 'is_verwerkt',
                     'account',
                     'wedstrijd_inschrijving', 'product', 'korting', 'bestelling', 'betaling_is_gelukt', 'bedrag_euro')
          }),
    )

    @staticmethod
    def code_plus(obj):     # pragma: no cover
        try:
            msg = "%s: %s" % (obj.code, BESTEL_MUTATIE_TO_STR[obj.code])
        except KeyError:
            msg = "%s: (onbekend)" % obj.code
        return msg


admin.site.register(BestelProduct, BestelProductAdmin)
admin.site.register(BestelMandje, BestelMandjeAdmin)
admin.site.register(Bestelling, BestellingAdmin)
admin.site.register(BestelMutatie, BestelMutatieAdmin)

# end of file
