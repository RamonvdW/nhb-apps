# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import Functie


class FunctieAdmin(admin.ModelAdmin):
    filter_horizontal = ('accounts',)
    ordering = ('beschrijving',)
    search_fields = ('beschrijving', 'nhb_ver__naam', 'nhb_ver__plaats')


admin.site.register(Functie, FunctieAdmin)

# end of file
