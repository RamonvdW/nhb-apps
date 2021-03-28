# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.admin.sites import AdminSite
from django.urls import reverse
from django.http import HttpResponseRedirect
from Account.rechten import account_rechten_is_otp_verified

# aanpassingen van de ingebouwde Admin site
# hiermee kunnen we 2FA checks doen
# hiermee verwijderen we de default login/logout/password change views

# django.contrib.admin.sites levert de urls en views
# maak een aangepaste versie


class BeheerAdminSite(AdminSite):

    """ Replace all the functions that handle the urls for login/logout/password-change """

    def password_change(self, request, extra_context=None):
        return HttpResponseRedirect(reverse('Account:nieuw-wachtwoord'))

    def logout(self, request, extra_context=None):
        return HttpResponseRedirect(reverse('Account:logout'))

    def login(self, request, extra_context=None):
        next_url = request.GET.get('next', '')

        # send the user to the login page only when required
        # send the 2FA page otherwise
        if request.user.is_active and request.user.is_staff and request.user.is_authenticated:
            # well, login is not needed
            if account_rechten_is_otp_verified(request):
                # what are we doing here?
                if next_url:
                    return HttpResponseRedirect(next_url)

                # reason for login unknown (no 'next') so send to main page
                return HttpResponseRedirect(reverse('Plein:plein'))

            # send to 2FA page
            url = reverse('Functie:otp-controle')
        else:
            # send to login page
            url = reverse('Account:login')

        if next_url:
            url += '?next=' + next_url
        return HttpResponseRedirect(url)

    def get_urls(self):
        # remove the password-change-done entry
        url_conf = super(BeheerAdminSite, self).get_urls()
        del url_conf[4]
        return url_conf

    def has_permission(self, request):
        """ geef True terug als de gebruiker bij de admin pagina mag """
        return (request.user.is_active
                and request.user.is_staff
                and request.user.is_authenticated
                and account_rechten_is_otp_verified(request))

# end of file
