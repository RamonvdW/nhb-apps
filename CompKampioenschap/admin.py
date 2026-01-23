# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from CompKampioenschap.models import SheetStatus


class SheetStatusAdmin(admin.ModelAdmin):

    list_filter = ('bestand__afstand', 'bestand__is_bk', 'bestand__is_teams', 'bevat_scores', 'uitslag_is_compleet', 'wedstrijd_fase')


admin.site.register(SheetStatus, SheetStatusAdmin)

# end of file
