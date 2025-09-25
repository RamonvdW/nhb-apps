# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Account.models import Account
from Feedback.models import Feedback


class FeedbackAdmin(admin.ModelAdmin):

    # filter mogelijkheid
    list_filter = ('is_afgehandeld',)

    readonly_fields = ('toegevoegd_op', 'bevinding', 'gebruiker', 'in_rol', 'email_adres', 'op_pagina',
                       'volledige_url', 'site_versie')

    # volgorde van de velden
    fields = ('toegevoegd_op', 'bevinding', 'is_afgehandeld', 'feedback', 'gebruiker', 'email_adres', 'op_pagina',
              'volledige_url', 'site_versie')

    ordering = ('-toegevoegd_op',)      # nieuwste bovenaan

    search_fields = ('gebruiker', 'feedback')

    @staticmethod
    def email_adres(obj):                             # pragma: no cover
        # obj.gebruiker = "Volledige Naam (username)"
        pos = obj.gebruiker.find('(')
        if pos > 0:
            username = obj.gebruiker[pos+1:-1]
            account = Account.objects.get(username=username)
            if account.email_is_bevestigd:
                return account.bevestigde_email

        return "?"


admin.site.register(Feedback, FeedbackAdmin)

# end of file
