# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Instaptoets.models import Categorie, Vraag, ToetsAntwoord, Instaptoets, Quiz, Uitdaging, VoorstelVraag


class InstaptoetsAdmin(admin.ModelAdmin):

    readonly_fields = ('sporter',)

    filter_horizontal = ('vraag_antwoord',)


admin.site.register(Categorie)
admin.site.register(Vraag)
admin.site.register(ToetsAntwoord)
admin.site.register(Instaptoets, InstaptoetsAdmin)
admin.site.register(Quiz)
admin.site.register(Uitdaging)
admin.site.register(VoorstelVraag)

# end of file
