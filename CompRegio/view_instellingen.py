# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils.formats import localize
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import (LAAG_REGIO, INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_2,
                               TEAM_PUNTEN_MODEL_FORMULE1, TEAM_PUNTEN_MODEL_TWEE, TEAM_PUNTEN_MODEL_SOM_SCORES, TEAM_PUNTEN,
                               Competitie, DeelCompetitie)
from Competitie.menu import menu_dynamics_competitie
from Functie.rol import Rollen, rol_get_huidige_functie
from Handleiding.views import reverse_handleiding
from types import SimpleNamespace
import datetime


TEMPLATE_COMPREGIO_RCL_INSTELLINGEN = 'compregio/rcl-instellingen.dtl'
TEMPLATE_COMPREGIO_INSTELLINGEN_REGIO_GLOBAAL = 'compregio/rcl-instellingen-globaal.dtl'


class RegioInstellingenView(UserPassesTestMixin, TemplateView):

    """ Deze view kan de RCL instellingen voor de regiocompetitie aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPREGIO_RCL_INSTELLINGEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_RCL

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            regio_nr = int(kwargs['regio_nr'][:6])  # afkappen voor de veiligheid
            comp_pk = int(kwargs['comp_pk'][:6])    # afkappen voor de veiligheid
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_regio')
                        .get(competitie=comp_pk,
                             laag=LAAG_REGIO,
                             nhb_regio__regio_nr=regio_nr))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404()

        if deelcomp.functie != self.functie_nu:
            # niet de beheerder
            raise PermissionDenied()

        deelcomp.competitie.bepaal_fase()
        if deelcomp.competitie.fase > 'F':
            raise Http404('Verkeerde competitie fase')

        if deelcomp.competitie.fase > 'A':
            context['readonly_na_fase_A'] = True

            if deelcomp.competitie.fase > 'D':
                context['readonly_na_fase_D'] = True

        context['deelcomp'] = deelcomp

        context['opt_team_alloc'] = opts = list()

        obj = SimpleNamespace()
        obj.choice_name = 'vast'
        obj.beschrijving = 'Statisch (vaste teams)'
        obj.actief = deelcomp.regio_heeft_vaste_teams
        opts.append(obj)

        obj = SimpleNamespace()
        obj.choice_name = 'vsg'
        obj.beschrijving = 'Dynamisch (voortschrijdend gemiddelde)'
        obj.actief = not deelcomp.regio_heeft_vaste_teams
        opts.append(obj)

        context['opt_team_punten'] = opts = list()

        obj = SimpleNamespace()
        obj.choice_name = 'F1'
        obj.beschrijving = 'Formule 1 systeem (10/8/6/5/4/3/2/1)'
        obj.actief = deelcomp.regio_team_punten_model == TEAM_PUNTEN_MODEL_FORMULE1
        opts.append(obj)

        obj = SimpleNamespace()
        obj.choice_name = '2P'
        obj.beschrijving = 'Twee punten systeem (2/1/0)'
        obj.actief = deelcomp.regio_team_punten_model == TEAM_PUNTEN_MODEL_TWEE
        opts.append(obj)

        obj = SimpleNamespace()
        obj.choice_name = 'SS'
        obj.beschrijving = 'Cumulatief: som van team totaal'
        obj.actief = deelcomp.regio_team_punten_model == TEAM_PUNTEN_MODEL_SOM_SCORES
        opts.append(obj)

        context['url_opslaan'] = reverse('CompRegio:regio-instellingen',
                                         kwargs={'comp_pk': deelcomp.competitie.pk,
                                                 'regio_nr': deelcomp.nhb_regio.regio_nr})

        context['wiki_rcl_regio_instellingen_url'] = reverse_handleiding(self.request, settings.HANDLEIDING_RCL_INSTELLINGEN_REGIO)

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp.competitie.pk)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Opslaan' gebruikt wordt door de RCL """

        try:
            regio_nr = int(kwargs['regio_nr'][:6])  # afkappen voor de veiligheid
            comp_pk = int(kwargs['comp_pk'][:6])    # afkappen voor de veiligheid
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_regio')
                        .get(competitie=comp_pk,
                             laag=LAAG_REGIO,
                             nhb_regio__regio_nr=regio_nr))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404()

        if deelcomp.functie != self.functie_nu:
            # niet de beheerder
            raise PermissionDenied()

        deelcomp.competitie.bepaal_fase()
        if deelcomp.competitie.fase > 'D':
            # niet meer te wijzigen
            raise Http404()

        readonly_partly = (deelcomp.competitie.fase >= 'B')
        updated = list()

        if not readonly_partly:
            # deze velden worden alleen doorgegeven als ze te wijzigen zijn
            teams = request.POST.get('teams', '?')[:3]  # ja/nee
            alloc = request.POST.get('team_alloc', '?')[:4]  # vast/vsg
            if teams == 'nee':
                deelcomp.regio_organiseert_teamcompetitie = False
                updated.append('regio_organiseert_teamcompetitie')
            elif teams == 'ja':
                deelcomp.regio_organiseert_teamcompetitie = True
                updated.append('regio_organiseert_teamcompetitie')
                deelcomp.regio_heeft_vaste_teams = (alloc == 'vast')
                updated.append('regio_heeft_vaste_teams')

        # kijk alleen naar de andere velden als er een teamcompetitie georganiseerd wordt in de regio
        # dit voorkomt foutmelding over de datum bij het uitzetten van de teamcompetitie
        if deelcomp.regio_organiseert_teamcompetitie:
            punten = request.POST.get('team_punten', '?')[:2]    # 2p/ss/f1
            if punten in (TEAM_PUNTEN_MODEL_TWEE, TEAM_PUNTEN_MODEL_FORMULE1, TEAM_PUNTEN_MODEL_SOM_SCORES):
                deelcomp.regio_team_punten_model = punten
                updated.append('regio_team_punten_model')

            einde_s = request.POST.get('einde_teams_aanmaken', '')[:10]       # yyyy-mm-dd
            if einde_s:
                try:
                    einde_p = datetime.datetime.strptime(einde_s, '%Y-%m-%d')
                except ValueError:
                    raise Http404('Datum fout formaat')
                else:
                    einde_p = einde_p.date()
                    comp = deelcomp.competitie
                    if einde_p < comp.begin_aanmeldingen or einde_p >= comp.eerste_wedstrijd:
                        raise Http404('Datum buiten toegestane reeks')
                    deelcomp.einde_teams_aanmaken = einde_p
                    updated.append('einde_teams_aanmaken')

        deelcomp.save(update_fields=updated)

        url = reverse('Competitie:overzicht',
                      kwargs={'comp_pk': deelcomp.competitie.pk})
        return HttpResponseRedirect(url)


class RegioInstellingenGlobaalView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft een overzicht van de regio keuzes """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPREGIO_INSTELLINGEN_REGIO_GLOBAAL
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])    # afkappen voor de veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Http404()

        deelcomps = (DeelCompetitie
                     .objects
                     .select_related('competitie',
                                     'nhb_regio',
                                     'nhb_regio__rayon')
                     .filter(competitie=comp_pk,
                             laag=LAAG_REGIO)
                     .order_by('nhb_regio__regio_nr'))

        context['comp'] = comp
        context['deelcomps'] = deelcomps

        punten2str = dict()
        for punten, beschrijving in TEAM_PUNTEN:
            punten2str[punten] = beschrijving
        # for

        for deelcomp in deelcomps:

            deelcomp.regio_str = str(deelcomp.nhb_regio.regio_nr)
            deelcomp.rayon_str = str(deelcomp.nhb_regio.rayon.rayon_nr)

            if deelcomp.inschrijf_methode == INSCHRIJF_METHODE_1:
                deelcomp.inschrijfmethode_str = '1: kies wedstrijden'
            elif deelcomp.inschrijf_methode == INSCHRIJF_METHODE_2:
                deelcomp.inschrijfmethode_str = '2: klasse naar locatie'
            else:
                deelcomp.inschrijfmethode_str = '3: voorkeur dagdelen'

            if deelcomp.regio_organiseert_teamcompetitie:
                deelcomp.teamcomp_str = 'Ja'

                deelcomp.einde_teams_aanmaken_str = localize(deelcomp.einde_teams_aanmaken)

                if deelcomp.regio_heeft_vaste_teams:
                    deelcomp.team_type_str = 'Statisch'
                else:
                    deelcomp.team_type_str = 'Dynamisch'

                deelcomp.puntenmodel_str = punten2str[deelcomp.regio_team_punten_model]
            else:
                deelcomp.teamcomp_str = 'Nee'
                deelcomp.einde_teams_aanmaken_str = '-'
                deelcomp.team_type_str = '-'
                deelcomp.puntenmodel_str = '-'

            if self.rol_nu == Rollen.ROL_RKO and deelcomp.nhb_regio.rayon == self.functie_nu.nhb_rayon:
                deelcomp.highlight = True
        # for

        menu_dynamics_competitie(self.request, context, comp_pk=comp_pk)
        return context


# end of file
