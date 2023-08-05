# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.


from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Bestel.definities import BESTEL_TRANSPORT_NVT, BESTEL_TRANSPORT_VERZEND, BESTEL_TRANSPORT_OPHALEN
from Bestel.models import BestelMandje
from Bestel.operations.mutaties import bestel_mutatieverzoek_transport
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige
from NhbStructuur.models import NhbVereniging
from Plein.menu import menu_dynamics


TEMPLATE_BESTEL_KEUZE_TRANSPORT = 'bestel/kies-transport.dtl'


class KiesTransportView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een gebruiker kiezen om zijn bestelling af te laten leveren of op te halen """

    # class variables shared by all instances
    template_name = TEMPLATE_BESTEL_KEUZE_TRANSPORT
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rollen.ROL_NONE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.request.user

        try:
            mandje = BestelMandje.objects.prefetch_related('producten').get(account=account)
        except BestelMandje.DoesNotExist:
            # geen mandje
            raise Http404('Mandje is leeg')

        if mandje.transport == BESTEL_TRANSPORT_NVT:
            raise Http404('Niet van toepassing')

        aantal_webwinkel = mandje.producten.exclude(webwinkel_keuze=None).count()
        if aantal_webwinkel < 1:
            # transport had op NVT moeten staan
            raise Http404('Niet van toepassing')

        context['wil_ophalen'] = (mandje.transport == BESTEL_TRANSPORT_OPHALEN)
        context['mag_ophalen'] = settings.WEBWINKEL_TRANSPORT_OPHALEN_MAG

        context['ophalen_ver'] = NhbVereniging.objects.get(ver_nr=settings.WEBWINKEL_VERKOPER_VER_NR)

        context['url_opslaan'] = reverse('Bestel:kies-transport')

        # force dat het mandje icoon getoond wordt
        context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Bestel:toon-inhoud-mandje'), 'Mandje'),
            (None, 'Keuze transport')
        )

        menu_dynamics(self.request, context)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de koper op de knop BESTELLING AFRONDEN gedrukt heeft
            Hier converteren we het mandje in een bevroren bestelling die afgerekend kan worden.
        """

        snel = str(request.POST.get('snel', ''))[:1]
        keuze = str(request.POST.get('keuze', ''))[:7]      # afkappen voor extra veiligheid
        account = self.request.user

        if keuze == 'verzend':
            bestel_mutatieverzoek_transport(account, BESTEL_TRANSPORT_VERZEND, snel == '1')

        elif keuze == 'ophalen' and settings.WEBWINKEL_TRANSPORT_OPHALEN_MAG:
            bestel_mutatieverzoek_transport(account, BESTEL_TRANSPORT_OPHALEN, snel == '1')

        else:
            raise Http404('Verkeerde parameter')

        # achtergrondtaak zet het mandje om in bestellingen

        # terug naar het mandje
        url = reverse('Bestel:toon-inhoud-mandje')
        return HttpResponseRedirect(url)


# end of file
