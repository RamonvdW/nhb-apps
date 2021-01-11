# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import HistCompetitie, HistCompetitieIndividueel, HistCompetitieTeam


class HistCompetitieAdmin(admin.ModelAdmin):

    list_filter = ('seizoen', 'comp_type')


class HistCompetitieIndividueelAdmin(admin.ModelAdmin):
    search_fields = ('schutter_nr', 'schutter_naam')

    # filter mogelijkheid
    list_filter = ('histcompetitie', 'boogtype')


admin.site.register(HistCompetitie, HistCompetitieAdmin)
admin.site.register(HistCompetitieIndividueel, HistCompetitieIndividueelAdmin)
admin.site.register(HistCompetitieTeam)

# end of file
