# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Instaptoets.models import Categorie, Vraag, ToetsAntwoord, Instaptoets, Quiz, Uitdaging


class InstaptoetsAdmin(admin.ModelAdmin):

    readonly_fields = ('sporter',)

    filter_horizontal = ('vraag_antwoord',)

    search_fields = ('sporter__lid_nr',)

    list_filter = ('geslaagd', 'aantal_goed')


admin.site.register(Categorie)
admin.site.register(Vraag)
admin.site.register(ToetsAntwoord)
admin.site.register(Instaptoets, InstaptoetsAdmin)
admin.site.register(Quiz)
admin.site.register(Uitdaging)

# end of file
