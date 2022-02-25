# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import SiteTijdelijkeUrl


class SiteTijdelijkeUrlAdmin(admin.ModelAdmin):

    # readonly voorkomt inladen van lange lijst met mogelijkheden
    # dit is ook meteen de volgorde waarin ze getoond worden
    readonly_fields = ('hoortbij_accountemail',
                       'hoortbij_functie',
                       'hoortbij_kampioenschap')

    list_select_related = ('hoortbij_functie',
                           'hoortbij_accountemail',
                           'hoortbij_accountemail__account')


admin.site.register(SiteTijdelijkeUrl, SiteTijdelijkeUrlAdmin)

# end of file
