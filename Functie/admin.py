# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Functie.models import Functie, VerklaringHanterenPersoonsgegevens


class FunctieAdmin(admin.ModelAdmin):

    filter_horizontal = ('accounts',)

    ordering = ('beschrijving',)

    search_fields = ('beschrijving', 'vereniging__naam', 'vereniging__plaats',
                     'bevestigde_email', 'nieuwe_email', 'rol')

    list_filter = ('rol',)


class VHPGAdmin(admin.ModelAdmin):
    search_fields = ('account__username',)
    list_select_related = ('account',)


admin.site.register(Functie, FunctieAdmin)
admin.site.register(VerklaringHanterenPersoonsgegevens, VHPGAdmin)


# end of file
