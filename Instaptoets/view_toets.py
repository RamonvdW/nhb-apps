# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.utils import timezone
from django.shortcuts import redirect
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Instaptoets.models import Instaptoets
from Instaptoets.operations import (selecteer_toets_vragen, selecteer_huidige_vraag, toets_geldig, controleer_toets,
                                    vind_toets, instaptoets_is_beschikbaar)
from Sporter.models import get_sporter

TEMPLATE_BEGIN_TOETS = 'instaptoets/begin-toets.dtl'
TEMPLATE_TOON_UITSLAG = 'instaptoets/toon-uitslag.dtl'
TEMPLATE_VOLGENDE_VRAAG = 'instaptoets/volgende-vraag.dtl'


class BeginToetsView(UserPassesTestMixin, TemplateView):
    """
        Deze view geeft de stand van zaken en laat de sporter de instaptoets opstarten.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_BEGIN_TOETS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sporter = None

    def dispatch(self, request, *args, **kwargs):
        if not instaptoets_is_beschikbaar():
            # geen toets --> terug naar landing page opleidingen
            return redirect('Opleidingen:overzicht')

        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn, geen gast zijn en rol Sporter gekozen hebben
        if rol_get_huidige(self.request) == Rol.ROL_SPORTER:
            account = get_account(self.request)
            if not account.is_gast:
                self.sporter = get_sporter(account)
                return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['toets'] = toets = vind_toets(self.sporter)
        context['aantal_vragen'] = settings.INSTAPTOETS_AANTAL_VRAGEN
        context['eis_percentage'] = settings.INSTAPTOETS_AANTAL_GOED_EIS
        context['laat_starten'] = False

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

        # kies de volgende vraag die we gaan tonen
        selecteer_huidige_vraag(toets)

        url = reverse('Instaptoets:volgende-vraag')
        return HttpResponseRedirect(url)


class ToonUitslagView(UserPassesTestMixin, TemplateView):
    """
        Deze view toont de gebruiker de uitslag van de toets.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_TOON_UITSLAG
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sporter = None
        self.toets = None

    def dispatch(self, request, *args, **kwargs):
        # gebruiker moet ingelogd zijn, geen gast zijn en rol Sporter gekozen hebben
        if rol_get_huidige(self.request) == Rol.ROL_SPORTER:
            account = get_account(self.request)
            if not account.is_gast:
                self.sporter = get_sporter(account)

        if self.sporter:
            # controleer dat een toets opgestart is
            self.toets = vind_toets(self.sporter)

            if self.toets is None:
                # geen toets --> stuur naar begin pagina
                url = reverse('Instaptoets:begin')
                return HttpResponseRedirect(url)

            # controleer of de toets is afgerond
            if not self.toets.is_afgerond:
                url = reverse('Instaptoets:begin')
                return HttpResponseRedirect(url)

        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn, geen gast zijn en rol Sporter gekozen hebben
        return self.sporter is not None

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['toets'] = self.toets

        context['url_basiscursus'] = reverse('Opleidingen:basiscursus')
        context['url_sluiten'] = reverse('Plein:plein')

        context['kruimels'] = (
            (reverse('Opleidingen:overzicht'), 'Opleidingen'),
            (None, 'Resultaat instaptoets'),
        )

        return context


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
        self.toets = None

    def dispatch(self, request, *args, **kwargs):
        # gebruiker moet ingelogd zijn, geen gast zijn en rol Sporter gekozen hebben
        if rol_get_huidige(self.request) == Rol.ROL_SPORTER:
            account = get_account(self.request)
            if not account.is_gast:
                self.sporter = get_sporter(account)

        if self.sporter:
            # controleer dat een toets opgestart is
            self.toets = vind_toets(self.sporter)

            if self.toets is None:
                # geen toets --> stuur naar begin pagina
                url = reverse('Instaptoets:begin')
                return HttpResponseRedirect(url)

            # toon de uitslag van de al afgeronde toets
            if self.toets.is_afgerond:
                url = reverse('Instaptoets:toon-uitslag')
                return HttpResponseRedirect(url)

        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn, geen gast zijn en rol Sporter gekozen hebben
        return self.sporter is not None

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['toets'] = self.toets

        self.toets.vraag_nr = self.toets.aantal_antwoorden + 1

        if self.toets.huidige_vraag is None:
            raise Http404('Toets is niet beschikbaar')

        vraag = self.toets.huidige_vraag.vraag
        vraag.toon_c = vraag.antwoord_c not in ('', '-')
        vraag.toon_d = vraag.antwoord_d not in ('', '-')
        context['vraag'] = vraag

        context['url_opslaan'] = reverse('Instaptoets:antwoord')
        context['op_pagina'] = 'instaptoets-vraag-%s' % self.toets.huidige_vraag.pk

        if self.toets.aantal_antwoorden + 1 < self.toets.aantal_vragen:
            context['url_overslaan'] = context['url_opslaan']

        return context


class OntvangAntwoordView(UserPassesTestMixin, View):
    """
        Deze view accepteert de POST met het antwoord
    """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sporter = None
        self.toets = None

    def dispatch(self, request, *args, **kwargs):
        # gebruiker moet ingelogd zijn, geen gast zijn en rol Sporter gekozen hebben
        if rol_get_huidige(self.request) == Rol.ROL_SPORTER:
            account = get_account(self.request)
            if not account.is_gast:
                self.sporter = get_sporter(account)

        if self.sporter:
            # controleer dat een toets opgestart is
            self.toets = vind_toets(self.sporter)

            if self.toets is None:
                # geen toets --> stuur naar begin pagina
                url = reverse('Instaptoets:begin')
                return HttpResponseRedirect(url)

            # toon de uitslag van de al afgeronde toets
            if self.toets.is_afgerond:
                url = reverse('Instaptoets:toon-uitslag')
                return HttpResponseRedirect(url)

        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn, geen gast zijn en rol Sporter gekozen hebben
        return self.sporter is not None

    def post(self, request, *args, **kwargs):
        """ gebruiker heeft op de knop Opslaan of Overslaan gedrukt """

        url = reverse('Instaptoets:volgende-vraag')

        keuze = request.POST.get('keuze', '')
        keuze = str(keuze)[:10]     # afkappen voor de veiligheid
        # print('keuze: %s' % repr(keuze))

        antwoord = self.toets.huidige_vraag

        if keuze == 'overslaan':
            # gebruiker wil een andere vraag zien
            selecteer_huidige_vraag(self.toets, forceer=True)

        elif keuze in ('A', 'B', 'C', 'D'):
            if antwoord.antwoord == '?':
                self.toets.aantal_antwoorden += 1
                self.toets.save(update_fields=['aantal_antwoorden'])

                if self.toets.aantal_antwoorden >= self.toets.aantal_vragen:
                    self.toets.afgerond = timezone.now()
                    self.toets.is_afgerond = True
                    self.toets.save(update_fields=['afgerond', 'is_afgerond'])

            antwoord.antwoord = keuze
            antwoord.save(update_fields=['antwoord'])

            if self.toets.is_afgerond:
                controleer_toets(self.toets)
                url = reverse('Instaptoets:toon-uitslag')
            else:
                selecteer_huidige_vraag(self.toets)
        else:
            raise Http404('Foutieve parameter')

        return HttpResponseRedirect(url)


# end of file
