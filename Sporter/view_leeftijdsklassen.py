# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import TemplateView
from django.urls import reverse
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige
from .leeftijdsklassen import bereken_leeftijdsklassen_nhb, bereken_leeftijdsklassen_ifaa
from .models import get_sporter_voorkeuren
import logging


TEMPLATE_LEEFTIJDSKLASSEN = 'sporter/leeftijdsklassen.dtl'

my_logger = logging.getLogger('NHBApps.Sporter')


class LeeftijdsklassenView(UserPassesTestMixin, TemplateView):
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
            (None, 'Leeftijdsklassen'),
        )

        menu_dynamics(self.request, context)
        return context


# end of file
