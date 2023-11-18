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
from Scheidsrechter.definities import SCHEIDS2LEVEL
from Sporter.models import SporterVoorkeuren, Sporter

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
        if rol_nu == Rollen.ROL_CS:
            return True
        if rol_nu == Rollen.ROL_SPORTER and gebruiker_is_scheids(self.request):
            return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        lid_nr2voorkeuren = dict()
        for voorkeuren in SporterVoorkeuren.objects.exclude(sporter__scheids=SCHEIDS_NIET).select_related('sporter'):
            lid_nr2voorkeuren[voorkeuren.sporter.lid_nr] = voorkeuren
        # for

        korps = (Sporter
                 .objects
                 .exclude(scheids=SCHEIDS_NIET)
                 .exclude(is_overleden=True))

        alle = list()
        for sporter in korps:
            if sporter.scheids == SCHEIDS_INTERNATIONAAL:
                sporter.scheids_str = 'SR5'
                order = 1
            elif sporter.scheids == SCHEIDS_BOND:
                sporter.scheids_str = 'SR4'
                order = 2
            else:
                sporter.scheids_str = 'SR3'
                order = 3

            sporter.opt_email = '-'
            sporter.opt_telefoon = '-'

            try:
                voorkeuren = lid_nr2voorkeuren[sporter.lid_nr]
            except KeyError:
                pass
            else:
                if voorkeuren.scheids_opt_in_korps_email:
                    sporter.opt_email = sporter.email

                if voorkeuren.scheids_opt_in_korps_tel_nr:
                    sporter.opt_telefoon = sporter.telefoon

            tup = (order, sporter.achternaam, sporter.voornaam, sporter.lid_nr, sporter)
            alle.append(tup)
        # for
        alle.sort()

        context['korps'] = [tup[-1] for tup in alle]
        context['aantal'] = len(alle)

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (None, 'Korps')
        )

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
        if rol_nu == Rollen.ROL_CS:
            return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        lid_nr2voorkeuren = dict()
        for voorkeuren in SporterVoorkeuren.objects.exclude(sporter__scheids=SCHEIDS_NIET).select_related('sporter'):
            lid_nr2voorkeuren[voorkeuren.sporter.lid_nr] = voorkeuren
        # for

        korps = list()
        for sporter in (Sporter
                        .objects
                        .exclude(scheids=SCHEIDS_NIET)
                        .exclude(is_overleden=True)):

            sporter.level_str = SCHEIDS2LEVEL[sporter.scheids]
            sporter.delen_str = 'Onbekend'

            try:
                voorkeuren = lid_nr2voorkeuren[sporter.lid_nr]
            except KeyError:
                sporter.delen_str = 'Onbekend'
            else:
                delen_korps = voorkeuren.scheids_opt_in_korps_tel_nr or voorkeuren.scheids_opt_in_korps_email
                delen_ver = voorkeuren.scheids_opt_in_ver_tel_nr or voorkeuren.scheids_opt_in_ver_email

                if delen_korps and delen_ver:
                    sporter.delen_str = 'Ja'
                elif delen_korps:
                    sporter.delen_str = 'Alleen korps'
                elif delen_ver:
                    sporter.delen_str = 'Alleen wedstrijd'
                else:
                    sporter.delen_str = 'Geen keuze'

            tup = (10 - int(sporter.level_str[-1]), sporter.achternaam, sporter.voornaam, sporter.lid_nr, sporter)
            korps.append(tup)
        # for

        korps.sort()

        context['korps'] = [tup[-1] for tup in korps]
        context['aantal'] = len(korps)

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (None, 'Korps')
        )

        return context


# end of file
