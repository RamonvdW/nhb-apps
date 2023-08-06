# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from TijdelijkeCodes.models import TijdelijkeCode


class TijdelijkeUrlAdmin(admin.ModelAdmin):

    # readonly voorkomt inladen van lange lijst met mogelijkheden
    # dit is ook meteen de volgorde waarin ze getoond worden
    readonly_fields = ('hoort_bij_account',
                       'hoort_bij_functie',
                       'hoort_bij_gast_reg',
                       'hoort_bij_kampioen')

    list_select_related = ('hoort_bij_functie', 'hoort_bij_account', 'hoort_bij_gast_reg', 'hoort_bij_kampioen')


admin.site.register(TijdelijkeCode, TijdelijkeUrlAdmin)

# end of file
