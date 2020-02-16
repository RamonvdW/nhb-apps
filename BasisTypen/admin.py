# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin

# all klassen zijn hard-coded
# --> zie migrations/m0002_basistypen_2018
from .models import BoogType, TeamType, WedstrijdKlasse, LeeftijdsKlasse, TeamTypeBoog, WedstrijdKlasseBoog, WedstrijdKlasseLeeftijd


class BasisTypenReadonlyAdmin(admin.ModelAdmin):
    """ Simpel admin model om alles read-only te maken """
    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


class BasisTypenWedstrijdKlasseAdmin(BasisTypenReadonlyAdmin):
    """ filter voor WedstrijdKlasse """
    list_filter = ('buiten_gebruik',)


class BasisTypenWedstrijdKlasseBoogAdmin(BasisTypenReadonlyAdmin):
    """ filter voor WedstrijdKlasseBoog """
    list_filter = ('wedstrijdklasse__buiten_gebruik',)


class BasisTypenWedstrijdKlasseLeeftijdAdmin(BasisTypenReadonlyAdmin):
    """ filter voor WedstrijdKlasseLeeftijd """
    list_filter = ('wedstrijdklasse__buiten_gebruik',)



admin.site.register(BoogType, BasisTypenReadonlyAdmin)
admin.site.register(TeamType, BasisTypenReadonlyAdmin)
admin.site.register(WedstrijdKlasse, BasisTypenWedstrijdKlasseAdmin)
admin.site.register(LeeftijdsKlasse, BasisTypenReadonlyAdmin)
admin.site.register(TeamTypeBoog, BasisTypenReadonlyAdmin)
admin.site.register(WedstrijdKlasseBoog, BasisTypenWedstrijdKlasseBoogAdmin)
admin.site.register(WedstrijdKlasseLeeftijd, BasisTypenWedstrijdKlasseLeeftijdAdmin)

# end of file
