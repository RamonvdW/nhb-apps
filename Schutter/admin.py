# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import SchutterVoorkeuren, SchutterBoog


class SchutterBoogAdmin(admin.ModelAdmin):
    """ Admin configuratie voor SchutterBoog klasse """
    search_fields = ('nhblid__nhb_nr', 'nhblid__voornaam', 'nhblid__achternaam')

    list_select_related = True

    autocomplete_fields = ('nhblid',)


class SchutterVoorkeurenAdmin(admin.ModelAdmin):
    """ Admin configuratie voor SchutterVoorkeuren klasse """

    list_select_related = True

    autocomplete_fields = ('nhblid',)

    search_fields = ('nhblid__nhb_nr', 'nhblid__voornaam', 'nhblid__achternaam')


admin.site.register(SchutterBoog, SchutterBoogAdmin)
admin.site.register(SchutterVoorkeuren, SchutterVoorkeurenAdmin)

# end of file
