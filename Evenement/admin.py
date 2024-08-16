# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Evenement.models import Evenement, EvenementInschrijving, EvenementAfgemeld


class EvenementAdmin(admin.ModelAdmin):

    list_filter = ('status', 'organiserende_vereniging')


class EvenementInschrijvingAdmin(admin.ModelAdmin):

    list_filter = ('status', 'evenement')

    # readonly ivm niet mogen wijzigen, maar ook voor performance
    readonly_fields = ('wanneer', 'evenement', 'sporter', 'koper')


class EvenementAfgemeldAdmin(admin.ModelAdmin):

    list_filter = ('status', 'evenement')

    # readonly ivm niet mogen wijzigen, maar ook voor performance
    readonly_fields = ('evenement', 'sporter', 'koper')


admin.site.register(Evenement, EvenementAdmin)
admin.site.register(EvenementInschrijving, EvenementInschrijvingAdmin)
admin.site.register(EvenementAfgemeld, EvenementAfgemeldAdmin)

# end of file
