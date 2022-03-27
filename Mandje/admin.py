# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import MandjeInhoud, MandjeTransactie


class MandjeInhoudAdmin(admin.ModelAdmin):

    readonly_fields = ('account', 'inschrijving')


class MandjeTransactieAdmin(admin.ModelAdmin):

    pass


admin.site.register(MandjeInhoud, MandjeInhoudAdmin)
admin.site.register(MandjeTransactie, MandjeTransactieAdmin)

# end of file
