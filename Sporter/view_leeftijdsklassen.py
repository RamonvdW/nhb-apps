# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige
from Sporter.leeftijdsklassen import bereken_leeftijdsklassen_nhb, bereken_leeftijdsklassen_ifaa
from Sporter.models import get_sporter_voorkeuren
from types import SimpleNamespace


TEMPLATE_LEEFTIJDSKLASSEN = 'sporter/leeftijdsklassen.dtl'
TEMPLATE_LEEFTIJDSGROEPEN = 'sporter/leeftijdsgroepen.dtl'


def redirect_leeftijdsklassen(request):
    url = reverse('Sporter:leeftijdsklassen')
    return HttpResponseRedirect(url)


class WedstrijdLeeftijdenPersoonlijkView(UserPassesTestMixin, TemplateView):
    """ Django class-based view voor de leeftijdsklassen """

    # class variables shared by all instances
    template_name = TEMPLATE_LEEFTIJDSKLASSEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol = rol_get_huidige(self.request)
        return rol != Rollen.ROL_NONE       # NONE is gebruiker die niet ingelogd is

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # gegarandeerd ingelogd door test_func()
        account = self.request.user
        sporter = account.sporter_set.all()[0]
        voorkeur = get_sporter_voorkeuren(sporter)

        if voorkeur.wedstrijd_geslacht_gekozen:
            # geslacht M/V of
            # geslacht X + keuze voor M/V gemaakt
            geslacht = voorkeur.wedstrijd_geslacht
        else:
            # geslacht X, geen keuze gemaakt --> neem mannen
            geslacht = 'M'

        geboorte_jaar = sporter.geboorte_datum.year

        huidige_jaar, leeftijd, wlst, clst, lkl_volgende_competitie = bereken_leeftijdsklassen_nhb(geboorte_jaar)
        context['huidige_jaar'] = huidige_jaar
        context['leeftijd'] = leeftijd
        context['wlst'] = wlst
        context['clst'] = clst
        context['lkl_volgende_competitie'] = lkl_volgende_competitie

        context['wlst_ifaa'] = bereken_leeftijdsklassen_ifaa(geboorte_jaar, geslacht)

        context['kruimels'] = (
            (reverse('Sporter:profiel'), 'Mijn pagina'),
            (None, 'Jouw leeftijdsklasse'),
        )

        menu_dynamics(self.request, context)
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

        context['kruimels'] = (
            (reverse('Sporter:profiel'), 'Mijn pagina'),
            (None, 'Leeftijdsgroepen')
        )

        menu_dynamics(self.request, context)
        return context


# end of file
