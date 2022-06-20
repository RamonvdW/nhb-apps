# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import Sporter, SporterVoorkeuren, SporterBoog, Secretaris, Speelsterkte


class SporterAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Sporter klasse """

    ordering = ('lid_nr',)

    search_fields = ('unaccented_naam', 'lid_nr')

    # filter mogelijkheid
    list_filter = ('geslacht', 'para_classificatie', 'is_actief_lid')

    list_select_related = True


class SporterBoogAdmin(admin.ModelAdmin):
    """ Admin configuratie voor SporterBoog klasse """

    search_fields = ('sporter__lid_nr', 'sporter__unaccented_naam')

    list_select_related = ('sporter', 'boogtype')

    autocomplete_fields = ('sporter',)


class SporterVoorkeurenAdmin(admin.ModelAdmin):
    """ Admin configuratie voor SporterVoorkeuren klasse """

    search_fields = ('sporter__lid_nr', 'sporter__unaccented_naam')

    list_select_related = True

    readonly_fields = ('sporter',)

    fieldsets = (
        ('Wie',
            {'fields': ('sporter',)
             }),
        ('Disciplines',
            {'fields': ('voorkeur_discipline_25m1pijl',
                        'voorkeur_discipline_outdoor',
                        'voorkeur_discipline_indoor',
                        'voorkeur_discipline_clout',
                        'voorkeur_discipline_veld',
                        'voorkeur_discipline_run',
                        'voorkeur_discipline_3d'),
             }),
        ('Wedstrijdgeslacht',
            {'fields': ('wedstrijd_geslacht_gekozen',
                        'wedstrijd_geslacht'),
             }),
        ('Overig',
            {'fields': ('voorkeur_eigen_blazoen',
                        'voorkeur_meedoen_competitie',
                        'opmerking_para_sporter')
             }),
    )


class SecretarisAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Secretaris klasse """

    search_fields = ('vereniging__ver_nr',
                     'vereniging__naam',)

    list_filter = ('vereniging',)

    list_select_related = ('vereniging', 'sporter')

    auto_complete = ('vereniging', 'sporter')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        if obj:
            self.obj = obj
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'sporter' and self.obj:
            kwargs['queryset'] = (Sporter
                                  .objects
                                  .filter(bij_vereniging=self.obj.vereniging)
                                  .order_by('unaccented_naam'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SpeelsterkteAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Speelsterkte klasse """

    search_fields = ('beschrijving', 'category', 'discipline', 'sporter__unaccented_naam')

    list_filter = ('discipline', 'beschrijving', 'category')

    readonly_fields = ('sporter',)

    list_select_related = True


admin.site.register(Sporter, SporterAdmin)
admin.site.register(SporterBoog, SporterBoogAdmin)
admin.site.register(SporterVoorkeuren, SporterVoorkeurenAdmin)
admin.site.register(Secretaris, SecretarisAdmin)
admin.site.register(Speelsterkte, SpeelsterkteAdmin)

# end of file
