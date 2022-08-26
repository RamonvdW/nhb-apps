# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from .models import (Competitie, DeelCompetitie, DeelcompetitieRonde, LAAG_REGIO, LAAG_RK,
                     CompetitieIndivKlasse, CompetitieTeamKlasse,
                     DeelcompetitieIndivKlasseLimiet, DeelcompetitieTeamKlasseLimiet,
                     CompetitieMatch, RegioCompetitieSchutterBoog, KampioenschapSchutterBoog,
                     RegiocompetitieTeam, RegiocompetitieTeamPoule, RegiocompetitieRondeTeam, KampioenschapTeam,
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

    filter_horizontal = ('rk_bk_matches',)


class DeelcompetitieRondeAdmin(CreateOnlyAdmin):

    list_filter = ('deelcompetitie__is_afgesloten', 'deelcompetitie__nhb_regio')

    list_select_related = ('deelcompetitie', 'deelcompetitie__nhb_regio')

    readonly_fields = ('deelcompetitie', 'cluster')

    filter_horizontal = ('matches',)

    # TODO: filter matches op verenigingen in de regio


class CompetitieAdmin(admin.ModelAdmin):

    filter_horizontal = ('boogtypen', 'teamtypen')


class CompetitieIndivKlasseAdmin(admin.ModelAdmin):

    list_filter = ('competitie', 'boogtype', 'is_voor_rk_bk')

    list_select_related = ('competitie', 'boogtype')

    ordering = ('volgorde',)


class CompetitieTeamKlasseAdmin(admin.ModelAdmin):

    list_filter = ('competitie', 'team_afkorting', 'is_voor_teams_rk_bk')

    list_select_related = ('competitie',)

    ordering = ('volgorde',)

    filter_horizontal = ('boog_typen',)


class CompetitieMatchAdmin(admin.ModelAdmin):

    filter_horizontal = ('indiv_klassen', 'team_klassen')

    # TODO: filter toepasselijke indiv_klassen / team_klassen aan de hand van obj.competitie


class RegioCompetitieSchutterBoogAdmin(CreateOnlyAdmin):

    fieldsets = (
        ('Wie',
            {'fields': ('deelcompetitie',
                        'bij_vereniging',
                        'sporterboog',
                        'competitieleeftijd')
             }),
        ('Individueel',
            {'fields': (('ag_voor_indiv',),
                        'indiv_klasse',
                        'inschrijf_voorkeur_rk_bk'),
             }),
        ('Team',
            {'fields': ('inschrijf_voorkeur_team',
                        'ag_voor_team',
                        'ag_voor_team_mag_aangepast_worden',
                        'gemiddelde_begin_team_ronde'),
             }),
        ('Inschrijving',
            {'fields': ('inschrijf_gekozen_matches',
                        'inschrijf_voorkeur_dagdeel',
                        'inschrijf_notitie',
                        'aangemeld_door'),
             }),
        ('Uitslag',
            {'fields': ('score1', 'score2', 'score3', 'score4', 'score5', 'score6', 'score7',
                        'aantal_scores', 'laagste_score_nr', 'totaal', 'gemiddelde')
             }),
    )

    filter_horizontal = ('inschrijf_gekozen_matches',)

    createonly_fields = ('deelcompetitie',
                         'sporterboog',
                         'bij_vereniging')

    autocomplete_fields = ('bij_vereniging',)

    readonly_fields = ('scores', 'aangemeld_door', 'competitieleeftijd')

    search_fields = ('sporterboog__sporter__unaccented_naam',
                     'sporterboog__sporter__lid_nr')

    list_filter = ('deelcompetitie__competitie',
                   'deelcompetitie__nhb_regio',
                   'sporterboog__boogtype',
                   'inschrijf_voorkeur_rk_bk',
                   ('sporterboog__sporter__bij_vereniging', admin.EmptyFieldListFilter),
                   'sporterboog__sporter__bij_vereniging')

    list_select_related = ('deelcompetitie',
                           'deelcompetitie__nhb_regio',
                           'deelcompetitie__nhb_rayon',
                           'deelcompetitie__competitie',
                           'sporterboog',
                           'sporterboog__sporter',
                           'sporterboog__boogtype')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    @staticmethod
    def competitieleeftijd(obj):     # pragma: no cover
        comp = obj.deelcompetitie.competitie
        msg = "%s jaar (seizoen %s/%s)" % (
                obj.sporterboog.sporter.bereken_wedstrijdleeftijd_wa(comp.begin_jaar) + 1,
                comp.begin_jaar,
                comp.begin_jaar + 1)
        return msg

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        if obj:
            self.obj = obj
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'indiv_klasse' and self.obj:
            kwargs['queryset'] = (CompetitieIndivKlasse
                                  .objects
                                  .filter(competitie=self.obj.deelcompetitie.competitie)
                                  .order_by('volgorde'))
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
        if db_field.name == 'inschrijf_gekozen_matches' and self.obj:
            pks = list()
            for ronde in (DeelcompetitieRonde
                          .objects
                          .prefetch_related('matches')
                          .filter(deelcompetitie=self.obj.deelcompetitie)):
                # sta alle matches in de regio toe, dus alle clusters
                pks.extend(ronde.matches.values_list('pk', flat=True))
            # for
            kwargs['queryset'] = (CompetitieMatch
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
                           'team_klasse')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        if obj:
            self.obj = obj
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'team_klasse' and self.obj:
            kwargs['queryset'] = (CompetitieTeamKlasse
                                  .objects
                                  .filter(competitie=self.obj.deelcompetitie.competitie,
                                          is_voor_teams_rk_bk=False)
                                  .order_by('volgorde'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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

    parameter_name = 'team_klasse'

    default_value = None

    def lookups(self, request, model_admin):                    # pragma: no cover
        """ Return list of tuples for the sidebar """
        return [
            ('leeg', 'Geen klasse'),
            ('regio', 'Regio klasse'),
            ('rk_bk', 'RK/BK klasse')
        ]

    def queryset(self, request, queryset):      # pragma: no cover
        selection = self.value()
        if selection == 'leeg':
            queryset = queryset.filter(team_klasse=None)
        elif selection == 'regio':
            queryset = queryset.filter(team_klasse__is_voor_teams_rk_bk=False)
        elif selection == 'rk_bk':
            queryset = queryset.filter(team_klasse__is_voor_teams_rk_bk=True)
        return queryset


class KampioenschapTeamAdmin(CreateOnlyAdmin):

    filter_horizontal = ('tijdelijke_schutters',
                         'gekoppelde_schutters',
                         'feitelijke_schutters')

    list_filter = ('deelcompetitie__competitie',
                   'vereniging__regio__rayon',
                   GebruikteKlassenFilter)

    list_select_related = ('deelcompetitie',
                           'deelcompetitie__nhb_rayon',
                           'deelcompetitie__nhb_regio',
                           'deelcompetitie__competitie',
                           'vereniging',
                           'team_klasse')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None
        self.competitie = None
        self.boog_pks = list()

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        if obj:
            self.obj = obj
            if obj.deelcompetitie:
                self.competitie = self.obj.deelcompetitie.competitie
            # bepaal welke bogen gebruik mogen worden voor dit team type
            self.boog_pks = list(obj.team_type.boog_typen.values_list('pk', flat=True))
        else:
            self.obj = None
            self.competitie = None
            self.boog_pks = list()

        return super().get_form(request, obj, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'tijdelijke_schutters':
            # alleen schutters van de juiste vereniging en boogtype laten kiezen
            if self.obj:
                # Edit
                kwargs['queryset'] = (RegioCompetitieSchutterBoog
                                      .objects
                                      .select_related('sporterboog',
                                                      'sporterboog__sporter',
                                                      'sporterboog__boogtype',
                                                      'bij_vereniging')
                                      .filter(deelcompetitie__competitie=self.competitie,
                                              bij_vereniging=self.obj.vereniging,
                                              sporterboog__boogtype__pk__in=self.boog_pks)
                                      .order_by('sporterboog__sporter__lid_nr'))
            else:
                # Add
                kwargs['queryset'] = RegioCompetitieSchutterBoog.objects.none()

        elif db_field.name in ('gekoppelde_schutters', 'feitelijke_schutters'):
            if self.obj:
                # Edit
                kwargs['queryset'] = (KampioenschapSchutterBoog
                                      .objects
                                      .select_related('sporterboog',
                                                      'sporterboog__sporter',
                                                      'sporterboog__boogtype',
                                                      'deelcompetitie__nhb_rayon')
                                      .filter(deelcompetitie__competitie=self.competitie,
                                              bij_vereniging=self.obj.vereniging,
                                              sporterboog__boogtype__pk__in=self.boog_pks)
                                      .order_by('sporterboog__sporter__lid_nr'))
            else:
                # Add
                kwargs['queryset'] = KampioenschapSchutterBoog.objects.none()

        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'deelcompetitie':
            kwargs['queryset'] = (DeelCompetitie
                                  .objects
                                  .filter(laag=LAAG_RK)
                                  .select_related('competitie',
                                                  'nhb_rayon')
                                  .order_by('competitie__pk',
                                            'nhb_rayon__rayon_nr'))

        elif db_field.name == 'team_klasse':
            if self.competitie:
                kwargs['queryset'] = (CompetitieTeamKlasse
                                      .objects
                                      .filter(competitie=self.competitie,
                                              is_voor_teams_rk_bk=True)
                                      .order_by('volgorde'))
            else:
                kwargs['queryset'] = CompetitieTeamKlasse.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class KampioenschapSchutterBoogAdmin(CreateOnlyAdmin):

    fieldsets = (
        ('Wie',
            {'fields': ('deelcompetitie',
                        'sporterboog',
                        'bij_vereniging')
             }),
        ('Klasse',
            {'fields': ('indiv_klasse',),
             }),
        ('Details',
            {'fields': ('gemiddelde',
                        'kampioen_label',
                        'regio_scores')
             }),
        ('Status aanmelding',
            {'fields': ('deelname',
                        'volgorde',
                        'rank'),
             }),
        ('Resultaten',
            {'fields': ('result_rank',
                        'result_score_1',
                        'result_score_2',
                        'result_counts',
                        'result_teamscore_1',
                        'result_teamscore_2')
             }),
    )

    readonly_fields = ('deelcompetitie',
                       'sporterboog')

    search_fields = ('sporterboog__sporter__unaccented_naam',
                     'sporterboog__sporter__lid_nr')

    list_select_related = ('deelcompetitie',
                           'deelcompetitie__nhb_rayon',
                           'deelcompetitie__competitie',
                           'indiv_klasse',
                           'sporterboog',
                           'sporterboog__boogtype',
                           'sporterboog__sporter')

    list_filter = ('deelcompetitie__competitie',
                   'deelcompetitie__nhb_rayon',
                   'sporterboog__boogtype',
                   ('sporterboog__sporter__bij_vereniging', admin.EmptyFieldListFilter),
                   'sporterboog__sporter__bij_vereniging')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        if obj:
            self.obj = obj
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'indiv_klasse' and self.obj:
            kwargs['queryset'] = (CompetitieIndivKlasse
                                  .objects
                                  .filter(competitie=self.obj.deelcompetitie.competitie)
                                  .order_by('volgorde'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class CompetitieMutatieAdmin(CreateOnlyAdmin):

    readonly_fields = ('mutatie', 'when', 'deelnemer', 'door')

    list_select_related = ('deelnemer__deelcompetitie',
                           'deelnemer__deelcompetitie__nhb_rayon',
                           'deelnemer__indiv_klasse',
                           'deelnemer__sporterboog__sporter',
                           'deelnemer__sporterboog__boogtype')

    list_filter = ('is_verwerkt', 'mutatie')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        if obj:
            self.obj = obj
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'deelcompetitie' and self.obj:
            kwargs['queryset'] = (DeelCompetitie
                                  .objects
                                  .select_related('nhb_regio',
                                                  'nhb_rayon')
                                  .filter(competitie=self.obj.competitie)
                                  .order_by('nhb_rayon__rayon_nr',
                                            'nhb_regio__regio_nr'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class RegiocompetitieRondeTeamAdmin(CreateOnlyAdmin):

    filter_horizontal = ('deelnemers_geselecteerd', 'deelnemers_feitelijk')

    readonly_fields = ('team', 'ronde_nr', 'feitelijke_scores')

    list_filter = ('team__deelcompetitie__competitie',
                   'team__vereniging__regio',
                   'ronde_nr')

    list_select_related = ('team', 'team__vereniging')

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
                                              inschrijf_voorkeur_team=True)
                                      .order_by('sporterboog__sporter__lid_nr'))

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


class DeelcompetitieIndivKlasseLimietAdmin(CreateOnlyAdmin):

    list_filter = ('deelcompetitie__competitie', 'deelcompetitie__nhb_rayon', 'indiv_klasse__boogtype')

    list_select_related = ('deelcompetitie',
                           'deelcompetitie__competitie',
                           'deelcompetitie__nhb_rayon',
                           'indiv_klasse')

    readonly_fields = ('deelcompetitie', 'indiv_klasse')

    ordering = ('indiv_klasse__volgorde',)


class DeelcompetitieTeamKlasseLimietAdmin(CreateOnlyAdmin):

    list_filter = ('deelcompetitie__competitie', 'deelcompetitie__nhb_rayon', 'team_klasse__team_afkorting')

    list_select_related = ('deelcompetitie',
                           'deelcompetitie__competitie',
                           'deelcompetitie__nhb_rayon',
                           'team_klasse')

    readonly_fields = ('deelcompetitie', 'team_klasse')

    ordering = ('team_klasse__volgorde',)


admin.site.register(Competitie, CompetitieAdmin)
admin.site.register(DeelCompetitie, DeelCompetitieAdmin)
admin.site.register(CompetitieIndivKlasse, CompetitieIndivKlasseAdmin)
admin.site.register(CompetitieTeamKlasse, CompetitieTeamKlasseAdmin)
admin.site.register(CompetitieMatch, CompetitieMatchAdmin)
admin.site.register(DeelcompetitieRonde, DeelcompetitieRondeAdmin)
admin.site.register(RegioCompetitieSchutterBoog, RegioCompetitieSchutterBoogAdmin)
admin.site.register(DeelcompetitieIndivKlasseLimiet, DeelcompetitieIndivKlasseLimietAdmin)
admin.site.register(DeelcompetitieTeamKlasseLimiet, DeelcompetitieTeamKlasseLimietAdmin)
admin.site.register(CompetitieMutatie, CompetitieMutatieAdmin)
admin.site.register(RegiocompetitieTeam, RegiocompetitieTeamAdmin)
admin.site.register(RegiocompetitieTeamPoule, RegiocompetitieTeamPouleAdmin)
admin.site.register(RegiocompetitieRondeTeam, RegiocompetitieRondeTeamAdmin)
admin.site.register(KampioenschapSchutterBoog, KampioenschapSchutterBoogAdmin)
admin.site.register(KampioenschapTeam, KampioenschapTeamAdmin)

# end of file
