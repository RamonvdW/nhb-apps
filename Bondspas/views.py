# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import FileResponse, JsonResponse, Http404
from django.utils import timezone
from django.shortcuts import render, reverse
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Bondspas.models import (Bondspas, BONDSPAS_STATUS_NIEUW, BONDSPAS_STATUS_AANWEZIG, BONDSPAS_STATUS_VERWIJDERD,
                             BONDSPAS_STATUS_OPHALEN, BONDSPAS_STATUS_BEZIG, BONDSPAS_STATUS_FAIL)
from Functie.rol import rol_get_huidige, Rollen
from Overig.background_sync import BackgroundSync
from Plein.menu import menu_dynamics
from Sporter.models import Sporter
import logging
import json
import os


TEMPLATE_BONDSPAS_OPHALEN = 'bondspas/bondspas-ophalen.dtl'

my_logger = logging.getLogger('NHBApps.Bondspas')

bondspas_downloader_ping = BackgroundSync(settings.BACKGROUND_SYNC__BONDSPAS_DOWNLOADER)


class ToonBondspasView(UserPassesTestMixin, View):

    """ Deze view kan de bondspas tonen, of een scherm met 'even wachten, we zoeken je pas op' """

    template_name = TEMPLATE_BONDSPAS_OPHALEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en rol Sporter gekozen hebben
        return rol_get_huidige(self.request) == Rollen.ROL_SPORTER

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """
        context = dict()

        account = self.request.user
        sporter = Sporter.objects.filter(account=account)[0]
        context['lid_nr'] = lid_nr = sporter.lid_nr

        # kijk of de pas al aanwezig is
        bondspas, _ = Bondspas.objects.get_or_create(lid_nr=lid_nr)
        if bondspas.status == BONDSPAS_STATUS_AANWEZIG:
            # meteen downloaden
            bondspas.aantal_keer_bekeken += 1
            bondspas.save(update_fields=['aantal_keer_bekeken'])

            fpath = os.path.join(settings.BONDSPAS_CACHE_PATH, bondspas.filename)
            try:
                return FileResponse(open(fpath, 'rb'))
            except (OSError, IOError) as exc:
                # we hebben een probleem: pas hoort er wel te zijn, maar is niet op te halen?
                my_logger.error('Kan bondspas niet openen: %s' % str(exc))

            # laat de pas opnieuw ophalen
            bondspas.status = BONDSPAS_STATUS_OPHALEN
            bondspas.aantal_keer_bekeken -= 1
            bondspas.save(update_fields=['aantal_keer_bekeken', 'status'])

            # ping het achtergrondproces
            bondspas_downloader_ping.ping()

        elif bondspas.status in (BONDSPAS_STATUS_NIEUW, BONDSPAS_STATUS_VERWIJDERD):
            # laat de pas ophalen
            bondspas.status = BONDSPAS_STATUS_OPHALEN
            bondspas.save(update_fields=['status'])

            # ping het achtergrondproces
            bondspas_downloader_ping.ping()

        elif bondspas.status == BONDSPAS_STATUS_FAIL:
            # laat de bondspas opnieuw ophalen als er voldoende tijd verstreken is
            context['now'] = now = timezone.now()

            if now > bondspas.opnieuw_proberen_na:
                bondspas.status = BONDSPAS_STATUS_OPHALEN
                bondspas.save(update_fields=['status'])

                # ping het achtergrondproces
                bondspas_downloader_ping.ping()
            else:
                context['has_error'] = True
                context['ophalen_na'] = bondspas.opnieuw_proberen_na

        context['url_status_check'] = reverse('Bondspas:dynamic-check-status')
        context['url_terug'] = reverse('Sporter:profiel')

        context['kruimels'] = (
            (None, 'Bondspas'),
        )

        # toon een pagina die wacht op de download
        menu_dynamics(request, context)
        return render(request, self.template_name, context)


class DynamicBondspasCheckStatus(UserPassesTestMixin, View):

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en rol Sporter gekozen hebben
        return rol_get_huidige(self.request) == Rollen.ROL_SPORTER

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen vanuit de template om te kijken wat de status van de bondspas is.

            Dit is een POST by design, om caching te voorkomen.
        """
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            # garbage in
            raise Http404('Geen valide verzoek')

        try:
            lid_nr = int(str(data['lid_nr'])[:6])   # afkappen voor extra veiligheid
            bondspas = Bondspas.objects.get(lid_nr=lid_nr)
        except (KeyError, ValueError, Bondspas.DoesNotExist):
            raise Http404('Niet gevonden')

        if bondspas.status == BONDSPAS_STATUS_AANWEZIG:
            status = 'aanwezig'
        elif bondspas.status in (BONDSPAS_STATUS_OPHALEN, BONDSPAS_STATUS_BEZIG):
            status = 'bezig'
        elif bondspas.status == BONDSPAS_STATUS_FAIL:
            status = 'fail'
        else:
            # nieuw: komt niet voor
            # verwijderd: zou vaag zijn, want net aangevraagd
            status = 'onbekend'

        out = {'status': status}

        return JsonResponse(out)


# end of file
