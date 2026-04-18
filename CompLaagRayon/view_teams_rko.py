# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.db.models import Count
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.definities import DEELNAME_JA, DEELNAME_NEE, KAMP_RANK_BLANCO
from Competitie.models import Competitie, CompetitieTeamKlasse
from CompLaagRayon.models import KampRK, TeamRK
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Geo.models import Rayon
from Logboek.models import schrijf_in_logboek
from Score.definities import AG_NUL

TEMPLATE_COMPRAYON_RKO_TEAMS = 'complaagrayon/rko-teams.dtl'
TEMPLATE_COMPRAYON_RKO_TEAM_BLANCO_SCORE = 'complaagrayon/rko-teams-blanco-resultaat.dtl'


class RayonTeamsTemplateView(TemplateView):

    """ Met deze view kan een lijst van teams getoond worden, zowel landelijk, rayon als regio """

    template_name = TEMPLATE_COMPRAYON_RKO_TEAMS
    subset_filter = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        # template - zie override classes verderop
        raise NotImplementedError("test_func is mandatory")     # pragma: no cover

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if self.subset_filter:
            # BB/BKO mode

            context['subset_filter'] = True

            try:
                comp_pk = int(str(kwargs['comp_pk'][:7]))       # afkappen voor de veiligheid
                comp = Competitie.objects.get(pk=comp_pk)
            except (ValueError, Competitie.DoesNotExist):
                raise Http404('Competitie niet gevonden')

            context['comp'] = comp
            comp.bepaal_fase()

            open_inschrijving = comp.fase_teams <= 'G'

            subset = kwargs['subset'][:10]      # afkappen voor de veiligheid
            if subset == 'auto':
                subset = 'alle'

            if subset == 'alle':
                # alle rayons
                context['rayon'] = 'Alle'
                deelkamp_pks = (KampRK
                                .objects
                                .filter(competitie=comp)
                                .values_list('pk', flat=True))
            else:
                # alleen het gekozen rayon
                try:
                    rayon_nr = int(str(subset))      # is al eerder afgekapt op 10
                    context['rayon'] = Rayon.objects.get(rayon_nr=rayon_nr)
                except (ValueError, Rayon.DoesNotExist):
                    raise Http404('Selectie wordt niet ondersteund')

                deelkamp_pks = (KampRK
                                .objects
                                .filter(competitie=comp,
                                        rayon=context['rayon'])
                                .values_list('pk', flat=True))

            context['filters'] = filters = list()
            alle_filter = dict(beschrijving='Alles',
                               sel='alle',
                               selected=(subset == 'alle'),
                               url=reverse('CompLaagRayon:rayon-teams-alle',
                                           kwargs={'comp_pk': comp.pk,
                                                   'subset': 'alle'}))
            filters.append(alle_filter)

            for rayon in Rayon.objects.all():
                rayon.beschrijving = 'Rayon %s' % rayon.rayon_nr
                rayon.sel = 'rayon_%s' % rayon.rayon_nr
                rayon.url = reverse('CompLaagRayon:rayon-teams-alle',
                                    kwargs={'comp_pk': comp.pk, 'subset': rayon.rayon_nr})
                rayon.selected = (str(rayon.rayon_nr) == subset)
                filters.append(rayon)
            # for

        else:
            # RKO mode
            try:
                deelkamp_pk = int(kwargs['deelkamp_pk'][:7])    # afkappen voor de veiligheid
                deelkamp = (KampRK
                            .objects
                            .select_related('competitie')
                            .get(pk=deelkamp_pk))
            except (ValueError, KampRK.DoesNotExist):
                raise Http404('Kampioenschap niet gevonden')

            if deelkamp.functie != self.functie_nu:
                # niet de beheerder
                raise PermissionDenied('Niet de beheerder')

            deelkamp_pks = [deelkamp.pk]

            context['comp'] = comp = deelkamp.competitie
            comp.bepaal_fase()

            open_inschrijving = comp.fase_teams <= 'G'

            context['rayon'] = self.functie_nu.rayon

        if comp.is_indoor():
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        totaal_teams = 0

        klassen = (CompetitieTeamKlasse
                   .objects
                   .filter(competitie=comp,
                           is_voor_teams_rk_bk=True)
                   .select_related('team_type')
                   .order_by('volgorde'))

        klasse2teams = dict()       # [klasse] = list(teams)
        prev_sterkte = ''
        prev_team = None
        for klasse in klassen:
            klasse2teams[klasse] = list()

            if klasse.team_type != prev_team:
                prev_sterkte = ''
                prev_team = klasse.team_type

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

        if open_inschrijving:
            tel_dit = 'tijdelijke_leden'
        else:
            tel_dit = 'gekoppelde_leden'

        rk_teams = (TeamRK
                    .objects
                    .select_related('vereniging',
                                    'vereniging__regio',
                                    'team_type',
                                    'team_klasse',
                                    'kamp')
                    .exclude(team_klasse=None)
                    .filter(kamp__in=deelkamp_pks)
                    .annotate(sporter_count=Count(tel_dit))
                    .order_by('team_klasse__volgorde',
                              '-aanvangsgemiddelde',
                              'vereniging__ver_nr'))

        prev_klasse = None
        for team in rk_teams:
            if team.team_klasse != prev_klasse:
                team.break_before = True
                prev_klasse = team.team_klasse

            # team AG is 0.0 - 30.0 --> toon als score: 000.0 .. 900.0
            ag_str = "%05.1f" % (float(team.aanvangsgemiddelde) * aantal_pijlen)
            team.ag_str = ag_str.replace('.', ',')

            if team.deelname == DEELNAME_NEE:
                team.status_str = 'Afgemeld'
                # aantal_afgemeld += 1

            elif team.deelname == DEELNAME_JA:
                team.status_str = 'Aangemeld'
                # aantal_aangemeld += 1

            else:
                team.status_str = 'Onbekend'
                # aantal_onbekend += 1

            if team.is_reserve:
                team.status_str += ', Reserve'

            totaal_teams += 1

            try:
                klasse2teams[team.team_klasse].append(team)
            except KeyError:
                # dit is geen acceptabele klasse (waarschijnlijk een regio klasse)
                pass
        # for

        context['rk_teams'] = klasse2teams

        # zoek de teams die niet 'af' zijn
        rk_teams = (TeamRK
                    .objects
                    .select_related('vereniging',
                                    'vereniging__regio',
                                    'team_type',
                                    'kamp')
                    .filter(kamp__in=deelkamp_pks,
                            team_klasse=None)
                    .annotate(sporter_count=Count(tel_dit))
                    .order_by('team_type__volgorde',
                              '-aanvangsgemiddelde',
                              'vereniging__ver_nr'))

        is_eerste = True
        for team in rk_teams:
            # team AG is 0.0 - 30.0 --> toon als score: 000,0 .. 900,0
            ag_str = "%05.1f" % (float(team.aanvangsgemiddelde) * aantal_pijlen)
            team.ag_str = ag_str.replace('.', ',')

            if comp.fase_teams <= 'K' and self.rol_nu == Rol.ROL_RKO:
                team.url_aanpassen = reverse('CompLaagRayon:teams-rk-koppelen',
                                             kwargs={'rk_team_pk': team.pk})

            # TODO: RKO moet team kunnen verwijderen. Zie url_verwijder in rko-teams.dtl.

            totaal_teams += 1

            team.break_before = is_eerste
            is_eerste = False
        # for

        context['rk_teams_niet_af'] = rk_teams
        context['totaal_teams'] = totaal_teams
        context['toon_klassen'] = comp.klassengrenzen_vastgesteld_rk_bk

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'RK Teams')
        )

        return context


class RayonTeamsRKOView(UserPassesTestMixin, RayonTeamsTemplateView):

    """ Met deze view kan de RKO de aangemaakte teams inzien """

    # class variables shared by all instances
    subset_filter = False
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_RKO


class RayonTeamsAlleView(UserPassesTestMixin, RayonTeamsTemplateView):

    """ Met deze view kunnen de BB en BKO de aangemaakte teams inzien, met mogelijkheid tot filteren op een rayon """

    # class variables shared by all instances
    subset_filter = True
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_BKO)


class RayonTeamsBlancoResultaatView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de RKO een blanco resultaat toekennen aan een RK team,
        waardoor deze door mag stromen naar het BK.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_RKO_TEAM_BLANCO_SCORE
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None
        self.kamp_rk = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_RKO

    def _get_kamp_rk_or_40x(self, kwargs):
        try:
            kamp_pk = int(kwargs['kamp_pk'][:7])  # afkappen voor de veiligheid
            self.kamp_rk = (KampRK
                            .objects
                            .select_related('competitie')
                            .get(pk=kamp_pk))
        except (ValueError, KampRK.DoesNotExist):
            raise Http404('RK niet gevonden')

        # controleer dat de juiste RKO aan de knoppen zit
        comp = self.kamp_rk.competitie
        if self.functie_nu.comp_type != comp.afstand or self.functie_nu.rayon != self.kamp_rk.rayon:
            raise PermissionDenied('Niet de beheerder')     # niet de juiste RKO

        # check competitie fase
        comp.bepaal_fase()
        if comp.fase_teams != 'L':
            raise Http404('Verkeerde fase')

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        self._get_kamp_rk_or_40x(kwargs)
        context['kamp_rk'] = self.kamp_rk

        klasse_met_uitslag = list()

        for team in (TeamRK
                     .objects
                     .filter(kamp=self.kamp_rk)
                     .exclude(team_klasse=None)
                     .prefetch_related('team_klasse')):

            if 0 < team.result_rank < KAMP_RANK_BLANCO:
                if team.team_klasse.pk not in klasse_met_uitslag:
                    klasse_met_uitslag.append(team.team_klasse.pk)
        # for

        # zoek teams zonder resultaat
        context['teams'] = teams = list()
        prev_klasse = None
        for team in (TeamRK
                     .objects
                     .filter(kamp=self.kamp_rk)
                     .exclude(team_klasse__in=klasse_met_uitslag)
                     .exclude(result_rank=KAMP_RANK_BLANCO)
                     .select_related('team_klasse',
                                     'vereniging')
                     .order_by('team_klasse__volgorde')):

            if prev_klasse != team.team_klasse:
                prev_klasse = team.team_klasse
                team.break_klasse = True

            ver = team.vereniging
            if ver:     # pragma: no branch
                team.url = reverse('CompLaagRayon:rayon-teams-blanco-score-toekennen',
                                   kwargs={'kamp_pk': self.kamp_rk.pk,
                                           'team_pk': team.pk})

            teams.append(team)
        # for

        comp = self.kamp_rk.competitie
        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Blanco scores teams')
        )

        return context

    def post(self, request, *args, **kwargs):
        self._get_kamp_rk_or_40x(kwargs)

        try:
            team_pk = int(kwargs['team_pk'][:7])  # afkappen voor de veiligheid
            team = (TeamRK
                    .objects
                    .filter(kamp=self.kamp_rk)
                    .get(pk=team_pk))
        except (KeyError, ValueError, TeamRK.DoesNotExist):
            raise Http404('Team niet gevonden')

        team.result_rank = KAMP_RANK_BLANCO
        team.save(update_fields=['result_rank'])

        account = get_account(request)
        schrijf_in_logboek(account, 'Competitie', 'Blanco score voor RK team %s van %s in %s' % (repr(team.team_naam),
                                                                                                 team.vereniging,
                                                                                                 self.kamp_rk))

        url = reverse('CompLaagRayon:rayon-teams-blanco-score', kwargs={'kamp_pk': self.kamp_rk.pk})
        return HttpResponseRedirect(url)



# end of file
