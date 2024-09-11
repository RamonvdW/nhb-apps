# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.sessions.models import Session
from Account.models import Account, AccountVerzoekenTeller
import pprint


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
                                       'scheids', 'gekoppelde_functies', 'is_staff', 'is_superuser')}),
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


class SessionAdmin(admin.ModelAdmin):

    @staticmethod
    def username(obj):
        session_user = obj.get_decoded().get('_auth_user_id')
        user = Account.objects.get(pk=session_user)
        return user.username

    @staticmethod
    def _session_data(obj):
        return pprint.pformat(obj.get_decoded())

    # _session_data.allow_tags = True
    list_display = ['session_key', 'username', 'expire_date']   # '_session_data'
    readonly_fields = ['session_key', 'expire_date', '_session_data', 'session_data']
    search_fields = ('session_key',)


admin.site.register(Session, SessionAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(AccountVerzoekenTeller, AccountVerzoekenTellerAdmin)

# end of file
