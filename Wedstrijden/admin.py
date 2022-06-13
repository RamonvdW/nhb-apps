# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import WedstrijdLocatie


class WedstrijdLocatieAdmin(admin.ModelAdmin):      # pragma: no cover
    """ Admin configuratie voor WedstrijdLocatie """

    list_filter = ('baan_type',
                   'discipline_outdoor', 'discipline_indoor', 'discipline_veld',
                   'discipline_25m1pijl',
                   'zichtbaar', 'adres_uit_crm')

    search_fields = ('adres', 'verenigingen__ver_nr')

    def get_queryset(self, request):
        """ deze functie is voor prestatieverbetering
            want helaas bestaat list_prefetch_related niet
        """
        # qs = super().get_queryset(request)
        return (WedstrijdLocatie
                .objects
                .prefetch_related('verenigingen')
                .all())


admin.site.register(WedstrijdLocatie, WedstrijdLocatieAdmin)

# FUTURE: Wedstrijd admin scherm word langzaam als str(WedstrijdLocatie) een self.verenigingen.count() doet
#         nog niet op kunnen lossen met een get_queryset(). Even uitgezet.

# end of file
