# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import MandjeProduct, MandjeBestelling, MandjeTransactie


class MandjeProductAdmin(admin.ModelAdmin):

    readonly_fields = ('account', 'inschrijving')


class MandjeBestellingAdmin(admin.ModelAdmin):

    readonly_fields = ('account', 'boekingsnummer', 'aangemaakt', 'producten')

    search_fields = ('boekingsnummer', 'account__username', 'account__unaccented_naam')

    ordering = ('aangemaakt',)

    fieldsets = (
        ('Koper',
            {'fields': ('boekingsnummer',
                        'account',
                        'aangemaakt')
             }),
        ('Producten',
            {'fields': (('producten',),),
             }),
        ('Betaling',
            {'fields': ('totaal_euro',
                        'is_betaald',
                        'wanneer_betaald'),
             }),
    )

class MandjeTransactieAdmin(admin.ModelAdmin):

    pass


admin.site.register(MandjeProduct, MandjeProductAdmin)
admin.site.register(MandjeBestelling, MandjeBestellingAdmin)
admin.site.register(MandjeTransactie, MandjeTransactieAdmin)

# end of file
