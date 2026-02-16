# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from HistComp.models import (HistCompSeizoen,
                             HistCompRegioIndiv, HistCompRegioTeam,
                             HistKampIndivRK, HistKampIndivBK, HistKampTeam)


class HistCompSeizoenAdmin(admin.ModelAdmin):

    list_filter = ('comp_type', 'seizoen', 'is_openbaar')


class HistCompRegioIndivAdmin(admin.ModelAdmin):

    search_fields = ('sporter_lid_nr', 'sporter_naam')

    # filter mogelijkheid
    list_filter = ('seizoen__seizoen', 'seizoen__comp_type', 'boogtype', 'regio_nr', 'indiv_klasse')


class HistCompRegioTeamAdmin(admin.ModelAdmin):

    list_filter = ('seizoen__seizoen', 'seizoen__comp_type', 'team_type', 'regio_nr', 'team_klasse')


class HistKampIndivRKAdmin(admin.ModelAdmin):

    list_filter = ('seizoen__seizoen', 'seizoen__comp_type', 'boogtype', 'rayon_nr', 'indiv_klasse')

    search_fields = ('sporter_lid_nr',)

    ordering = ['rank_rk', 'boogtype', 'indiv_klasse']


class HistKampIndivBKAdmin(admin.ModelAdmin):

    list_filter = ('seizoen__seizoen', 'seizoen__comp_type', 'boogtype')

    search_fields = ('sporter_lid_nr',)

    ordering = ['-seizoen', 'rank_bk', 'boogtype', 'bk_indiv_klasse']


class HistKampTeamAdmin(admin.ModelAdmin):

    list_filter = ('seizoen__seizoen', 'seizoen__comp_type', 'rk_of_bk', 'team_type', 'rayon_nr', 'teams_klasse')

    autocomplete_fields = ('lid_1', 'lid_2', 'lid_3', 'lid_4')

    ordering = ['-seizoen', 'rank', 'team_type', 'teams_klasse']

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
        if db_field.name in ('lid_1', 'lid_2', 'lid_3', 'lid_4'):
            if self.obj:
                hist_seizoen = self.obj.seizoen
            else:
                hist_seizoen = None     # finds nothing until hist_seizoen has been filled in

            kwargs['queryset'] = (HistKampIndivRK
                                  .objects
                                  .filter(seizoen=hist_seizoen)
                                  .order_by('sporter_lid_nr'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(HistCompSeizoen, HistCompSeizoenAdmin)
admin.site.register(HistCompRegioIndiv, HistCompRegioIndivAdmin)
admin.site.register(HistCompRegioTeam, HistCompRegioTeamAdmin)
admin.site.register(HistKampIndivRK, HistKampIndivRKAdmin)
admin.site.register(HistKampIndivBK, HistKampIndivBKAdmin)
admin.site.register(HistKampTeam, HistKampTeamAdmin)

# end of file
