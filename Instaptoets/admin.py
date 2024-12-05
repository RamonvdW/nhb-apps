# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Instaptoets.models import Vraag, ToetsAntwoord, Instaptoets, Quiz, Uitdaging, VoorstelVraag


class InstaptoetsAdmin(admin.ModelAdmin):

    readonly_fields = ('sporter',)

    filter_horizontal = ('vraag_antwoord',)


admin.site.register(Vraag)  # VraagAdmin)
admin.site.register(ToetsAntwoord)  # ToetsAntwoordAdmin)
admin.site.register(Instaptoets, InstaptoetsAdmin)
admin.site.register(Quiz)   # QuizAdmin)
admin.site.register(Uitdaging)  # UitdagingAdmin)
admin.site.register(VoorstelVraag)  # VoorstelVraagAdmin)

# end of file
