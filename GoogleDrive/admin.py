# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from GoogleDrive.models import Transactie, Token


class TransactieAdmin(admin.ModelAdmin):

    list_filter = ('has_been_used',)

    ordering = ('-when',)


admin.site.register(Transactie, TransactieAdmin)
admin.site.register(Token)

# end of file
