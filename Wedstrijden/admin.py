# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Wedstrijden.models import (WedstrijdLocatie, Wedstrijd, WedstrijdSessie,
                                WedstrijdKorting, WedstrijdInschrijving)


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


class WedstrijdAdmin(admin.ModelAdmin):                 # pragma: no cover
    """ Admin configuratie voor Wedstrijd """

    list_filter = ('status', 'extern_beheerd', 'is_ter_info', 'organisatie', 'wa_status', 'discipline')

    readonly_fields = ('sessies', 'boogtypen', 'wedstrijdklassen')

    search_fields = ('titel',)

    ordering = ('datum_begin',)

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    def get_queryset(self, request):
        """ deze functie is voor prestatieverbetering
            want helaas bestaat list_prefetch_related niet
        """
        # qs = super().get_queryset(request)
        return (Wedstrijd
                .objects
                .select_related('locatie')
                .prefetch_related('boogtypen',
                                  'sessies')
                .all())

    def get_form(self, request, obj=None, **kwargs):
        if obj:                 # pragma: no branch
            self.obj = obj      # pragma: no cover
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'locatie' and self.obj:
            ver = self.obj.organiserende_vereniging
            kwargs['queryset'] = ver.wedstrijdlocatie_set.all()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class WedstrijdSessieAdmin(admin.ModelAdmin):             # pragma: no cover
    """ Admin configuratie voor WedstrijdSessie """

    search_fields = ('pk',)

    readonly_fields = ('wedstrijdklassen',)

    def get_queryset(self, request):
        """ deze functie is voor prestatieverbetering
            want helaas bestaat list_prefetch_related niet
        """
        # qs = super().get_queryset(request)
        return (WedstrijdSessie
                .objects
                .prefetch_related('wedstrijdklassen')
                .all())


class WedstrijdKortingAdmin(admin.ModelAdmin):

    list_filter = (
                   ('uitgegeven_door', admin.RelatedOnlyFieldListFilter),
                  )

    autocomplete_fields = ('voor_wedstrijden', 'voor_sporter', 'uitgegeven_door')


class WedstrijdInschrijvingAdmin(admin.ModelAdmin):

    readonly_fields = ('wanneer', 'wedstrijd', 'sessie', 'sporterboog', 'koper')

    list_filter = ('status',)

    search_fields = ('sporterboog__sporter__lid_nr',)


admin.site.register(WedstrijdLocatie, WedstrijdLocatieAdmin)
admin.site.register(Wedstrijd, WedstrijdAdmin)
admin.site.register(WedstrijdSessie, WedstrijdSessieAdmin)
admin.site.register(WedstrijdKorting, WedstrijdKortingAdmin)
admin.site.register(WedstrijdInschrijving, WedstrijdInschrijvingAdmin)

# FUTURE: Wedstrijd admin scherm word langzaam als str(WedstrijdLocatie) een self.verenigingen.count() doet
#         nog niet op kunnen lossen met een get_queryset(). Even uitgezet.

# end of file
