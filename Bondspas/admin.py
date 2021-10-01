# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Bondspas.models import Bondspas


class BondspasAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Sporter klasse """

    ordering = ('lid_nr',)

    search_fields = ('lid_nr',)

    # filter mogelijkheid
    list_filter = ('status',)


admin.site.register(Bondspas, BondspasAdmin)

# end of file
