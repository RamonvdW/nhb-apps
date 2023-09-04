# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige
from Sporter.models import SporterBoog
from Score.definities import SCORE_WAARDE_VERWIJDERD
from Score.forms import ScoreGeschiedenisForm
from Score.models import AanvangsgemiddeldeHist, ScoreHist
from Plein.menu import menu_dynamics


TEMPLATE_OVERZICHT = 'scheidsrechter/overzicht.dtl'


class OverzichtView(UserPassesTestMixin, View):

    """ Django class-based view voor het de sporter """

    # class variables shared by all instances
    template = TEMPLATE_OVERZICHT
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_get_huidige(self.request) == Rollen.ROL_SPORTER

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """

        context = dict()

        context['kruimels'] = (
            (None, 'Scheidsrechters'),
        )

        menu_dynamics(self.request, context)
        return render(request, self.template, context)


# end of file
