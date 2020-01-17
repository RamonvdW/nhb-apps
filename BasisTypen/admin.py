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


admin.site.register(BoogType, BasisTypenReadonlyAdmin)
admin.site.register(TeamType, BasisTypenReadonlyAdmin)
admin.site.register(WedstrijdKlasse, BasisTypenReadonlyAdmin)
admin.site.register(LeeftijdsKlasse, BasisTypenReadonlyAdmin)
admin.site.register(TeamTypeBoog, BasisTypenReadonlyAdmin)
admin.site.register(WedstrijdKlasseBoog, BasisTypenReadonlyAdmin)
admin.site.register(WedstrijdKlasseLeeftijd, BasisTypenReadonlyAdmin)

# end of file
