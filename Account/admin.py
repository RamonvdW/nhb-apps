# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext, gettext_lazy as _
from .models import Account, AccountEmail, LogboekRegel, HanterenPersoonsgegevens


class AccountAdmin(UserAdmin):
    # volgorde van de velden in de admin site
    exclude = ('email', 'last_name')

    # volgorde van de te tonen velden
    fieldsets = (
        (None, {'fields': ('username', 'password', 'vraag_nieuw_wachtwoord')}),
        (_('Personal info'), {'fields': ('first_name', 'is_voltooid', 'extra_info_pogingen')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )


admin.site.register(Account, AccountAdmin)
admin.site.register(AccountEmail)
admin.site.register(LogboekRegel)
admin.site.register(HanterenPersoonsgegevens)

# end of file
