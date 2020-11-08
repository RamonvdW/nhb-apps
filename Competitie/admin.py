# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin

from NhbStructuur.models import NhbCluster
from .models import (Competitie, DeelCompetitie, DeelcompetitieRonde,
                     CompetitieKlasse, RegioCompetitieSchutterBoog, KampioenschapSchutterBoog)


class DeelCompetitieAdmin(admin.ModelAdmin):
    list_select_related = ('competitie', 'nhb_regio', 'nhb_rayon')


class DeelcompetitieRondeAdmin(admin.ModelAdmin):
    list_filter = ('deelcompetitie__is_afgesloten', 'deelcompetitie__nhb_regio')

    list_select_related = ('deelcompetitie', 'deelcompetitie__nhb_regio')

    readonly_fields = ('deelcompetitie', 'cluster', 'plan')


class CompetitieKlasseAdmin(admin.ModelAdmin):
    list_select_related = ('competitie', 'indiv', 'team')


class RegioCompetitieSchutterBoogAdmin(admin.ModelAdmin):

    fieldsets = (
        ('Wie',
            {'fields': ('deelcompetitie',
                        'schutterboog',
                        'bij_vereniging')
             }),
        ('Klasse',
            {'fields': (('aanvangsgemiddelde', 'is_handmatig_ag'),
                        'klasse'),
             }),
        ('Inschrijving',
            {'fields': ('inschrijf_voorkeur_team',
                        'inschrijf_notitie',
                        'inschrijf_voorkeur_dagdeel'),
             }),
        ('Uitslag',
            {'fields': ('score1', 'score2', 'score3', 'score4', 'score5', 'score6', 'score7',
                        'aantal_scores', 'laagste_score_nr', 'totaal', 'gemiddelde')
             }),
        ('Alternatieve Uitslag',
            {'fields': ('alt_score1', 'alt_score2', 'alt_score3', 'alt_score4', 'alt_score5', 'alt_score6', 'alt_score7',
                        'alt_aantal_scores', 'alt_laagste_score_nr', 'alt_totaal', 'alt_gemiddelde')
             }),
    )

    readonly_fields = ('deelcompetitie',
                       'schutterboog',
                       'bij_vereniging', 'scores')

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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'klasse':
            kwargs['queryset'] = (CompetitieKlasse
                                  .objects
                                  .select_related('indiv', 'team')
                                  .all())

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class KampioenschapSchutterBoogAdmin(admin.ModelAdmin):

    fieldsets = (
        ('Wie',
            {'fields': ('deelcompetitie',
                        'schutterboog')
             }),
        ('Klasse',
            {'fields': ('klasse',),
             }),
        ('Details',
            {'fields': ('gemiddelde',
                        'kampioen_label')
             }),
        ('Status aanmelding',
            {'fields': ('deelname_bevestigd',
                        'is_afgemeld',
                        'volgorde'),
             }),
    )

    readonly_fields = ('deelcompetitie',
                       'schutterboog')

    search_fields = ('schutterboog__nhblid__voornaam',
                     'schutterboog__nhblid__achternaam',
                     'schutterboog__nhblid__nhb_nr')

    list_select_related = ('deelcompetitie',
                           'deelcompetitie__nhb_rayon',
                           'deelcompetitie__competitie',
                           'klasse',
                           'klasse__indiv',
                           'klasse__team',
                           'schutterboog',
                           'schutterboog__boogtype',
                           'schutterboog__nhblid')

    list_filter = ('deelcompetitie__competitie',
                   'deelcompetitie__nhb_rayon',
                   'schutterboog__boogtype')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'klasse':
            kwargs['queryset'] = (CompetitieKlasse
                                  .objects
                                  .select_related('indiv', 'team')
                                  .all())

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Competitie)
admin.site.register(DeelCompetitie, DeelCompetitieAdmin)
admin.site.register(CompetitieKlasse, CompetitieKlasseAdmin)
admin.site.register(DeelcompetitieRonde, DeelcompetitieRondeAdmin)
admin.site.register(RegioCompetitieSchutterBoog, RegioCompetitieSchutterBoogAdmin)
admin.site.register(KampioenschapSchutterBoog, KampioenschapSchutterBoogAdmin)

# end of file
