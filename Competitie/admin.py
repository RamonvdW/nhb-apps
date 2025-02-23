# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from django.db.models import F
from django.contrib.admin.widgets import FilteredSelectMultiple
from BasisTypen.definities import SCHEIDS_NIET
from BasisTypen.models import TeamType
from Competitie.definities import DEEL_BK, DEEL_RK
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse, CompetitieMatch,
                               Regiocompetitie, RegiocompetitieRonde, RegiocompetitieSporterBoog, RegiocompetitieTeam,
                               RegiocompetitieTeamPoule, RegiocompetitieRondeTeam,
                               KampioenschapIndivKlasseLimiet, KampioenschapTeamKlasseLimiet, KampioenschapSporterBoog,
                               KampioenschapTeam, Kampioenschap, CompetitieMutatie)
from Sporter.models import Sporter


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


class RegiocompetitieAdmin(CreateOnlyAdmin):

    list_filter = ('competitie', 'regio')

    list_select_related = ('competitie', 'regio')


class KampioenschapAdmin(CreateOnlyAdmin):

    list_filter = ('competitie', 'deel')

    list_select_related = ('competitie', 'rayon')

    filter_horizontal = ('rk_bk_matches',)


class RegiocompetitieRondeAdmin(CreateOnlyAdmin):

    list_filter = ('regiocompetitie__competitie', 'regiocompetitie__is_afgesloten', 'regiocompetitie__regio')

    list_select_related = ('regiocompetitie', 'regiocompetitie__regio')

    readonly_fields = ('regiocompetitie', 'cluster')

    filter_horizontal = ('matches',)

    # FUTURE: filter matches op verenigingen in de regio


class CompetitieAdmin(admin.ModelAdmin):

    filter_horizontal = ('boogtypen', 'teamtypen')


class CompetitieIndivKlasseAdmin(admin.ModelAdmin):

    list_filter = ('competitie', 'boogtype', 'is_ook_voor_rk_bk', 'titel_bk', 'krijgt_scheids_rk', 'krijgt_scheids_bk')

    list_select_related = ('competitie', 'boogtype')

    readonly_fields = ('competitie', 'volgorde', 'boogtype', 'is_ook_voor_rk_bk', 'krijgt_scheids_rk',
                       'krijgt_scheids_bk', 'is_onbekend', 'is_aspirant_klasse')

    ordering = ('volgorde',)


class CompetitieTeamKlasseAdmin(admin.ModelAdmin):

    list_filter = ('competitie', 'team_afkorting', 'is_voor_teams_rk_bk', 'titel_bk',
                   'krijgt_scheids_rk', 'krijgt_scheids_bk')

    list_select_related = ('competitie',)

    ordering = ('volgorde',)

    filter_horizontal = ('boog_typen',)

    readonly_fields = ('competitie', 'volgorde', 'team_type', 'krijgt_scheids_rk', 'krijgt_scheids_bk',
                       'team_afkorting', 'is_voor_teams_rk_bk')


class CompetitieMatchAdmin(admin.ModelAdmin):

    filter_horizontal = ('indiv_klassen', 'team_klassen')

    list_select_related = ('competitie', 'vereniging')

    list_filter = ('competitie', 'aantal_scheids')

    # FUTURE: filter toepasselijke indiv_klassen / team_klassen aan de hand van obj.competitie

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
        if db_field.name == 'gekozen_sr' and self.obj:
            # alleen laten kiezen uit scheidsrechters
            kwargs['queryset'] = (Sporter
                                  .objects
                                  .exclude(scheids=SCHEIDS_NIET)
                                  .order_by('lid_nr'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class TeamAGListFilter(admin.SimpleListFilter):

    title = 'Team AG'

    parameter_name = 'TeamAG'

    def lookups(self, request, model_admin):
        return (
            ('Ontbreekt', 'Nog niet ingevuld'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'Ontbreekt':
            queryset = queryset.filter(regiocompetitie__regio_organiseert_teamcompetitie=True,
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


class RegiocompetitieSporterBoogAdmin(CreateOnlyAdmin):

    fieldsets = (
        ('Wie',
            {'fields': ('regiocompetitie',
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

    createonly_fields = ('regiocompetitie',
                         'sporterboog',
                         'bij_vereniging')

    autocomplete_fields = ('bij_vereniging', 'sporterboog')

    readonly_fields = ('scores', 'aangemeld_door', 'competitieleeftijd', 'wanneer_aangemeld')

    search_fields = ('sporterboog__sporter__unaccented_naam',
                     'sporterboog__sporter__lid_nr')

    list_filter = ('regiocompetitie__competitie',
                   'regiocompetitie__regio',
                   ZelfstandigIngeschrevenListFilter,
                   TeamAGListFilter,
                   'sporterboog__boogtype',
                   'inschrijf_voorkeur_rk_bk',
                   ('sporterboog__sporter__bij_vereniging', admin.EmptyFieldListFilter),
                   'sporterboog__sporter__bij_vereniging')

    list_select_related = ('regiocompetitie',
                           'regiocompetitie__regio',
                           'regiocompetitie__competitie',
                           'sporterboog',
                           'sporterboog__sporter',
                           'sporterboog__boogtype')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    @staticmethod
    def competitieleeftijd(obj):     # pragma: no cover
        comp = obj.regiocompetitie.competitie
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
                                  .filter(competitie=self.obj.regiocompetitie.competitie)
                                  .order_by('volgorde'))

        elif db_field.name == 'regiocompetitie':
            # alleen laten kiezen uit de regiocompetitie van deze competitie
            kwargs['queryset'] = (Regiocompetitie
                                  .objects
                                  .select_related('competitie',
                                                  'regio')
                                  .order_by('competitie__afstand',
                                            'regio__regio_nr'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'inschrijf_gekozen_matches' and self.obj:
            pks = list()
            for ronde in (RegiocompetitieRonde
                          .objects
                          .prefetch_related('matches')
                          .filter(regiocompetitie=self.obj.regiocompetitie)):
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


class RegiocompetitieTeamAdmin(CreateOnlyAdmin):

    filter_horizontal = ('leden',)

    list_filter = ('regiocompetitie__competitie',
                   'vereniging__regio',
                   TeamTypeFilter)

    list_select_related = ('regiocompetitie',
                           'regiocompetitie__regio',
                           'regiocompetitie__competitie',
                           'vereniging',
                           'team_klasse')

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
        if db_field.name == 'team_klasse' and self.obj:
            # alleen laten kiezen uit de team klassen van deze competitie
            kwargs['queryset'] = (CompetitieTeamKlasse
                                  .objects
                                  .filter(competitie=self.obj.regiocompetitie.competitie,
                                          is_voor_teams_rk_bk=False)
                                  .order_by('volgorde'))

        elif db_field.name == 'regiocompetitie':
            # alleen laten kiezen uit regiocompetities van deze competitie
            kwargs['queryset'] = (Regiocompetitie
                                  .objects
                                  .select_related('competitie',
                                                  'regio')
                                  .order_by('competitie__afstand',
                                            'regio__regio_nr'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'leden' and self.obj:
            # alleen leden van de juiste vereniging laten kiezen
            kwargs['queryset'] = (RegiocompetitieSporterBoog
                                  .objects
                                  .filter(regiocompetitie=self.obj.regiocompetitie,
                                          bij_vereniging=self.obj.vereniging,
                                          inschrijf_voorkeur_team=True)
                                  .select_related('sporterboog',
                                                  'sporterboog__sporter',
                                                  'sporterboog__boogtype'))

        return super().formfield_for_manytomany(db_field, request, **kwargs)


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


class KampioenschapTypeFilter(admin.SimpleListFilter):

    title = "Soort kampioenschap"

    parameter_name = 'rk_bk_type'

    default_value = None

    def lookups(self, request, model_admin):                    # pragma: no cover
        """ Return list of tuples for the sidebar """
        return [
            ('RK', 'RK teams'),
            ('BK', 'BK teams')
        ]

    def queryset(self, request, queryset):
        selection = self.value()
        if selection == 'RK':
            queryset = queryset.filter(kampioenschap__deel=DEEL_RK)
        elif selection == 'BK':
            queryset = queryset.filter(kampioenschap__deel=DEEL_BK)
        return queryset


class KampioenschapTeamAdmin(CreateOnlyAdmin):

    fieldsets = (
        ('Context',
            {'fields': ('kampioenschap',
                        'team_type')
             }),
        ('Team',
            {'fields': ('team_naam',
                        'vereniging',
                        'volg_nr',
                        'rk_kampioen_label',
                        'aanvangsgemiddelde')
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
            {'fields': ('tijdelijke_leden',
                        'gekoppelde_leden',
                        'feitelijke_leden'),
             }),
        ('Uitslag',
            {'fields': ('result_rank',
                        'result_volgorde',
                        'result_teamscore',
                        'result_counts')
             }),
    )

    filter_horizontal = ('tijdelijke_leden',
                         'gekoppelde_leden',
                         'feitelijke_leden')

    list_filter = ('kampioenschap__competitie',
                   KampioenschapTypeFilter,
                   'team_type',
                   'is_reserve',
                   'deelname',
                   'vereniging__regio__rayon',
                   TeamKlassenFilter,
                   IncompleetTeamFilter)

    list_select_related = ('kampioenschap',
                           'kampioenschap__rayon',
                           'kampioenschap__competitie',
                           'vereniging',
                           'team_klasse')

    search_fields = ('vereniging__ver_nr', 'vereniging__naam', 'team_naam')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None
        self.competitie = None
        self.boog_pks = list()

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        """ initialisatie van het admin formulier
            hier "vangen" we het database object waar we mee bezig gaan
        """
        if obj:
            self.obj = obj
            if obj.kampioenschap:
                self.competitie = self.obj.kampioenschap.competitie
            # bepaal welke bogen gebruik mogen worden voor dit team type
            self.boog_pks = list(obj.team_type.boog_typen.values_list('pk', flat=True))
        else:
            self.obj = None
            self.competitie = None
            self.boog_pks = list()

        return super().get_form(request, obj, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name == 'tijdelijke_leden':
            # alleen leden van de juiste vereniging en boogtype laten kiezen
            if self.obj:
                # Edit
                kwargs['queryset'] = (RegiocompetitieSporterBoog
                                      .objects
                                      .select_related('sporterboog',
                                                      'sporterboog__sporter',
                                                      'sporterboog__boogtype',
                                                      'bij_vereniging')
                                      .filter(regiocompetitie__competitie=self.competitie,
                                              bij_vereniging=self.obj.vereniging,
                                              sporterboog__boogtype__pk__in=self.boog_pks)
                                      .order_by('sporterboog__sporter__lid_nr'))
            else:
                # Add
                kwargs['queryset'] = RegiocompetitieSporterBoog.objects.none()

        elif db_field.name in ('gekoppelde_leden', 'feitelijke_leden'):
            if self.obj:
                # Edit
                kwargs['queryset'] = (KampioenschapSporterBoog
                                      .objects
                                      .select_related('sporterboog',
                                                      'sporterboog__sporter',
                                                      'sporterboog__boogtype',
                                                      'kampioenschap__rayon')
                                      .filter(kampioenschap__competitie=self.competitie,
                                              kampioenschap__deel=DEEL_RK,      # altijd RK sporters koppelen
                                              bij_vereniging=self.obj.vereniging,
                                              sporterboog__boogtype__pk__in=self.boog_pks)
                                      .order_by('sporterboog__sporter__lid_nr'))
            else:
                # Add
                kwargs['queryset'] = KampioenschapSporterBoog.objects.none()

        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        """ bepaal de relevante keuzemogelijkheden voor specifieke velden
        """
        if db_field.name == 'kampioenschap':
            kwargs['queryset'] = (Kampioenschap
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


class KampioenschapSporterBoogAdmin(CreateOnlyAdmin):

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
            {'fields': ('gemiddelde',
                        'gemiddelde_scores',
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
                        'result_counts',
                        'result_rk_teamscore_1',
                        'result_rk_teamscore_2',
                        'result_bk_teamscore_1',
                        'result_bk_teamscore_2')
             }),
    )

    readonly_fields = ('kampioenschap',
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

    list_filter = ('kampioenschap__competitie',
                   'kampioenschap__deel',
                   'kampioenschap__rayon',
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
        if db_field.name == 'indiv_klasse' and self.obj:
            # alleen klassen laten kiezen van deze competitie
            kwargs['queryset'] = (CompetitieIndivKlasse
                                  .objects
                                  .filter(competitie=self.obj.kampioenschap.competitie)
                                  .order_by('volgorde'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class CompetitieMutatieAdmin(CreateOnlyAdmin):

    readonly_fields = ('mutatie', 'when', 'deelnemer', 'door')

    list_select_related = ('deelnemer__kampioenschap',
                           'deelnemer__kampioenschap__rayon',
                           'deelnemer__indiv_klasse',
                           'deelnemer__sporterboog__sporter',
                           'deelnemer__sporterboog__boogtype')

    list_filter = ('is_verwerkt', 'mutatie')

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
        if self.obj:
            if db_field.name == 'regiocompetitie':
                kwargs['queryset'] = (Regiocompetitie
                                      .objects
                                      .select_related('regio')
                                      .filter(competitie=self.obj.competitie)
                                      .order_by('regio__regio_nr'))
            elif db_field.name == 'kampioenschap':
                # alleen laten kiezen uit de kampioenschappen van deze competitie
                kwargs['queryset'] = (Kampioenschap
                                      .objects
                                      .select_related('rayon')
                                      .filter(competitie=self.obj.competitie)
                                      .order_by('deel',
                                                'rayon__rayon_nr'))
            elif db_field.name in ('team_klasse',):
                # alleen laten kiezen uit de RK/BK team klassen van deze competitie
                kwargs['queryset'] = (CompetitieTeamKlasse
                                      .objects
                                      .filter(competitie=self.obj.competitie,
                                              is_voor_teams_rk_bk=True)
                                      .order_by('volgorde'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class RondeTeamVerFilter(admin.SimpleListFilter):

    title = 'Vereniging'

    parameter_name = 'RondeTeamVer'

    def __init__(self, request, params, model, model_admin):
        # print('init: q=%s' % list(request.GET.items()))
        self.limit_comp = request.GET.get('team__regiocompetitie__competitie__id__exact')
        self.limit_regio = request.GET.get('team__vereniging__regio__regio_nr__exact')
        self.limit_teamtype = request.GET.get('RondeTeamType')
        super().__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin):

        teams = RegiocompetitieTeam.objects.select_related('vereniging')
        if self.limit_comp:
            teams = teams.filter(regiocompetitie__competitie__id=self.limit_comp)
        if self.limit_regio:
            teams = teams.filter(vereniging__regio__regio_nr=self.limit_regio)
        if self.limit_teamtype:
            teams = teams.filter(team_type__afkorting=self.limit_teamtype)

        tups = list()
        for team in teams.order_by('vereniging__ver_nr', 'volg_nr'):
            tups.append((team.pk, team.maak_team_naam()))
        # for
        # print('lookups: aantal=%s' % len(tups))
        return tups

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(team__id=self.value())
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


class RegiocompetitieRondeTeamAdmin(CreateOnlyAdmin):

    filter_horizontal = ('deelnemers_geselecteerd', 'deelnemers_feitelijk')

    readonly_fields = ('feitelijke_scores',)

    list_filter = ('team__regiocompetitie__competitie',
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
        self.deelcomp = None
        self.ver = None

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        """ initialisatie van het admin formulier
            hier "vangen" we het database object waar we mee bezig gaan
        """
        if obj:
            team = obj.team
            self.deelcomp = team.regiocompetitie
            self.ver = team.vereniging
        else:
            self.deelcomp = self.ver = None

        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    # pragma: no cover
        """ bepaal de relevante keuzemogelijkheden voor specifieke velden
        """
        if db_field.name == 'team' and self.deelcomp:
            kwargs['queryset'] = (RegiocompetitieTeam
                                  .objects
                                  .select_related('regiocompetitie',
                                                  'vereniging',
                                                  'team_type')
                                  .filter(regiocompetitie=self.deelcomp)
                                  .order_by('team_naam', 'pk'))
        else:
            kwargs['queryset'] = (RegiocompetitieTeam
                                  .objects
                                  .select_related('regiocompetitie',
                                                  'vereniging',
                                                  'team_type')
                                  .order_by('team_naam',
                                            'pk'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if db_field.name in ('deelnemers_geselecteerd', 'deelnemers_feitelijk'):
            kwargs['widget'] = FilteredSelectMultiple(db_field.verbose_name, False)
            if self.deelcomp and self.ver:
                kwargs['queryset'] = (RegiocompetitieSporterBoog
                                      .objects
                                      .filter(regiocompetitie=self.deelcomp,
                                              bij_vereniging=self.ver,
                                              inschrijf_voorkeur_team=True)
                                      .select_related('sporterboog',
                                                      'sporterboog__sporter',
                                                      'sporterboog__sporter__bij_vereniging',
                                                      'sporterboog__boogtype')
                                      .order_by('sporterboog__sporter__lid_nr'))
            else:
                kwargs['queryset'] = (RegiocompetitieSporterBoog
                                      .objects
                                      .filter(inschrijf_voorkeur_team=True)
                                      .select_related('sporterboog',
                                                      'sporterboog__sporter',
                                                      'sporterboog__sporter__bij_vereniging',
                                                      'sporterboog__boogtype')
                                      .order_by('sporterboog__sporter__lid_nr'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class RegiocompetitieTeamPouleAdmin(CreateOnlyAdmin):

    list_filter = ('regiocompetitie__competitie',
                   'regiocompetitie__regio')

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.deelcomp = None

    def get_form(self, request, obj=None, **kwargs):                    # pragma: no cover
        """ initialisatie van het admin formulier
            hier "vangen" we het database object waar we mee bezig gaan
        """
        if obj:
            self.deelcomp = obj.regiocompetitie
        else:
            self.deelcomp = None

        return super().get_form(request, obj, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):    # pragma: no cover
        if self.deelcomp:
            if db_field.name == 'teams':
                kwargs['widget'] = FilteredSelectMultiple(db_field.verbose_name, False)
                kwargs['queryset'] = (RegiocompetitieTeam
                                      .objects
                                      .filter(regiocompetitie=self.deelcomp))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class KlasseLimietBoogTypeFilter(admin.SimpleListFilter):

    title = 'Boog type'

    parameter_name = 'BoogType'

    def lookups(self, request, model_admin):
        tups = list()
        for indiv_klasse in CompetitieIndivKlasse.objects.distinct('boogtype').select_related('boogtype'):
            boog_type = indiv_klasse.boogtype
            tups.append((boog_type.afkorting, boog_type.beschrijving))
        # for
        return tups

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(indiv_klasse__boogtype__afkorting=self.value())
        return queryset


class KampioenschapIndivKlasseLimietAdmin(CreateOnlyAdmin):

    list_filter = ('kampioenschap__competitie',
                   'kampioenschap__rayon',
                   KlasseLimietBoogTypeFilter)

    list_select_related = ('kampioenschap',
                           'kampioenschap__competitie',
                           'kampioenschap__rayon',
                           'indiv_klasse')

    readonly_fields = ('kampioenschap',
                       'indiv_klasse')

    ordering = ('indiv_klasse__volgorde',)


class KampioenschapTeamKlasseLimietAdmin(CreateOnlyAdmin):

    list_filter = ('kampioenschap__competitie',
                   'kampioenschap__rayon',
                   'team_klasse__team_afkorting')

    list_select_related = ('kampioenschap',
                           'kampioenschap__competitie',
                           'kampioenschap__rayon',
                           'team_klasse')

    readonly_fields = ('kampioenschap',
                       'team_klasse')

    ordering = ('team_klasse__volgorde',)


admin.site.register(Competitie, CompetitieAdmin)
admin.site.register(CompetitieIndivKlasse, CompetitieIndivKlasseAdmin)
admin.site.register(CompetitieTeamKlasse, CompetitieTeamKlasseAdmin)
admin.site.register(CompetitieMatch, CompetitieMatchAdmin)
admin.site.register(CompetitieMutatie, CompetitieMutatieAdmin)

admin.site.register(Regiocompetitie, RegiocompetitieAdmin)
admin.site.register(RegiocompetitieRonde, RegiocompetitieRondeAdmin)
admin.site.register(RegiocompetitieSporterBoog, RegiocompetitieSporterBoogAdmin)
admin.site.register(RegiocompetitieTeam, RegiocompetitieTeamAdmin)
admin.site.register(RegiocompetitieTeamPoule, RegiocompetitieTeamPouleAdmin)
admin.site.register(RegiocompetitieRondeTeam, RegiocompetitieRondeTeamAdmin)

admin.site.register(Kampioenschap, KampioenschapAdmin)
admin.site.register(KampioenschapSporterBoog, KampioenschapSporterBoogAdmin)
admin.site.register(KampioenschapTeam, KampioenschapTeamAdmin)
admin.site.register(KampioenschapIndivKlasseLimiet, KampioenschapIndivKlasseLimietAdmin)
admin.site.register(KampioenschapTeamKlasseLimiet, KampioenschapTeamKlasseLimietAdmin)

# end of file
