# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from GoogleDrive.models import Transactie, Token, Bestand


class TransactieAdmin(admin.ModelAdmin):

    list_filter = ('has_been_used',)

    ordering = ('-when',)


class BestandAdmin(admin.ModelAdmin):

    list_filter = ('afstand', 'is_teams', 'is_bk')


admin.site.register(Transactie, TransactieAdmin)
admin.site.register(Token)
admin.site.register(Bestand, BestandAdmin)

# end of file
