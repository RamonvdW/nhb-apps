# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.utils import timezone
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Functie.rol import rol_get_huidige, Rollen
from Instaptoets.models import Instaptoets
from Instaptoets.operations import selecteer_toets_vragen, selecteer_huidige_vraag, toets_geldig, controleer_toets
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
        self.toets = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn, geen gast zijn en rol Sporter gekozen hebben
        return self.sporter is not None

    def dispatch(self, request, *args, **kwargs):
        # gebruiker moet ingelogd zijn, geen gast zijn en rol Sporter gekozen hebben
        if rol_get_huidige(self.request) == Rollen.ROL_SPORTER:
            account = get_account(self.request)
            if not account.is_gast:
                self.sporter = get_sporter(account)

        if self.sporter:
            # controleer dat een toets opgestart is
            self.toets = (Instaptoets
                          .objects
                          .filter(sporter=self.sporter)
                          .order_by('opgestart')         # nieuwste eerst
                          .first())

            if self.toets is None:
                # geen toets --> stuur naar begin pagina
                url = reverse('Instaptoets:begin')
                return HttpResponseRedirect(url)

            # controleer of de toets is afgerond
            if self.toets.is_afgerond:
                url = reverse('Instaptoets:begin')
                return HttpResponseRedirect(url)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['toets'] = self.toets

        self.toets.vraag_nr = self.toets.aantal_antwoorden + 1

        # kies de huidige vraag, indien deze nog niet gekozen is
        selecteer_huidige_vraag(self.toets)

        vraag = self.toets.huidige_vraag.vraag
        vraag.toon_c = vraag.antwoord_c not in ('', '-')
        vraag.toon_d = vraag.antwoord_d not in ('', '-')
        context['vraag'] = vraag

        context['url_opslaan'] = reverse('Instaptoets:antwoord')

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

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn, geen gast zijn en rol Sporter gekozen hebben
        return self.sporter is not None

    def dispatch(self, request, *args, **kwargs):
        # gebruiker moet ingelogd zijn, geen gast zijn en rol Sporter gekozen hebben
        if rol_get_huidige(self.request) == Rollen.ROL_SPORTER:
            account = get_account(self.request)
            if not account.is_gast:
                self.sporter = get_sporter(account)

        if self.sporter:
            # controleer dat een toets opgestart is
            self.toets = (Instaptoets
                          .objects
                          .filter(sporter=self.sporter)
                          .order_by('opgestart')         # nieuwste eerst
                          .select_related('huidige_vraag')
                          .first())

            if self.toets is None:
                # geen toets --> stuur naar begin pagina
                url = reverse('Instaptoets:begin')
                return HttpResponseRedirect(url)

        return super().dispatch(request, *args, **kwargs)

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
                    url = reverse('Instaptoets:begin')

            antwoord.antwoord = keuze
            antwoord.save(update_fields=['antwoord'])

            if self.toets.is_afgerond:
                controleer_toets(self.toets)
            else:
                selecteer_huidige_vraag(self.toets)
        else:
            raise Http404('Foutieve parameter')

        return HttpResponseRedirect(url)


# end of file
