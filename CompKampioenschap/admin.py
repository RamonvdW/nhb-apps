# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from CompKampioenschap.models import SheetStatus


class SheetStatusAdmin(admin.ModelAdmin):

    list_filter = ('bestand__afstand', 'wedstrijd_fase',
                   'bestand__is_bk', 'bestand__is_teams', 'bestand__rayon_nr', 'bevat_scores', 'uitslag_is_compleet',
                   'aantal_deelnemers')


admin.site.register(SheetStatus, SheetStatusAdmin)

# end of file
