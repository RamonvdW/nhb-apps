# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from django.db.models import Count
from Account.models import Account
from GoogleDrive.models import Transactie, Token, Bestand


class TransactieAdmin(admin.ModelAdmin):

    list_filter = ('has_been_used',)

    ordering = ('-when',)


class BestandAdmin(admin.ModelAdmin):

    list_filter = ('afstand', 'is_teams', 'is_bk')

    exclude = ('gedeeld_met',)

    readonly_fields = ('my_gedeeld_met',)

    def my_gedeeld_met(self, obj):          # pragma: no cover
        met = list()
        for account in obj.gedeeld_met.all():
            msg = '[%s] %s / %s' % (account.username, account.volledige_naam(), account.bevestigde_email)
            met.append(msg)
        # for
        if len(met) == 0:
            msg = 'niemand'
        else:
            msg = "\n".join(met)
        return msg

    my_gedeeld_met.short_description = 'Bestand is gedeeld met'

admin.site.register(Transactie, TransactieAdmin)
admin.site.register(Token)
admin.site.register(Bestand, BestandAdmin)

# end of file
