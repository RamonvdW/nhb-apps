# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from Account.models import get_account
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from GoogleDrive.operations.authenticatie import get_authorization_url

TEMPLATE_TOESTEMMING = 'googledrive/toestemming.dtl'


class ToestemmingView(TemplateView):

    """ Deze view is voor de manage """

    # class variables shared by all instances
    template_name = TEMPLATE_TOESTEMMING
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_BB

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['url_toestemming'] = reverse('GoogleDrive:toestemming-drive')

        context['kruimels'] = (
            (None, 'Toestemming'),
        )

        return context

    @staticmethod
    def post(request, *args, **kwargs):

        account = get_account(request)
        url = get_authorization_url(account.username, account.bevestigde_email)

        # stuur de gebruiker door naar Google
        return HttpResponseRedirect(url)


# end of file
