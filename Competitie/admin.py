# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Wedstrijden.models import CompetitieWedstrijd
from .models import (Competitie, DeelCompetitie, DeelcompetitieRonde,
                     CompetitieKlasse, DeelcompetitieKlasseLimiet,
                     RegioCompetitieSchutterBoog, KampioenschapSchutterBoog,
                     RegiocompetitieTeam, RegiocompetitieTeamPoule, RegiocompetitieRondeTeam,
                     KampioenschapMutatie)


class DeelCompetitieAdmin(admin.ModelAdmin):
    list_filter = ('nhb_regio',)

    list_select_related = ('competitie', 'nhb_regio', 'nhb_rayon')


class DeelcompetitieRondeAdmin(admin.ModelAdmin):
    list_filter = ('deelcompetitie__is_afgesloten', 'deelcompetitie__nhb_regio')

    list_select_related = ('deelcompetitie', 'deelcompetitie__nhb_regio')

    readonly_fields = ('deelcompetitie', 'cluster', 'plan')


class CompetitieKlasseAdmin(admin.ModelAdmin):

    list_filter = ('competitie',)

    list_select_related = ('competitie', 'indiv', 'team')

    ordering = ('team__volgorde', 'indiv__volgorde')


class RegioCompetitieSchutterBoogAdmin(admin.ModelAdmin):

    fieldsets = (
        ('Wie',
            {'fields': ('deelcompetitie',
                        'schutterboog',
                        'bij_vereniging')
             }),
        ('Individueel',
            {'fields': (('ag_voor_indiv',),
                        'klasse'),
             }),
        ('Team',
            {'fields': ('inschrijf_voorkeur_team',
                        'ag_voor_team', 'ag_voor_team_mag_aangepast_worden'),
             }),
        ('Inschrijving',
            {'fields': ('inschrijf_gekozen_wedstrijden',
                        'inschrijf_voorkeur_dagdeel',
                        'inschrijf_notitie'),
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

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    def get_form(self, request, obj=None, **kwargs):
        if obj:                 # pragma: no branch
            self.obj = obj      # pragma: no cover
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'klasse':
            kwargs['queryset'] = (CompetitieKlasse
                                  .objects
                                  .select_related('indiv', 'team')
                                  .all())

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'inschrijf_gekozen_wedstrijden' and self.obj:
            pks = list()
            for ronde in (DeelcompetitieRonde
                          .objects
                          .select_related('plan')
                          .filter(deelcompetitie=self.obj.deelcompetitie)):
                if not ronde.is_voor_import_oude_programma():
                    # sta alle wedstrijden in de regio toe, dus alle clusters
                    pks.extend(ronde.plan.wedstrijden.values_list('pk', flat=True))
            # for
            kwargs['queryset'] = (CompetitieWedstrijd
                                  .objects
                                  .filter(pk__in=pks)
                                  .order_by('datum_wanneer',
                                            'tijd_begin_wedstrijd'))
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class RegiocompetitieTeamAdmin(admin.ModelAdmin):
    filter_horizontal = ('gekoppelde_schutters', )

    list_filter = ('deelcompetitie__competitie',
                   'vereniging__regio',)

    list_select_related = ('deelcompetitie',
                           'deelcompetitie__nhb_regio',
                           'deelcompetitie__nhb_rayon',
                           'deelcompetitie__competitie',
                           'vereniging',
                           'klasse',
                           'klasse__indiv',
                           'klasse__team')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    def get_form(self, request, obj=None, **kwargs):
        if obj:                 # pragma: no branch
            self.obj = obj      # pragma: no cover
        return super().get_form(request, obj, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'gekoppelde_schutters' and self.obj:
            # alleen schutters van de juiste vereniging laten kiezen
            kwargs['queryset'] = (RegioCompetitieSchutterBoog
                                  .objects
                                  .filter(bij_vereniging=self.obj.vereniging))
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class KampioenschapSchutterBoogAdmin(admin.ModelAdmin):

    fieldsets = (
        ('Wie',
            {'fields': ('deelcompetitie',
                        'schutterboog',
                        'bij_vereniging')
             }),
        ('Klasse',
            {'fields': ('klasse',),
             }),
        ('Details',
            {'fields': ('gemiddelde',
                        'kampioen_label')
             }),
        ('Status aanmelding',
            {'fields': ('deelname',
                        'volgorde',
                        'rank'),
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


class KampioenschapMutatieAdmin(admin.ModelAdmin):

    readonly_fields = ('mutatie', 'when', 'deelnemer', 'door')

    list_select_related = ('deelnemer__deelcompetitie',
                           'deelnemer__klasse',
                           'deelnemer__schutterboog__nhblid')

    list_filter = ('is_verwerkt', 'mutatie')


admin.site.register(Competitie)
admin.site.register(DeelCompetitie, DeelCompetitieAdmin)
admin.site.register(CompetitieKlasse, CompetitieKlasseAdmin)
admin.site.register(DeelcompetitieRonde, DeelcompetitieRondeAdmin)
admin.site.register(RegioCompetitieSchutterBoog, RegioCompetitieSchutterBoogAdmin)
admin.site.register(KampioenschapSchutterBoog, KampioenschapSchutterBoogAdmin)
admin.site.register(DeelcompetitieKlasseLimiet)
admin.site.register(KampioenschapMutatie, KampioenschapMutatieAdmin)
admin.site.register(RegiocompetitieTeam, RegiocompetitieTeamAdmin)
admin.site.register(RegiocompetitieTeamPoule)
admin.site.register(RegiocompetitieRondeTeam)

# end of file
