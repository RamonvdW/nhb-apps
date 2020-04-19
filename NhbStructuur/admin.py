# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import NhbRayon, NhbRegio, NhbLid, NhbVereniging


class NhbLidAdmin(admin.ModelAdmin):
    """ Admin configuratie voor NhbLid klasse """
    ordering = ('nhb_nr',)
    search_fields = ('voornaam', 'achternaam', 'nhb_nr')

    # filter mogelijkheid
    list_filter = ('geslacht', 'para_classificatie', 'is_actief_lid')


class NhbVerenigingAdmin(admin.ModelAdmin):
    """ Admin configuratie voor NhbVereniging klasse """
    ordering = ('nhb_nr',)
    search_fields = ('naam', 'nhb_nr')


class NhbRayonAdmin(admin.ModelAdmin):
    """ Admin configuratie voor NhbRayon klasse """
    ordering = ('rayon_nr',)

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class NhbRegioAdmin(admin.ModelAdmin):
    """ Admin configuratie voor NhbRegio klasse """
    ordering = ('regio_nr',)

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(NhbLid, NhbLidAdmin)
admin.site.register(NhbVereniging, NhbVerenigingAdmin)

# NhbRayon en NhbRegio zijn hard-coded, dus geen admin interface
# hard-coded data: zie NhbStructuur/migrations/m00??_nhbstructuur_20??
admin.site.register(NhbRayon, NhbRayonAdmin)
admin.site.register(NhbRegio, NhbRegioAdmin)

# end of file
