# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404, HttpResponseRedirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Betaal.models import BetaalInstellingenVereniging, MOLLIE_API_KEY_MAXLENGTH
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving
from mollie.api.client import RequestSetupError, Client

TEMPLATE_BETALING_INSTELLINGEN = 'betaal/vereniging-instellingen.dtl'


class BetalingInstellingenView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de beheerders van de vereniging """

    # class variables shared by all instances
    template_name = TEMPLATE_BETALING_INSTELLINGEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu in (Rol.ROL_SEC, Rol.ROL_HWL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['ver'] = ver = self.functie_nu.vereniging
        context['huidige_rol'] = rol_get_beschrijving(self.request)

        try:
            instellingen = BetaalInstellingenVereniging.objects.get(vereniging=ver)
        except BetaalInstellingenVereniging.DoesNotExist:
            pass
        else:
            if instellingen.mollie_api_key:
                context['huidige_api_key'] = instellingen.obfuscated_mollie_api_key()

            if instellingen.akkoord_via_bond:
                context['akkoord_via_bond'] = True

        context['url_opslaan'] = reverse('Betaal:vereniging-instellingen')

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
            (None, 'Instellingen'),
        )

        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de gebruiken op Opslaan drukt in het instellingenscherm. """

        ver = self.functie_nu.vereniging
        apikey = request.POST.get('apikey', '')[:MOLLIE_API_KEY_MAXLENGTH]

        if apikey:
            # laat de Mollie-client de key opschonen en controleren
            client = Client()
            try:
                apikey = client.validate_api_key(apikey)
            except RequestSetupError:
                # niet geaccepteerd
                # hoe moeilijk is knippen & plakken? Niet veel moeite in stoppen
                raise Http404('Niet geaccepteerd')

            # FUTURE: doe een interactie met Mollie om te controleren dat de API key echt werkt

            instellingen, is_created = BetaalInstellingenVereniging.objects.get_or_create(vereniging=ver)
            instellingen.mollie_api_key = apikey
            instellingen.save()

        url = reverse('Wedstrijden:vereniging')
        return HttpResponseRedirect(url)


# end of file
