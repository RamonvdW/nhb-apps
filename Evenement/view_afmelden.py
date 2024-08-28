# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Bestel.operations.mutaties import (bestel_mutatieverzoek_afmelden_evenement,
                                        bestel_mutatieverzoek_verwijder_product_uit_mandje)
from Evenement.definities import EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE
from Evenement.models import EvenementInschrijving
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige_functie


class AfmeldenView(UserPassesTestMixin, View):

    """ Via deze view kunnen beheerders een sporter afmelden voor een evenement """

    raise_exception = True          # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_HWL

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen om de POST af te handelen"""

        try:
            inschrijving_pk = str(kwargs['inschrijving_pk'])[:6]     # afkappen voor de veiligheid
            inschrijving_pk = int(inschrijving_pk)
            inschrijving = EvenementInschrijving.objects.get(pk=inschrijving_pk)
        except (TypeError, ValueError, EvenementInschrijving.DoesNotExist):
            raise Http404('Inschrijving niet gevonden')

        # controleer dat dit een inschrijving is op een wedstrijd van de vereniging
        if inschrijving.evenement.organiserende_vereniging != self.functie_nu.vereniging:
            raise Http404('Verkeerde vereniging')

        snel = str(request.POST.get('snel', ''))[:1]

        if inschrijving.status == EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE:
            if inschrijving.bestelproduct_set.count() > 0:          # pragma: no branch
                product = inschrijving.bestelproduct_set.first()
                bestel_mutatieverzoek_verwijder_product_uit_mandje(inschrijving.koper, product, snel == '1')
        else:
            bestel_mutatieverzoek_afmelden_evenement(inschrijving, snel == '1')

        url = reverse('Evenement:aanmeldingen', kwargs={'evenement_pk': inschrijving.evenement.pk})

        return HttpResponseRedirect(url)


# end of file
