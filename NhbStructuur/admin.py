# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import NhbRayon, NhbRegio, NhbLid, NhbVereniging


class NhbLidAdmin(admin.ModelAdmin):
    """ Admin configuratie voor NhbLid klasse """
    ordering = ('nhb_nr',)


class NhbVerenigingAdmin(admin.ModelAdmin):
    """ Admin configuratie voor NhbVereniging klasse """
    ordering = ('nhb_nr',)


class NhbRayonAdmin(admin.ModelAdmin):
    """ Admin configuratie voor NhbRayon klasse """
    ordering = ('rayon_nr',)


class NhbRegioAdmin(admin.ModelAdmin):
    """ Admin configuratie voor NhbRegio klasse """
    ordering = ('regio_nr',)


admin.site.register(NhbLid, NhbLidAdmin)
admin.site.register(NhbVereniging, NhbVerenigingAdmin)

# NhbRayon en NhbRegio zijn hard-coded, dus geen admin interface
# hard-coded data: zie NhbStructuur/migrations/m0002_nhbstructuur_2018
# bij voorkeur weglaten
admin.site.register(NhbRayon, NhbRayonAdmin)
admin.site.register(NhbRegio, NhbRegioAdmin)

# end of file
