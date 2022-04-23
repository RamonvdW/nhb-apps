# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import BestelProduct, BestelMandje, Bestelling


class BestelProductAdmin(admin.ModelAdmin):

    readonly_fields = ('inschrijving',)


class BestelMandjeAdmin(admin.ModelAdmin):

    readonly_fields = ('account', 'producten')

    search_fields = ('account__username', 'account__unaccented_naam')


class BestellingAdmin(admin.ModelAdmin):

    readonly_fields = ('account', 'bestel_nr', 'aangemaakt',)

    search_fields = ('bestel_nr', 'account__username', 'account__unaccented_naam')

    ordering = ('aangemaakt',)

    fieldsets = (
        ('Koper',
            {'fields': ('bestel_nr',
                        'account',
                        'aangemaakt',
                        'totaal_euro')
             }),
        ('Transactie',
            {'fields': ('ontvanger',
                        'actief_mutatie',           # BetaalMutatie
                        'actief_transactie',        # BetaalActief
                        'log')
             }),
        ('Niet wijzigen!', {'fields': ('producten', 'transacties')}),
    )


admin.site.register(BestelProduct, BestelProductAdmin)
admin.site.register(BestelMandje, BestelMandjeAdmin)
admin.site.register(Bestelling, BestellingAdmin)

# end of file
