# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Account, AccountEmail, HanterenPersoonsgegevens


class AccountAdmin(UserAdmin):
    # volgorde van de velden in de admin site
    exclude = ('email', )

    # velden die niet gewijzigd mogen worden via de admin interface
    readonly_fields = ('is_staff', )

    # volgorde van de te tonen velden
    fieldsets = (
        (None, {'fields': ('username', 'password', 'vraag_nieuw_wachtwoord')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('2FA'), {'fields': ('otp_code', 'otp_is_actief')}),
        (_('Permissions'), {'fields': ('is_active', 'is_BB', 'is_Observer', 'is_staff')}),
        (_('Beveiliging'), {'fields': ('verkeerd_wachtwoord_teller', 'is_geblokkeerd_tot')}),
        (_('Important dates'), {'fields': ('laatste_inlog_poging', 'last_login', 'date_joined')}),
    )

    list_display = ('get_account_full_name', 'last_login', 'is_staff')

    list_filter = ('is_staff', 'is_BB', 'otp_is_actief')

    # velden om in te zoeken (in de lijst)
    search_fields = ('username', 'nhblid__voornaam', 'nhblid__achternaam')


class AccountEmailAdmin(admin.ModelAdmin):

    # velden om in te zoeken (in de lijst)
    search_fields = ('account__username',)

    list_filter = ('email_is_bevestigd',)


admin.site.register(Account, AccountAdmin)
admin.site.register(AccountEmail, AccountEmailAdmin)
admin.site.register(HanterenPersoonsgegevens)

# end of file
