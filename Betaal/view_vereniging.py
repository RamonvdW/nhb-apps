# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404, HttpResponseRedirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Betaal.models import BetaalInstellingenVereniging, MOLLIE_API_KEY_MAXLENGTH
from Functie.rol import Rollen, rol_get_huidige_functie, rol_get_beschrijving
from Plein.menu import menu_dynamics
from mollie.api.client import RequestSetupError, Client

TEMPLATE_BETALINGEN_INSTELLEN = 'betaal/vereniging-instellingen.dtl'


class BetalingenInstellenView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de beheerders van de vereniging """

    # class variables shared by all instances
    template_name = TEMPLATE_BETALINGEN_INSTELLEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['ver'] = ver = self.functie_nu.nhb_ver
        context['huidige_rol'] = rol_get_beschrijving(self.request)

        instellingen, is_created = BetaalInstellingenVereniging.objects.get_or_create(vereniging=ver)

        if instellingen.mollie_api_key:
            context['huidige_api_key'] = instellingen.obfuscated_mollie_api_key()

        if instellingen.akkoord_via_nhb:
            context['akkoord_via_nhb'] = True

        context['url_opslaan'] = reverse('Betaal:vereniging-instellingen')

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (None, 'Financieel'),
        )

        menu_dynamics(self.request, context)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de gebruiken op Opslaan drukt in het scherm met Financieel. """

        ver = self.functie_nu.nhb_ver
        apikey = request.POST.get('apikey', '')[:MOLLIE_API_KEY_MAXLENGTH]

        # laat de Mollie-client de key opschonen en controleren
        client = Client()
        try:
            apikey = client.validate_api_key(apikey)
        except RequestSetupError:
            # niet geaccepteerd
            # hoe moeilijk is knippen & plakken? Niet veel moeite in stoppen
            raise Http404('Niet geaccepteerd')

        # TODO: doe een echte transactie om te controleren dat de API key echt werkt

        instellingen, is_created = BetaalInstellingenVereniging.objects.get_or_create(vereniging=ver)
        instellingen.mollie_api_key = apikey
        instellingen.save()

        url = reverse('Vereniging:overzicht')
        return HttpResponseRedirect(url)


# end of file
