# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from NhbStructuur.models import Rayon, Regio, Cluster


class NhbRayonAdmin(admin.ModelAdmin):
    """ Admin configuratie voor NhbRayon klasse """
    ordering = ('rayon_nr',)
    list_select_related = True

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class NhbRegioAdmin(admin.ModelAdmin):
    """ Admin configuratie voor NhbRegio klasse """
    ordering = ('regio_nr',)
    list_select_related = True

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class NhbClusterAdmin(admin.ModelAdmin):
    list_select_related = ('regio',)

    list_filter = ('regio',)

    ordering = ('regio', 'gebruik', 'letter')


admin.site.register(Cluster, NhbClusterAdmin)

# NhbRayon en NhbRegio zijn hard-coded, dus geen admin interface
# hard-coded data: zie NhbStructuur/migrations/m00??_nhbstructuur_20??
admin.site.register(Rayon, NhbRayonAdmin)
admin.site.register(Regio, NhbRegioAdmin)

# end of file
