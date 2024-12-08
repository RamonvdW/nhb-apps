# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.shortcuts import redirect, reverse
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.menu import get_url_voor_competitie
from Functie.definities import Rollen
from Functie.models import Functie
from Functie.rol import (rol_mag_wisselen, rol_get_huidige_functie, rol_get_beschrijving,
                         rol_activeer_rol, rol_activeer_functie)
from Overig.helpers import get_safe_from_ip
from Taken.operations import eval_open_taken
from Wedstrijden.definities import WEDSTRIJD_STATUS_URL_WACHT_OP_GOEDKEURING
import logging


TEMPLATE_WISSEL_VAN_ROL = 'functie/wissel-van-rol.dtl'
TEMPLATE_WISSEL_NAAR_SEC = 'functie/wissel-naar-sec.dtl'

my_logger = logging.getLogger('MH.Functie')


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

        account = get_account(request)

        if 'rol' in kwargs:
            # activeer rol
            my_logger.info('%s ROL account %s wissel naar rol %s' % (
                                from_ip,
                                account.username,
                                repr(kwargs['rol'])))

            rol_activeer_rol(account, request, kwargs['rol'])

        elif 'functie_pk' in kwargs:
            # activeer functie
            functie_pk = kwargs['functie_pk'][:6]       # afkappen voor de veiligheid
            try:
                functie_pk = int(functie_pk)
                functie = Functie.objects.get(pk=functie_pk)
            except (ValueError, TypeError, Functie.DoesNotExist):
                raise Http404('Foute parameter (functie)')

            my_logger.info('%s ROL account %s wissel naar functie %s (%s)' % (
                            from_ip,
                            account.username,
                            functie.pk,
                            functie))

            rol_activeer_functie(account, request, functie)

        else:
            ver_nr = request.POST.get('ver_nr', '')[:4]     # afkappen voor de veiligheid
            try:
                ver_nr = int(ver_nr)
                functie = Functie.objects.get(rol='HWL',
                                              vereniging__ver_nr=ver_nr)
            except (ValueError, TypeError, Functie.DoesNotExist):
                # in plaats van een foutmelding, stuur door naar Wissel van Rol pagina
                # raise Http404('Foute parameter (vereniging)')
                return redirect('Functie:wissel-van-rol')

            my_logger.info('%s ROL account %s wissel naar functie %s (%s)' % (
                            from_ip,
                            account.username,
                            functie.pk,
                            functie))

            rol_activeer_functie(account, request, functie)

        rol_beschrijving = rol_get_beschrijving(request)
        my_logger.info('%s ROL account %s is nu %s' % (from_ip, account.username, rol_beschrijving))

        # update het aantal open taken gemeld in het menu
        # want dit is afhankelijk van de huidige rol
        eval_open_taken(self.request, forceer=True)

        # stuur een aantal rollen door naar een functionele pagina
        # de rest blijft in Wissel van Rol
        rol_nu, functie_nu = rol_get_huidige_functie(request)

        if rol_nu == Rollen.ROL_SPORTER:
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

        if rol_nu == Rollen.ROL_MWZ:
            url = reverse('Wedstrijden:manager-status', kwargs={'status': WEDSTRIJD_STATUS_URL_WACHT_OP_GOEDKEURING})
            return redirect(url)

        if rol_nu == Rollen.ROL_CS:
            url = reverse('Scheidsrechter:overzicht')
            return redirect(url)

        return redirect('Functie:wissel-van-rol')


# end of file
