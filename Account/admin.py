# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext, gettext_lazy as _
from .models import Account, AccountEmail, HanterenPersoonsgegevens


class AccountAdmin(UserAdmin):
    # volgorde van de velden in de admin site
    exclude = ('email', 'last_name')

    readonly_fields = ('is_staff', )

    # volgorde van de te tonen velden
    fieldsets = (
        (None, {'fields': ('username', 'password', 'vraag_nieuw_wachtwoord')}),
        (_('Personal info'), {'fields': ('first_name', )}),
        (_('Coupling'), {'fields': ('nhblid',)}),
        (_('Important dates'), {'fields': ('laatste_inlog_poging', 'last_login', 'date_joined')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_BKO', 'is_staff', 'groups', 'user_permissions'),
        }),
        (_('OTP'), { 'fields': ('otp_code', 'otp_is_actief')}),
        (_('Beveiliging'), {'fields': ('verkeerd_wachtwoord_teller', 'is_geblokkeerd_tot')})
    )

    list_display = ('username', 'last_login', 'is_staff')


admin.site.register(Account, AccountAdmin)
admin.site.register(AccountEmail)
admin.site.register(HanterenPersoonsgegevens)

# end of file
