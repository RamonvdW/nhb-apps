# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" In de sessie bijhouden wat de meest recent geactiveerde rol en functie is """

from Account.operations import zet_sessionvar_if_changed
from Functie.definities import Rol
from Functie.models import Functie
import logging

my_logger = logging.getLogger('MH.Functie')

SESSIONVAR_ROL_HUIDIGE = 'gebruiker_rol_huidige'
SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK = 'gebruiker_rol_functie_pk'


def rol_zet_huidige_rol(request, rol: Rol):
    if request.user.is_authenticated:           # pragma: no branch
        zet_sessionvar_if_changed(request, SESSIONVAR_ROL_HUIDIGE, rol.value)


def rol_zet_huidige_functie_pk(request, functie_pk: int | None):
    if request.user.is_authenticated:           # pragma: no branch
        zet_sessionvar_if_changed(request, SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK, functie_pk)


def rol_get_huidige(request):
    """ Retourneer de huidige rol van de gebruiker.
        Zie Functie.definities.Rollen.ROL_xxx
    """
    rol = Rol.ROL_NONE
    if request.user.is_authenticated:
        try:
            rol = request.session[SESSIONVAR_ROL_HUIDIGE]
        except KeyError:
            rol = Rol.ROL_NONE

    return rol


def rol_get_huidige_functie(request) -> tuple[Rol, Functie]:
    """ Retourneer de huidige rol en functie van de gebruiker.
        rol:     zie Functie.definities.Rollen.ROL_xxx
        functie: een van de Functie records
    """
    rol = rol_get_huidige(request)

    functie = None
    if request.user.is_authenticated:
        try:
            functie_pk = request.session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK]
        except KeyError:
            # geen functie opgeslagen
            pass
        else:
            if functie_pk:      # filter None
                try:
                    functie_pk = int(functie_pk)
                    functie = (Functie
                               .objects
                               .select_related('rayon',
                                               'regio',
                                               'regio__rayon',
                                               'vereniging',
                                               'vereniging__regio')
                               .get(pk=functie_pk))
                except (ValueError, Functie.DoesNotExist):
                    # slecht getal of geen bestaande functie
                    pass
                else:
                    # controleer dat de rol en de functie gerelateerd zijn
                    bad = ((functie.rol == 'HWL' and rol != Rol.ROL_HWL) or
                           (functie.rol == 'SEC' and rol != Rol.ROL_SEC) or
                           (functie.rol == 'RKO' and rol != Rol.ROL_RKO) or
                           (functie.rol == 'BKO' and rol != Rol.ROL_BKO) or
                           (functie.rol == 'RCL' and rol != Rol.ROL_RCL) or
                           (functie.rol == 'MWZ' and rol != Rol.ROL_MWZ) or
                           (functie.rol == 'MWW' and rol != Rol.ROL_MWW) or
                           (functie.rol == 'MLA' and rol != Rol.ROL_MLA) or
                           (functie.rol == 'LA' and rol != Rol.ROL_LA) or
                           (functie.rol == 'WL' and rol != Rol.ROL_WL))

                    if bad:
                        # afwijkende combinatie
                        my_logger.warning(
                            '{rol_get_huidige_functie} sessie zegt functie_pk=%s met rol=%s terwijl rol=%s' % (
                                functie_pk, repr(functie.rol), repr(rol)))

    return rol, functie


# end of file
