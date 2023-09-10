# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rollen, SCHEIDS_NIET, SCHEIDS_TO_STR, SCHEIDS_INTERNATIONAAL, SCHEIDS_BOND
from Functie.rol import rol_get_huidige
from Functie.scheids import gebruiker_is_scheids
from Plein.menu import menu_dynamics
from Sporter.models import Sporter
from Wedstrijden.definities import (WEDSTRIJD_STATUS_ONTWERP, WEDSTRIJD_ORGANISATIE_TO_STR, ORGANISATIE_WA,
                                    WEDSTRIJD_WA_STATUS_TO_STR)
from Wedstrijden.models import Wedstrijd

TEMPLATE_OVERZICHT = 'scheidsrechter/overzicht.dtl'
TEMPLATE_KORPS = 'scheidsrechter/korps.dtl'
TEMPLATE_WEDSTRIJDEN = 'scheidsrechter/wedstrijden.dtl'


class OverzichtView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rollen.ROL_BB:
            return True
        if rol_nu == Rollen.ROL_SPORTER and gebruiker_is_scheids(self.request):
            return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['kruimels'] = (
            (None, 'Scheidsrechters'),
        )

        menu_dynamics(self.request, context)
        return context


class KorpsView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_KORPS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rollen.ROL_BB:
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


class WedstrijdenView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rollen.ROL_BB:
            return True
        if rol_nu == Rollen.ROL_SPORTER and gebruiker_is_scheids(self.request):
            return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        wedstrijden = (Wedstrijd
                       .objects
                       .exclude(status=WEDSTRIJD_STATUS_ONTWERP)
                       .exclude(is_ter_info=True)
                       .exclude(toon_op_kalender=False)
                       .order_by('-datum_begin'))       # nieuwste bovenaan

        for wedstrijd in wedstrijden:
            wedstrijd.organisatie_str = WEDSTRIJD_ORGANISATIE_TO_STR[wedstrijd.organisatie]
            if wedstrijd.organisatie == ORGANISATIE_WA:
                wedstrijd.organisatie_str += ' ' + WEDSTRIJD_WA_STATUS_TO_STR[wedstrijd.wa_status]

            wedstrijd.url_details = reverse('Wedstrijden:wedstrijd-details',
                                            kwargs={'wedstrijd_pk': wedstrijd.pk})
        # for

        context['wedstrijden'] = wedstrijden

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (None, 'Wedstrijden')
        )

        menu_dynamics(self.request, context)
        return context


# end of file
