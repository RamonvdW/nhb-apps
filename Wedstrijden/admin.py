# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import WedstrijdLocatie, Wedstrijd, WedstrijdenPlan


class WedstrijdLocatieAdmin(admin.ModelAdmin):      # pragma: no cover

    list_filter = ('zichtbaar',)

    search_fields = ('adres', 'verenigingen__nhb_nr')

    def get_queryset(self, request):
        """ deze functie is voor prestatieverbetering
            helaas bestaat list_prefetch_related niet
        """
        # qs = super().get_queryset(request)
        return (WedstrijdLocatie
                .objects
                .prefetch_related('verenigingen')
                .all())


admin.site.register(WedstrijdLocatie, WedstrijdLocatieAdmin)
admin.site.register(Wedstrijd)
admin.site.register(WedstrijdenPlan)

# TODO: Wedstrijd admin scherm is langzaam omdat str(WedstrijdLocatie) een self.verenigingen.count() doet
#       nog niet op kunnen lossen met een get_queryset()

# end of file
