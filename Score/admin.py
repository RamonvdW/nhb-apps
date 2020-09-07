# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import Score, ScoreHist


class ScoreAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Score klasse """
    list_filter = ('afstand_meter',
                   'is_ag',
                   'schutterboog__boogtype',
                   'schutterboog__nhblid__bij_vereniging')

    list_select_related = ('schutterboog',
                           'schutterboog__nhblid',
                           'schutterboog__boogtype')

    autocomplete_fields = ('schutterboog',)

    # velden die niet gewijzigd mogen worden via de admin interface
    readonly_fields = ('geschiedenis', )

    @staticmethod
    def geschiedenis(obj):     # pragma: no cover
        return "\n".join([str(scorehist) for scorehist in obj.scorehist_set.all()])


class ScoreHistAdmin(admin.ModelAdmin):
    """ Admin configuratie voor ScoreHist klasse """
    list_filter = ('when', 'score__afstand_meter')


admin.site.register(Score, ScoreAdmin)
admin.site.register(ScoreHist, ScoreHistAdmin)

# end of file
