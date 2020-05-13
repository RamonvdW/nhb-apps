# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from django.utils.html import format_html_join, format_html
from django.utils.safestring import mark_safe

# all klassen zijn hard-coded
# --> zie migrations/m0008_basistypen_2020
from .models import BoogType, LeeftijdsKlasse, IndivWedstrijdklasse, TeamWedstrijdklasse


class BasisTypenReadonlyAdmin(admin.ModelAdmin):
    """ Simpel admin model om alles read-only te maken """
    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class BasisTypenIndivWedstrijdklasseAdmin(BasisTypenReadonlyAdmin):
    """ filter voor IndivWedstrijdklasse """

    # lijstweergave
    list_filter = ('buiten_gebruik',)
    ordering = ('volgorde',)

    # record weergave
    fieldsets = (
        (None, {'fields': ('beschrijving', 'boogtype', 'is_onbekend', '_leeftijdsklassen', 'niet_voor_rk_bk', 'volgorde', 'buiten_gebruik')}),
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


class BasisTypenTeamWedstrijdklasseAdmin(BasisTypenReadonlyAdmin):
    """ filter voor TeamWedstrijdklasse """

    # lijstweergave
    list_filter = ('buiten_gebruik',)
    ordering = ('volgorde',)

    # record weergave
    fieldsets = (
        (None, {'fields': ('beschrijving', '_boogtypen', 'volgorde', 'buiten_gebruik')}),
    )

    @staticmethod
    def _boogtypen(instance):
        """ formatteer de read-only lijst van boogtypen onder elkaar
            wordt alleen gebruikt in de admin interface
        """
        html = ""
        for boogtype in instance.boogtypen.all():
            html += '<p>' + format_html(str(boogtype)) + '</p>'
        return mark_safe(html)


admin.site.register(BoogType, BasisTypenReadonlyAdmin)
admin.site.register(LeeftijdsKlasse, BasisTypenReadonlyAdmin)
admin.site.register(IndivWedstrijdklasse, BasisTypenIndivWedstrijdklasseAdmin)
admin.site.register(TeamWedstrijdklasse, BasisTypenTeamWedstrijdklasseAdmin)

# end of file
