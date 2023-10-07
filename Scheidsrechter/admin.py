# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from BasisTypen.definities import SCHEIDS_NIET
from Scheidsrechter.definities import SCHEIDS2LEVEL
from Scheidsrechter.models import ScheidsBeschikbaarheid, WedstrijdDagScheids
from Sporter.models import Sporter
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD
from Wedstrijden.models import Wedstrijd


class WedstrijdDagScheidsAdmin(admin.ModelAdmin):

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        if obj:
            self.obj = obj

        form = super().get_form(request, obj, **kwargs)
        form.base_fields['gekozen'].label_from_instance = lambda inst: "%s %s" % (SCHEIDS2LEVEL[inst.scheids],
                                                                                  inst.lid_nr_en_volledige_naam())

        form.base_fields['wedstrijd'].label_from_instance = lambda inst: "%s %s" % (inst.datum_begin,
                                                                                    inst.titel)
        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'wedstrijd' and self.obj:
            kwargs['queryset'] = (Wedstrijd
                                  .objects
                                  .filter(status=WEDSTRIJD_STATUS_GEACCEPTEERD)
                                  .order_by('datum_begin',
                                            'pk'))

        elif db_field.name == 'gekozen':
            kwargs['queryset'] = (Sporter
                                  .objects
                                  .exclude(scheids=SCHEIDS_NIET)
                                  .order_by('scheids',
                                            'lid_nr'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ScheidsBeschikbaarheidAdmin(admin.ModelAdmin):

    fieldsets = (
        ('', {'fields': ('scheids', 'wedstrijd' ,'datum', 'opgaaf', 'log')},),
    )
    readonly_fields = ('scheids', 'wedstrijd', 'datum')


admin.site.register(ScheidsBeschikbaarheid, ScheidsBeschikbaarheidAdmin)
admin.site.register(WedstrijdDagScheids, WedstrijdDagScheidsAdmin)

# end of file
