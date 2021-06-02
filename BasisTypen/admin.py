# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

# all klassen zijn hard-coded
from .models import (BoogType, TeamType, LeeftijdsKlasse,
                     IndivWedstrijdklasse, TeamWedstrijdklasse,
                     KalenderWedstrijdklasse)


class BasisTypenReadonlyAdmin(admin.ModelAdmin):
    """ Simpel admin model om alles read-only te maken """
    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class BasisTypenReadonlyMetVolgordeAdmin(BasisTypenReadonlyAdmin):
    ordering = ('volgorde',)


class BasisTypenIndivWedstrijdklasseAdmin(BasisTypenReadonlyMetVolgordeAdmin):
    """ filter voor IndivWedstrijdklasse """

    # lijstweergave
    list_filter = ('buiten_gebruik',)

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


class BasisTypenTeamWedstrijdklasseAdmin(BasisTypenReadonlyMetVolgordeAdmin):
    """ filter voor TeamWedstrijdklasse """

    # lijstweergave
    list_filter = ('buiten_gebruik',)

    # record weergave
    fieldsets = (
        (None, {'fields': ('beschrijving', 'team_type', 'volgorde', 'buiten_gebruik')}),
    )


class BasisTypenKalenderWedstrijdklasseAdmin(BasisTypenReadonlyMetVolgordeAdmin):

    list_filter = ('boogtype', 'leeftijdsklasse__klasse_kort')


admin.site.register(BoogType, BasisTypenReadonlyMetVolgordeAdmin)
admin.site.register(TeamType, BasisTypenReadonlyMetVolgordeAdmin)
admin.site.register(LeeftijdsKlasse, BasisTypenReadonlyMetVolgordeAdmin)
admin.site.register(IndivWedstrijdklasse, BasisTypenIndivWedstrijdklasseAdmin)
admin.site.register(TeamWedstrijdklasse, BasisTypenTeamWedstrijdklasseAdmin)
admin.site.register(KalenderWedstrijdklasse, BasisTypenKalenderWedstrijdklasseAdmin)

# end of file
