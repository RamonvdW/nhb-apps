# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin

from .models import (Competitie, DeelCompetitie, DeelcompetitieRonde,
                     CompetitieKlasse, RegioCompetitieSchutterBoog)


class DeelCompetitieAdmin(admin.ModelAdmin):
    list_select_related = ('competitie', 'nhb_regio', 'nhb_rayon')


class DeelcompetitieRondeAdmin(admin.ModelAdmin):
    list_filter = ('deelcompetitie__is_afgesloten', 'deelcompetitie__nhb_regio')

    list_select_related = ('deelcompetitie', 'deelcompetitie__nhb_regio', 'cluster', 'cluster__regio')


class CompetitieKlasseAdmin(admin.ModelAdmin):
    list_select_related = ('competitie', 'indiv', 'team')


class RegioCompetitieSchutterBoogAdmin(admin.ModelAdmin):

    readonly_fields = ('deelcompetitie',
                       'schutterboog',
                       'bij_vereniging')

    search_fields = ('schutterboog__nhblid__voornaam',
                     'schutterboog__nhblid__achternaam',
                     'schutterboog__nhblid__nhb_nr')

    #list_filter = ('deelcompetitie',)      # kost veel database accesses (komt door __str__)

    list_select_related = ('deelcompetitie',
                           'deelcompetitie__nhb_regio',
                           'deelcompetitie__nhb_rayon',
                           'deelcompetitie__competitie',
                           'klasse',
                           'klasse__indiv',
                           'klasse__team',
                           'schutterboog',
                           'schutterboog__nhblid')


admin.site.register(Competitie)
admin.site.register(DeelCompetitie, DeelCompetitieAdmin)
admin.site.register(CompetitieKlasse, CompetitieKlasseAdmin)
admin.site.register(DeelcompetitieRonde, DeelcompetitieRondeAdmin)
admin.site.register(RegioCompetitieSchutterBoog, RegioCompetitieSchutterBoogAdmin)

# end of file
