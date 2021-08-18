# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import NhbRayon, NhbRegio, NhbCluster, NhbLid, NhbVereniging, Speelsterkte


class NhbLidAdmin(admin.ModelAdmin):
    """ Admin configuratie voor NhbLid klasse """
    ordering = ('nhb_nr',)
    search_fields = ('unaccented_naam', 'voornaam', 'achternaam', 'nhb_nr')

    # filter mogelijkheid
    list_filter = ('geslacht', 'para_classificatie', 'is_actief_lid')

    list_select_related = True


class NhbVerenigingAdmin(admin.ModelAdmin):
    """ Admin configuratie voor NhbVereniging klasse """
    ordering = ('ver_nr',)
    search_fields = ('naam', 'ver_nr')

    # filter mogelijkheid
    list_filter = ('regio',)

    list_select_related = True

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self._nhbver_regio = None

    def get_object(self, request, object_id, from_field=None):          # pragma: no cover
        obj = super().get_object(request, object_id, from_field)
        if obj:
            self._nhbver_regio = obj.regio
        return obj

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'clusters':
            regio_clusters = (NhbCluster
                              .objects
                              .select_related('regio')
                              .filter(regio=self._nhbver_regio)
                              .order_by('letter'))
            kwargs['queryset'] = regio_clusters
        return super().formfield_for_manytomany(db_field, request, **kwargs)


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


class SpeelsterkteAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Speelsterkte klasse """

    search_fields = ('beschrijving', 'category', 'discipline', 'lid__unaccented_naam')

    list_filter = ('discipline', 'beschrijving', 'category')

    readonly_fields = ('lid',)

    list_select_related = True


admin.site.register(NhbLid, NhbLidAdmin)
admin.site.register(NhbVereniging, NhbVerenigingAdmin)
admin.site.register(NhbCluster, NhbClusterAdmin)
admin.site.register(Speelsterkte, SpeelsterkteAdmin)

# NhbRayon en NhbRegio zijn hard-coded, dus geen admin interface
# hard-coded data: zie NhbStructuur/migrations/m00??_nhbstructuur_20??
admin.site.register(NhbRayon, NhbRayonAdmin)
admin.site.register(NhbRegio, NhbRegioAdmin)

# end of file
