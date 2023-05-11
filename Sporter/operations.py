# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Functie.definities import Rollen
from Functie.rol import rol_get_huidige_functie
from NhbStructuur.models import NhbRegio


def get_request_regio_nr(request):
    """ Geeft het regionummer van de ingelogde sporter terug,
        of 101 als er geen regio vastgesteld kan worden
    """
    regio_nr = 101

    rol_nu, functie_nu = rol_get_huidige_functie(request)

    if functie_nu:
        if functie_nu.nhb_ver:
            # HWL, WL
            regio_nr = functie_nu.nhb_ver.regio.regio_nr
        elif functie_nu.nhb_regio:
            # RCL
            regio_nr = functie_nu.nhb_regio.regio_nr
        elif functie_nu.nhb_rayon:
            # RKO
            regio = (NhbRegio
                     .objects
                     .filter(rayon=functie_nu.nhb_rayon,
                             is_administratief=False)
                     .order_by('regio_nr'))[0]
            regio_nr = regio.regio_nr

    elif rol_nu == Rollen.ROL_SPORTER:
        # sporter
        account = request.user
        if account.sporter_set.count() > 0:         # pragma: no branch
            sporter = account.sporter_set.select_related('bij_vereniging__regio').all()[0]
            if sporter.is_actief_lid and sporter.bij_vereniging:
                nhb_ver = sporter.bij_vereniging
                regio_nr = nhb_ver.regio.regio_nr

    return regio_nr


# end of file
