# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils.formats import localize
from django.db.models import Count
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige_functie
from Handleiding.views import reverse_handleiding
from Logboek.models import schrijf_in_logboek
from NhbStructuur.models import NhbRayon
from Overig.background_sync import BackgroundSync
from .models import (LAAG_REGIO, AG_NUL,
                     TEAM_PUNTEN_FORMULE1, TEAM_PUNTEN_TWEE, TEAM_PUNTEN_SOM_SCORES, TEAM_PUNTEN,
                     INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_2, INSCHRIJF_METHODE_3,
                     Competitie, CompetitieKlasse, DeelCompetitie, RegioCompetitieSchutterBoog,
                     RegiocompetitieTeam, RegiocompetitieTeamPoule, RegiocompetitieRondeTeam,
                     CompetitieMutatie, MUTATIE_TEAM_RONDE)
from .menu import menu_dynamics_competitie
from types import SimpleNamespace
import datetime
import time


TEMPLATE_COMPETITIE_RCL_INSTELLINGEN = 'competitie/rcl-instellingen.dtl'
TEMPLATE_COMPETITIE_INSTELLINGEN_REGIO_GLOBAAL = 'competitie/rcl-instellingen-globaal.dtl'
TEMPLATE_COMPETITIE_RCL_TEAMS = 'competitie/rcl-teams.dtl'
TEMPLATE_COMPETITIE_RCL_TEAMS_POULES = 'competitie/rcl-teams-poules.dtl'
TEMPLATE_COMPETITIE_RCL_WIJZIG_POULE = 'competitie/wijzig-poule.dtl'
TEMPLATE_COMPETITIE_RCL_AG_CONTROLE = 'competitie/rcl-ag-controle.dtl'
TEMPLATE_COMPETITIE_RCL_TEAM_RONDE = 'competitie/rcl-team-ronde.dtl'

mutatie_ping = BackgroundSync(settings.BACKGROUND_SYNC__REGIOCOMP_MUTATIES)


class RegioInstellingenView(UserPassesTestMixin, TemplateView):

    """ Deze view kan de RCL instellingen voor de regiocompetitie aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_RCL_INSTELLINGEN
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

        if deelcomp.competitie.fase > 'A':
            context['readonly_na_fase_A'] = True

            if deelcomp.competitie.fase > 'C':
                context['readonly_na_fase_C'] = True

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

        context['wiki_rcl_regio_instellingen_url'] = reverse_handleiding(self.request, settings.HANDLEIDING_RCL_INSTELLINGEN_REGIO)

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
            if punten in (TEAM_PUNTEN_TWEE, TEAM_PUNTEN_FORMULE1, TEAM_PUNTEN_SOM_SCORES):
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


class RegioTeamsView(TemplateView):

    """ Met deze view kan een lijst van teams getoond worden, zowel landelijk, rayon als regio """

    template_name = TEMPLATE_COMPETITIE_RCL_TEAMS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if self.subset_filter:
            context['subset_filter'] = True

            # BB/BKO/RKO mode
            try:
                comp_pk = int(str(kwargs['comp_pk'][:6]))       # afkappen geeft veiligheid
                comp = Competitie.objects.get(pk=comp_pk)
            except (ValueError, Competitie.DoesNotExist):
                raise Http404('Competitie niet gevonden')

            context['comp'] = comp

            subset = kwargs['subset'][:10]
            if subset == 'auto':
                if self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO):
                    subset = 'alle'
                elif self.rol_nu == Rollen.ROL_RKO:
                    subset = str(self.functie_nu.nhb_rayon.rayon_nr)
                else:
                    raise Http404('Selectie wordt niet ondersteund')

            if subset == 'alle':
                # alle regios
                context['rayon'] = 'Alle'
                deelcomp_pks = (DeelCompetitie
                                .objects
                                .filter(competitie=comp)
                                .values_list('pk', flat=True))
            else:
                # alleen de regio's van het rayon
                try:
                    context['rayon'] = NhbRayon.objects.get(rayon_nr=subset)
                except NhbRayon.DoesNotExist:
                    raise Http404('Selectie wordt niet ondersteund')

                deelcomp_pks = (DeelCompetitie
                                .objects
                                .filter(competitie=comp,
                                        nhb_regio__rayon__rayon_nr=subset)
                                .values_list('pk', flat=True))

            context['filters'] = filters = list()
            alle_filter = {'label': 'Alles'}
            if subset != 'alle':
                alle_filter['url'] = reverse('Competitie:regio-teams-alle',
                                             kwargs={'comp_pk': comp.pk,
                                                     'subset': 'alle'})
            filters.append(alle_filter)

            for rayon in NhbRayon.objects.all():
                rayon.label = 'Rayon %s' % rayon.rayon_nr
                if str(rayon.rayon_nr) != subset:
                    rayon.url = reverse('Competitie:regio-teams-alle', kwargs={'comp_pk': comp.pk, 'subset': rayon.rayon_nr})
                filters.append(rayon)
            # for

        else:
            # RCL mode
            try:
                deelcomp_pk = int(kwargs['deelcomp_pk'][:6])    # afkappen geeft veiligheid
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

            deelcomp_pks = [deelcomp.pk]

            context['comp'] = comp = deelcomp.competitie
            context['deelcomp'] = deelcomp
            context['rayon'] = self.functie_nu.nhb_regio.rayon
            context['regio'] = self.functie_nu.nhb_regio

            subset = 'regio'

        if comp.afstand == '18':
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        totaal_teams = 0

        klassen = (CompetitieKlasse
                   .objects
                   .filter(competitie=comp,
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

            min_ag_str = "%05.1f" % (klasse.min_ag * aantal_pijlen)
            min_ag_str = min_ag_str.replace('.', ',')
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
                                      'vereniging__regio',
                                      'team_type',
                                      'klasse',
                                      'klasse__team')
                      .exclude(klasse=None)
                      .filter(deelcompetitie__in=deelcomp_pks)
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
            team.ag_str = team.ag_str.replace('.', ',')
            totaal_teams += 1

            klasse2teams[team.klasse].append(team)
        # for

        context['regioteams'] = klasse2teams

        # zoek de teams die niet 'af' zijn
        regioteams = (RegiocompetitieTeam
                      .objects
                      .select_related('vereniging',
                                      'vereniging__regio',
                                      'team_type')
                      .filter(deelcompetitie__in=deelcomp_pks,
                              klasse=None)
                      .order_by('team_type__volgorde',
                                '-aanvangsgemiddelde',
                                'vereniging__ver_nr'))

        is_eerste = True
        for team in regioteams:
            # team AG is 0.0 - 30.0 --> toon als score: 000.0 .. 900.0
            team.ag_str = "%05.1f" % (team.aanvangsgemiddelde * aantal_pijlen)
            team.ag_str = team.ag_str.replace('.', ',')
            totaal_teams += 1

            team.break_before = is_eerste
            is_eerste = False
        # for

        context['regioteams_niet_af'] = regioteams
        context['totaal_teams'] = totaal_teams

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return context


class RegioTeamsRCLView(UserPassesTestMixin, RegioTeamsView):

    """ Met deze view kan de RCL de aangemaakte teams inzien """

    # class variables shared by all instances
    subset_filter = False
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_RCL


class RegioTeamsAlleView(UserPassesTestMixin, RegioTeamsView):

    """ Met deze view kan de RCL de aangemaakte teams inzien """

    # class variables shared by all instances
    subset_filter = True
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL)


class AGControleView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de RCL de handmatig ingevoerde aanvangsgemiddelden zien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_RCL_AG_CONTROLE
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

    """ Met deze view kan de RCL de poules hanteren """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_RCL_TEAMS_POULES
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
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])    # afkappen voor veiligheid
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie',
                                        'nhb_regio',
                                        'nhb_regio__rayon')
                        .get(pk=deelcomp_pk,
                             laag=LAAG_REGIO))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        if deelcomp.nhb_regio != self.functie_nu.nhb_regio:
            raise PermissionDenied('Niet de beheerder van deze regio')

        context['deelcomp'] = deelcomp

        comp = deelcomp.competitie
        comp.bepaal_fase()
        context['readonly'] = readonly = (comp.fase > 'D')

        context['regio'] = deelcomp.nhb_regio

        poules = (RegiocompetitieTeamPoule
                  .objects
                  .prefetch_related('teams')
                  .filter(deelcompetitie=deelcomp)
                  .annotate(team_count=Count('teams')))

        team_pk2poule = dict()
        for poule in poules:
            if not readonly:
                poule.url_wijzig = reverse('Competitie:wijzig-poule',
                                           kwargs={'poule_pk': poule.pk})

            for team in poule.teams.all():
                team_pk2poule[team.pk] = poule
        # for

        context['poules'] = poules

        teams = RegiocompetitieTeam.objects.filter(deelcompetitie=deelcomp).order_by('klasse__team__volgorde')

        for team in teams:
            try:
                poule = team_pk2poule[team.pk]
            except KeyError:
                pass
            else:
                team.poule = poule
        # for

        context['teams'] = teams

        if not readonly:
            context['url_nieuwe_poule'] = reverse('Competitie:regio-poules',
                                                  kwargs={'deelcomp_pk': deelcomp.pk})

        context['wiki_rcl_poules_url'] = reverse_handleiding(self.request, settings.HANDLEIDING_POULES)

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp.competitie.pk)
        return context

    def post(self, request, *args, **kwargs):
        """ maak een nieuwe poule aan """
        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])    # afkappen voor veiligheid
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie',
                                        'nhb_regio',
                                        'nhb_regio__rayon')
                        .get(pk=deelcomp_pk,
                             laag=LAAG_REGIO))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        if deelcomp.nhb_regio != self.functie_nu.nhb_regio:
            raise PermissionDenied('Niet de beheerder van deze regio')

        comp = deelcomp.competitie
        comp.bepaal_fase()
        if comp.fase > 'D':
            raise Http404('Poules kunnen niet meer aangepast worden')

        aantal = (RegiocompetitieTeamPoule
                  .objects
                  .filter(deelcompetitie=deelcomp)
                  .count())
        nummer = aantal + 1

        # maak een nieuwe poule aan
        RegiocompetitieTeamPoule(
                deelcompetitie=deelcomp,
                beschrijving='poule %s' % nummer).save()

        url = reverse('Competitie:regio-poules',
                      kwargs={'deelcomp_pk': deelcomp.pk})
        return HttpResponseRedirect(url)


class WijzigPouleView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de RCL een poule beheren """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_RCL_WIJZIG_POULE
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
            poule_pk = int(kwargs['poule_pk'][:6])      # afkappen voor de veiligheid
            poule = (RegiocompetitieTeamPoule
                     .objects
                     .select_related('deelcompetitie',
                                     'deelcompetitie__nhb_regio',
                                     'deelcompetitie__competitie')
                     .prefetch_related('teams')
                     .get(pk=poule_pk))
        except (ValueError, RegiocompetitieTeamPoule.DoesNotExist):
            raise Http404('Poule bestaat niet')

        deelcomp = poule.deelcompetitie
        if deelcomp.nhb_regio != self.functie_nu.nhb_regio:
            raise PermissionDenied('Niet de beheerder van deze regio')

        comp = deelcomp.competitie
        comp.bepaal_fase()
        if comp.fase > 'D':
            raise Http404('Poules kunnen niet meer aangepast worden')

        team_pks = list(poule.teams.values_list('pk', flat=True))

        teams = (RegiocompetitieTeam
                 .objects
                 .select_related('klasse__team',
                                 'team_type')
                 .prefetch_related('regiocompetitieteampoule_set')
                 .filter(deelcompetitie=deelcomp)
                 .order_by('klasse__team__volgorde'))
        for team in teams:
            team.sel_str = 'team_%s' % team.pk
            if team.pk in team_pks:
                team.geselecteerd = True
            else:
                if team.regiocompetitieteampoule_set.count():
                    team.in_andere_poule = True

            if team.klasse:
                team.klasse_str = team.klasse.team.beschrijving
            else:
                team.klasse_str = ''        # blokkeert selectie voor poule
        # for
        context['teams'] = teams

        context['poule'] = poule
        context['url_opslaan'] = reverse('Competitie:wijzig-poule',
                                         kwargs={'poule_pk': poule.pk})
        context['url_terug'] = reverse('Competitie:regio-poules',
                                       kwargs={'deelcomp_pk': deelcomp.pk})

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp.competitie.pk)
        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als ... knop ... """

        try:
            poule_pk = int(kwargs['poule_pk'][:6])      # afkappen voor de veiligheid
            poule = (RegiocompetitieTeamPoule
                     .objects
                     .select_related('deelcompetitie')
                     .prefetch_related('teams')
                     .get(pk=poule_pk))
        except (ValueError, RegiocompetitieTeamPoule.DoesNotExist):
            raise Http404('Poule bestaat niet')

        deelcomp = poule.deelcompetitie
        if deelcomp.nhb_regio != self.functie_nu.nhb_regio:
            raise PermissionDenied('Niet de beheerder van deze regio')

        comp = deelcomp.competitie
        comp.bepaal_fase()
        if comp.fase > 'D':
            raise Http404('Poules kunnen niet meer aangepast worden')

        if request.POST.get('verwijder_poule', ''):
            # deze poule is niet meer nodig
            poule.delete()
        else:
            beschrijving = request.POST.get('beschrijving', '')[:100]   # afkappen voor de veiligheid
            beschrijving = beschrijving.strip()
            if poule.beschrijving != beschrijving:
                poule.beschrijving = beschrijving
                poule.save(update_fields=['beschrijving'])

            gekozen = list()
            type_counts = dict()
            for team in (RegiocompetitieTeam
                         .objects
                         .prefetch_related('regiocompetitieteampoule_set')
                         .filter(deelcompetitie=deelcomp)):

                sel_str = 'team_%s' % team.pk
                if request.POST.get(sel_str, ''):
                    kies = False

                    if team.regiocompetitieteampoule_set.count() == 0:
                        # nog niet in te een poule, dus mag gekozen worden
                        kies = True
                    else:
                        if team.regiocompetitieteampoule_set.all()[0].pk == poule.pk:
                            # herverkozen in dezelfde poule
                            kies = True

                    if kies:
                        gekozen.append(team)

                        try:
                            type_counts[team.team_type] += 1
                        except KeyError:
                            type_counts[team.team_type] = 1
            # for

            # kijk welk team type dit gaat worden
            if len(gekozen) == 0:
                poule.teams.clear()
            else:
                tups = [(count, team_type) for team_type, count in type_counts.items()]
                tups.sort(reverse=True)     # hoogste eerst
                team_type = tups[0][1]

                # laat teams toe die binnen dit team type passen
                goede_teams = [team for team in gekozen if team.team_type == team_type]
                goede_teams = goede_teams[:8]       # maximaal 8 teams in een poule

                # vervang door de overgebleven teams
                poule.teams.set(goede_teams)

        url = reverse('Competitie:regio-poules',
                      kwargs={'deelcomp_pk': deelcomp.pk})
        return HttpResponseRedirect(url)


class StartVolgendeTeamRondeView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de RCL de punten verdelen in de teamcompetitie en deze doorzetten naar de volgende ronde.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_RCL_TEAM_RONDE
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
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])      # afkappen voor de veiligheid
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(pk=deelcomp_pk,
                             nhb_regio=self.functie_nu.nhb_regio))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie bestaat niet')

        context['deelcomp'] = deelcomp
        context['regio'] = self.functie_nu.nhb_regio

        teams = RegiocompetitieTeam.objects.filter(deelcompetitie=deelcomp).values_list('pk', flat=True)
        ronde_teams = (RegiocompetitieRondeTeam
                       .objects
                       .filter(team__in=teams,
                               ronde_nr=deelcomp.huidige_team_ronde)
                       .order_by('-team_score'))        # hoogste bovenaan

        context['ronde_teams'] = ronde_teams

        if deelcomp.huidige_team_ronde <= 7:
            context['url_volgende_ronde'] = reverse('Competitie:start-volgende-team-ronde',
                                                    kwargs={'deelcomp_pk': deelcomp.pk})

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp.competitie.pk)
        return context

    def post(self, request, *args, **kwargs):

        """ deze functie wordt aangeroepen als de RCL op de knop drukt om de volgende ronde te beginnen.

            verwerking gebeurt in de achtergrond taak.
        """

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])      # afkappen voor de veiligheid
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(pk=deelcomp_pk,
                             nhb_regio=self.functie_nu.nhb_regio))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie bestaat niet')

        # TODO: controleer dat het redelijk is om de volgende ronde op te starten
        if deelcomp.huidige_team_ronde <= 7:

            account = request.user
            schrijf_in_logboek(account, 'Competitie', 'Teamcompetitie doorzetten naar ronde %s voor %s' % (deelcomp.huidige_team_ronde+1, deelcomp))

            # voor concurrency protection, laat de achtergrondtaak de competitie aanmaken
            door_str = "RCL %s" % account.volledige_naam()
            mutatie = CompetitieMutatie(mutatie=MUTATIE_TEAM_RONDE,
                                        deelcompetitie=deelcomp,
                                        door=door_str)
            mutatie.save()

            mutatie_ping.ping()

            snel = str(request.POST.get('snel', ''))[:1]
            if snel != '1':
                # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
                interval = 0.2  # om steeds te verdubbelen
                total = 0.0  # om een limiet te stellen
                while not mutatie.is_verwerkt and total + interval <= 3.0:
                    time.sleep(interval)
                    total += interval  # 0.0 --> 0.2, 0.6, 1.4, 3.0
                    interval *= 2  # 0.2 --> 0.4, 0.8, 1.6, 3.2
                    mutatie = CompetitieMutatie.objects.get(pk=mutatie.pk)
                # while

        url = reverse('Competitie:overzicht',
                      kwargs={'comp_pk': deelcomp.competitie.pk})
        return HttpResponseRedirect(url)


# end of file
