# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Records.models import IndivRecord, BesteIndivRecords, AnderRecord


class IndivRecordAdmin(admin.ModelAdmin):

    """ Admin configuratie voor Records.IndivRecord klasse """

    search_fields = ('naam', 'plaats', 'score', 'volg_nr')

    # filter mogelijkheid
    list_filter = ('discipline', 'soort_record', 'geslacht', 'leeftijdscategorie', 'materiaalklasse', 'verbeterbaar',
                   'is_european_record', 'is_world_record')

    autocomplete_fields = ('sporter',)


class BesteIndivRecordsAdmin(admin.ModelAdmin):

    # filter mogelijkheid
    list_filter = ('discipline', 'soort_record', 'geslacht', 'leeftijdscategorie', 'materiaalklasse')


class AnderRecordAdmin(admin.ModelAdmin):

    pass


admin.site.register(IndivRecord, IndivRecordAdmin)
admin.site.register(BesteIndivRecords, BesteIndivRecordsAdmin)
admin.site.register(AnderRecord, AnderRecordAdmin)

# end of file
