# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import Sporter, SporterVoorkeuren, SporterBoog, Secretaris, Speelsterkte


class SporterAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Sporter klasse """

    ordering = ('lid_nr',)

    search_fields = ('unaccented_naam', 'lid_nr')

    # filter mogelijkheid
    list_filter = ('geslacht', 'para_classificatie', 'is_actief_lid')

    list_select_related = True


class SporterBoogAdmin(admin.ModelAdmin):
    """ Admin configuratie voor SporterBoog klasse """

    search_fields = ('sporter__lid_nr', 'sporter__unaccented_naam')

    list_select_related = True

    autocomplete_fields = ('sporter',)


class SporterVoorkeurenAdmin(admin.ModelAdmin):
    """ Admin configuratie voor SporterVoorkeuren klasse """

    search_fields = ('sporter__lid_nr', 'sporter__unaccented_naam')

    list_select_related = True

    autocomplete_fields = ('sporter',)


class SecretarisAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Secretaris klasse """

    # TODO: alleen leden van de eigen vereniging laten kiezen

    search_fields = ('vereniging__ver_nr', 'vereniging__naam',)

    list_filter = ('vereniging',)

    list_select_related = True

    auto_complete = ('vereniging', 'sporter')


class SpeelsterkteAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Speelsterkte klasse """

    search_fields = ('beschrijving', 'category', 'discipline', 'sporter__unaccented_naam')

    list_filter = ('discipline', 'beschrijving', 'category')

    readonly_fields = ('sporter',)

    list_select_related = True


admin.site.register(Sporter, SporterAdmin)
admin.site.register(SporterBoog, SporterBoogAdmin)
admin.site.register(SporterVoorkeuren, SporterVoorkeurenAdmin)
admin.site.register(Secretaris, SecretarisAdmin)
admin.site.register(Speelsterkte, SpeelsterkteAdmin)

# end of file
