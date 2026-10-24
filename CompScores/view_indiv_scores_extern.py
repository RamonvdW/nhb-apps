# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import View
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from CompLaagRegio.operations.maak_mutatie_regio import maak_mutatie_scores_extern_ophalen
from CompScores.helpers import (mag_deelcomp_wedstrijd_wijzigen, bepaal_match_en_deelcomp_of_404,
                                vereniging_heeft_externe_scores)
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving


class UitslagExternOphalenView(UserPassesTestMixin, View):

    """ Deze view laat de HWL of WL de uitslag van een wedstrijd extern ophalen """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_HWL, Rol.ROL_WL)

    def get(self, request, *args, **kwargs):
        """
            Stappenplan:
                1) opdracht geven aan achtergrondtaak
                2) wacht op uitvoer door achtergrondtaak
                3) doorverwijzen naar score invoer scherm
        """

        snel = str(request.POST.get('snel', ''))[:1]

        match_pk = kwargs['match_pk'][:7]     # afkappen voor de veiligheid
        match, deelcomp, ronde = bepaal_match_en_deelcomp_of_404(match_pk)

        if not mag_deelcomp_wedstrijd_wijzigen(match, self.functie_nu, deelcomp):
            raise PermissionDenied('Niet de beheerder')

        if not vereniging_heeft_externe_scores(self.functie_nu.vereniging):
            raise PermissionDenied('Niet ondersteund')

        # geef opdracht aan de achtergrondtaak
        account = get_account(request)
        door_str = "%s %s" % (rol_get_beschrijving(request), account.volledige_naam())
        door_str = door_str[:149]

        # deze wacht maximaal 3 seconden
        maak_mutatie_scores_extern_ophalen(match, door_str, account, snel == '1')

        # stuur gebruiker terug naar het invoerscherm
        url = reverse('CompScores:uitslag-invoeren',
                      kwargs={'match_pk': match.pk})

        return HttpResponseRedirect(url)


# end of file
