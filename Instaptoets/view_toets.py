# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Functie.rol import rol_get_huidige, Rollen
from Instaptoets.models import Instaptoets
from Instaptoets.operations import selecteer_toets_vragen, selecteer_huidige_vraag, toets_geldig
from Sporter.models import get_sporter

TEMPLATE_BEGIN_TOETS = 'instaptoets/begin-toets.dtl'
TEMPLATE_VOLGENDE_VRAAG = 'instaptoets/volgende-vraag.dtl'


class BeginToetsView(UserPassesTestMixin, TemplateView):
    """
        Deze view geeft de pagina waarmee de gebruiker zijn wachtwoord kan wijzigen
    """

    # class variables shared by all instances
    template_name = TEMPLATE_BEGIN_TOETS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sporter = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn, geen gast zijn en rol Sporter gekozen hebben
        if rol_get_huidige(self.request) == Rollen.ROL_SPORTER:
            account = get_account(self.request)
            if not account.is_gast:
                self.sporter = get_sporter(account)
                return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['toets'] = toets = Instaptoets.objects.filter(sporter=self.sporter).first()
        if not toets:
            context['laat_starten'] = True
            context['url_starten'] = reverse('Instaptoets:begin')
        else:
            if toets.aantal_antwoorden < toets.aantal_vragen:
                context['url_vervolg'] = reverse('Instaptoets:volgende-vraag')
            else:
                geldig, toets.geldig_dagen = toets_geldig(toets)
                if not geldig:
                    context['laat_starten'] = True
                    context['url_starten'] = reverse('Instaptoets:begin')

        context['kruimels'] = (
            (reverse('Opleidingen:overzicht'), 'Opleidingen'),
            (None, 'Instaptoets'),
        )

        return context

    def post(self, request, *args, **kwargs):
        """ Sporter heeft op de knop gedrukt om de toets op te starten """
        toets, _ = Instaptoets.objects.get_or_create(sporter=self.sporter)

        selecteer_toets_vragen(toets)

        url = reverse('Instaptoets:volgende-vraag')
        return HttpResponseRedirect(url)


class VolgendeVraagView(UserPassesTestMixin, TemplateView):
    """
        Deze view geeft de pagina waarmee de gebruiker zijn wachtwoord kan wijzigen
    """

    # class variables shared by all instances
    template_name = TEMPLATE_VOLGENDE_VRAAG
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sporter = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn, geen gast zijn en rol Sporter gekozen hebben
        if rol_get_huidige(self.request) == Rollen.ROL_SPORTER:
            account = get_account(self.request)
            if not account.is_gast:
                self.sporter = get_sporter(account)
                return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        toets = (Instaptoets
                 .objects
                 .filter(sporter=self.sporter)
                 .order_by('opgestart')         # nieuwste eerst
                 .first())

        context['toets'] = toets
        toets.vraag_nr = toets.aantal_antwoorden + 1

        selecteer_huidige_vraag(toets)
        vraag = toets.huidige_vraag.vraag
        vraag.toon_d = vraag.antwoord_d not in ('', '-')
        context['vraag'] = vraag

        return context


# end of file
