# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from BasisTypen.models import IndivWedstrijdklasse, TeamWedstrijdklasse
from .models import WedstrijdLocatie, CompetitieWedstrijd, CompetitieWedstrijdenPlan, CompetitieWedstrijdUitslag


class WedstrijdLocatieAdmin(admin.ModelAdmin):      # pragma: no cover
    """ Admin configuratie voor WedstrijdLocatie """

    list_filter = ('baan_type',
                   'discipline_outdoor', 'discipline_indoor', 'discipline_veld',
                   'discipline_25m1pijl',
                   'zichtbaar', 'adres_uit_crm')

    search_fields = ('adres', 'verenigingen__ver_nr')

    def get_queryset(self, request):
        """ deze functie is voor prestatieverbetering
            want helaas bestaat list_prefetch_related niet
        """
        # qs = super().get_queryset(request)
        return (WedstrijdLocatie
                .objects
                .prefetch_related('verenigingen')
                .all())


class CompetitieWedstrijdAdmin(admin.ModelAdmin):             # pragma: no cover
    """ Admin configuratie voor Wedstrijd """

    readonly_fields = ('hoort_bij_plan',)

    search_fields = ('beschrijving', 'vereniging__ver_nr', 'vereniging__naam')

    filter_horizontal = ('indiv_klassen', 'team_klassen')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.ver = None

    def get_form(self, request, obj=None, **kwargs):
        if obj:                     # pragma: no cover
            self.ver = obj.vereniging

        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'locatie' and self.ver:
            kwargs['queryset'] = self.ver.wedstrijdlocatie_set.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        print('db_field.name=%s' % db_field.name)
        if db_field.name == 'indiv_klassen':
            kwargs['queryset'] = (IndivWedstrijdklasse
                                  .objects
                                  .select_related('boogtype')
                                  .all())
        elif db_field.name == 'team_klassen':
            kwargs['queryset'] = (TeamWedstrijdklasse
                                  .objects
                                  .select_related('team_type')
                                  .all())

        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_queryset(self, request):
        """ deze functie is voor prestatieverbetering
            want helaas bestaat list_prefetch_related niet
        """
        # qs = super().get_queryset(request)
        return (CompetitieWedstrijd
                .objects
                .select_related('locatie', 'vereniging')
                .prefetch_related('indiv_klassen', 'team_klassen')
                .all())

    @staticmethod
    def hoort_bij_plan(obj):     # pragma: no cover
        plans = obj.competitiewedstrijdenplan_set.all()
        if plans.count() > 0:
            return plans[0]
        return "geen??"


class CompetitieWedstrijdenPlanAdmin(admin.ModelAdmin):      # pragma: no cover
    """ Admin configuratie voor WedstrijdenPlan"""

    search_fields = ('pk',)

    autocomplete_fields = ('wedstrijden',)


class CompetitieWedstrijdUitslagAdmin(admin.ModelAdmin):      # pragma: no cover
    """ Admin configuratie voor WedstrijdenUitslag"""

    readonly_fields = ('scores', 'hoort_bij_wedstrijd')

    list_filter = ('max_score', 'afstand_meter', 'is_bevroren')

    @staticmethod
    def hoort_bij_wedstrijd(obj):     # pragma: no cover
        try:
            comp = CompetitieWedstrijd.objects.get(uitslag=obj.pk)
        except CompetitieWedstrijd.DoesNotExist:
            comp = "geen??"
        return comp


admin.site.register(WedstrijdLocatie, WedstrijdLocatieAdmin)
admin.site.register(CompetitieWedstrijd, CompetitieWedstrijdAdmin)
admin.site.register(CompetitieWedstrijdenPlan, CompetitieWedstrijdenPlanAdmin)
admin.site.register(CompetitieWedstrijdUitslag, CompetitieWedstrijdUitslagAdmin)

# FUTURE: Wedstrijd admin scherm word langzaam als str(WedstrijdLocatie) een self.verenigingen.count() doet
#         nog niet op kunnen lossen met een get_queryset(). Even uitgezet.

# end of file
