# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from BasisTypen.definities import SCHEIDS_NIET
from Scheidsrechter.definities import SCHEIDS2LEVEL
from Scheidsrechter.models import (ScheidsBeschikbaarheid, WedstrijdDagScheidsrechters, MatchScheidsrechters,
                                   ScheidsMutatie)
from Sporter.models import Sporter


class WedstrijdDagScheidsrechtersAdmin(admin.ModelAdmin):

    fieldsets = (
        ('', {'fields': ('wedstrijd', 'dag_offset')}),
        ('Hoofdscheidsrechter', {'fields': ('gekozen_hoofd_sr',)}),
        ('Scheidsrechters', {'fields': ('gekozen_sr1', 'gekozen_sr2', 'gekozen_sr3', 'gekozen_sr4', 'gekozen_sr5',
                                        'gekozen_sr6', 'gekozen_sr7', 'gekozen_sr8', 'gekozen_sr9')}),
        ('Berichtgeving', {'fields': ('notified_srs',)})
    )

    readonly_fields = ('wedstrijd', 'dag_offset', 'notified_srs')

    list_filter = ('wedstrijd',)

    ordering = ('-wedstrijd__datum_begin', 'dag_offset')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    @staticmethod
    def label_voor_scheids_met_niveau(inst):
        return "%s %s" % (SCHEIDS2LEVEL[inst.scheids], inst.lid_nr_en_volledige_naam())     # pragma: no cover

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        """ initialisatie van het admin formulier
            hier "vangen" we het database object waar we mee bezig gaan
        """
        form = super().get_form(request, obj, **kwargs)

        if obj:
            self.obj = obj

        # toon de keuze opties voor de hoofdscheidsrechter met het opleidingsniveau, zoals SR4
        form.base_fields['gekozen_hoofd_sr'].label_from_instance = self.label_voor_scheids_met_niveau

        # alternatief label voor de wedstrijd (zonder de status)
        # form.base_fields['wedstrijd'].label_from_instance = lambda inst: "%s %s" % (inst.datum_begin, inst.titel)
        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        """ bepaal de relevante keuzemogelijkheden voor specifieke velden
        """
        if db_field.name == 'gekozen_hoofd_sr' or db_field.name.startswith('gekozen_sr'):
            # alleen scheidsrechters tonen
            kwargs['queryset'] = (Sporter
                                  .objects
                                  .exclude(scheids=SCHEIDS_NIET)
                                  .order_by('scheids',
                                            'lid_nr'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class MatchScheidsrechtersAdmin(admin.ModelAdmin):

    fieldsets = (
        ('', {'fields': ('match',)}),
        ('Hoofdscheidsrechter', {'fields': ('gekozen_hoofd_sr',)}),
        ('Scheidsrechters', {'fields': ('gekozen_sr1', 'gekozen_sr2')}),
        ('Berichtgeving', {'fields': ('notified_srs',)})
    )

    readonly_fields = ('match', 'notified_srs')

    ordering = ('-match__datum_wanneer', 'match__pk')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    @staticmethod
    def label_voor_scheids_met_niveau(inst):
        return "%s %s" % (SCHEIDS2LEVEL[inst.scheids], inst.lid_nr_en_volledige_naam())     # pragma: no cover

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        """ initialisatie van het admin formulier
            hier "vangen" we het database object waar we mee bezig gaan
        """
        form = super().get_form(request, obj, **kwargs)

        if obj:
            self.obj = obj

        # toon de keuze opties voor de hoofdscheidsrechter met het opleidingsniveau, zoals SR4
        form.base_fields['gekozen_hoofd_sr'].label_from_instance = self.label_voor_scheids_met_niveau

        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        """ bepaal de relevante keuzemogelijkheden voor specifieke velden
        """
        if db_field.name == 'gekozen_hoofd_sr' or db_field.name.startswith('gekozen_sr'):
            # alleen scheidsrechters tonen
            kwargs['queryset'] = (Sporter
                                  .objects
                                  .exclude(scheids=SCHEIDS_NIET)
                                  .order_by('scheids',
                                            'lid_nr'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ScheidsFilter(admin.SimpleListFilter):

    title = 'Scheidsrechter'

    parameter_name = 'Scheids'

    def lookups(self, request, model_admin):
        qset = Sporter.objects.exclude(scheids=SCHEIDS_NIET).order_by('scheids', 'lid_nr')
        return [(sporter.lid_nr, sporter.lid_nr_en_volledige_naam()) for sporter in qset]

    def queryset(self, request, qs):        # pragma: no cover
        if self.value():
            qs = qs.filter(scheids__lid_nr=self.value())
        return qs


class ScheidsBeschikbaarheidAdmin(admin.ModelAdmin):

    fieldsets = (
        ('', {'fields': ('scheids', 'wedstrijd', 'datum', 'opgaaf', 'opmerking', 'log')},),
    )

    readonly_fields = ('scheids', 'wedstrijd', 'datum')

    search_fields = ('scheids__voornaam', 'scheids__achternaam')

    list_filter = ('opgaaf', ScheidsFilter,)


admin.site.register(ScheidsBeschikbaarheid, ScheidsBeschikbaarheidAdmin)
admin.site.register(WedstrijdDagScheidsrechters, WedstrijdDagScheidsrechtersAdmin)
admin.site.register(MatchScheidsrechters, MatchScheidsrechtersAdmin)
admin.site.register(ScheidsMutatie)

# end of file
