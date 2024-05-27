# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Spelden.models import Speld, SpeldScore, SpeldAanvraag, SpeldBijlage


class SpeldScoreAdmin(admin.ModelAdmin):

    list_filter = ('wedstrijd_soort', 'leeftijdsklasse__wedstrijd_geslacht', 'afstand', 'speld', 'boog_type')


admin.site.register(Speld)
admin.site.register(SpeldScore, SpeldScoreAdmin)
admin.site.register(SpeldAanvraag)
admin.site.register(SpeldBijlage)

# end of file
