# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Bestelling.operations.mutaties import (bestel_mutatieverzoek_afmelden_opleiding,
                                            bestel_mutatieverzoek_verwijder_regel_uit_mandje)
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Opleiding.definities import OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE
from Opleiding.models import OpleidingInschrijving


class AfmeldenView(UserPassesTestMixin, View):

    """ Via deze view kunnen beheerders een sporter afmelden voor een opleiding """

    raise_exception = True          # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_HWL

    @staticmethod
    def post(request, *args, **kwargs):
        """ wordt aangeroepen om de POST af te handelen"""

        try:
            inschrijving_pk = str(kwargs['inschrijving_pk'])[:6]     # afkappen voor de veiligheid
            inschrijving_pk = int(inschrijving_pk)
            inschrijving = OpleidingInschrijving.objects.get(pk=inschrijving_pk)
        except (TypeError, ValueError, OpleidingInschrijving.DoesNotExist):
            raise Http404('Inschrijving niet gevonden')

        snel = str(request.POST.get('snel', ''))[:1]

        if inschrijving.status == OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE:
            regel = inschrijving.bestelling
            bestel_mutatieverzoek_verwijder_regel_uit_mandje(inschrijving.koper, regel, snel == '1')
        else:
            bestel_mutatieverzoek_afmelden_opleiding(inschrijving, snel == '1')

        url = reverse('Opleiding:aanmeldingen', kwargs={'opleiding_pk': inschrijving.opleiding.pk})

        return HttpResponseRedirect(url)


# end of file
