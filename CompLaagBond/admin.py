# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from django.db.models import F
from Competitie.models import CompetitieIndivKlasse, CompetitieTeamKlasse
from CompLaagBond.models import KampBK, DeelnemerBK, TeamBK
from CompLaagRayon.models import DeelnemerRK


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


class KampBKAdmin(CreateOnlyAdmin):

    list_filter = ('competitie',)

    list_select_related = ('competitie',)

    filter_horizontal = ('matches',)


class TeamKlassenFilter(admin.SimpleListFilter):

    title = "Team Wedstrijdklasse"

    parameter_name = 'team_klasse'

    default_value = None

    def __init__(self, request, params, model, model_admin):
        # print('init: q=%s' % list(request.GET.items()))
        self.limit_comp = request.GET.get('kampioenschap__competitie__id__exact')
        super().__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin):                    # pragma: no cover
        """ Return list of tuples for the sidebar """
        lst = [('leeg', 'Geen klasse')]

        for team_klasse in (CompetitieTeamKlasse
                            .objects
                            .filter(competitie=self.limit_comp,
                                    is_voor_teams_rk_bk=True)
                            .order_by('volgorde')):
            tup = (team_klasse.volgorde, team_klasse.beschrijving)
            lst.append(tup)
        # for

        return lst

    def queryset(self, request, queryset):      # pragma: no cover
        selection = self.value()
        if selection:
            if selection == 'leeg':
                queryset = queryset.filter(team_klasse=None)
            else:
                queryset = queryset.filter(team_klasse__volgorde=selection)
        return queryset


class IncompleetTeamFilter(admin.SimpleListFilter):

    title = "Incompleet Team"

    parameter_name = 'incompleet'

    default_value = None

    def lookups(self, request, model_admin):                    # pragma: no cover
        """ Return list of tuples for the sidebar """
        return [
            ('incompleet', 'Incomplete teams'),
            ('compleet', 'Volledige teams')
        ]

    def queryset(self, request, queryset):
        selection = self.value()
        if selection == 'incompleet':
            queryset = queryset.filter(aanvangsgemiddelde__lt=1)
        elif selection == 'compleet':
            queryset = queryset.filter(aanvangsgemiddelde__gte=1)
        return queryset


class VerenigingFilter(admin.SimpleListFilter):

    title = "Vereniging"

    parameter_name = 'ver_in_rayon'

    default_value = None

    def __init__(self, request, params, model, model_admin):
        # print('init: q=%s' % list(request.GET.items()))
        self.limit_rayon = request.GET.get('vereniging__regio__rayon__rayon_nr__exact', None)
        super().__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin):                    # pragma: no cover
        """ Return list of tuples for the sidebar """
        lst = list()

        qset = TeamBK.objects.all()
        if self.limit_rayon:
            qset = qset.filter(vereniging__regio__rayon_nr=self.limit_rayon)

        for team in qset.distinct('vereniging').order_by('vereniging__ver_nr'):
            ver = team.vereniging
            tup = (str(ver.ver_nr), ver)
            lst.append(tup)
        # for

        return lst

    def queryset(self, request, queryset):      # pragma: no cover
        selection = self.value()
        if selection:
            queryset = queryset.filter(vereniging__ver_nr=selection)
        return queryset


class TeamBKAdmin(CreateOnlyAdmin):

    fieldsets = (
        ('Context',
            {'fields': ('kamp_bk',
                        'team_type')
             }),
        ('Team',
            {'fields': ('team_naam',
                        'vereniging',
                        'volg_nr',
                        'rk_score')
             }),
        ('Deelname',
            {'fields': ('deelname',
                        'is_reserve',
                        'volgorde',
                        'rank'),
             }),
        ('Klasse',
            {'fields': ('team_klasse',
                        'team_klasse_volgende_ronde'),
             }),
        ('Leden',
            {'fields': ('gekoppelde_leden',
                        'feitelijke_leden'),
             }),
        ('Uitslag',
            {'fields': ('result_rank',
                        'result_volgorde',
                        'result_teamscore',
                        'result_shootoff_str')
             }),
    )

    filter_horizontal = ('gekoppelde_leden',
                         'feitelijke_leden')

    list_filter = ('kamp_bk__competitie',
                   'team_type',
                   'is_reserve',
                   'deelname',
                   TeamKlassenFilter,
                   IncompleetTeamFilter,
                   VerenigingFilter)

    list_select_related = ('kamp_bk',
                           'kamp_bk__competitie',
                           'vereniging',
                           'team_klasse')

    search_fields = ('vereniging__ver_nr', 'vereniging__naam', 'team_naam')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None
        self.competitie = None
        self.boog_pks = list()

    def get_form(self, request, obj: TeamBK=None, **kwargs):                    # pragma: no cover
        """ initialisatie van het admin formulier
            hier "vangen" we het database object waar we mee bezig gaan
        """
        if obj:
            self.obj = obj
            if obj.kamp_bk:
                self.competitie = self.obj.kamp_bk.competitie
            # bepaal welke bogen gebruik mogen worden voor dit team type
            self.boog_pks = list(obj.team_type.boog_typen.values_list('pk', flat=True))
        else:
            self.obj = None
            self.competitie = None
            self.boog_pks = list()

        return super().get_form(request, obj, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name in ('gekoppelde_leden', 'feitelijke_leden'):
            if self.obj:
                # Edit
                kwargs['queryset'] = (DeelnemerRK
                                      .objects
                                      .select_related('sporterboog',
                                                      'sporterboog__sporter',
                                                      'sporterboog__boogtype',
                                                      'kampioenschap__rayon')
                                      .filter(kamp_rk__competitie=self.competitie,
                                              bij_vereniging=self.obj.vereniging,
                                              sporterboog__boogtype__pk__in=self.boog_pks)
                                      .order_by('sporterboog__sporter__lid_nr'))
            else:
                # Add
                kwargs['queryset'] = DeelnemerRK.objects.none()

        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        """ bepaal de relevante keuzemogelijkheden voor specifieke velden
        """
        if db_field.name == 'kamp_bk':
            kwargs['queryset'] = (KampBK
                                  .objects
                                  .select_related('competitie',
                                                  'rayon')
                                  .order_by('competitie__pk',
                                            'rayon__rayon_nr'))

        elif db_field.name in ('team_klasse', 'team_klasse_volgende_ronde'):
            if self.competitie:
                # alleen laten kiezen uit de team klassen van deze competitie
                kwargs['queryset'] = (CompetitieTeamKlasse
                                      .objects
                                      .filter(competitie=self.competitie,
                                              is_voor_teams_rk_bk=True)
                                      .order_by('volgorde'))
            else:
                kwargs['queryset'] = CompetitieTeamKlasse.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class RkBkIndivKlasseFilter(admin.SimpleListFilter):

    title = "Indiv Klasse (RK/BK)"

    parameter_name = 'indiv_klasse_rk_bk'

    default_value = None

    def lookups(self, request, model_admin):                    # pragma: no cover
        """ Return list of tuples for the sidebar """
        return [(klasse.volgorde, klasse.beschrijving) for klasse in (CompetitieIndivKlasse
                                                                      .objects
                                                                      .filter(is_ook_voor_rk_bk=True)
                                                                      .distinct('volgorde')
                                                                      .order_by('volgorde'))]

    def queryset(self, request, queryset):                      # pragma: no cover
        selection = self.value()
        if selection:
            queryset = queryset.filter(indiv_klasse__volgorde=selection)
        return queryset


class VerenigingMismatchFilter(admin.SimpleListFilter):

    title = 'mismatch vereniging'

    parameter_name = 'mismatch'

    def lookups(self, request, model_admin):
        return (
            ('Geen', 'Geen vereniging'),
            ('Ja', 'Overgestapt'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'Geen':
            queryset = queryset.filter(sporterboog__sporter__bij_vereniging=None)
        if self.value() == 'Ja':
            queryset = queryset.exclude(sporterboog__sporter__bij_vereniging=F('bij_vereniging'))
        return queryset


class DeelnemerBKAdmin(CreateOnlyAdmin):

    fieldsets = (
        ('Wie',
            {'fields': ('kampioenschap',
                        'sporterboog',
                        'bij_vereniging')
             }),
        ('Klasse',
            {'fields': ('indiv_klasse',
                        'indiv_klasse_volgende_ronde'),
             }),
        ('Details',
            {'fields': ('rk_score',
                        'kampioen_label')
             }),
        ('Status aanmelding',
            {'fields': ('deelname',
                        'volgorde',
                        'rank',
                        'logboek'),
             }),
        ('Resultaten',
            {'fields': ('result_rank',
                        'result_volgorde',
                        'result_score_1',
                        'result_score_2',
                        'result_counts')
             }),
    )

    readonly_fields = ('kamp_bk',
                       'sporterboog')

    search_fields = ('sporterboog__sporter__unaccented_naam',
                     'sporterboog__sporter__lid_nr')

    list_select_related = ('kampioenschap',
                           'kampioenschap__competitie',
                           'kampioenschap__rayon',
                           'indiv_klasse',
                           'sporterboog',
                           'sporterboog__boogtype',
                           'sporterboog__sporter')

    list_filter = ('kamp_bk__competitie',
                   'deelname',
                   VerenigingMismatchFilter,
                   'sporterboog__boogtype',
                   RkBkIndivKlasseFilter,
                   'sporterboog__sporter__bij_vereniging')

    ordering = ['volgorde']

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
        if db_field.name in ('indiv_klasse', 'indiv_klasse_volgende_ronde') and self.obj:
            # alleen klassen laten kiezen van deze competitie
            kwargs['queryset'] = (CompetitieIndivKlasse
                                  .objects
                                  .filter(competitie=self.obj.kampioenschap.competitie)
                                  .order_by('volgorde'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)



admin.site.register(KampBK, KampBKAdmin)
admin.site.register(DeelnemerBK, DeelnemerBKAdmin)
admin.site.register(TeamBK, TeamBKAdmin)

# end of file
