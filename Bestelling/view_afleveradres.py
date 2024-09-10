# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.shortcuts import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Bestelling.definities import BESTELLING_TRANSPORT_NVT
from Bestelling.models import BestellingMandje
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige


TEMPLATE_BESTEL_AFLEVERADRES = 'bestelling/kies-afleveradres.dtl'


class WijzigAfleveradresView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een gebruiker kiezen om zijn bestelling af te laten leveren of op te halen """

    # class variables shared by all instances
    template_name = TEMPLATE_BESTEL_AFLEVERADRES
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

        account = get_account(self.request)
        if not account.is_gast:
            raise Http404('Geen toegang')

        try:
            mandje = BestellingMandje.objects.get(account=account)
        except BestellingMandje.DoesNotExist:
            # geen mandje
            raise Http404('Mandje is leeg')

        if mandje.transport == BESTELLING_TRANSPORT_NVT:
            raise Http404('Niet van toepassing')

        context['mandje'] = mandje
        context['url_opslaan'] = reverse('Bestel:wijzig-afleveradres')
        context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Bestel:toon-inhoud-mandje'), 'Mandje'),
            (None, 'Wijzig afleveradres')
        )

        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de koper op de knop BESTELLING AFRONDEN gedrukt heeft
            Hier converteren we het mandje in een bevroren bestelling die afgerekend kan worden.
        """

        account = get_account(self.request)
        if not account.is_gast:
            raise Http404('Geen toegang')

        try:
            mandje = BestellingMandje.objects.get(account=account)
        except BestellingMandje.DoesNotExist:
            # geen mandje
            raise Http404('Mandje is leeg')

        regels = list()
        for nr in (1, 2, 3, 4, 5):
            regel = str(request.POST.get('regel%s' % nr, ''))[:100]      # afkappen voor extra veiligheid
            regel = regel.strip()
            if regel:
                regels.append(regel)
        # for
        regels.extend(['', '', '', '', ''])

        mandje.afleveradres_regel_1 = regels[0]
        mandje.afleveradres_regel_2 = regels[1]
        mandje.afleveradres_regel_3 = regels[2]
        mandje.afleveradres_regel_4 = regels[3]
        mandje.afleveradres_regel_5 = regels[4]
        mandje.save(update_fields=['afleveradres_regel_1', 'afleveradres_regel_2', 'afleveradres_regel_3',
                                   'afleveradres_regel_4', 'afleveradres_regel_5'])

        # terug naar het mandje
        url = reverse('Bestel:toon-inhoud-mandje')
        return HttpResponseRedirect(url)


# end of file
