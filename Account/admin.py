# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from Account.models import Account, AccountVerzoekenTeller


class AccountAdmin(UserAdmin):

    # volgorde van de velden in de admin site
    exclude = ('email', )

    # velden die niet gewijzigd mogen worden via de admin interface
    readonly_fields = ('is_staff', 'is_superuser', 'gekoppelde_functies', 'otp_controle_gelukt_op',
                       'date_joined', 'last_login', 'laatste_inlog_poging')

    # volgorde van de te tonen velden
    fieldsets = (
        (None, {'fields': ('username',)}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'unaccented_naam')}),
        (_('Email'), {'fields': ('email_is_bevestigd', 'bevestigde_email', 'nieuwe_email',
                                 'optout_nieuwe_taak', 'optout_herinnering_taken', 'laatste_email_over_taken')}),
        (_('Permissions'), {'fields': ('is_active', 'is_gast', 'is_BB',
                                       'gekoppelde_functies', 'is_staff', 'is_superuser')}),
        (_('Beveiliging'), {'fields': ('password',
                                       'vraag_nieuw_wachtwoord', 'verkeerd_wachtwoord_teller',
                                       'is_geblokkeerd_tot',
                                       'otp_code', 'otp_is_actief')}),
        (_('Important dates'), {'fields': ('date_joined', 'laatste_inlog_poging',
                                           'last_login', 'otp_controle_gelukt_op')}),
    )

    list_display = ('get_account_full_name',)

    list_filter = ('is_BB', 'otp_is_actief', 'email_is_bevestigd')

    # velden om in te zoeken (in de lijst)
    search_fields = ('username', 'unaccented_naam', 'first_name', 'last_name', 'bevestigde_email', 'nieuwe_email')

    ordering = ('-username',)       # nieuwste eerst

    @staticmethod
    def gekoppelde_functies(obj):     # pragma: no cover
        return "\n".join([functie.beschrijving for functie in obj.functie_set.all()])


class AccountVerzoekenTellerAdmin(admin.ModelAdmin):

    search_fields = ('account__username', 'account__unaccented_naam')


admin.site.register(Account, AccountAdmin)
admin.site.register(AccountVerzoekenTeller, AccountVerzoekenTellerAdmin)

# end of file
