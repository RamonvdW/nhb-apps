# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Registreer.models import GastLidNummer, GastRegistratie, GastRegistratieRateTracker


class GastRegistratieRateTrackerAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Sporter klasse """

    ordering = ('teller_uur',)


class GastRegistratieAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Sporter klasse """

    ordering = ('-aangemaakt',)       # nieuwste bovenaan

    search_fields = ('voornaam', 'achternaam', 'lid_nr', 'email')

    list_select_related = True

    autocomplete_fields = ('account', 'sporter')


admin.site.register(GastRegistratie, GastRegistratieAdmin)
admin.site.register(GastRegistratieRateTracker, GastRegistratieRateTrackerAdmin)
admin.site.register(GastLidNummer)

# end of file
