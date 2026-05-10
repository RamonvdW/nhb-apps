# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from django.db.models import F
from django.contrib.admin.widgets import FilteredSelectMultiple
from BasisTypen.models import TeamType
from Competitie.models import CompetitieIndivKlasse, CompetitieTeamKlasse, CompetitieMatch
from CompLaagRegio.models import RegioComp, RegioRonde, RegioDeelnemer, RegioTeam, RegioPoule, RegioRondeTeam


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


class RegioCompAdmin(CreateOnlyAdmin):

    list_filter = ('competitie', 'regio')

    list_select_related = ('competitie', 'regio')

    readonly_fields = ('competitie', 'regio', 'functie')


class RegioRondeAdmin(CreateOnlyAdmin):

    list_filter = ('regiocomp__competitie', 'regiocomp__is_afgesloten', 'regiocomp__regio')

    list_select_related = ('regiocomp', 'regiocomp__regio')

    readonly_fields = ('regiocomp', 'cluster')

    filter_horizontal = ('matches',)

    # FUTURE: filter matches op verenigingen in de regio


class TeamAGListFilter(admin.SimpleListFilter):

    title = 'Team AG'

    parameter_name = 'TeamAG'

    def lookups(self, request, model_admin):
        return (
            ('Ontbreekt', 'Nog niet ingevuld'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'Ontbreekt':
            queryset = queryset.filter(regiocomp__regio_organiseert_teamcompetitie=True,
                                       inschrijf_voorkeur_team=True,
                                       ag_voor_team_mag_aangepast_worden=True,
                                       ag_voor_team__lte="0.1")
        return queryset


class ZelfstandigIngeschrevenListFilter(admin.SimpleListFilter):

    title = 'Inschrijving'

    parameter_name = 'Zelfstandig'

    def lookups(self, request, model_admin):
        return (
            ('HWL', 'Ingeschreven door de HWL'),
            ('Zelf', 'Zelfstandig ingeschreven'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'Zelf':
            queryset = queryset.filter(sporterboog__sporter__account=F('aangemeld_door'))
        if self.value() == 'HWL':
            queryset = queryset.exclude(sporterboog__sporter__account=F('aangemeld_door'))
        return queryset


class RegioDeelnemerAdmin(CreateOnlyAdmin):

    fieldsets = (
        ('Wie',
            {'fields': ('regiocomp',
                        'bij_vereniging',
                        'sporterboog',
                        'competitieleeftijd')
             }),
        ('Individueel',
            {'fields': ('ag_voor_indiv',
                        'indiv_klasse'),
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
                        'aangemeld_door',
                        'wanneer_aangemeld',
                        'inschrijf_voorkeur_rk_bk',
                        'logboekje'),
             }),
        ('Uitslag',
            {'fields': ('score1', 'score2', 'score3', 'score4', 'score5', 'score6', 'score7',
                        'aantal_scores', 'laagste_score_nr', 'totaal', 'gemiddelde')
             }),
    )

    filter_horizontal = ('inschrijf_gekozen_matches',)

    createonly_fields = ('regiocomp',
                         'sporterboog',
                         'bij_vereniging')

    autocomplete_fields = ('bij_vereniging', 'sporterboog')

    readonly_fields = ('scores', 'aangemeld_door', 'competitieleeftijd', 'wanneer_aangemeld')

    search_fields = ('sporterboog__sporter__unaccented_naam',
                     'sporterboog__sporter__lid_nr')

    list_filter = ('regiocomp__competitie',
                   'regiocomp__regio',
                   ZelfstandigIngeschrevenListFilter,
                   TeamAGListFilter,
                   'sporterboog__boogtype',
                   'inschrijf_voorkeur_rk_bk',
                   ('sporterboog__sporter__bij_vereniging', admin.EmptyFieldListFilter),
                   'sporterboog__sporter__bij_vereniging')

    list_select_related = ('regiocomp',
                           'regiocomp__regio',
                           'regiocomp__competitie',
                           'sporterboog',
                           'sporterboog__sporter',
                           'sporterboog__boogtype')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    @staticmethod
    def competitieleeftijd(obj):     # pragma: no cover
        comp = obj.regiocomp.competitie
        msg = "%s jaar (seizoen %s/%s)" % (
                obj.sporterboog.sporter.bereken_wedstrijdleeftijd_wa(comp.begin_jaar) + 1,
                comp.begin_jaar,
                comp.begin_jaar + 1)
        return msg

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
        if db_field.name == 'indiv_klasse' and self.obj:
            # alleen laten kiezen uit de klassen van deze competitie
            kwargs['queryset'] = (CompetitieIndivKlasse
                                  .objects
                                  .filter(competitie=self.obj.regiocomp.competitie)
                                  .order_by('volgorde'))

        elif db_field.name == 'regiocomp':
            # alleen laten kiezen uit de regiocompetitie van deze competitie
            kwargs['queryset'] = (RegioComp
                                  .objects
                                  .select_related('competitie',
                                                  'regio')
                                  .order_by('competitie__afstand',
                                            'regio__regio_nr'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'inschrijf_gekozen_matches' and self.obj:
            pks = list()
            for ronde in (RegioRonde
                          .objects
                          .prefetch_related('matches')
                          .filter(regiocomp=self.obj.regiocomp)):
                # sta alle matches in de regio toe, dus alle clusters
                pks.extend(ronde.matches.values_list('pk', flat=True))
            # for
            kwargs['queryset'] = (CompetitieMatch
                                  .objects
                                  .filter(pk__in=pks)
                                  .order_by('datum_wanneer',
                                            'tijd_begin_wedstrijd'))

        return super().formfield_for_manytomany(db_field, request, **kwargs)


class TeamTypeFilter(admin.SimpleListFilter):

    title = 'Team type'

    parameter_name = 'TeamType'

    def lookups(self, request, model_admin):
        tups = list()
        for team_type in TeamType.objects.all():
            tups.append((team_type.afkorting, team_type.beschrijving))
        # for
        return tups

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(team_type__afkorting=self.value())
        return queryset


class RegioTeamAdmin(CreateOnlyAdmin):

    filter_horizontal = ('leden',)

    list_filter = ('regiocomp__competitie',
                   'vereniging__regio',
                   TeamTypeFilter)

    list_select_related = ('regiocomp',
                           'regiocomp__regio',
                           'regiocomp__competitie',
                           'vereniging',
                           'team_klasse')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    def get_form(self, request, obj: RegioComp=None, **kwargs):             # pragma: no cover
        """ initialisatie van het admin formulier
            hier "vangen" we het database object waar we mee bezig gaan
        """
        if obj:
            self.obj = obj
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        """ bepaal de relevante keuzemogelijkheden voor specifieke velden
        """
        if db_field.name == 'team_klasse' and self.obj:
            # alleen laten kiezen uit de team klassen van deze competitie
            kwargs['queryset'] = (CompetitieTeamKlasse
                                  .objects
                                  .filter(competitie=self.obj.regiocomp.competitie,
                                          is_voor_teams_rk_bk=False)
                                  .order_by('volgorde'))

        elif db_field.name == 'regiocomp':
            # alleen laten kiezen uit regiocompetities van deze competitie
            kwargs['queryset'] = (RegioComp
                                  .objects
                                  .select_related('competitie',
                                                  'regio')
                                  .order_by('competitie__afstand',
                                            'regio__regio_nr'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'leden' and self.obj:
            # alleen leden van de juiste vereniging laten kiezen
            kwargs['queryset'] = (RegioDeelnemer
                                  .objects
                                  .filter(regiocomp=self.obj.regiocomp,
                                          bij_vereniging=self.obj.vereniging,
                                          inschrijf_voorkeur_team=True)
                                  .select_related('sporterboog',
                                                  'sporterboog__sporter',
                                                  'sporterboog__boogtype'))

        return super().formfield_for_manytomany(db_field, request, **kwargs)


class RondeTeamVerFilter(admin.SimpleListFilter):

    title = 'Vereniging'

    parameter_name = 'RondeTeamVer'

    def __init__(self, request, params, model, model_admin):
        # print('init: q=%s' % list(request.GET.items()))
        self.limit_comp = request.GET.get('team__regiocomp__competitie__id__exact')
        self.limit_regio = request.GET.get('team__vereniging__regio__regio_nr__exact')
        self.limit_teamtype = request.GET.get('RondeTeamType')
        super().__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin):

        teams = RegioTeam.objects.select_related('vereniging')
        if self.limit_comp:
            teams = teams.filter(regiocomp__competitie__id=self.limit_comp)
        if self.limit_regio:
            teams = teams.filter(vereniging__regio__regio_nr=self.limit_regio)
        if self.limit_teamtype:
            teams = teams.filter(team_type__afkorting=self.limit_teamtype)

        tups = list()
        for team in teams.order_by('vereniging__ver_nr').distinct('vereniging'):
            ver = team.vereniging
            tups.append((ver.ver_nr, ver.ver_nr_en_naam()))
        # for
        # print('lookups: aantal=%s' % len(tups))
        return tups

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(team__vereniging__ver_nr=self.value())
        return queryset


class RondeTeamTypeFilter(admin.SimpleListFilter):

    title = 'Team type'

    parameter_name = 'RondeTeamType'

    def lookups(self, request, model_admin):
        tups = list()
        for team_type in TeamType.objects.all():
            tups.append((team_type.afkorting, team_type.beschrijving))
        # for
        return tups

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(team__team_type__afkorting=self.value())
        return queryset


class RegioRondeTeamAdmin(CreateOnlyAdmin):

    filter_horizontal = ('deelnemers_geselecteerd', 'deelnemers_feitelijk')

    readonly_fields = ('feitelijke_scores',)

    list_filter = ('team__regiocomp__competitie',
                   'team__vereniging__regio',
                   RondeTeamTypeFilter,
                   'ronde_nr',
                   RondeTeamVerFilter)

    list_select_related = ('team', 'team__vereniging')

    ordering = ('team__vereniging__ver_nr', 'ronde_nr')

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
        msg += "\n".join([str(score) for score in (obj
                                                   .scores_feitelijk
                                                   .select_related('sporterboog',
                                                                   'sporterboog__sporter',
                                                                   'sporterboog__sporter__bij_vereniging')
                                                   .all())])
        msg += "\n\nScoreHist:\n"
        msg += "\n".join([str(scorehist) for scorehist in (obj
                                                           .scorehist_feitelijk
                                                           .select_related('door_account')
                                                           .all())])
        return msg

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.regiocomp = None
        self.ver = None

    def get_form(self, request, obj: RegioRondeTeam=None, **kwargs):      # pragma: no cover
        """ initialisatie van het admin formulier
            hier "vangen" we het database object waar we mee bezig gaan
        """
        if obj:
            team = obj.team
            self.regiocomp = team.regiocomp
            self.ver = team.vereniging
        else:
            self.regiocomp = self.ver = None

        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):                # pragma: no cover
        """ bepaal de relevante keuzemogelijkheden voor specifieke velden
        """
        if db_field.name == 'team' and self.regiocomp:
            kwargs['queryset'] = (RegioTeam
                                  .objects
                                  .select_related('regiocomp',
                                                  'vereniging',
                                                  'team_type')
                                  .filter(regiocomp=self.regiocomp)
                                  .order_by('team_naam', 'pk'))
        else:
            kwargs['queryset'] = (RegioTeam
                                  .objects
                                  .select_related('regiocomp',
                                                  'vereniging',
                                                  'team_type')
                                  .order_by('team_naam',
                                            'pk'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name in ('deelnemers_geselecteerd', 'deelnemers_feitelijk'):
            kwargs['widget'] = FilteredSelectMultiple(db_field.verbose_name, False)
            if self.regiocomp and self.ver:
                kwargs['queryset'] = (RegioDeelnemer
                                      .objects
                                      .filter(regiocomp=self.regiocomp,
                                              bij_vereniging=self.ver,
                                              inschrijf_voorkeur_team=True)
                                      .select_related('sporterboog',
                                                      'sporterboog__sporter',
                                                      'sporterboog__sporter__bij_vereniging',
                                                      'sporterboog__boogtype')
                                      .order_by('sporterboog__sporter__lid_nr'))
            else:
                kwargs['queryset'] = (RegioDeelnemer
                                      .objects
                                      .filter(inschrijf_voorkeur_team=True)
                                      .select_related('sporterboog',
                                                      'sporterboog__sporter',
                                                      'sporterboog__sporter__bij_vereniging',
                                                      'sporterboog__boogtype')
                                      .order_by('sporterboog__sporter__lid_nr'))

        return super().formfield_for_manytomany(db_field, request, **kwargs)


class RegioPouleAdmin(CreateOnlyAdmin):

    list_filter = ('regiocomp__competitie',
                   'regiocomp__regio')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.regiocomp = None

    def get_form(self, request, obj: RegioPoule=None, **kwargs):                    # pragma: no cover
        """ initialisatie van het admin formulier
            hier "vangen" we het database object waar we mee bezig gaan
        """
        if obj:
            self.regiocomp = obj.regiocomp
        else:
            self.regiocomp = None

        return super().get_form(request, obj, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if self.regiocomp:
            if db_field.name == 'teams':
                kwargs['widget'] = FilteredSelectMultiple(db_field.verbose_name, False)
                kwargs['queryset'] = (RegioTeam
                                      .objects
                                      .filter(regiocomp=self.regiocomp))

        return super().formfield_for_manytomany(db_field, request, **kwargs)


admin.site.register(RegioComp, RegioCompAdmin)
admin.site.register(RegioRonde, RegioRondeAdmin)
admin.site.register(RegioDeelnemer, RegioDeelnemerAdmin)
admin.site.register(RegioTeam, RegioTeamAdmin)
admin.site.register(RegioPoule, RegioPouleAdmin)
admin.site.register(RegioRondeTeam, RegioRondeTeamAdmin)

# end of file
