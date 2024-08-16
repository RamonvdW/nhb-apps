# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Evenement.models import Evenement, EvenementInschrijving


class EvenementAdmin(admin.ModelAdmin):
    pass


class EvenementInschrijvingAdmin(admin.ModelAdmin):
    pass


admin.site.register(Evenement, EvenementAdmin)
admin.site.register(EvenementInschrijving, EvenementInschrijvingAdmin)

# end of file
