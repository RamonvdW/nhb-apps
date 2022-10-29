# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Sporter.models import Sporter
from Vereniging.models import Secretaris


class SecretarisAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Secretaris klasse """

    search_fields = ('vereniging__ver_nr',
                     'vereniging__naam',)

    list_filter = ('vereniging',)

    list_select_related = ('vereniging',)

    auto_complete = ('vereniging', 'sporters')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        if obj:
            self.obj = obj
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'sporters' and self.obj:
            kwargs['queryset'] = (Sporter
                                  .objects
                                  .filter(bij_vereniging=self.obj.vereniging)
                                  .order_by('unaccented_naam'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Secretaris, SecretarisAdmin)

# end of file
