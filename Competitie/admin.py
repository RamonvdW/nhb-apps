# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin

from .models import Competitie, DeelCompetitie, CompetitieKlasse, RegioCompetitieSchutterBoog


class DeelCompetitieAdmin(admin.ModelAdmin):
    list_select_related = ('competitie', 'nhb_regio', 'nhb_rayon')


class CompetitieKlasseAdmin(admin.ModelAdmin):
    list_select_related = ('competitie', 'indiv', 'team')


class RegioCompetitieSchutterBoogAdmin(admin.ModelAdmin):
    list_select_related = ('deelcompetitie', 'deelcompetitie__nhb_regio', 'deelcompetitie__nhb_rayon',
                           'deelcompetitie__competitie',
                           'klasse', 'klasse__indiv', 'klasse__team',
                           'schutterboog', 'schutterboog__nhblid')


admin.site.register(Competitie)
admin.site.register(DeelCompetitie, DeelCompetitieAdmin)
admin.site.register(CompetitieKlasse, CompetitieKlasseAdmin)
admin.site.register(RegioCompetitieSchutterBoog, RegioCompetitieSchutterBoogAdmin)

# end of file
