# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from django.forms import ModelForm, Textarea
from Logboek.models import LogboekRegel


class LogboekRegelForm(ModelForm):

    class Meta:
        model = LogboekRegel
        fields = '__all__'
        widgets = {
            'activiteit': Textarea(attrs={'cols': 100, 'rows': 8}),
        }


class LogboekRegelAdmin(admin.ModelAdmin):

    list_select_related = ('actie_door_account',)

    list_filter = ('gebruikte_functie',)

    search_fields = ('activiteit', 'actie_door_account__username')

    form = LogboekRegelForm


admin.site.register(LogboekRegel, LogboekRegelAdmin)

# end of file
