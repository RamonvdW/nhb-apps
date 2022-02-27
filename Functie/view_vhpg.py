# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.rechten import account_rechten_eval_now
from Plein.menu import menu_dynamics
from Logboek.models import schrijf_in_logboek
from .rol import Rollen, rol_get_huidige
from .models import VerklaringHanterenPersoonsgegevens, account_needs_vhpg
from .forms import AccepteerVHPGForm


TEMPLATE_VHPG_ACCEPTATIE = 'functie/vhpg-acceptatie.dtl'
TEMPLATE_VHPG_AFSPRAKEN = 'functie/vhpg-afspraken.dtl'
TEMPLATE_VHPG_OVERZICHT = 'functie/vhpg-overzicht.dtl'


class VhpgAfsprakenView(UserPassesTestMixin, TemplateView):

    """ Django class-based view om van rol te wisselen """

    # class variables shared by all instances
    template_name = TEMPLATE_VHPG_AFSPRAKEN

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.vhpg = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        if self.request.user.is_authenticated:
            _, self.vhpg = account_needs_vhpg(self.request.user)
            return True
        return False

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['acceptatie_datum'] = self.vhpg.acceptatie_datum

        context['kruimels'] = (
            (reverse('Functie:wissel-van-rol'), 'Wissel van rol'),
            (None, 'Afspraken inzien')
        )

        menu_dynamics(self.request, context)
        return context


def account_vhpg_is_geaccepteerd(account):
    """ onthoud dat de vhpg net geaccepteerd is door de gebruiker
    """
    # Deze functie wordt aangeroepen vanuit een POST handler
    # concurrency beveiliging om te voorkomen dat 2 records gemaakt worden
    _ = (VerklaringHanterenPersoonsgegevens
         .objects
         .update_or_create(account=account,
                           defaults={'acceptatie_datum': timezone.now()}))


class VhpgAcceptatieView(TemplateView):
    """ Met deze view kan de gebruiker de verklaring hanteren persoonsgegevens accepteren
    """

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        if not request.user.is_authenticated:
            # gebruiker is niet ingelogd, dus zou hier niet moeten komen
            return HttpResponseRedirect(reverse('Plein:plein'))

        account = request.user
        needs_vhpg, _ = account_needs_vhpg(account)
        if not needs_vhpg:
            # gebruiker heeft geen VHPG nodig
            return HttpResponseRedirect(reverse('Plein:plein'))

        form = AccepteerVHPGForm()

        context = dict()
        context['form'] = form

        context['kruimels'] = (
            (reverse('Functie:wissel-van-rol'), 'Wissel van rol'),
            (None, 'Persoonsgegevens')
        )

        menu_dynamics(request, context, actief="wissel-van-rol")
        return render(request, TEMPLATE_VHPG_ACCEPTATIE, context)

    @staticmethod
    def post(request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de knop van het formulier.
        """
        if not request.user.is_authenticated:
            # gebruiker is niet ingelogd, dus stuur terug naar af
            return HttpResponseRedirect(reverse('Plein:plein'))

        form = AccepteerVHPGForm(request.POST)
        if form.is_valid():
            # hier komen we alleen als de checkbox gezet is
            account = request.user
            account_vhpg_is_geaccepteerd(account)
            schrijf_in_logboek(account, 'Rollen', 'VHPG geaccepteerd')
            account_rechten_eval_now(request, account)
            return HttpResponseRedirect(reverse('Functie:wissel-van-rol'))

        # checkbox is verplicht --> nog een keer
        context = {'form': form}
        menu_dynamics(request, context, actief="hetplein")
        return render(request, TEMPLATE_VHPG_ACCEPTATIE, context)


class VhpgOverzichtView(UserPassesTestMixin, ListView):

    """ Met deze view kan de Manager Competitiezaken een overzicht krijgen van alle beheerders
        die de VHPG geaccepteerd hebben en wanneer dit voor het laatste was.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_VHPG_OVERZICHT
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        if self.request.user.is_authenticated:
            rol_nu = rol_get_huidige(self.request)
            return rol_nu == Rollen.ROL_BB
        return False

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        # er zijn ongeveer 30 beheerders
        # voorlopig geen probleem als een beheerder vaker voorkomt
        return VerklaringHanterenPersoonsgegevens.objects.order_by('-acceptatie_datum')[:100]

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['kruimels'] = (
            (None, 'VHPG status'),
        )

        menu_dynamics(self.request, context)
        return context


# end of file
