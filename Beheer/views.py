# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.admin.sites import AdminSite
from django.urls import reverse
from django.http import HttpResponseRedirect
from Account.models import user_is_otp_verified

# vervanger van de ingebouwde Admin site
# hiermee kunnen we 2FA checks doen
# hiermee verwijderen we de login/logout/password change views

# django.contrib.admin.sites levert de urls en views
# maak een aangepaste versie

class BeheerAdminSite(AdminSite):

    # replace all the functions that handle the urls for login/logout/password-change

    # TODO: wachtwoord wijzigen implementeren
    #def password_change(self, request, extra_context=None):
    #    return HttpResponseRedirect(reverse('Plein:plein'))


    def logout(self, request, extra_context=None):
        return HttpResponseRedirect(reverse('Account:logout'))

    def login(self, request, extra_context=None):
        return HttpResponseRedirect(reverse('Account:login'))

    def get_urls(self):
        # remove the password-change-done entry
        urlcfg = super(BeheerAdminSite, self).get_urls()
        del urlcfg[4]
        return urlcfg

    def has_permission(self, request):
        """ geef True terug als de gebruiker bij de admin pagina mag """
        return request.user.is_active and request.user.is_staff and request.user.is_authenticated and user_is_otp_verified(request)

# end of file
