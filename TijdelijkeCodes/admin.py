# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from TijdelijkeCodes.models import TijdelijkeCode


class TijdelijkeUrlAdmin(admin.ModelAdmin):

    # readonly voorkomt inladen van lange lijst met mogelijkheden
    # dit is ook meteen de volgorde waarin ze getoond worden
    readonly_fields = ('hoortbij_account',
                       'hoortbij_functie',
                       'hoortbij_kampioenschap')

    list_select_related = ('hoortbij_functie', 'hoortbij_account')


admin.site.register(TijdelijkeCode, TijdelijkeUrlAdmin)

# end of file
