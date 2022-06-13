# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import Score, ScoreHist, Uitslag


class ScoreAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Score klasse """
    
    list_filter = ('afstand_meter',
                   'type',
                   'sporterboog__boogtype',
                   'sporterboog__sporter__bij_vereniging')

    list_select_related = ('sporterboog',
                           'sporterboog__sporter',
                           'sporterboog__boogtype')

    autocomplete_fields = ('sporterboog',)

    # velden die niet gewijzigd mogen worden via de admin interface
    readonly_fields = ('geschiedenis', )

    search_fields = ('sporterboog__sporter__lid_nr',)

    @staticmethod
    def geschiedenis(obj):     # pragma: no cover
        return "\n".join([str(scorehist) for scorehist in obj.scorehist_set.all()])


class ScoreHistAdmin(admin.ModelAdmin):
    """ Admin configuratie voor ScoreHist klasse """

    list_filter = ('when', 'score__afstand_meter')

    # voorkom trage admin interface (lange lijstjes die veel queries kosten)
    readonly_fields = ('score', 'door_account', 'when')

    list_select_related = ('door_account',)


class UitslagAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Uitslag klasse """

    list_filter = ('afstand', )

    readonly_fields = ('scores', )


admin.site.register(Score, ScoreAdmin)
admin.site.register(ScoreHist, ScoreHistAdmin)
admin.site.register(Uitslag, UitslagAdmin)

# end of file
