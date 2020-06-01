# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import LogboekRegel


class LogboekRegelAdmin(admin.ModelAdmin):
    list_select_related = ('actie_door_account',)


admin.site.register(LogboekRegel, LogboekRegelAdmin)

# end of file
