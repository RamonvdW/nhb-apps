# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

# all klassen zijn hard-coded
from .models import (BoogType, TeamType, LeeftijdsKlasse,
                     TemplateCompetitieIndivKlasse, TemplateCompetitieTeamKlasse,
                     KalenderWedstrijdklasse)


class BasisTypenReadonlyAdmin(admin.ModelAdmin):
    """ Simpel admin model om alles read-only te maken """
    def has_change_permission(self, request, obj=None):
        return False            # pragma: no cover

    def has_add_permission(self, request, obj=None):
        return False            # pragma: no cover

    def has_delete_permission(self, request, obj=None):
        return False            # pragma: no cover


class BasisTypenReadonlyMetVolgordeAdmin(BasisTypenReadonlyAdmin):

    ordering = ('-volgorde',)       # oudste bovenaan

    list_filter = ('organisatie',)


class BoogTypeAdmin(BasisTypenReadonlyAdmin):

    ordering = ('volgorde',)        # alfanumeriek

    list_filter = ('organisatie', 'buiten_gebruik')


class BasisTypenLeeftijdsKlasseAdmin(BasisTypenReadonlyMetVolgordeAdmin):

    list_filter = ('organisatie', 'wedstrijd_geslacht',)


class BasisTypenTemplateCompetitieIndivKlasseAdmin(BasisTypenReadonlyMetVolgordeAdmin):
    """ filter voor TemplateCompetitieIndivKlasse """

    # lijstweergave
    list_filter = ('buiten_gebruik', 'boogtype', 'is_aspirant_klasse')

    list_select_related = ('boogtype',)

    ordering = ('volgorde',)

    # record weergave
    fieldsets = (
        (None, {'fields': ('volgorde', 'beschrijving', 'boogtype', 'buiten_gebruik')}),
        ('Details', {'fields': ('leeftijdsklassen', 'is_aspirant_klasse', 'is_onbekend', 'niet_voor_rk_bk', )}),
        ('Blazoenen Indoor', {'fields': ('blazoen1_18m_regio', 'blazoen2_18m_regio', 'blazoen_18m_rk_bk')}),
        ('Blazoenen 25m 1pijl', {'fields': ('blazoen1_25m_regio', 'blazoen2_25m_regio', 'blazoen_25m_rk_bk')})
    )

    @staticmethod
    def _leeftijdsklassen(instance):
        """ formatteer de read-only lijst van leeftijdsklassen onder elkaar
            wordt alleen gebruikt in de admin interface
        """
        html = ""
        for lkl in instance.leeftijdsklassen.all():
            html += '<p>' + format_html(str(lkl)) + '</p>'
        return mark_safe(html)


class BasisTypenTemplateCompetitieTeamKlasseAdmin(BasisTypenReadonlyMetVolgordeAdmin):
    """ filter voor TemplateCompetitieTeamKlasse """

    # lijstweergave
    list_filter = ('buiten_gebruik',)

    list_select_related = ('team_type',)

    ordering = ('volgorde',)

    # record weergave
    fieldsets = (
        (None, {'fields': ('volgorde', 'beschrijving', 'team_type', 'buiten_gebruik')}),
        ('Blazoenen Indoor', {'fields': ('blazoen1_18m_regio', 'blazoen2_18m_regio', 'blazoen1_18m_rk_bk', 'blazoen2_18m_rk_bk')}),
        ('Blazoenen 25m 1pijl', {'fields': ('blazoen1_25m_regio', 'blazoen2_25m_regio', 'blazoen_25m_rk_bk')})
    )


class BasisTypenKalenderWedstrijdklasseAdmin(BasisTypenReadonlyMetVolgordeAdmin):

    ordering = ('volgorde',)

    list_filter = ('organisatie', 'boogtype', 'leeftijdsklasse__klasse_kort', 'leeftijdsklasse__wedstrijd_geslacht')

    # record weergave
    fieldsets = (
        (None, {'fields': ('organisatie', 'beschrijving', 'volgorde', 'boogtype', 'leeftijdsklasse', 'afkorting', 'buiten_gebruik')}),
    )


admin.site.register(BoogType, BoogTypeAdmin)
admin.site.register(TeamType, BasisTypenReadonlyMetVolgordeAdmin)
admin.site.register(LeeftijdsKlasse, BasisTypenLeeftijdsKlasseAdmin)
admin.site.register(TemplateCompetitieIndivKlasse, BasisTypenTemplateCompetitieIndivKlasseAdmin)
admin.site.register(TemplateCompetitieTeamKlasse, BasisTypenTemplateCompetitieTeamKlasseAdmin)
admin.site.register(KalenderWedstrijdklasse, BasisTypenKalenderWedstrijdklasseAdmin)

# end of file
