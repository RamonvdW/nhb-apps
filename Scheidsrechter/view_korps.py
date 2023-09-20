# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.definities import SCHEIDS_NIET, SCHEIDS_BOND, SCHEIDS_INTERNATIONAAL, SCHEIDS_TO_STR
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige
from Functie.scheids import gebruiker_is_scheids
from Plein.menu import menu_dynamics
from Scheidsrechter.definities import SCHEIDS2LEVEL
from Sporter.models import Sporter

TEMPLATE_KORPS = 'scheidsrechter/korps.dtl'
TEMPLATE_KORPS_CONTACT = 'scheidsrechter/korps-contactgegevens.dtl'


class KorpsView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_KORPS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        if rol_nu in (Rollen.ROL_BB, Rollen.ROL_CS):
            return True
        if rol_nu == Rollen.ROL_SPORTER and gebruiker_is_scheids(self.request):
            return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        korps = (Sporter
                 .objects
                 .exclude(scheids=SCHEIDS_NIET)
                 .exclude(is_overleden=True)
                 .order_by('scheids',
                           'sinds_datum'))

        sr3 = list()
        sr4 = list()
        sr5 = list()

        for sporter in korps:
            if sporter.scheids == SCHEIDS_INTERNATIONAAL:
                sr5.append(sporter)
            elif sporter.scheids == SCHEIDS_BOND:
                sr4.append(sporter)
            else:
                sr3.append(sporter)
        # for

        for lijst in (sr3, sr4, sr5):
            if len(lijst) > 0:
                sporter = lijst[0]
                sporter.is_break = True
                sporter.scheids_str = SCHEIDS_TO_STR[sporter.scheids]
        # for

        context['korps'] = sr5 + sr4 + sr3
        context['aantal'] = len(korps)

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (None, 'Korps')
        )

        menu_dynamics(self.request, context)
        return context


class KorpsMetContactGegevensView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_KORPS_CONTACT
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        if rol_nu in (Rollen.ROL_BB, Rollen.ROL_CS):
            return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        korps = list()
        for scheids in (Sporter
                        .objects
                        .exclude(scheids=SCHEIDS_NIET)
                        .exclude(is_overleden=True)):

            scheids.level_str = SCHEIDS2LEVEL[scheids.scheids]

            tup = (10 - int(scheids.level_str[-1]), scheids.sinds_datum, scheids.pk, scheids)
            korps.append(tup)
        # for

        korps.sort()

        context['korps'] = [scheids for _, _, _, scheids in korps]
        context['aantal'] = len(korps)

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (None, 'Korps')
        )

        menu_dynamics(self.request, context)
        return context


# end of file
