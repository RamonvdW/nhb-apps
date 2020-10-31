# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import Taak


class TaakAdmin(admin.ModelAdmin):

    """ Admin configuratie voor Taak klasse """

    list_filter = ('is_afgerond',)

    list_select_related = ('toegekend_aan',
                           'aangemaakt_door')

    autocomplete_fields = ('toegekend_aan',
                           'aangemaakt_door')


admin.site.register(Taak, TaakAdmin)

# end of file
