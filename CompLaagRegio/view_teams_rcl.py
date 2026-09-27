# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.definities import TEAM_PUNTEN_MODEL_FORMULE1, TEAM_PUNTEN_MODEL_TWEE
from Competitie.models import Competitie, CompetitieTeamKlasse
from CompLaagRegio.models import RegioComp, RegioTeam, RegioPoule, RegioDeelnemer
from CompLaagRegio.operations.maak_mutatie_regio import maak_mutatie_regio_team_ronde
from CompLaagRegio.operations.bepaal_wedstrijdpunten import bepaal_wedstrijdpunten
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving
from Geo.models import Rayon
from Logboek.operations import schrijf_in_logboek
from Score.definities import AG_NUL
from codecs import BOM_UTF8
import csv

TEMPLATE_COMPREGIO_RCL_TEAMS = 'complaagregio/rcl-teams.dtl'
TEMPLATE_COMPREGIO_RCL_AG_CONTROLE = 'complaagregio/rcl-ag-controle.dtl'
TEMPLATE_COMPREGIO_RCL_TEAM_RONDE = 'complaagregio/rcl-team-ronde.dtl'

CONTENT_TYPE_CSV = 'text/csv; charset=UTF-8'


class RegioTeamsTemplateView(TemplateView):

    """ Met deze view kan een lijst van teams getoond worden, zowel landelijk, rayon als regio """

    template_name = TEMPLATE_COMPREGIO_RCL_TEAMS
    subset_filter = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        # template - zie override classes verderop
        raise NotImplementedError("test_func is mandatory")     # pragma: no cover

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        deelcomp = None

        if self.subset_filter:
            # BB/BKO/RKO mode

            context['subset_filter'] = True

            try:
                comp_pk = int(str(kwargs['comp_pk'][:7]))       # afkappen voor de veiligheid
                comp = Competitie.objects.get(pk=comp_pk)
            except (ValueError, Competitie.DoesNotExist):
                raise Http404('Competitie niet gevonden')

            context['comp'] = comp
            comp.bepaal_fase()

            subset = kwargs['subset'][:10]      # afkappen voor de veiligheid
            if subset == 'auto':
                if self.rol_nu in (Rol.ROL_BB, Rol.ROL_BKO):
                    subset = 'alle'
                elif self.rol_nu == Rol.ROL_RKO:
                    subset = str(self.functie_nu.rayon.rayon_nr)
                else:
                    raise Http404('Selectie wordt niet ondersteund')

            if subset == 'alle':
                # alle regios
                context['rayon'] = 'Alle'
                deelcomp_pks = (RegioComp
                                .objects
                                .filter(competitie=comp)
                                .values_list('pk', flat=True))
            else:
                # alleen de regio's van het rayon
                try:
                    context['rayon'] = Rayon.objects.get(rayon_nr=subset)
                except (ValueError, Rayon.DoesNotExist):
                    raise Http404('Selectie wordt niet ondersteund')

                deelcomp_pks = (RegioComp
                                .objects
                                .filter(competitie=comp,
                                        regio__rayon_nr=subset)
                                .values_list('pk', flat=True))

            context['filters'] = filters = list()
            alle_filter = dict(label='Alles',
                               sel='alle',
                               selected=(subset == 'alle'),
                               url=reverse('CompLaagRegio:regio-teams-alle',
                                           kwargs={'comp_pk': comp.pk,
                                                   'subset': 'alle'}))
            filters.append(alle_filter)

            for rayon in Rayon.objects.all():
                rayon.label = 'Rayon %s' % rayon.rayon_nr
                rayon.sel = 'rayon_%s' % rayon.rayon_nr
                rayon.selected = (str(rayon.rayon_nr) == subset)
                rayon.url = reverse('CompLaagRegio:regio-teams-alle',
                                    kwargs={'comp_pk': comp.pk, 'subset': rayon.rayon_nr})
                filters.append(rayon)
            # for

        else:
            # RCL mode
            try:
                deelcomp_pk = int(kwargs['deelcomp_pk'][:7])    # afkappen voor de veiligheid
                deelcomp = (RegioComp
                            .objects
                            .select_related('competitie')
                            .get(pk=deelcomp_pk))
            except (ValueError, RegioComp.DoesNotExist):
                raise Http404('Competitie niet gevonden')

            if deelcomp.functie != self.functie_nu:
                # niet de beheerder
                raise PermissionDenied('Niet de beheerder')

            context['url_download'] = reverse('CompLaagRegio:regio-teams-als-bestand',
                                              kwargs={'deelcomp_pk': deelcomp.pk})

            # alleen de eigen regio tonen
            deelcomp_pks = [deelcomp.pk]

            context['deelcomp'] = deelcomp
            deelcomp.bepaal_fase()

            comp = deelcomp.competitie
            context['comp'] = comp

            context['rayon'] = self.functie_nu.regio.rayon
            context['regio'] = self.functie_nu.regio

        if comp.is_indoor():
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        totaal_teams = 0

        team_klassen = (CompetitieTeamKlasse
                        .objects
                        .filter(competitie=comp,
                                is_voor_teams_rk_bk=False)
                        .select_related('team_type')
                        .order_by('volgorde'))

        team_klasse2teams = dict()       # [team_klasse] = list(teams)
        prev_sterkte = ''
        prev_team = None
        for team_klasse in team_klassen:
            team_klasse2teams[team_klasse] = list()

            if team_klasse.team_type != prev_team:
                prev_sterkte = ''
                prev_team = team_klasse.team_type

            min_ag_str = "%05.1f" % (team_klasse.min_ag * aantal_pijlen)
            min_ag_str = min_ag_str.replace('.', ',')
            if prev_sterkte:
                if team_klasse.min_ag > AG_NUL:
                    team_klasse.sterkte_str = "sterkte " + min_ag_str + " tot " + prev_sterkte
                else:
                    team_klasse.sterkte_str = "sterkte tot " + prev_sterkte
            else:
                team_klasse.sterkte_str = "sterkte " + min_ag_str + " en hoger"

            prev_sterkte = min_ag_str
        # for

        regioteams = (RegioTeam
                      .objects
                      .select_related('vereniging',
                                      'vereniging__regio',
                                      'team_type',
                                      'team_klasse')
                      .prefetch_related('regiopoule_set')
                      .exclude(team_klasse=None)
                      .filter(regiocomp__in=deelcomp_pks)
                      .order_by('team_klasse__volgorde',
                                '-aanvangsgemiddelde',
                                'vereniging__ver_nr'))

        prev_klasse = None
        for team in regioteams:
            if team.team_klasse != prev_klasse:
                team.break_before = True
                prev_klasse = team.team_klasse

            # team AG is 0.0 - 30.0 --> toon als score: 000.0 .. 900.0
            ag_str = "%05.1f" % (float(team.aanvangsgemiddelde) * aantal_pijlen)
            team.ag_str = ag_str.replace('.', ',')

            poule = team.regiopoule_set.first()
            team.in_poule = (poule is not None)

            if self.rol_nu == Rol.ROL_RCL and deelcomp.fase_teams <= 'D':
                team.url_aanpassen = reverse('CompLaagRegio:teams-regio-koppelen',
                                             kwargs={'team_pk': team.pk})
            totaal_teams += 1

            team_klasse2teams[team.team_klasse].append(team)
        # for

        context['regioteams'] = team_klasse2teams

        for team_klasse, teams in team_klasse2teams.items():
            team_klasse.aantal_regels = max(len(teams), 1) + 2
        # for

        # zoek de teams die niet 'af' zijn
        regioteams = (RegioTeam
                      .objects
                      .select_related('vereniging',
                                      'vereniging__regio',
                                      'team_type',
                                      'regiocomp')
                      .filter(regiocomp__in=deelcomp_pks,
                              team_klasse=None)
                      .order_by('team_type__volgorde',
                                '-aanvangsgemiddelde',
                                'vereniging__ver_nr'))

        is_eerste = True
        for team in regioteams:
            # team AG is 0.0 - 30.0 --> toon als score: 000.0 .. 900.0
            ag_str = "%05.1f" % (float(team.aanvangsgemiddelde) * aantal_pijlen)
            team.ag_str = ag_str.replace('.', ',')

            if self.rol_nu == Rol.ROL_RCL:
                assert isinstance(deelcomp, RegioComp)

                if deelcomp.fase_teams <= 'D':
                    team.url_aanpassen = reverse('CompLaagRegio:teams-regio-koppelen',
                                                 kwargs={'team_pk': team.pk})

                if deelcomp.fase_teams < 'F':
                    team.url_verwijder = reverse('CompLaagRegio:teams-regio-wijzig',
                                                 kwargs={'deelcomp_pk': team.regiocomp.pk,
                                                         'team_pk': team.pk})
            totaal_teams += 1

            team.break_before = is_eerste
            is_eerste = False
        # for

        context['regioteams_niet_af'] = regioteams
        context['aantal_regels_niet_af'] = len(regioteams) + 2
        context['totaal_teams'] = totaal_teams

        context['cols'] = 5
        if self.subset_filter:       # rayon selectie
            context['cols'] += 1     # toon kolom met regio nummer
        context['hdr_cols'] = context['cols'] + 2

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Regio Teams')
        )

        return context


class RegioTeamsRCLView(UserPassesTestMixin, RegioTeamsTemplateView):

    """ Met deze view kan de RCL de aangemaakte teams inzien """

    # class variables shared by all instances
    subset_filter = False
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_RCL


class RegioTeamsAlleView(UserPassesTestMixin, RegioTeamsTemplateView):

    """ Met deze view kan de BKO / RKO de aangemaakte teams inzien, per rayon """

    # class variables shared by all instances
    subset_filter = True    # Rayon selectie
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL)


class RegioTeamsAlsBestand(UserPassesTestMixin, View):

    """ Deze klasse wordt gebruikt om de lijst van aangemelde teams in een regio te downloaden als csv bestand
    """

    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.functie_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return rol_nu == Rol.ROL_RCL

    def get(self, request, *args, **kwargs):

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:7])    # afkappen voor de veiligheid
            deelcomp = (RegioComp
                        .objects
                        .select_related('competitie')
                        .get(pk=deelcomp_pk))
        except (ValueError, RegioComp.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        if deelcomp.functie != self.functie_nu:
            # niet de beheerder
            raise PermissionDenied('Verkeerde beheerder')

        regio_nr = deelcomp.regio.regio_nr

        comp = deelcomp.competitie
        comp.bepaal_fase()

        if comp.is_indoor():
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        response = HttpResponse(content_type=CONTENT_TYPE_CSV)
        response['Content-Disposition'] = 'attachment; filename="aanmeldingen-teams-regio-%s.csv"' % regio_nr

        response.write(BOM_UTF8)
        writer = csv.writer(response,
                            delimiter=";")  # ; is good for import with dutch regional settings

        writer.writerow(['Ver nr', 'Vereniging',
                         'Team type', 'Naam', 'Aantal sporters', 'Team sterkte',
                         'Wedstrijdklasse', 'Sporters'])

        # zoek de teams die niet 'af' zijn
        regioteams_niet_af = (RegioTeam
                              .objects
                              .select_related('vereniging',
                                              'vereniging__regio',
                                              'team_type',
                                              'regiocomp')
                              .filter(regiocomp=deelcomp,
                                      team_klasse=None)
                              .prefetch_related('leden')
                              .order_by('team_type__volgorde',
                                        '-aanvangsgemiddelde',
                                        'vereniging__ver_nr'))

        klasse_str = '"NIET COMPLEET"'

        for team in regioteams_niet_af:
            # team AG is 0.0 - 30.0 --> toon als score: 000.0 .. 900.0
            ag_str = "%05.1f" % (float(team.aanvangsgemiddelde) * aantal_pijlen)
            ag_str = ag_str.replace('.', ',')

            ver = team.vereniging
            aantal_sporters = team.leden.count()
            sporters_str = ", ".join([str(deelnemer.sporterboog.sporter.lid_nr) for deelnemer in team.leden.select_related('sporterboog__sporter').all()])

            tup = (ver.ver_nr, ver.naam,
                   team.team_type.beschrijving, team.team_naam, aantal_sporters, ag_str,
                   klasse_str, sporters_str)

            writer.writerow(tup)
        # for

        regioteams = (RegioTeam
                      .objects
                      .select_related('vereniging',
                                      'vereniging__regio',
                                      'team_type',
                                      'team_klasse')
                      .exclude(team_klasse=None)
                      .filter(regiocomp=deelcomp)
                      .order_by('team_klasse__volgorde',
                                '-aanvangsgemiddelde',
                                'vereniging__ver_nr'))

        for team in regioteams:
            # team AG is 0.0 - 30.0 --> toon als score: 000.0 .. 900.0
            ag_str = "%05.1f" % (float(team.aanvangsgemiddelde) * aantal_pijlen)
            ag_str = ag_str.replace('.', ',')

            ver = team.vereniging
            aantal_sporters = team.leden.count()
            klasse_str = team.team_klasse.beschrijving
            sporters_str = ", ".join([str(deelnemer.sporterboog.sporter.lid_nr) for deelnemer in team.leden.select_related('sporterboog__sporter').all()])

            tup = (ver.ver_nr, ver.naam,
                   team.team_type.beschrijving, team.team_naam, aantal_sporters, ag_str,
                   klasse_str, sporters_str)

            writer.writerow(tup)
        # for

        return response


class AGControleView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de RCL de handmatig ingevoerde aanvangsgemiddelden zien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPREGIO_RCL_AG_CONTROLE
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_RCL

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            regio_nr = int(kwargs['regio_nr'][:7])  # afkappen voor de veiligheid
            comp_pk = int(kwargs['comp_pk'][:7])    # afkappen voor de veiligheid
            deelcomp = (RegioComp
                        .objects
                        .select_related('competitie', 'regio')
                        .get(competitie=comp_pk,
                             regio__regio_nr=regio_nr))
        except (ValueError, RegioComp.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        if deelcomp.functie != self.functie_nu:
            # niet de beheerder
            raise PermissionDenied('Niet de beheerder')

        deelcomp.bepaal_fase()
        if deelcomp.fase_teams >= 'F':
            raise Http404('Verkeerde competitie fase')

        context['deelcomp'] = deelcomp

        context['handmatige_ag'] = ag_lijst = list()
        context['geen_ag'] = geen_ag_lijst = list()

        # zoek de sportersboog met handmatig_ag voor de teamcompetitie
        for obj in (RegioDeelnemer
                    .objects
                    .filter(regiocomp=deelcomp,
                            inschrijf_voorkeur_team=True,
                            ag_voor_team_mag_aangepast_worden=True)
                    .select_related('sporterboog',
                                    'sporterboog__sporter',
                                    'sporterboog__boogtype',
                                    'bij_vereniging')
                    .order_by('bij_vereniging__ver_nr',
                              'sporterboog__sporter__lid_nr',
                              'sporterboog__boogtype__volgorde')):

            obj.ver_str = obj.bij_vereniging.ver_nr_en_naam()

            obj.naam_str = obj.sporterboog.sporter.lid_nr_en_volledige_naam()

            obj.boog_str = obj.sporterboog.boogtype.beschrijving

            obj.ag_str = "%.3f" % obj.ag_voor_team
            obj.ag_str = obj.ag_str.replace('.', ',')

            if obj.ag_voor_team < 0.0001:
                geen_ag_lijst.append(obj)
            else:
                obj.url_details = reverse('CompLaagRegio:wijzig-ag',
                                          kwargs={'deelnemer_pk': obj.pk})

                ag_lijst.append(obj)
        # for

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        comp = deelcomp.competitie
        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'AG controle')
        )

        return context


class StartVolgendeTeamRondeView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de RCL de punten verdelen in de teamcompetitie en deze doorzetten naar de volgende ronde.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPREGIO_RCL_TEAM_RONDE
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_RCL

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:7])      # afkappen voor de veiligheid
            deelcomp = (RegioComp
                        .objects
                        .select_related('competitie')
                        .get(pk=deelcomp_pk,
                             regio=self.functie_nu.regio))
        except (ValueError, RegioComp.DoesNotExist):
            raise Http404('Competitie bestaat niet')

        context['deelcomp'] = deelcomp
        context['regio'] = self.functie_nu.regio

        # TODO: check competitie fase

        probleem_met_teams = False

        if deelcomp.huidige_team_ronde == 0:
            # check dat alle teams in een wedstrijdklasse staan (dus genoeg sporters gekoppeld hebben)
            # en dat alle teams in een poule zitten

            team_pk2poule = dict()
            poules = RegioPoule.objects.filter(regiocomp=deelcomp).prefetch_related('teams')
            for poule in poules:
                for team in poule.teams.all():
                    team_pk2poule[team.pk] = poule
                # for
            # for

            regioteams = (RegioTeam
                          .objects
                          .select_related('vereniging',
                                          'vereniging__regio',
                                          'team_type')
                          .filter(regiocomp=deelcomp)
                          .prefetch_related('leden')
                          .order_by('team_type__volgorde',
                                    '-aanvangsgemiddelde',
                                    'vereniging__ver_nr'))

            geen_poule_teams = list()

            for team in regioteams:
                team.aantal_sporters = team.leden.count()

                if not team.team_klasse:
                    probleem_met_teams = True
                    team.is_niet_af = True

                try:
                    team.poule = team_pk2poule[team.pk]
                except KeyError:
                    team.poule = None
                    team.is_niet_af = True
                    geen_poule_teams.append(team)
            # for

            if probleem_met_teams:
                context['teams_niet_af'] = regioteams

            if len(geen_poule_teams) > 0:
                probleem_met_teams = True
                context['teams_niet_in_poule'] = geen_poule_teams

        if not probleem_met_teams:
            if 1 <= deelcomp.huidige_team_ronde <= 7:
                tup = bepaal_wedstrijdpunten(deelcomp, deelcomp.huidige_team_ronde)
                context['alle_regels'], context['is_redelijk'] = tup

            if deelcomp.huidige_team_ronde <= 7:
                context['url_team_scores'] = reverse('CompScores:selecteer-team-scores',
                                                     kwargs={'deelcomp_pk': deelcomp.pk})

                context['url_volgende_ronde'] = reverse('CompLaagRegio:start-volgende-team-ronde',
                                                        kwargs={'deelcomp_pk': deelcomp.pk})

        if deelcomp.regio_team_punten_model == TEAM_PUNTEN_MODEL_FORMULE1:
            context['toon_f1'] = True
            context['wp_model_str'] = 'Formule 1'
        elif deelcomp.regio_team_punten_model == TEAM_PUNTEN_MODEL_TWEE:
            context['toon_h2h'] = True
            context['wp_model_str'] = '2 punten, directe tegenstanders'
        else:
            context['toon_som'] = True
            context['wp_model_str'] = 'Som van de scores'

        comp = deelcomp.competitie
        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Team Ronde')
        )

        return context

    def post(self, request, *args, **kwargs):

        """ deze functie wordt aangeroepen als de RCL op de knop drukt om de volgende ronde te beginnen.

            verwerking gebeurt in de achtergrond taak.
        """

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:7])      # afkappen voor de veiligheid
            deelcomp = (RegioComp
                        .objects
                        .select_related('competitie')
                        .get(pk=deelcomp_pk,
                             regio=self.functie_nu.regio))
        except (ValueError, RegioComp.DoesNotExist):
            raise Http404('Competitie bestaat niet')

        if deelcomp.huidige_team_ronde <= 7:

            # controleer dat het redelijk is om de volgende ronde op te starten
            if deelcomp.huidige_team_ronde > 0:
                alle_regels, is_redelijk = bepaal_wedstrijdpunten(deelcomp, deelcomp.huidige_team_ronde)
                if not is_redelijk:
                    raise Http404('Te weinig scores')

                # pas de wedstrijdpunten toe
                # TODO: verplaats naar background task
                if deelcomp.regio_team_punten_model == TEAM_PUNTEN_MODEL_TWEE:
                    for regel in alle_regels:
                        regel.ronde_team1.team_punten = regel.team1_wp
                        regel.ronde_team1.save(update_fields=['team_punten'])

                        if regel.ronde_team2:       # None == Bye
                            regel.ronde_team2.team_punten = regel.team2_wp
                            regel.ronde_team2.save(update_fields=['team_punten'])
                    # for

                elif deelcomp.regio_team_punten_model == TEAM_PUNTEN_MODEL_FORMULE1:
                    for ronde_team in alle_regels:
                        ronde_team.team_punten = ronde_team.ronde_wp
                        ronde_team.save(update_fields=['team_punten'])
                    # for

            account = get_account(request)
            schrijf_in_logboek(account, 'Competitie',
                               'Teamcompetitie doorzetten naar ronde %s voor %s' % (deelcomp.huidige_team_ronde+1,
                                                                                    deelcomp))

            # voor concurrency protection, laat de achtergrondtaak de ronde doorzetten
            door_str = "RCL %s" % account.volledige_naam()
            door_str = door_str[:149]

            snel = str(request.POST.get('snel', ''))[:1]

            maak_mutatie_regio_team_ronde(deelcomp, door_str, snel == '1')

        url = reverse('CompBeheer:overzicht',
                      kwargs={'comp_pk': deelcomp.competitie.pk})
        return HttpResponseRedirect(url)


# end of file
