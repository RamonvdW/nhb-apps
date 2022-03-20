# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.db.models import Count
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import LAAG_RK, AG_NUL, Competitie, CompetitieTeamKlasse, DeelCompetitie, KampioenschapTeam
from Functie.rol import Rollen, rol_get_huidige_functie
from NhbStructuur.models import NhbRayon
from Plein.menu import menu_dynamics


TEMPLATE_COMPRAYON_RKO_TEAMS = 'complaagrayon/rko-teams.dtl'


class RayonTeamsView(TemplateView):

    """ Met deze view kan een lijst van teams getoond worden, zowel landelijk, rayon als regio """

    template_name = TEMPLATE_COMPRAYON_RKO_TEAMS
    subset_filter = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        raise NotImplementedError("test_func is mandatory")     # pragma: no cover

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if self.subset_filter:
            # BB/BKO mode

            context['subset_filter'] = True

            try:
                comp_pk = int(str(kwargs['comp_pk'][:6]))       # afkappen voor de veiligheid
                comp = Competitie.objects.get(pk=comp_pk)
            except (ValueError, Competitie.DoesNotExist):
                raise Http404('Competitie niet gevonden')

            context['comp'] = comp
            comp.bepaal_fase()

            open_inschrijving = comp.fase <= 'G'

            subset = kwargs['subset'][:10]      # afkappen voor de veiligheid
            if subset == 'auto':
                subset = 'alle'

            if subset == 'alle':
                # alle rayons
                context['rayon'] = 'Alle'
                rk_deelcomp_pks = (DeelCompetitie
                                   .objects
                                   .filter(competitie=comp,
                                           laag=LAAG_RK)
                                   .values_list('pk', flat=True))
            else:
                # alleen het gekozen rayon
                try:
                    rayon_nr = int(str(subset))      # is al eerder afgekapt op 10
                    context['rayon'] = NhbRayon.objects.get(rayon_nr=rayon_nr)
                except (ValueError, NhbRayon.DoesNotExist):
                    raise Http404('Selectie wordt niet ondersteund')

                rk_deelcomp_pks = (DeelCompetitie
                                   .objects
                                   .filter(competitie=comp,
                                           nhb_rayon=context['rayon'])
                                   .values_list('pk', flat=True))

            context['filters'] = filters = list()
            alle_filter = dict(beschrijving='Alles',
                               sel='alle',
                               selected=(subset == 'alle'),
                               url=reverse('CompLaagRayon:rayon-teams-alle',
                                           kwargs={'comp_pk': comp.pk,
                                                   'subset': 'alle'}))
            filters.append(alle_filter)

            for rayon in NhbRayon.objects.all():
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
                rk_deelcomp_pk = int(kwargs['rk_deelcomp_pk'][:6])    # afkappen voor de veiligheid
                deelcomp_rk = (DeelCompetitie
                               .objects
                               .select_related('competitie')
                               .get(pk=rk_deelcomp_pk,
                                    laag=LAAG_RK))
            except (ValueError, DeelCompetitie.DoesNotExist):
                raise Http404('Competitie niet gevonden')

            if deelcomp_rk.functie != self.functie_nu:
                # niet de beheerder
                raise PermissionDenied()

            rk_deelcomp_pks = [deelcomp_rk.pk]

            context['comp'] = comp = deelcomp_rk.competitie
            comp.bepaal_fase()

            open_inschrijving = comp.fase <= 'G'

            context['deelcomp'] = deelcomp_rk
            context['rayon'] = self.functie_nu.nhb_rayon

        if comp.afstand == '18':
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
            tel_dit = 'tijdelijke_schutters'
        else:
            tel_dit = 'gekoppelde_schutters'

        rk_teams = (KampioenschapTeam
                    .objects
                    .select_related('vereniging',
                                    'vereniging__regio',
                                    'team_type',
                                    'team_klasse')
                    .exclude(team_klasse=None)
                    .filter(deelcompetitie__in=rk_deelcomp_pks)
                    .annotate(sporter_count=Count(tel_dit))
                    .order_by('team_klasse__volgorde',
                              '-aanvangsgemiddelde',
                              'vereniging__ver_nr'))

        prev_klasse = None
        for team in rk_teams:
            if team.klasse != prev_klasse:
                team.break_before = True
                prev_klasse = team.klasse

            # team AG is 0.0 - 30.0 --> toon als score: 000.0 .. 900.0
            ag_str = "%05.1f" % (team.aanvangsgemiddelde * aantal_pijlen)
            team.ag_str = ag_str.replace('.', ',')

            totaal_teams += 1

            try:
                klasse2teams[team.klasse].append(team)
            except KeyError:
                # dit is geen acceptabele klasse (waarschijnlijk een regio klasse)
                # pas dit meteen even aan
                team.klasse = None
                team.save(update_fields=['klasse'])
        # for

        context['rk_teams'] = klasse2teams

        # zoek de teams die niet 'af' zijn
        rk_teams = (KampioenschapTeam
                    .objects
                    .select_related('vereniging',
                                    'vereniging__regio',
                                    'team_type',
                                    'deelcompetitie')
                    .filter(deelcompetitie__in=rk_deelcomp_pks,
                            team_klasse=None)
                    .annotate(sporter_count=Count(tel_dit))
                    .order_by('team_type__volgorde',
                              '-aanvangsgemiddelde',
                              'vereniging__ver_nr'))

        is_eerste = True
        for team in rk_teams:
            # team AG is 0.0 - 30.0 --> toon als score: 000,0 .. 900,0
            ag_str = "%05.1f" % (team.aanvangsgemiddelde * aantal_pijlen)
            team.ag_str = ag_str.replace('.', ',')

            if comp.fase <= 'K' and self.rol_nu == Rollen.ROL_RKO:
                team.url_aanpassen = reverse('CompLaagRayon:teams-rk-koppelen',
                                             kwargs={'rk_team_pk': team.pk})

            totaal_teams += 1

            team.break_before = is_eerste
            is_eerste = False
        # for

        context['rk_teams_niet_af'] = rk_teams
        context['totaal_teams'] = totaal_teams
        context['toon_klassen'] = comp.klassengrenzen_vastgesteld_rk_bk

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'RK Teams')
        )

        menu_dynamics(self.request, context)
        return context


class RayonTeamsRKOView(UserPassesTestMixin, RayonTeamsView):

    """ Met deze view kan de RKO de aangemaakte teams inzien """

    # class variables shared by all instances
    subset_filter = False
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_RKO


class RayonTeamsAlleView(UserPassesTestMixin, RayonTeamsView):

    """ Met deze view kunnen de BB en BKO de aangemaakte teams inzien, met mogelijkheid tot filteren op een rayon """

    # class variables shared by all instances
    subset_filter = True
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO)


# end of file
