# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Bestel.models import BestelProduct, BestelMandje, Bestelling, BestelMutatie, BESTEL_MUTATIE_TO_STR


class BestelProductAdmin(admin.ModelAdmin):

    readonly_fields = ('wedstrijd_inschrijving',)


class BestelMandjeAdmin(admin.ModelAdmin):

    readonly_fields = ('account', 'producten_in_mandje')
    exclude = ('producten',)

    search_fields = ('account__username', 'account__unaccented_naam')

    @staticmethod
    def producten_in_mandje(obj):     # pragma: no cover
        return "\n".join(['(pk %s) %s' % (product.pk, product) for product in
                                            obj.producten.select_related('wedstrijd_inschrijving').all()])


class BestellingAdmin(admin.ModelAdmin):

    readonly_fields = ('account', 'bestel_nr', 'aangemaakt',)

    search_fields = ('bestel_nr', 'account__username', 'account__unaccented_naam')

    ordering = ('-aangemaakt',)     # nieuwste bovenaan

    auto_complete = ('account', 'ontvanger', 'betaal_mutatie', 'betaal_actief')

    filter_horizontal = ('producten',)

    list_filter = ('status',)

    fieldsets = (
        ('Koper',
            {'fields': ('bestel_nr',
                        'account',
                        'aangemaakt',
                        'totaal_euro')
             }),
        ('Verkoper',
            {'fields': ('verkoper_naam',
                        'verkoper_adres1',
                        'verkoper_adres2',
                        'verkoper_kvk',
                        'verkoper_email',
                        'verkoper_telefoon')
             }),
        ('Transactie',
            {'fields': ('status',
                        'ontvanger',
                        'betaal_mutatie',       # BetaalMutatie
                        'betaal_actief',        # BetaalActief
                        'log')
             }),
        ('Niet wijzigen!',
            {'fields': ('producten',
                        'transacties')}),
    )


class BestelMutatieAdmin(admin.ModelAdmin):

    readonly_fields = ('when', 'account', 'code_plus')

    auto_complete = ('wedstrijd_inschrijving', 'product', 'bestelling')

    fieldsets = (
        ('BestelMutatie',
         {'fields': ('when', 'code_plus', 'is_verwerkt',
                     'account',
                     'wedstrijd_inschrijving', 'product', 'korting', 'bestelling', 'betaling_is_gelukt')
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
