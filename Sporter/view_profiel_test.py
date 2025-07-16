# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404, HttpResponse
from django.conf import settings
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from BasisTypen.definities import ORGANISATIE_WA
from BasisTypen.models import BoogType
from Competitie.plugin_sporter import get_sporter_competities
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Sporter.operations import get_sporter_gekozen_bogen, get_sporter_voorkeuren

TEMPLATE_PROFIEL = 'sporter/profiel.dtl'


class ProfielTestView(UserPassesTestMixin, TemplateView):

    """ Dit een van de bondscompetities sectie van de profielpagina van een sporter """

    template_name = TEMPLATE_PROFIEL
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None
        self.account = None
        self.sporter = None
        self.ver = None
        self.voorkeuren = None
        self.alle_competitie_bogen = BoogType.objects.filter(organisatie=ORGANISATIE_WA)
        self.alle_wedstrijd_bogen = BoogType.objects.all()

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en rol Sporter gekozen hebben
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu == Rol.ROL_SPORTER

    def dispatch(self, request, *args, **kwargs):
        """ wegsturen als het we geen vragen meer hebben + bij oneigenlijk gebruik """

        if not settings.IS_TEST_SERVER:
            return HttpResponse(status=410)

        if request.user.is_authenticated:
            self.account = get_account(request)

            if self.account.is_gast:
                raise Http404('Geen toegang')

            self.sporter = (self.account
                            .sporter_set
                            .select_related('bij_vereniging',
                                            'bij_vereniging__regio',
                                            'bij_vereniging__regio__rayon')
                            .first())

            if self.sporter:                                    # pragma: no branch
                self.ver = self.sporter.bij_vereniging

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['case_nr'] = kwargs['case'][:6]                             # afkappen voor de veiligheid
        context['case_tekst'] = self.request.GET.get('tekst', '??')[:100]   # afkappen voor de veiligheid

        context['sporter'] = self.sporter
        self.voorkeuren = get_sporter_voorkeuren(self.sporter)

        boog_afk2sporterboog, wedstrijdbogen = get_sporter_gekozen_bogen(self.sporter, self.alle_wedstrijd_bogen)
        context['moet_bogen_kiezen'] = len(wedstrijdbogen) == 0

        context['toon_bondscompetities'] = False
        if self.ver:

            # case 1 toont geen bondscompetities
            # dekt ook: geen voorkeur voor de bondscompetities
            context['toon_bondscompetities'] = True

            # er is een Indoor en 25m1pijl competitie
            lijst_comps, lijst_kan_inschrijven, lijst_inschrijvingen = get_sporter_competities(self.sporter,
                                                                                               wedstrijdbogen,
                                                                                               boog_afk2sporterboog)
            # print('case: %s' % case_nr)
            # print('   lijst_kan_inschrijven:', lijst_kan_inschrijven)
            # print('   lijst_inschrijvingen:', lijst_inschrijvingen)

            context['competities'] = lijst_comps
            context['comp_kan_inschrijven'] = len(lijst_kan_inschrijven) > 0
            context['deelcomps_lijst_kan_inschrijven'] = lijst_kan_inschrijven

            context['comp_is_ingeschreven'] = len(lijst_inschrijvingen) > 0
            context['comp_inschrijvingen_sb'] = lijst_inschrijvingen

            context['hint_voorkeuren'] = False
            # als de competitie open is voor inschrijven
            # en de sporter is nog niet aangemeld
            # en de sporter heeft geen bogen ingeschreven
            if not context['comp_kan_inschrijven']:
                for comp in lijst_comps:
                    if comp.is_open_voor_inschrijven():
                        context['hint_voorkeuren'] = True
                # for

            if not self.voorkeuren.voorkeur_meedoen_competitie:
                if len(lijst_inschrijvingen) == 0:      # pragma: no branch
                    # niet ingeschreven en geen interesse
                    context['toon_bondscompetities'] = False

        context['geen_basic'] = True        # onderdrukt delen van het profiel

        context['kruimels'] = (
            (None, 'Mijn pagina test'),
        )

        return context


# end of file
