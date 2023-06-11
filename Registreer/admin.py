# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Registreer.models import GastLidNummer, GastRegistratie, GastRegistratieRateTracker


class GastRegistratieAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Sporter klasse """

    ordering = ('-datum_aangemaakt',)       # nieuwste bovenaan

    search_fields = ('voornaam', 'achternaam', 'lid_nr', 'email')

    list_select_related = True


admin.site.register(GastRegistratie, GastRegistratieAdmin)
admin.site.register(GastLidNummer)
admin.site.register(GastRegistratieRateTracker)

# end of file
