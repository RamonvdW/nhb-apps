# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Wedstrijden.models import (Wedstrijd, WedstrijdSessie, WedstrijdKorting,
                                WedstrijdInschrijving, WedstrijdAfgemeld, Kwalificatiescore)


class WedstrijdAdmin(admin.ModelAdmin):                 # pragma: no cover
    """ Admin configuratie voor Wedstrijd """

    list_filter = ('status', 'extern_beheerd', 'is_ter_info', 'toon_op_kalender', 'organisatie', 'wa_status',
                   'discipline', 'aantal_scheids', 'organiserende_vereniging')

    readonly_fields = ('sessies', 'boogtypen', 'wedstrijdklassen')

    search_fields = ('titel',)

    ordering = ('-datum_begin',)        # nieuwste bovenaan

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    def get_queryset(self, request):
        """ deze functie is voor prestatieverbetering
            want helaas bestaat list_prefetch_related niet
        """
        # qs = super().get_queryset(request)
        return (Wedstrijd
                .objects
                .select_related('locatie',
                                'organiserende_vereniging')
                .prefetch_related('boogtypen',
                                  'sessies')
                .all())

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
        if db_field.name == 'locatie' and self.obj:
            ver = self.obj.organiserende_vereniging
            kwargs['queryset'] = ver.wedstrijdlocatie_set.all()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class WedstrijdSessieAdmin(admin.ModelAdmin):             # pragma: no cover
    """ Admin configuratie voor WedstrijdSessie """

    search_fields = ('pk',)

    list_filter = ('datum',)

    readonly_fields = ('wedstrijdklassen',)

    def get_queryset(self, request):
        """ deze functie is voor prestatieverbetering
            want helaas bestaat list_prefetch_related niet
        """
        # qs = super().get_queryset(request)
        return (WedstrijdSessie
                .objects
                .prefetch_related('wedstrijdklassen')
                .all())


class WedstrijdKortingAdmin(admin.ModelAdmin):

    list_filter = (
                   ('uitgegeven_door', admin.RelatedOnlyFieldListFilter),
                  )

    autocomplete_fields = ('voor_wedstrijden', 'voor_sporter', 'uitgegeven_door')


class InschrijvingBijVerenigingFilter(admin.SimpleListFilter):

    title = 'sporter vereniging'
    parameter_name = 'van_ver'

    def lookups(self, request, model_admin):
        org_vers = list()

        for inschrijving in (WedstrijdInschrijving
                             .objects
                             .select_related('sporterboog__sporter__bij_vereniging')
                             .order_by('sporterboog__sporter__bij_vereniging')
                             .distinct('sporterboog__sporter__bij_vereniging')):

            ver = inschrijving.sporterboog.sporter.bij_vereniging
            if ver:
                tup = (str(ver.pk), ver.ver_nr_en_naam())
                org_vers.append(tup)
        # for

        return org_vers

    def queryset(self, request, queryset):
        ver_pk = self.value()
        if ver_pk:
            queryset = queryset.filter(sporterboog__sporter__bij_vereniging__pk=ver_pk)
        return queryset


class WedstrijdInschrijvingAdmin(admin.ModelAdmin):

    readonly_fields = ('wanneer', 'wedstrijd', 'sporterboog', 'koper')

    list_filter = ('status', InschrijvingBijVerenigingFilter, 'wedstrijd')

    search_fields = ('sporterboog__sporter__lid_nr',)

    ordering = ('-wanneer',)        # nieuwste bovenaan

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.vereniging = None
        self.wedstrijd = None

    def get_queryset(self, request):
        """ deze functie is voor prestatieverbetering
            want helaas bestaat list_prefetch_related niet
        """
        return (WedstrijdInschrijving
                .objects
                .prefetch_related('sporterboog',
                                  'sporterboog__sporter',
                                  'sporterboog__sporter__bij_vereniging',
                                  'wedstrijd')
                .order_by('-wanneer'))

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        """ initialisatie van het admin formulier
            hier "vangen" we het database object waar we mee bezig gaan
        """
        if obj:
            assert isinstance(obj, WedstrijdInschrijving)
            if obj.wedstrijd:
                self.wedstrijd = obj.wedstrijd
                self.vereniging = obj.wedstrijd.organiserende_vereniging

        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        """ bepaal de relevante keuzemogelijkheden voor specifieke velden
        """
        if db_field.name == 'korting' and self.vereniging:
            # toon alleen de kortingen van deze vereniging
            kwargs['queryset'] = WedstrijdKorting.objects.filter(uitgegeven_door=self.vereniging)

        elif db_field.name == 'sessie' and self.wedstrijd:
            kwargs['queryset'] = WedstrijdSessie.objects.filter(wedstrijd=self.wedstrijd)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class KwalificatiescoreAdmin(admin.ModelAdmin):

    readonly_fields = ('inschrijving',)


class AfgemeldBijVerenigingFilter(admin.SimpleListFilter):

    title = 'sporter vereniging'
    parameter_name = 'van_ver'

    def lookups(self, request, model_admin):
        org_vers = list()

        for inschrijving in (WedstrijdAfgemeld
                             .objects
                             .select_related('sporterboog__sporter__bij_vereniging')
                             .order_by('sporterboog__sporter__bij_vereniging')
                             .distinct('sporterboog__sporter__bij_vereniging')):

            ver = inschrijving.sporterboog.sporter.bij_vereniging
            if ver:
                tup = (str(ver.pk), ver.ver_nr_en_naam())
                org_vers.append(tup)
        # for

        return org_vers

    def queryset(self, request, queryset):
        ver_pk = self.value()
        if ver_pk:
            queryset = queryset.filter(sporterboog__sporter__bij_vereniging__pk=ver_pk)
        return queryset


class WedstrijdAfgemeldAdmin(admin.ModelAdmin):

    readonly_fields = ('wanneer_inschrijving', 'wanneer_afgemeld', 'wedstrijd', 'sporterboog', 'koper')

    list_filter = (AfgemeldBijVerenigingFilter, 'wedstrijd')

    search_fields = ('sporterboog__sporter__lid_nr',)

    ordering = ('-wanneer_afgemeld',)       # nieuwste bovenaan

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.vereniging = None
        self.wedstrijd = None

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        """ initialisatie van het admin formulier
            hier "vangen" we het database object waar we mee bezig gaan
        """
        if obj:
            assert isinstance(obj, WedstrijdAfgemeld)
            if obj.wedstrijd:
                self.wedstrijd = obj.wedstrijd
                self.vereniging = obj.wedstrijd.organiserende_vereniging

        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        """ bepaal de relevante keuzemogelijkheden voor specifieke velden
        """
        if db_field.name == 'korting' and self.vereniging:
            # toon alleen de kortingen van deze vereniging
            kwargs['queryset'] = WedstrijdKorting.objects.filter(uitgegeven_door=self.vereniging)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Wedstrijd, WedstrijdAdmin)
admin.site.register(WedstrijdSessie, WedstrijdSessieAdmin)
admin.site.register(WedstrijdKorting, WedstrijdKortingAdmin)
admin.site.register(WedstrijdInschrijving, WedstrijdInschrijvingAdmin)
admin.site.register(WedstrijdAfgemeld, WedstrijdAfgemeldAdmin)
admin.site.register(Kwalificatiescore, KwalificatiescoreAdmin)

# FUTURE: langzaam admin scherm for Wedstrijd str(Locatie) een self.verenigingen.count()
#         nog niet op kunnen lossen met een get_queryset(). Even uitgezet.

# end of file
