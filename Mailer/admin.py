# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import MailQueue


class MailQueueAdmin(admin.ModelAdmin):
    search_fields = ('mail_to',)


admin.site.register(MailQueue, MailQueueAdmin)

# end of file
