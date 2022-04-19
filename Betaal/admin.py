# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import BetaalInstellingenVereniging, BetaalActief, BetaalTransactie, BetaalMutatie


class BetaalTransactieAdmin(admin.ModelAdmin):

    search_fields = ('payment_id', 'beschrijving')


class BetaalActiefAdmin(admin.ModelAdmin):

    search_fields = ('payment_id',)


class BetaalInstellingenVerenigingAdmin(admin.ModelAdmin):

    search_fields = ('vereniging__ver_nr', 'vereniging__naam')


class BetaalMutatieAdmin(admin.ModelAdmin):

    pass


admin.site.register(BetaalInstellingenVereniging, BetaalInstellingenVerenigingAdmin)
admin.site.register(BetaalActief, BetaalActiefAdmin)
admin.site.register(BetaalTransactie, BetaalTransactieAdmin)
admin.site.register(BetaalMutatie, BetaalMutatieAdmin)

# end of file
