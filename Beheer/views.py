# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.template.response import TemplateResponse
from django.contrib.admin.sites import AdminSite
from Account.rechten import account_rechten_is_otp_verified
from collections import OrderedDict

# aanpassingen van de ingebouwde Admin site
# hiermee
# - verwijderen we de default login/logout/password change views
# - kunnen we 2FA checks forceren
# - kunnen we de volgorde van modellen sturen

# django.contrib.admin.sites levert de urls en views
# maak een aangepaste versie


class BeheerAdminSite(AdminSite):

    """ Replace all the functions that handle the urls for login/logout/password-change """

    site_header = settings.NAAM_SITE + ' Admin'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._registry = OrderedDict()

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

    # overrides django/contrib/admin/sites.py:AdminSite:get_app_list
    def get_app_list(self, request):
        """ kopie van contrib/admin/sites.py aangepast om de modellen niet meer te sorteren """
        app_dict = self._build_app_dict(request)

        # Sort the apps alphabetically.
        app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())

        # don't show unused apps
        app_list = [elem for elem in app_list if elem['app_label'] != 'auth']

        return app_list

    # overrides django/contrib/admin/sites.py:AdminSite:app_index
    def app_index(self, request, app_label, extra_context=None):
        """ deze functie wordt aangeroepen om de lijst van modellen binnen een applicatie te tonen"""

        app_dict = self._build_app_dict(request, app_label)
        if not app_dict:
            raise Http404("The requested admin page does not exist.")

        # sorteren is uitgezet zodat de volgorde uit models.py aangehouden wordt

        # Sort the models alphabetically within each app.
        # app_dict["models"].sort(key=lambda x: x["name"])

        context = {
            **self.each_context(request),
            "title": "%(app)s administration" % {"app": app_dict["name"]},
            "subtitle": None,
            "app_list": [app_dict],
            "app_label": app_label,
            **(extra_context or {}),
        }

        request.current_app = self.name

        return TemplateResponse(
            request,
            self.app_index_template
            or ["admin/%s/app_index.html" % app_label, "admin/app_index.html"],
            context,
        )

# end of file
