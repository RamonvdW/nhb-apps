# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.definities import SCHEIDS_NIET
from Functie.definities import Rol
from Functie.rol import rol_get_huidige, gebruiker_is_scheids
from Opleidingen.definities import CODE2SCHEIDS
from Opleidingen.models import OpleidingDiploma
from Scheidsrechter.definities import SCHEIDS2LEVEL
from Sporter.models import SporterVoorkeuren, Sporter

TEMPLATE_KORPS = 'scheidsrechter/korps.dtl'
TEMPLATE_KORPS_CS = 'scheidsrechter/korps-cs.dtl'
TEMPLATE_KORPS_CS_EMAILS = 'scheidsrechter/korps-cs-emails.dtl'


class KorpsView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_KORPS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rol.ROL_CS:
            return True
        if rol_nu == Rol.ROL_SPORTER and gebruiker_is_scheids(self.request):
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
            sporter.level_str = SCHEIDS2LEVEL[sporter.scheids]

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

            tup = (sporter.voornaam, sporter.achternaam, sporter.lid_nr, sporter)
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


class KorpsCSView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_KORPS_CS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rol.ROL_CS:
            return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        lid_nr2voorkeuren = dict()
        for voorkeuren in SporterVoorkeuren.objects.exclude(sporter__scheids=SCHEIDS_NIET).select_related('sporter'):
            lid_nr2voorkeuren[voorkeuren.sporter.lid_nr] = voorkeuren
        # for

        ja_nee = {True: 'Ja', False: 'Nee'}

        pks = list(Sporter
                   .objects
                   .exclude(scheids=SCHEIDS_NIET)
                   .exclude(is_overleden=True)
                   .values_list('pk', flat=True))

        sporter_scheids2datum = dict()
        for diploma in (OpleidingDiploma
                        .objects
                        .filter(sporter__pk__in=pks,
                                code__in=CODE2SCHEIDS.keys())
                        .select_related('sporter')):
            sporter_scheids2datum[(diploma.sporter.pk, CODE2SCHEIDS[diploma.code])] = diploma.datum_begin
        # for

        korps = list()
        for sporter in (Sporter
                        .objects
                        .exclude(scheids=SCHEIDS_NIET)
                        .exclude(is_overleden=True)):

            sporter.level_str = SCHEIDS2LEVEL[sporter.scheids]

            try:
                sporter.level_sinds = sporter_scheids2datum[(sporter.pk, sporter.scheids)]
            except KeyError:
                sporter.level_sinds = '?'

            sporter.delen_tel_str = sporter.delen_email_str = 'Geen account'

            try:
                voorkeuren = lid_nr2voorkeuren[sporter.lid_nr]
            except KeyError:
                pass
            else:
                sporter.delen_tel_str = '%s, %s' % (ja_nee[voorkeuren.scheids_opt_in_korps_tel_nr],
                                                    ja_nee[voorkeuren.scheids_opt_in_ver_tel_nr])

                sporter.delen_email_str = '%s, %s' % (ja_nee[voorkeuren.scheids_opt_in_korps_email],
                                                      ja_nee[voorkeuren.scheids_opt_in_ver_email])

            tup = (sporter.voornaam, sporter.achternaam, sporter.lid_nr, sporter)
            korps.append(tup)
        # for

        korps.sort()

        context['korps'] = [tup[-1] for tup in korps]
        context['aantal'] = len(korps)

        context['url_emails'] = reverse('Scheidsrechter:korps-emails')

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (None, 'Korps')
        )

        return context


class KorpsCSAlleEmailsView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de CS en geeft een knip-en-plak-baar overzicht van
        van de e-mailadressen van alle SRs.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_KORPS_CS_EMAILS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rol.ROL_CS:
            return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        emails = (Sporter
                  .objects
                  .exclude(scheids=SCHEIDS_NIET)
                  .exclude(is_overleden=True)
                  .values_list('email', flat=True))

        context['aantal'] = len(emails)
        context['emails'] = "; ".join(emails)

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (reverse('Scheidsrechter:korps-met-contactgegevens'), 'Korps'),
            (None, 'E-mailadressen')
        )

        return context


# end of file
