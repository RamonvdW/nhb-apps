# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404, UnreadablePostError, JsonResponse
from django.utils import timezone
from django.shortcuts import render
from django.db.models import ObjectDoesNotExist
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Bestelling.operations.mandje import mandje_tel_inhoud
from Bestelling.operations.mutaties import bestel_mutatieverzoek_inschrijven_opleiding
from Betaal.format import format_bedrag_euro
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Instaptoets.operations import vind_toets, toets_geldig
from Opleiding.definities import OPLEIDING_STATUS_INSCHRIJVEN
from Opleiding.models import Opleiding, OpleidingInschrijving
from Sporter.models import get_sporter
import json

TEMPLATE_OPLEIDINGEN_INSCHRIJVEN_BASISCURSUS = 'opleiding/inschrijven-basiscursus.dtl'
TEMPLATE_OPLEIDINGEN_TOEGEVOEGD_AAN_MANDJE = 'opleiding/inschrijven-toegevoegd-aan-mandje.dtl'


class InschrijvenBasiscursusView(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDINGEN_INSCHRIJVEN_BASISCURSUS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sporter = None
        self.opleiding = None

    def _zoek_opleiding_basiscursus(self):
        self.opleiding = (Opleiding
                          .objects
                          .filter(is_basiscursus=True,
                                  status=OPLEIDING_STATUS_INSCHRIJVEN)
                          .order_by('periode_jaartal', 'periode_kwartaal')       # meest recente cursus eerst
                          .first())

    def _zoek_inschrijving(self, mag_database_wijzigen=False):
        """ zoek de OpleidingDeelnemer voor de sporter
            tijdens POST maken we deze aan
        """
        inschrijving = OpleidingInschrijving.objects.filter(sporter=self.sporter, opleiding=self.opleiding).first()

        if not inschrijving:
            inschrijving = OpleidingInschrijving(
                            sporter=self.sporter,
                            opleiding=self.opleiding)

            if mag_database_wijzigen:
                inschrijving.save()

        return inschrijving

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        # instaptoets alleen aan leden tonen
        # gebruiker moet ingelogd zijn, geen gast zijn en rol Sporter gekozen hebben
        if rol_get_huidige(self.request) == Rol.ROL_SPORTER:
            account = get_account(self.request)
            if not account.is_gast:
                self.sporter = get_sporter(account)

        if self.sporter:
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

        if self.sporter:
            inschrijving = self._zoek_inschrijving()

            if inschrijving.aanpassing_email == '':
                inschrijving.aanpassing_email = self.sporter.email
            if inschrijving.aanpassing_telefoon == '':
                inschrijving.aanpassing_telefoon = self.sporter.telefoon
            if inschrijving.aanpassing_geboorteplaats == '':
                inschrijving.aanpassing_geboorteplaats = self.sporter.geboorteplaats
            context['inschrijving'] = inschrijving

            context['url_wijzig'] = reverse('Opleiding:inschrijven-basiscursus')
            context['url_toevoegen'] = reverse('Opleiding:inschrijven-toevoegen-aan-mandje')

        context['kruimels'] = (
            (reverse('Opleiding:overzicht'), 'Opleidingen'),
            (None, 'Inschrijven')
        )

        return context

    # TODO: deze handler hergebruiken voor alle opleidingen
    def post(self, request, *args, **kwargs):
        """ Sporter heeft telefoonnummer/email/plaats aangepast en op Wijzigingen Doorgeven knop gedrukt
            We slaan de nieuwe gegevens op in het OpleidingDeelnemer record
        """

        # instaptoets alleen aan leden tonen
        # gebruiker moet ingelogd zijn, geen gast zijn en rol Sporter gekozen hebben
        if rol_get_huidige(self.request) == Rol.ROL_SPORTER:
            account = get_account(self.request)
            if not account.is_gast:
                self.sporter = get_sporter(account)

        if not self.sporter:
            raise Http404('Inlog nodig')

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

                deelnemer = self._zoek_inschrijving(True)

                stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')

                if deelnemer.aanpassing_telefoon != telefoon:
                    deelnemer.log += "[%s] Telefoon aangepast naar %s\n" % (stamp_str, telefoon)
                    deelnemer.aanpassing_telefoon = telefoon

                if deelnemer.aanpassing_email != email:
                    deelnemer.log += "[%s] E-mail aangepast naar %s\n" % (stamp_str, email)
                    deelnemer.aanpassing_email = email

                if deelnemer.aanpassing_geboorteplaats != plaats:
                    deelnemer.log += "[%s] Geboorteplaats aangepast naar %s\n" % (stamp_str, plaats)
                    deelnemer.aanpassing_geboorteplaats = plaats

                deelnemer.save(update_fields=['aanpassing_telefoon', 'aanpassing_email', 'aanpassing_geboorteplaats'])

        out = dict()
        return JsonResponse(out)


class ToevoegenAanMandjeView(UserPassesTestMixin, View):

    """ Met deze view wordt het toevoegen van een opleiding aan het mandje van de koper afgehandeld """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sporter = None

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

    def post(self, request, *args, **kwargs):
        opleiding_str = request.POST.get('opleiding', '')[:6]       # afkappen voor de veiligheid

        try:
            opleiding_pk = int(opleiding_str)
        except (ValueError, TypeError):
            raise Http404('Slecht verzoek')

        try:
            opleiding = Opleiding.objects.filter(status=OPLEIDING_STATUS_INSCHRIJVEN).get(pk=opleiding_pk)
        except ObjectDoesNotExist:
            raise Http404('Slecht verzoek (2)')

        account_koper = get_account(request)

        now = timezone.now()
        stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Toegevoegd aan het mandje van %s\n" % (stamp_str, account_koper.get_account_full_name())

        # zoek of maak de deelnemer
        inschrijving, _ = OpleidingInschrijving.objects.get_or_create(sporter=self.sporter, opleiding=opleiding)
        inschrijving.wanneer_aangemeld = now       # overschrijf eventueel moment wijzigen persoonsgegevens
        inschrijving.koper = account_koper
        inschrijving.log += msg
        inschrijving.save()

        # zet dit verzoek door naar de achtergrondtaak
        snel = str(request.POST.get('snel', ''))[:1]
        bestel_mutatieverzoek_inschrijven_opleiding(account_koper, inschrijving, snel == '1')

        mandje_tel_inhoud(self.request, account_koper)

        # render de pagina "toegevoegd aan mandje"

        context = dict()

        context['url_verder'] = reverse('Opleiding:inschrijven-basiscursus')
        context['url_mandje'] = reverse('Bestel:toon-inhoud-mandje')
        context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Opleiding:overzicht'), 'Opleidingen'),
            (None, 'Toegevoegd aan mandje')
        )

        return render(request, TEMPLATE_OPLEIDINGEN_TOEGEVOEGD_AAN_MANDJE, context)


# end of file
