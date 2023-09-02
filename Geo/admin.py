# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Geo.models import Rayon, Regio, Cluster


class RayonAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Rayon klasse """
    ordering = ('rayon_nr',)
    list_select_related = True

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class RegioAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Regio klasse """
    ordering = ('regio_nr',)
    list_select_related = True

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ClusterAdmin(admin.ModelAdmin):
    list_select_related = ('regio',)

    list_filter = ('regio',)

    ordering = ('regio', 'gebruik', 'letter')


# Rayon en Regio zijn hard-coded, dus geen admin interface
# hard-coded data: zie Locatie/migrations/m00??_squashed.py
admin.site.register(Rayon, RayonAdmin)
admin.site.register(Regio, RegioAdmin)
admin.site.register(Cluster, ClusterAdmin)

# end of file
