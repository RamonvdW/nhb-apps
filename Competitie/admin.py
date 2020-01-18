# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin

from .models import Competitie, DeelCompetitie, CompetitieWedstrijdKlasse


class CompetitieWedstrijdKlasseAdmin(admin.ModelAdmin):
    # filter mogelijkheid
    list_filter = ('is_afgesloten',)

class CompetitieAdmin(admin.ModelAdmin):

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no coverage
        if db_field.name == 'klassen_indiv':
            kwargs['queryset'] = CompetitieWedstrijdKlasse.objects.filter(wedstrijdklasse__is_voor_teams=False)
        elif db_field.name == 'klassen_team':
            kwargs['queryset'] = CompetitieWedstrijdKlasse.objects.filter(wedstrijdklasse__is_voor_teams=True)
        return super(CompetitieAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)


admin.site.register(Competitie, CompetitieAdmin)
admin.site.register(DeelCompetitie)
admin.site.register(CompetitieWedstrijdKlasse, CompetitieWedstrijdKlasseAdmin)

# end of file
