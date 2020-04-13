# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin

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


class BasisTypenWedstrijdklasseAdmin(BasisTypenReadonlyAdmin):
    """ filter voor IndivWedstrijdklasse en TeamWedstrijdklasse """
    list_filter = ('buiten_gebruik',)


admin.site.register(BoogType, BasisTypenReadonlyAdmin)
admin.site.register(LeeftijdsKlasse, BasisTypenReadonlyAdmin)
admin.site.register(IndivWedstrijdklasse, BasisTypenWedstrijdklasseAdmin)
admin.site.register(TeamWedstrijdklasse, BasisTypenWedstrijdklasseAdmin)

# end of file
