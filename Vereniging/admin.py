# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Geo.models import Cluster
from Sporter.models import Sporter
from Vereniging.models import Vereniging, Secretaris


class SecretarisAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Secretaris """

    search_fields = ('vereniging__ver_nr',
                     'vereniging__naam',)

    list_filter = ('vereniging',)

    list_select_related = ('vereniging',)

    filter_horizontal = ('sporters',)

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        """ initialisatie van het admin formulier
            hier "vangen" we het database object waar we mee bezig gaan
        """
        if obj:
            self.obj = obj
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        """ bepaal de relevante keuzemogelijkheden voor specifieke velden
        """
        if db_field.name == 'sporters' and self.obj:
            kwargs['queryset'] = (Sporter
                                  .objects
                                  .filter(bij_vereniging=self.obj.vereniging)
                                  .order_by('unaccented_naam'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class VerenigingAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Vereniging """

    ordering = ('ver_nr',)
    search_fields = ('naam', 'ver_nr')

    # filter mogelijkheid
    list_filter = ('regio__rayon_nr', 'geen_wedstrijden', 'regio',)

    list_select_related = True

    filter_horizontal = ('clusters',)

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self._ver_regio = None

    def get_object(self, request, object_id, from_field=None):          # pragma: no cover
        obj = super().get_object(request, object_id, from_field)
        if obj:
            self._ver_regio = obj.regio
        return obj

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'clusters':
            regio_clusters = (Cluster
                              .objects
                              .select_related('regio')
                              .filter(regio=self._ver_regio)
                              .order_by('letter'))
            kwargs['queryset'] = regio_clusters
        return super().formfield_for_manytomany(db_field, request, **kwargs)


admin.site.register(Vereniging, VerenigingAdmin)
admin.site.register(Secretaris, SecretarisAdmin)

# end of file
