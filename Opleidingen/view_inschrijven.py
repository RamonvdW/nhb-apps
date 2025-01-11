# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404, UnreadablePostError, JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Betaal.format import format_bedrag_euro
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Instaptoets.operations import vind_toets, toets_geldig
from Opleidingen.definities import OPLEIDING_STATUS_INSCHRIJVEN
from Opleidingen.models import Opleiding, OpleidingDeelnemer
from Sporter.models import get_sporter
import json

TEMPLATE_OPLEIDINGEN_INSCHRIJVEN_BASISCURSUS = 'opleidingen/inschrijven-basiscursus.dtl'


class InschrijvenBasiscursusView(UserPassesTestMixin, TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDINGEN_INSCHRIJVEN_BASISCURSUS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sporter = None
        self.opleiding = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # instaptoets alleen aan leden tonen
        # gebruiker moet ingelogd zijn, geen gast zijn en rol Sporter gekozen hebben
        if rol_get_huidige(self.request) == Rol.ROL_SPORTER:
            account = get_account(self.request)
            if not account.is_gast:
                self.sporter = get_sporter(account)
                return True
        return False

    def _zoek_opleiding_basiscursus(self):
        self.opleiding = (Opleiding
                          .objects
                          .filter(is_basiscursus=True,
                                  status=OPLEIDING_STATUS_INSCHRIJVEN)
                          .order_by('periode_jaartal', 'periode_kwartaal')       # meest recente cursus eerst
                          .first())

    def _zoek_deelnemer(self, mag_database_wijzigen=False):
        """ zoek de OpleidingDeelnemer voor de sporter
            tijdens POST maken we deze aan
        """
        deelnemer = self.opleiding.deelnemers.filter(sporter=self.sporter).first()

        if not deelnemer:
            deelnemer = OpleidingDeelnemer(
                            sporter=self.sporter)

            if mag_database_wijzigen:
                deelnemer.save()
                self.opleiding.deelnemers.add(deelnemer)

        return deelnemer

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)
        context['sporter'] = self.sporter
        context['voldoet_aan_voorwaarden'] = False

        toets = vind_toets(self.sporter)
        if toets:
            is_geldig, _ = toets_geldig(toets)
            context['voldoet_aan_voorwaarden'] = is_geldig

        self._zoek_opleiding_basiscursus()

        if not self.opleiding:
            raise Http404('Basiscursus niet gevonden')

        context['opleiding'] = self.opleiding
        self.opleiding.kosten_str = format_bedrag_euro(self.opleiding.kosten_euro)

        deelnemer = self._zoek_deelnemer()

        if deelnemer.aanpassing_email == '':
            deelnemer.aanpassing_email = self.sporter.email
        if deelnemer.aanpassing_telefoon == '':
            deelnemer.aanpassing_telefoon = self.sporter.telefoon
        if deelnemer.aanpassing_geboorteplaats == '':
            deelnemer.aanpassing_geboorteplaats = self.sporter.geboorteplaats
        context['deelnemer'] = deelnemer

        context['url_wijzig'] = reverse('Opleidingen:inschrijven-basiscursus')

        context['kruimels'] = (
            (reverse('Opleidingen:overzicht'), 'Opleidingen'),
            (reverse('Opleidingen:basiscursus'), 'Basiscursus'),
            (None, 'Inschrijven')
        )

        return context

    # TODO: deze handler hergebruiken voor alle opleidingen
    def post(self, request, *args, **kwargs):
        """ Sporter heeft telefoonnummer/email/plaats aangepast en op Wijzigingen Doorgeven knop gedrukt
            We slaan de nieuwe gegevens op in het OpleidingDeelnemer record
        """

        try:
            data = json.loads(request.body)
            email = data['email'][:255]             # afkappen voor de veiligheid
            plaats = data['plaats'][:100]           # afkappen voor de veiligheid
            telefoon = data['telefoon'][:25]        # afkappen voor de veiligheid
        except (json.JSONDecodeError, UnreadablePostError, KeyError):
            # garbage in
            raise Http404('Geen valide verzoek')
        else:
            telefoon = telefoon.strip()
            if telefoon == self.sporter.telefoon:
                telefoon = ''

            email = email.strip()
            if email == self.sporter.email:
                email = ''

            plaats = plaats.strip()
            if plaats == self.sporter.geboorteplaats:
                plaats = ''

            self._zoek_opleiding_basiscursus()
            if self.opleiding:

                deelnemer = self._zoek_deelnemer(True)
                deelnemer.aanpassing_telefoon = telefoon
                deelnemer.aanpassing_email = email
                deelnemer.aanpassing_geboorteplaats = plaats
                deelnemer.save(update_fields=['aanpassing_telefoon', 'aanpassing_email', 'aanpassing_geboorteplaats'])

        out = dict()
        return JsonResponse(out)

# end of file
