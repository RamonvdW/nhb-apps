# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from django.urls import reverse
from Account.models import get_account
from BasisTypen.models import TemplateCompetitieIndivKlasse
from Geo.models import Regio
from Plein.menu import menu_dynamics
from Sporter.models import Sporter

TEMPLATE_INFO_COMPETITIE = 'competitie/info-competitie.dtl'
TEMPLATE_INFO_TEAMCOMPETITIE = 'competitie/info-teamcompetitie.dtl'


class InfoCompetitieView(TemplateView):

    """ Django class-based view voor de Competitie Info """

    # class variables shared by all instances
    template_name = TEMPLATE_INFO_COMPETITIE

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['regios'] = (Regio
                             .objects
                             .filter(is_administratief=False)
                             .select_related('rayon')
                             .order_by('regio_nr'))

        account = get_account(self.request)
        if account and account.is_authenticated:
            sporter = Sporter.objects.filter(account=account).first()
            if sporter:
                ver = sporter.bij_vereniging
                if ver:
                    context['mijn_vereniging'] = ver
                    for obj in context['regios']:
                        if obj == ver.regio:
                            obj.mijn_regio = True
                    # for

        # tel de template klassen, zodat dit ook werkt als er geen competitie actief is
        context['klassen_count'] = (TemplateCompetitieIndivKlasse
                                    .objects
                                    .exclude(is_onbekend=True)
                                    .count())

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (None, 'Informatie')
        )

        menu_dynamics(self.request, context)
        return context


class InfoTeamCompetitieView(TemplateView):

    """ Django class-based view voor de Competitie Info Teams """

    # class variables shared by all instances
    template_name = TEMPLATE_INFO_TEAMCOMPETITIE

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (None, 'Info teamcompetitie')
        )

        menu_dynamics(self.request, context)
        return context


def redirect_leeftijden(request):
    url = reverse('Sporter:leeftijdsgroepen')
    return HttpResponseRedirect(url)


# end of file
