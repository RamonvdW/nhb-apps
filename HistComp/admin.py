# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from HistComp.models import (HistCompetitie,
                             HistCompRegioIndiv, HistCompRegioTeam,
                             HistKampIndiv, HistKampTeam)


class HistCompetitieAdmin(admin.ModelAdmin):

    list_filter = ('comp_type', 'seizoen', 'is_team', 'beschrijving', 'is_openbaar')


class HistCompRegioIndivAdmin(admin.ModelAdmin):

    search_fields = ('sporter_lid_nr', 'sporter_naam')

    # filter mogelijkheid
    list_filter = ('histcompetitie__seizoen', 'histcompetitie__comp_type', 'boogtype')


class HistCompRegioTeamAdmin(admin.ModelAdmin):

    list_filter = ('histcompetitie__seizoen', 'histcompetitie__comp_type', 'team_klasse')


class HistKampIndivAdmin(admin.ModelAdmin):

    list_filter = ('histcompetitie__seizoen', 'histcompetitie__comp_type', 'boogtype')


class HistKampTeamAdmin(admin.ModelAdmin):

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        if obj:
            self.obj = obj
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name in ('lid_1', 'lid_2', 'lid_3', 'lid_4'):
            if self.obj:
                histcomp = self.obj.histcompetitie
            else:
                histcomp = None     # finds nothing until histcompetitie has been filled in

            kwargs['queryset'] = (HistCompRegioIndiv
                                  .objects
                                  .filter(histcompetitie=histcomp)
                                  .order_by('sporter_lid_nr'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(HistCompetitie, HistCompetitieAdmin)
admin.site.register(HistCompRegioIndiv, HistCompRegioIndivAdmin)
admin.site.register(HistCompRegioTeam, HistCompRegioTeamAdmin)
admin.site.register(HistKampIndiv, HistKampIndivAdmin)
admin.site.register(HistKampTeam, HistKampTeamAdmin)

# end of file
