# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from BasisTypen.definities import GESLACHT_MAN, GESLACHT_ANDERS
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Sporter.leeftijdsklassen import (bereken_leeftijdsklassen_wa,
                                      bereken_leeftijdsklassen_khsn,
                                      bereken_leeftijdsklassen_ifaa,
                                      bereken_leeftijdsklassen_bondscompetitie)
from Sporter.models import get_sporter
from Sporter.operations import get_sporter_voorkeuren
from types import SimpleNamespace


TEMPLATE_LEEFTIJDSKLASSEN = 'sporter/jouw_leeftijdsklassen.dtl'
TEMPLATE_LEEFTIJDSGROEPEN = 'sporter/leeftijdsgroepen.dtl'


class WedstrijdLeeftijdenPersoonlijkView(UserPassesTestMixin, TemplateView):
    """ Django class-based view voor de leeftijdsklassen """

    # class variables shared by all instances
    template_name = TEMPLATE_LEEFTIJDSKLASSEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rol.ROL_NONE       # NONE is gebruiker die niet ingelogd is

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # gegarandeerd ingelogd door test_func()
        account = get_account(self.request)
        sporter = get_sporter(account)
        voorkeur = get_sporter_voorkeuren(sporter)

        context['is_gast'] = sporter.is_gast

        if voorkeur.wedstrijd_geslacht_gekozen:
            # geslacht M/V of
            # geslacht X + keuze voor M/V gemaakt
            wedstrijdgeslacht = voorkeur.wedstrijd_geslacht
            wedstrijdgeslacht_khsn = voorkeur.wedstrijd_geslacht
        else:
            # geslacht X, geen keuze gemaakt --> neem mannen
            wedstrijdgeslacht = GESLACHT_MAN
            wedstrijdgeslacht_khsn = GESLACHT_ANDERS

        # pak het huidige jaar na conversie naar lokale tijdzone
        # zodat dit ook goed gaat in de laatste paar uren van het jaar
        now = timezone.now()  # is in UTC
        now = timezone.localtime(now)  # convert to active timezone (say Europe/Amsterdam)

        geboorte_jaar = sporter.geboorte_datum.year

        huidige_jaar, leeftijd, lkl_dit_jaar, lkl_list = bereken_leeftijdsklassen_wa(geboorte_jaar, wedstrijdgeslacht, now.year)
        context['huidige_jaar'] = huidige_jaar
        context['leeftijd'] = leeftijd
        context['lkl_wa'] = lkl_list
        context['lkl_wa_dit_jaar'] = lkl_dit_jaar

        huidige_jaar, leeftijd, lkl_dit_jaar, lkl_lst = bereken_leeftijdsklassen_khsn(geboorte_jaar, wedstrijdgeslacht_khsn, now.year)
        context['lkl_khsn'] = lkl_lst
        spl = lkl_dit_jaar.split(' of ')
        context['lkl_khsn_dit_jaar_1'] = spl[0]
        if len(spl) > 1:
            context['lkl_khsn_dit_jaar_2'] = spl[1]

        _, lkl_lst = bereken_leeftijdsklassen_bondscompetitie(geboorte_jaar, wedstrijdgeslacht_khsn, now.year, now.month)
        context['lkl_comp'] = lkl_lst

        context['wlst_ifaa'] = bereken_leeftijdsklassen_ifaa(geboorte_jaar, wedstrijdgeslacht, now.year)

        context['kruimels'] = (
            (reverse('Sporter:profiel'), 'Mijn pagina'),
            (None, 'Jouw leeftijdsklasse'),
        )

        return context


class InfoLeeftijdenView(TemplateView):

    """ Django class-based view voor de Competitie Info """

    # class variables shared by all instances
    template_name = TEMPLATE_LEEFTIJDSGROEPEN

    @staticmethod
    def _maak_jaren(jaar, begin_leeftijd, aantal):
        jaar -= begin_leeftijd
        jaren = list()
        while aantal > 0:
            jaren.append(str(jaar))
            jaar -= 1
            aantal -= 1
        # while
        return ", ".join(jaren)

    def _comp_info(self, jaar):
        comp = SimpleNamespace()
        comp.seizoen = '%s/%s' % (jaar, jaar+1)
        comp.klassen = dict()       # ['klasse'] = list(jaartal, jaartal, ..)

        jaar += 1       # informatie voor het tweede jaar produceren
        comp.onder12 = self._maak_jaren(jaar, 11, 1)     # 10, 11
        comp.onder14 = self._maak_jaren(jaar, 12, 2)     # 12, 13
        comp.onder18 = self._maak_jaren(jaar, 14, 4)     # 14, 15, 16, 17
        comp.onder21 = self._maak_jaren(jaar, 18, 3)     # 18, 19, 20
        comp.vanaf21 = str(jaar - 21)
        return comp

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        huidige_jaar = timezone.now().year

        context['comp_1'] = self._comp_info(huidige_jaar - 1)
        context['comp_2'] = self._comp_info(huidige_jaar)

        context['persoonlijke_leeftijdsklassen'] = self.request.user.is_authenticated

        rol = rol_get_huidige(self.request)
        if rol == Rol.ROL_SPORTER:
            context['kruimels'] = (
                (reverse('Sporter:profiel'), 'Mijn pagina'),
                (None, 'Leeftijdsgroepen')
            )
        else:
            context['kruimels'] = (
                (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
                (None, 'Leeftijdsgroepen')
            )

        return context


# end of file
