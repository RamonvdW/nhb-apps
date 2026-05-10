# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from BasisTypen.definities import SCHEIDS_NIET
from Competitie.models import (Competitie,
                               CompetitieIndivKlasse, CompetitieTeamKlasse,
                               CompetitieMatch,
                               CompetitieMutatie)
from CompLaagBond.models import KampBK
from CompLaagRayon.models import KampRK
from CompLaagRegio.models import RegioComp
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


class CompetitieMutatieAdmin(CreateOnlyAdmin):

    readonly_fields = ('mutatie', 'when', 'deelnemer_rk', 'deelnemer_bk', 'kamp_rk', 'kamp_bk', 'door')

    list_select_related = ('deelnemer_rk__kamp',
                           'deelnemer_rk__kamp__rayon',
                           'deelnemer_rk__indiv_klasse',
                           'deelnemer_rk__sporterboog__sporter',
                           'deelnemer_rk__sporterboog__boogtype',
                           'deelnemer_bk__kamp',
                           'deelnemer_bk__indiv_klasse',
                           'deelnemer_bk__sporterboog__sporter',
                           'deelnemer_bk__sporterboog__boogtype'
                           )

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
            if db_field.name == 'regiocomp':
                kwargs['queryset'] = (RegioComp
                                      .objects
                                      .select_related('regio')
                                      .filter(competitie=self.obj.competitie)
                                      .order_by('regio__regio_nr'))

            elif db_field.name == 'kamp_rk':
                # alleen laten kiezen uit de kampioenschappen van deze competitie
                kwargs['queryset'] = (KampRK
                                      .objects
                                      .select_related('rayon')
                                      .filter(competitie=self.obj.competitie)
                                      .order_by('rayon__rayon_nr'))

            elif db_field.name == 'kamp_bk':
                # alleen laten kiezen uit de kampioenschappen van deze competitie
                kwargs['queryset'] = (KampBK
                                      .objects
                                      .filter(competitie=self.obj.competitie))

            elif db_field.name in ('team_klasse',):
                # alleen laten kiezen uit de RK/BK team klassen van deze competitie
                kwargs['queryset'] = (CompetitieTeamKlasse
                                      .objects
                                      .filter(competitie=self.obj.competitie,
                                              is_voor_teams_rk_bk=True)
                                      .order_by('volgorde'))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Competitie, CompetitieAdmin)
admin.site.register(CompetitieIndivKlasse, CompetitieIndivKlasseAdmin)
admin.site.register(CompetitieTeamKlasse, CompetitieTeamKlasseAdmin)
admin.site.register(CompetitieMatch, CompetitieMatchAdmin)
admin.site.register(CompetitieMutatie, CompetitieMutatieAdmin)

# end of file
