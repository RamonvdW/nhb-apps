# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import IndivRecord


class IndivRecordAdmin(admin.ModelAdmin):
    """ Admin configuratie voor NhbLid klasse """
    search_fields = ('naam', 'plaats', 'score', 'volg_nr')

    # filter mogelijkheid
    list_filter = ('discipline', 'soort_record', 'geslacht', 'leeftijdscategorie', 'materiaalklasse')

admin.site.register(IndivRecord, IndivRecordAdmin)


# end of file
