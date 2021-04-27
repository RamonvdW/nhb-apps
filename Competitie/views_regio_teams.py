# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige_functie
from Handleiding.views import reverse_handleiding
from .models import (LAAG_REGIO, AG_NUL,
                     TEAM_PUNTEN_FORMULE1, TEAM_PUNTEN_TWEE, TEAM_PUNTEN_SOM_SCORES, TEAM_PUNTEN,
                     Competitie, DeelCompetitie,
                     CompetitieKlasse, RegioCompetitieSchutterBoog, RegiocompetitieTeam)
from .menu import menu_dynamics_competitie
from types import SimpleNamespace
import datetime


TEMPLATE_COMPETITIE_PLANNING_REGIO_TEAMS = 'competitie/rcl-teams.dtl'
TEMPLATE_COMPETITIE_INSTELLINGEN_REGIO = 'competitie/rcl-instellingen.dtl'
TEMPLATE_COMPETITIE_INSTELLINGEN_REGIO_GLOBAAL = 'competitie/rcl-instellingen-globaal.dtl'
TEMPLATE_COMPETITIE_AG_CONTROLE_REGIO = 'competitie/rcl-ag-controle.dtl'


class RegioInstellingenView(UserPassesTestMixin, TemplateView):

    """ Deze view kan de RCL instellingen voor de regiocompetitie aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_INSTELLINGEN_REGIO
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
            regio_nr = int(kwargs['regio_nr'][:6])  # afkappen voor veiligheid
            comp_pk = int(kwargs['comp_pk'][:6])    # afkappen voor veiligheid
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

        if deelcomp.competitie.fase >= 'B':
            context['readonly_partly'] = True

            if deelcomp.competitie.fase > 'C':
                context['readonly'] = True

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
        obj.actief = deelcomp.regio_team_punten_model == TEAM_PUNTEN_FORMULE1
        opts.append(obj)

        obj = SimpleNamespace()
        obj.choice_name = '2P'
        obj.beschrijving = 'Twee punten systeem (2/1/0)'
        obj.actief = deelcomp.regio_team_punten_model == TEAM_PUNTEN_TWEE
        opts.append(obj)

        obj = SimpleNamespace()
        obj.choice_name = 'SS'
        obj.beschrijving = 'Cumulatief: som van team totaal'
        obj.actief = deelcomp.regio_team_punten_model == TEAM_PUNTEN_SOM_SCORES
        opts.append(obj)

        context['url_opslaan'] = reverse('Competitie:regio-instellingen',
                                         kwargs={'comp_pk': deelcomp.competitie.pk,
                                                 'regio_nr': deelcomp.nhb_regio.regio_nr})

        context['wiki_rcl_regio_instellingen_url'] = reverse_handleiding(settings.HANDLEIDING_RCL_INSTELLINGEN_REGIO)

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp.competitie.pk)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Opslaan' gebruikt wordt door de RCL """

        try:
            regio_nr = int(kwargs['regio_nr'][:6])  # afkappen voor veiligheid
            comp_pk = int(kwargs['comp_pk'][:6])    # afkappen voor veiligheid
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
        if deelcomp.competitie.fase > 'C':
            # niet meer te wijzigen
            raise Http404()

        readonly_partly = (deelcomp.competitie.fase >= 'B')

        if not readonly_partly:
            # deze velden worden alleen doorgegeven als ze te wijzigen zijn
            teams = request.POST.get('teams', '?')[:3]  # ja/nee
            alloc = request.POST.get('team_alloc', '?')[:4]  # vast/vsg
            if teams == 'nee':
                deelcomp.regio_organiseert_teamcompetitie = False
            elif teams == 'ja':
                deelcomp.regio_organiseert_teamcompetitie = True
                deelcomp.regio_heeft_vaste_teams = (alloc == 'vast')

        punten = request.POST.get('team_punten', '?')[:2]    # 2p/ss/f1
        if punten in (TEAM_PUNTEN_TWEE, TEAM_PUNTEN_FORMULE1, TEAM_PUNTEN_SOM_SCORES):
            deelcomp.regio_team_punten_model = punten

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

        deelcomp.save()

        url = reverse('Competitie:overzicht',
                      kwargs={'comp_pk': deelcomp.competitie.pk})
        return HttpResponseRedirect(url)


class RegioInstellingenGlobaalView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft een overzicht van de regio keuzes """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_INSTELLINGEN_REGIO_GLOBAAL
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
            comp_pk = int(kwargs['comp_pk'][:6])    # afkappen voor veiligheid
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

            if deelcomp.regio_organiseert_teamcompetitie:
                deelcomp.teamcomp_str = 'Ja'

                if deelcomp.regio_heeft_vaste_teams:
                    deelcomp.team_type_str = 'Statisch'
                else:
                    deelcomp.team_type_str = 'Dynamisch'

                deelcomp.puntenmodel_str = punten2str[deelcomp.regio_team_punten_model]
            else:
                deelcomp.teamcomp_str = 'Nee'
                deelcomp.team_type_str = '-'
                deelcomp.puntenmodel_str = '-'

            if self.rol_nu == Rollen.ROL_RKO and deelcomp.nhb_regio.rayon == self.functie_nu.nhb_rayon:
                deelcomp.highlight = True
        # for

        menu_dynamics_competitie(self.request, context, comp_pk=comp_pk)
        return context


class RegioTeamsView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de RCL de aangemaakte teams inzien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_PLANNING_REGIO_TEAMS
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
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen geeft beveiliging
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(pk=deelcomp_pk,
                             laag=LAAG_REGIO))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        if deelcomp.functie != self.functie_nu:
            # niet de beheerder
            raise PermissionDenied()

        context['deelcomp'] = deelcomp
        context['regio'] = self.functie_nu.nhb_regio

        if deelcomp.competitie.afstand == '18':
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        totaal_teams = 0

        klassen = (CompetitieKlasse
                   .objects
                   .filter(competitie=deelcomp.competitie,
                           indiv=None)
                   .select_related('team',
                                   'team__team_type')
                   .order_by('team__volgorde'))

        klasse2teams = dict()       # [klasse] = list(teams)
        prev_sterkte = ''
        prev_team = None
        for klasse in klassen:
            klasse2teams[klasse] = list()

            if klasse.team.team_type != prev_team:
                prev_sterkte = ''
                prev_team = klasse.team.team_type

            min_ag_str = "%5.1f" % (klasse.min_ag * aantal_pijlen)
            if prev_sterkte:
                if klasse.min_ag > AG_NUL:
                    klasse.sterkte_str = "sterkte " + min_ag_str + " tot " + prev_sterkte
                else:
                    klasse.sterkte_str = "sterkte tot " + prev_sterkte
            else:
                klasse.sterkte_str = "sterkte " + min_ag_str + " en hoger"

            prev_sterkte = min_ag_str
        # for

        regioteams = (RegiocompetitieTeam
                      .objects
                      .select_related('vereniging',
                                      'team_type',
                                      'klasse',
                                      'klasse__team')
                      .exclude(klasse=None)
                      .filter(deelcompetitie=deelcomp)
                      .order_by('klasse__team__volgorde',
                                '-aanvangsgemiddelde',
                                'vereniging__ver_nr'))

        prev_klasse = None
        for team in regioteams:
            if team.klasse != prev_klasse:
                team.break_before = True
                prev_klasse = team.klasse

            # team AG is 0.0 - 30.0 --> toon als score: 000.0 .. 900.0
            team.ag_str = "%05.1f" % (team.aanvangsgemiddelde * aantal_pijlen)
            totaal_teams += 1

            klasse2teams[team.klasse].append(team)
        # for

        context['regioteams'] = klasse2teams

        regioteams = (RegiocompetitieTeam
                      .objects
                      .select_related('vereniging',
                                      'team_type')
                      .filter(deelcompetitie=deelcomp,
                              klasse=None)
                      .order_by('team_type__volgorde',
                                '-aanvangsgemiddelde',
                                'vereniging__ver_nr'))

        is_eerste = True
        for team in regioteams:
            # team AG is 0.0 - 30.0 --> toon als score: 000.0 .. 900.0
            team.ag_str = "%05.1f" % (team.aanvangsgemiddelde * aantal_pijlen)
            totaal_teams += 1

            team.break_before = is_eerste
            is_eerste = False
        # for

        context['regioteams_niet_af'] = regioteams
        context['totaal_teams'] = totaal_teams

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp.competitie.pk)
        return context


class AGControleView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de RCL de handmatig ingevoerde aanvangsgemiddelden zien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_AG_CONTROLE_REGIO
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
            regio_nr = int(kwargs['regio_nr'][:6])  # afkappen voor veiligheid
            comp_pk = int(kwargs['comp_pk'][:6])    # afkappen voor veiligheid
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_regio')
                        .get(competitie=comp_pk,
                             laag=LAAG_REGIO,
                             nhb_regio__regio_nr=regio_nr))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        if deelcomp.functie != self.functie_nu:
            # niet de beheerder
            raise PermissionDenied()

        deelcomp.competitie.bepaal_fase()
        if deelcomp.competitie.fase > 'F':
            raise Http404('Verkeerde competitie fase')

        context['deelcomp'] = deelcomp

        context['handmatige_ag'] = ag_lijst = list()

        # zoek de schuttersboog met handmatig_ag voor de teamcompetitie
        for obj in (RegioCompetitieSchutterBoog
                    .objects
                    .filter(deelcompetitie=deelcomp,
                            inschrijf_voorkeur_team=True,
                            ag_voor_team_mag_aangepast_worden=True,
                            ag_voor_team__gt=0.0)
                    .select_related('schutterboog',
                                    'schutterboog__nhblid',
                                    'schutterboog__boogtype',
                                    'bij_vereniging')
                    .order_by('bij_vereniging__ver_nr',
                              'schutterboog__nhblid__nhb_nr',
                              'schutterboog__boogtype__volgorde')):

            ver = obj.bij_vereniging
            obj.ver_str = "[%s] %s" % (ver.ver_nr, ver.naam)

            lid = obj.schutterboog.nhblid
            obj.naam_str = "[%s] %s" % (lid.nhb_nr, lid.volledige_naam())

            obj.boog_str = obj.schutterboog.boogtype.beschrijving

            obj.ag_str = "%.3f" % obj.ag_voor_team

            obj.url_details = reverse('Vereniging:wijzig-ag',
                                      kwargs={'deelnemer_pk': obj.pk})

            ag_lijst.append(obj)
        # for

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp.competitie.pk)
        return context


class RegioPoulesView(UserPassesTestMixin, TemplateView):
    pass


# end of file
