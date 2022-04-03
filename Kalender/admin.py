# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import (KalenderWedstrijd, KalenderWedstrijdSessie, KalenderWedstrijdDeeluitslag,
                     KalenderWedstrijdKortingscode, KalenderInschrijving, KalenderMutatie)


class KalenderWedstrijdAdmin(admin.ModelAdmin):                 # pragma: no cover
    """ Admin configuratie voor KalenderWedstrijd """

    list_filter = ('organisatie', 'discipline', 'status', 'wa_status')

    readonly_fields = ('sessies', 'deeluitslagen', 'boogtypen', 'wedstrijdklassen')

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
        return (KalenderWedstrijd
                .objects
                .select_related('locatie')
                .prefetch_related('boogtypen',
                                  'sessies',
                                  'deeluitslagen')
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


class KalenderWedstrijdSessieAdmin(admin.ModelAdmin):             # pragma: no cover
    """ Admin configuratie voor KalenderWedstrijdSessie """

    search_fields = ('pk',)

    readonly_fields = ('wedstrijdklassen',)

    def get_queryset(self, request):
        """ deze functie is voor prestatieverbetering
            want helaas bestaat list_prefetch_related niet
        """
        # qs = super().get_queryset(request)
        return (KalenderWedstrijdSessie
                .objects
                .prefetch_related('wedstrijdklassen')
                .all())


class KalenderWedstrijdDeeluitslagAdmin(admin.ModelAdmin):          # pragma: no cover
    """ Admin configuratie voor KalenderWedstrijdDeeluitslag """

    search_fields = ('pk',)


class KalenderWedstrijdKortingscodeAdmin(admin.ModelAdmin):

    list_filter = (
                   ('uitgegeven_door', admin.RelatedOnlyFieldListFilter),
                  )

    autocomplete_fields = ('voor_wedstrijden', 'voor_sporter', 'voor_vereniging', 'uitgegeven_door')


class KalenderInschrijvingAdmin(admin.ModelAdmin):

    readonly_fields = ('wanneer', 'wedstrijd', 'sessie', 'sporterboog', 'koper')


class KalenderMutatieAdmin(admin.ModelAdmin):

    readonly_fields = ('code', 'inschrijving', 'korting', 'korting_voor_account')


admin.site.register(KalenderWedstrijd, KalenderWedstrijdAdmin)
admin.site.register(KalenderWedstrijdSessie, KalenderWedstrijdSessieAdmin)
admin.site.register(KalenderWedstrijdDeeluitslag, KalenderWedstrijdDeeluitslagAdmin)
admin.site.register(KalenderWedstrijdKortingscode, KalenderWedstrijdKortingscodeAdmin)
admin.site.register(KalenderInschrijving, KalenderInschrijvingAdmin)
admin.site.register(KalenderMutatie, KalenderMutatieAdmin)

# end of file
