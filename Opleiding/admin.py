# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from django.utils import timezone
from Opleiding.models import OpleidingDiploma, Opleiding, OpleidingMoment, OpleidingInschrijving, OpleidingAfgemeld


class CreateOnlyAdmin(admin.ModelAdmin):
    """
        Extend the ModelAdmin with createonly_fields,
        which act like readonly_fields except when creating a new object
    """

    createonly_fields = ()

    def get_readonly_fields(self, request, obj=None):                       # pragma: no cover
        readonly_fields = list(super().get_readonly_fields(request, obj))
        createonly_fields = list(getattr(self, 'createonly_fields', []))
        if obj:
            # editing an existing object
            readonly_fields.extend(createonly_fields)
        return readonly_fields


class HeeftAccountFilter(admin.SimpleListFilter):

    title = 'Heeft account'

    parameter_name = 'heeft_account'

    def lookups(self, request, model_admin):
        return (
            ('Ja', 'Sporter heeft account'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'Ja':        # pragma: no cover
            queryset = queryset.exclude(sporter__account=None)
        return queryset


class GeldigheidFilter(admin.SimpleListFilter):

    title = 'Geldigheid'

    parameter_name = 'is_nog_geldig'

    def lookups(self, request, model_admin):
        return (
            ('X', 'Diploma is verlopen'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'X':        # pragma: no cover
            now = timezone.now()
            queryset = queryset.filter(datum_einde__lt=now)
        return queryset


class OpleidingAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Opleiding klasse """

    # ordering = ('lid_nr',)

    # search_fields = ('unaccented_naam', 'lid_nr')

    # filter mogelijkheid
    # list_filter = ('geslacht', 'para_classificatie', 'is_actief_lid')

    # list_select_related = True

    pass


class OpleidingMomentAdmin(admin.ModelAdmin):
    """ Admin configuratie voor OpleidingMoment klasse """

    # search_fields = ('sporter__lid_nr', 'sporter__unaccented_naam')

    # list_select_related = ('sporter', 'boogtype')

    # autocomplete_fields = ('sporter',)
    pass


class OpleidingInschrijvingAdmin(admin.ModelAdmin):
    """ Admin configuratie voor OpleidingInschrijving klasse """

    readonly_fields = ('sporter', 'koper')


class OpleidingAfgemeldAdmin(admin.ModelAdmin):
    """ Admin configuratie voor OpleidingAfgemeld klasse """

    readonly_fields = ('sporter', 'koper')


class OpleidingDiplomaAdmin(CreateOnlyAdmin):
    """ Admin configuratie voor OpleidingDiploma klasse """

    search_fields = ('sporter__lid_nr', 'sporter__unaccented_naam')

    list_filter = ('toon_op_pas', HeeftAccountFilter, GeldigheidFilter, 'code')

    list_select_related = ('sporter',)

    createonly_fields = ('sporter',)

    autocomplete_fields = ('sporter',)

    # list_select_related = True


admin.site.register(Opleiding, OpleidingAdmin)
admin.site.register(OpleidingMoment, OpleidingMomentAdmin)
admin.site.register(OpleidingInschrijving, OpleidingInschrijvingAdmin)
admin.site.register(OpleidingAfgemeld, OpleidingAfgemeldAdmin)
admin.site.register(OpleidingDiploma, OpleidingDiplomaAdmin)

# end of file
