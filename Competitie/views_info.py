# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from Account.models import get_account
from BasisTypen.models import TemplateCompetitieIndivKlasse
from Competitie.models import Regiocompetitie, RegiocompetitieTeam
from Geo.models import Regio
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
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (None, 'Informatie')
        )

        return context


class InfoTeamCompetitieView(TemplateView):

    """ Django class-based view voor de Competitie Info Teams """

    # class variables shared by all instances
    template_name = TEMPLATE_INFO_TEAMCOMPETITIE

    jouw_regio_team_comp = {
        (True, True): "Jouw regio organiseert een teamcompetitie voor de bondscompetities Indoor en 25m 1pijl.",
        (True, False): "Jouw regio organiseert een teamcompetitie voor de bondscompetitie Indoor.",
        (False, True): "Jouw regio organiseert een teamcompetitie voor de bondscompetitie 25m 1pijl.",
        (False, False): "Jouw regio organiseert geen teamcompetitie.",
    }

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        account = get_account(self.request)
        if account and account.is_authenticated:
            sporter = (Sporter
                       .objects
                       .filter(account=account)
                       .select_related('bij_vereniging',
                                       'bij_vereniging__regio')
                       .first())
            if sporter:
                ver = sporter.bij_vereniging
                if ver:
                    context['toon_teams_persoonlijk'] = True
                    context['jouw_regio'] = ver.regio

                    # aantal teams tellen
                    aantal_18m = 0
                    aantal_25m = 0
                    for team in (RegiocompetitieTeam
                                 .objects
                                 .filter(vereniging=ver)
                                 .select_related('regiocompetitie__regio',
                                                 'regiocompetitie__competitie')):

                        is_indoor = team.regiocompetitie.competitie.is_indoor()
                        if is_indoor:
                            aantal_18m += 1
                        else:
                            aantal_25m += 1
                    # for
                    context['jouw_ver_aantal_regio_teams_18m'] = aantal_18m
                    context['jouw_ver_aantal_regio_teams_25m'] = aantal_25m

                    # bepaal of de regio een teamcompetitie organiseert
                    # en welk type teams (VSG / vast)
                    regio_teams_indoor = False
                    vaste_teams_indoor = False
                    regio_teams_25m1pijl = False
                    vaste_teams_25m1pijl = False
                    for deelcomp in (Regiocompetitie
                                     .objects
                                     .filter(regio=ver.regio)
                                     .select_related('competitie')):
                        is_indoor = deelcomp.competitie.is_indoor()
                        if is_indoor:
                            regio_teams_indoor = deelcomp.regio_organiseert_teamcompetitie
                            vaste_teams_indoor = deelcomp.regio_heeft_vaste_teams
                        else:
                            regio_teams_25m1pijl = deelcomp.regio_organiseert_teamcompetitie
                            vaste_teams_25m1pijl = deelcomp.regio_heeft_vaste_teams
                    # for

                    tup = (regio_teams_indoor, regio_teams_25m1pijl)
                    context['jouw_regio_team_comp'] = self.jouw_regio_team_comp[tup]
                    context['jouw_regio_vaste_teams'] = vaste_teams_indoor or vaste_teams_25m1pijl

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (None, 'Info teamcompetitie')
        )

        return context


def redirect_leeftijden(request):
    url = reverse('Sporter:leeftijdsgroepen')
    return HttpResponseRedirect(url)


# end of file
