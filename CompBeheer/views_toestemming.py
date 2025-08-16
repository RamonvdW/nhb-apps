# -*- coding: utf-8 -*-
#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.models import Competitie
from CompKamp.operations.maak_mutatie import maak_mutatie_wedstrijdformulieren_aanmaken
from CompKamp.operations.kamp_programmas import ontbrekende_wedstrijdformulieren_rk_bk
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from GoogleDrive.operations.authenticatie import check_heeft_toestemming
from GoogleDrive.operations.authenticatie import get_authorization_url

TEMPLATE_COMPBEHEER_DRIVE_TOESTEMMING = 'compbeheer/drive-toestemming.dtl'
TEMPLATE_COMPBEHEER_DRIVE_AANMAKEN = 'compbeheer/drive-aanmaken.dtl'


class ToestemmingView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de manager om toestemming te geven tot een Google Drive """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPBEHEER_DRIVE_TOESTEMMING
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_BB

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # kijk of de toestemming er al is
        if check_heeft_toestemming():
            context['heeft_toestemming'] = True
        else:
            context['url_toestemming'] = reverse('CompBeheer:wf-toestemming-drive')

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (None, 'Toestemming Google Drive'),
        )

        return context

    @staticmethod
    def post(request, *args, **kwargs):

        account = get_account(request)
        url = get_authorization_url(account.username, account.bevestigde_email)

        # stuur de gebruiker door naar Google
        return HttpResponseRedirect(url)


class AanmakenView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de manager om het aanmaken van de formulieren op te starten """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPBEHEER_DRIVE_AANMAKEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_BB

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # kijk of de toestemming er al is
        if not check_heeft_toestemming():
            raise Http404('Geen toestemming')

        comp18 = Competitie.objects.exclude(regiocompetitie_is_afgesloten=True).filter(afstand=18).first()
        if comp18:
            lst18 = ontbrekende_wedstrijdformulieren_rk_bk(comp18)
            context['aantal_aanmaken_18'] = len(lst18)

        comp25 = Competitie.objects.exclude(regiocompetitie_is_afgesloten=True).filter(afstand=25).first()
        if comp25:
            lst25 = ontbrekende_wedstrijdformulieren_rk_bk(comp25)
            context['aantal_aanmaken_25'] = len(lst25)

        context['url_aanmaken'] = reverse('CompBeheer:wf-aanmaken')

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (None, 'Aanmaken wedstrijdformulieren'),
        )

        return context

    @staticmethod
    def post(request, *args, **kwargs):
        # gebruiker heeft op de knop BEGIN gedrukt
        # het form heeft een POST gedaan, welke hier uit komt

        account = get_account(request)
        door_str = account.get_account_full_name()

        comp18 = Competitie.objects.exclude(regiocompetitie_is_afgesloten=True).filter(afstand=18).first()
        if comp18:
            maak_mutatie_wedstrijdformulieren_aanmaken(comp18, door_str)

        comp25 = Competitie.objects.exclude(regiocompetitie_is_afgesloten=True).filter(afstand=25).first()
        if comp25:
            maak_mutatie_wedstrijdformulieren_aanmaken(comp25, door_str)

        return HttpResponseRedirect(reverse('Competitie:kies'))


# end of file
