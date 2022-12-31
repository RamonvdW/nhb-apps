# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.shortcuts import redirect
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.menu import get_url_voor_competitie
from Functie.models import Rollen
from Functie.rol import (rol_mag_wisselen, rol_get_huidige_functie, rol_get_beschrijving,
                         rol_activeer_rol, rol_activeer_functie)
from Overig.helpers import get_safe_from_ip
from Taken.operations import eval_open_taken
import logging


TEMPLATE_WISSEL_VAN_ROL = 'functie/wissel-van-rol.dtl'
TEMPLATE_WISSEL_NAAR_SEC = 'functie/wissel-naar-sec.dtl'

my_logger = logging.getLogger('NHBApps.Functie')


class ActiveerRolView(UserPassesTestMixin, View):
    """ Django class-based view om een andere rol aan te nemen """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return self.request.user.is_authenticated and rol_mag_wisselen(self.request)

    def post(self, request, *args, **kwargs):
        from_ip = get_safe_from_ip(self.request)

        if 'rol' in kwargs:
            # activeer rol
            my_logger.info('%s ROL account %s wissel naar rol %s' % (
                                from_ip,
                                self.request.user.username,
                                repr(kwargs['rol'])))
            rol_activeer_rol(request, kwargs['rol'])
        else:
            # activeer functie
            my_logger.info('%s ROL account %s wissel naar functie %s' % (
                            from_ip,
                            self.request.user.username,
                            repr(kwargs['functie_pk'])))
            rol_activeer_functie(request, kwargs['functie_pk'])

        rol_beschrijving = rol_get_beschrijving(request)
        my_logger.info('%s ROL account %s is nu %s' % (from_ip, self.request.user.username, rol_beschrijving))

        # update het aantal open taken gemeld in het menu
        # want dit is afhankelijk van de huidige rol
        eval_open_taken(self.request, forceer=True)

        # stuur een aantal rollen door naar een functionele pagina
        # de rest blijft in Wissel van Rol
        rol_nu, functie_nu = rol_get_huidige_functie(request)

        if rol_nu in (Rollen.ROL_BB, Rollen.ROL_SPORTER):
            return redirect('Plein:plein')

        if rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_WL):
            return redirect('Vereniging:overzicht')

        if rol_nu in (Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL):
            url = get_url_voor_competitie(functie_nu)
            return redirect(url)

        if rol_nu == Rollen.ROL_SUP:
            return redirect('Feedback:inzicht')

        if rol_nu == Rollen.ROL_MO:
            return redirect('Opleidingen:manager')

        if rol_nu == Rollen.ROL_MWW:
            return redirect('Webwinkel:manager')

        # TODO: add MWZ

        return redirect('Functie:wissel-van-rol')


# end of file
