# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from Wedstrijden.models import CompetitieWedstrijd
from .models import (Competitie, DeelCompetitie, DeelcompetitieRonde, LAAG_REGIO,
                     CompetitieKlasse, DeelcompetitieKlasseLimiet,
                     RegioCompetitieSchutterBoog, KampioenschapSchutterBoog, KampioenschapTeam,
                     RegiocompetitieTeam, RegiocompetitieTeamPoule, RegiocompetitieRondeTeam,
                     CompetitieMutatie)


class CreateOnlyAdmin(admin.ModelAdmin):
    """
        Extend the ModelAdmin with createonly_fields,
        which act like readonly_fields except when creating a new object
    """

    createonly_fields = ()

    def get_readonly_fields(self, request, obj=None):                       # pragma: no cover
        readonly_fields = list(super().get_readonly_fields(request, obj))
        createonly_fields = list(getattr(self, 'createonly_fields', []))
        if obj:
            # editing an existing object
            readonly_fields.extend(createonly_fields)
        return readonly_fields


class DeelCompetitieAdmin(CreateOnlyAdmin):

    list_filter = ('competitie', 'nhb_regio')

    list_select_related = ('competitie', 'nhb_regio', 'nhb_rayon')


class DeelcompetitieRondeAdmin(CreateOnlyAdmin):

    list_filter = ('deelcompetitie__is_afgesloten', 'deelcompetitie__nhb_regio')

    list_select_related = ('deelcompetitie', 'deelcompetitie__nhb_regio')

    readonly_fields = ('deelcompetitie', 'cluster', 'plan')


class CompetitieKlasseAdmin(CreateOnlyAdmin):

    list_filter = ('competitie', 'team__team_type')

    list_select_related = ('competitie', 'indiv', 'team')

    ordering = ('team__volgorde', 'indiv__volgorde')


class RegioCompetitieSchutterBoogAdmin(CreateOnlyAdmin):

    fieldsets = (
        ('Wie',
            {'fields': ('deelcompetitie',
                        'bij_vereniging',
                        'sporterboog')
             }),
        ('Individueel',
            {'fields': (('ag_voor_indiv',),
                        'klasse'),
             }),
        ('Team',
            {'fields': ('inschrijf_voorkeur_team',
                        'ag_voor_team',
                        'ag_voor_team_mag_aangepast_worden',
                        'gemiddelde_begin_team_ronde'),
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
    )

    createonly_fields = ('deelcompetitie',
                         'sporterboog',
                         'bij_vereniging')

    autocomplete_fields = ('bij_vereniging',)

    readonly_fields = ('scores', )

    search_fields = ('sporterboog__sporter__unaccented_naam',
                     'sporterboog__sporter__lid_nr')

    list_filter = ('deelcompetitie__competitie',
                   'deelcompetitie__nhb_regio',)

    list_select_related = ('deelcompetitie',
                           'deelcompetitie__nhb_regio',
                           'deelcompetitie__nhb_rayon',
                           'deelcompetitie__competitie',
                           'klasse',
                           'klasse__indiv',
                           'klasse__team',
                           'sporterboog',
                           'sporterboog__sporter',
                           'sporterboog__boogtype')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        if obj:
            self.obj = obj
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'klasse':
            kwargs['queryset'] = (CompetitieKlasse
                                  .objects
                                  .select_related('indiv', 'team')
                                  .all())
        elif db_field.name == 'deelcompetitie':
            kwargs['queryset'] = (DeelCompetitie
                                  .objects
                                  .select_related('competitie',
                                                  'nhb_regio')
                                  .filter(laag=LAAG_REGIO)
                                  .order_by('competitie__afstand',
                                            'nhb_regio__regio_nr'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'inschrijf_gekozen_wedstrijden' and self.obj:
            pks = list()
            for ronde in (DeelcompetitieRonde
                          .objects
                          .select_related('plan')
                          .filter(deelcompetitie=self.obj.deelcompetitie)):
                # sta alle wedstrijden in de regio toe, dus alle clusters
                pks.extend(ronde.plan.wedstrijden.values_list('pk', flat=True))
            # for
            kwargs['queryset'] = (CompetitieWedstrijd
                                  .objects
                                  .filter(pk__in=pks)
                                  .order_by('datum_wanneer',
                                            'tijd_begin_wedstrijd'))
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class RegiocompetitieTeamAdmin(CreateOnlyAdmin):

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

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        if obj:
            self.obj = obj
        return super().get_form(request, obj, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'gekoppelde_schutters' and self.obj:
            # alleen schutters van de juiste vereniging laten kiezen
            kwargs['queryset'] = (RegioCompetitieSchutterBoog
                                  .objects
                                  .filter(deelcompetitie=self.obj.deelcompetitie,
                                          bij_vereniging=self.obj.vereniging,
                                          inschrijf_voorkeur_team=True))
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class GebruikteKlassenFilter(admin.SimpleListFilter):

    title = "Team Wedstrijdklasse"

    parameter_name = 'klasse'

    default_value = None

    def lookups(self, request, model_admin):
        """ Return list of tuples for the sidebar """
        return [
            ('leeg', 'Geen klasse'),
            ('regio', 'Regio klasse'),
            ('rk_bk', 'RK/BK klasse')
        ]

    def queryset(self, request, queryset):      # pragma: no cover
        selection = self.value()
        if selection == 'leeg':
            queryset = queryset.filter(klasse__team=None)
        elif selection == 'regio':
            queryset = queryset.filter(klasse__is_voor_teams_rk_bk=False)
        elif selection == 'rk_bk':
            queryset = queryset.filter(klasse__is_voor_teams_rk_bk=True)
        return queryset


class KampioenschapTeamAdmin(CreateOnlyAdmin):

    filter_horizontal = ('tijdelijke_schutters', 'gekoppelde_schutters', 'feitelijke_schutters')

    list_filter = ('deelcompetitie__competitie',
                   'vereniging__regio__rayon',
                   GebruikteKlassenFilter)

    list_select_related = ('deelcompetitie',
                           'deelcompetitie__nhb_rayon',
                           'deelcompetitie__competitie',
                           'vereniging',
                           'klasse',
                           'klasse__indiv',
                           'klasse__team')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None
        self.boog_pks = list()

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        if obj:
            self.obj = obj
            # bepaal welke bogen gebruik mogen worden voor dit team type
            self.boog_pks = list(obj.team_type.boog_typen.values_list('pk', flat=True))

        return super().get_form(request, obj, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover

        if db_field.name == 'tijdelijke_schutters' and self.obj:
            # alleen schutters van de juiste vereniging en boogtype laten kiezen
            kwargs['queryset'] = (RegioCompetitieSchutterBoog
                                  .objects
                                  .filter(bij_vereniging=self.obj.vereniging,
                                          sporterboog__boogtype__pk__in=self.boog_pks))

        elif db_field.name in ('gekoppelde_schutters', 'feitelijke_schutters') and self.obj:
            kwargs['queryset'] = (KampioenschapSchutterBoog
                                  .objects
                                  .filter(bij_vereniging=self.obj.vereniging,
                                          sporterboog__boogtype__pk__in=self.boog_pks))

        return super().formfield_for_manytomany(db_field, request, **kwargs)


class KampioenschapSchutterBoogAdmin(CreateOnlyAdmin):

    fieldsets = (
        ('Wie',
            {'fields': ('deelcompetitie',
                        'sporterboog',
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
                       'sporterboog')

    search_fields = ('sporterboog__sporter__unaccented_name',
                     'sporterboog__sporter__lid_nr')

    list_select_related = ('deelcompetitie',
                           'deelcompetitie__nhb_rayon',
                           'deelcompetitie__competitie',
                           'klasse',
                           'klasse__indiv',
                           'klasse__team',
                           'sporterboog',
                           'sporterboog__boogtype',
                           'sporterboog__sporter')

    list_filter = ('deelcompetitie__competitie',
                   'deelcompetitie__nhb_rayon',
                   'sporterboog__boogtype')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'klasse':
            kwargs['queryset'] = (CompetitieKlasse
                                  .objects
                                  .select_related('indiv', 'team')
                                  .all())

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class CompetitieMutatieAdmin(CreateOnlyAdmin):

    readonly_fields = ('mutatie', 'when', 'deelnemer', 'door')

    list_select_related = ('deelnemer__deelcompetitie',
                           'deelnemer__klasse',
                           'deelnemer__sporterboog__sporter')

    list_filter = ('is_verwerkt', 'mutatie')


class RegiocompetitieRondeTeamAdmin(CreateOnlyAdmin):

    filter_horizontal = ('deelnemers_geselecteerd', 'deelnemers_feitelijk')

    readonly_fields = ('team', 'ronde_nr', 'feitelijke_scores')

    list_filter = ('team__deelcompetitie__competitie',
                   'team__vereniging__regio',
                   'ronde_nr')

    list_select_related = ('team', )

    fieldsets = (
        ('',
            {'fields': ('team',
                        'ronde_nr',
                        'deelnemers_geselecteerd',
                        'deelnemers_feitelijk',
                        'team_score',
                        'team_punten',
                        'logboek',
                        'feitelijke_scores')
             }),
    )

    @staticmethod
    def feitelijke_scores(obj):     # pragma: no cover
        msg = "Scores:\n"
        msg += "\n".join([str(score) for score in obj.scores_feitelijk.all()])
        msg += "\n\nScoreHist:\n"
        msg += "\n".join([str(scorehist) for scorehist in obj.scorehist_feitelijk.all()])
        return msg

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.deelcomp = None
        self.ver = None

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        if obj:
            team = obj.team
            self.deelcomp = team.deelcompetitie
            self.ver = team.vereniging
        else:
            self.deelcomp = self.ver = None

        return super().get_form(request, obj, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if self.deelcomp and self.ver:
            if db_field.name in ('deelnemers_geselecteerd', 'deelnemers_feitelijk'):
                kwargs['widget'] = FilteredSelectMultiple(db_field.verbose_name, False)
                kwargs['queryset'] = (RegioCompetitieSchutterBoog
                                      .objects
                                      .select_related('sporterboog',
                                                      'sporterboog__sporter',
                                                      'sporterboog__boogtype')
                                      .filter(deelcompetitie=self.deelcomp,
                                              bij_vereniging=self.ver,
                                              inschrijf_voorkeur_team=True))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class RegiocompetitieTeamPouleAdmin(CreateOnlyAdmin):

    list_filter = ('deelcompetitie__competitie',
                   'deelcompetitie__nhb_regio')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.deelcomp = None

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        if obj:
            self.deelcomp = obj.deelcompetitie
        else:
            self.deelcomp = None

        return super().get_form(request, obj, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if self.deelcomp:
            if db_field.name == 'teams':
                kwargs['widget'] = FilteredSelectMultiple(db_field.verbose_name, False)
                kwargs['queryset'] = (RegiocompetitieTeam
                                      .objects
                                      .filter(deelcompetitie=self.deelcomp))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class DeelcompetitieKlasseLimietAdmin(CreateOnlyAdmin):

    list_filter = ('deelcompetitie__competitie', 'deelcompetitie__nhb_rayon', 'klasse__indiv__boogtype', 'klasse__team__team_type')

    list_select_related = ('deelcompetitie',
                           'deelcompetitie__competitie',
                           'deelcompetitie__nhb_rayon',
                           'klasse',
                           'klasse__indiv',
                           'klasse__team')

    readonly_fields = ('deelcompetitie', 'klasse')

    ordering = ('klasse__indiv__volgorde', 'klasse__team__volgorde')


admin.site.register(Competitie)
admin.site.register(DeelCompetitie, DeelCompetitieAdmin)
admin.site.register(CompetitieKlasse, CompetitieKlasseAdmin)
admin.site.register(DeelcompetitieRonde, DeelcompetitieRondeAdmin)
admin.site.register(RegioCompetitieSchutterBoog, RegioCompetitieSchutterBoogAdmin)
admin.site.register(DeelcompetitieKlasseLimiet, DeelcompetitieKlasseLimietAdmin)
admin.site.register(CompetitieMutatie, CompetitieMutatieAdmin)
admin.site.register(RegiocompetitieTeam, RegiocompetitieTeamAdmin)
admin.site.register(RegiocompetitieTeamPoule, RegiocompetitieTeamPouleAdmin)
admin.site.register(RegiocompetitieRondeTeam, RegiocompetitieRondeTeamAdmin)
admin.site.register(KampioenschapSchutterBoog, KampioenschapSchutterBoogAdmin)
admin.site.register(KampioenschapTeam, KampioenschapTeamAdmin)

# end of file
