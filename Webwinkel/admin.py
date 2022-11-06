# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Webwinkel.models import WebwinkelFoto, WebwinkelProduct


class WebwinkelFotoAdmin(admin.ModelAdmin):

    # autocomplete_fields = ('voor_wedstrijden', 'voor_sporter', 'voor_vereniging', 'uitgegeven_door')
    pass


class WebwinkelProductAdmin(admin.ModelAdmin):

    # readonly_fields = ('wanneer', 'wedstrijd', 'sessie', 'sporterboog', 'koper')

    # list_filter = ('status',)

    #autocomplete_fields = ()

    search_fields = ('omslag_titel',)

    filter_horizontal = ('fotos',)


admin.site.register(WebwinkelFoto, WebwinkelFotoAdmin)
admin.site.register(WebwinkelProduct, WebwinkelProductAdmin)

# end of file
