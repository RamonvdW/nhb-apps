# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Webwinkel.models import WebwinkelFoto, WebwinkelProduct, WebwinkelKeuze


class WebwinkelFotoAdmin(admin.ModelAdmin):
    pass


class WebwinkelProductAdmin(admin.ModelAdmin):

    search_fields = ('omslag_titel',)

    filter_horizontal = ('fotos',)

    ordering = ('volgorde',)


class WebwinkelKeuzeAdmin(admin.ModelAdmin):

    list_filter = ('status',)


admin.site.register(WebwinkelFoto, WebwinkelFotoAdmin)
admin.site.register(WebwinkelProduct, WebwinkelProductAdmin)
admin.site.register(WebwinkelKeuze, WebwinkelKeuzeAdmin)

# end of file
