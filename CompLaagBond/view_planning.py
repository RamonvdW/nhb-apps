# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.views.generic import TemplateView, View
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.definities import DEEL_RK, DEEL_BK, MUTATIE_KAMP_CUT, DEELNAME_NEE
from Competitie.models import (CompetitieIndivKlasse, CompetitieTeamKlasse, CompetitieMatch, CompetitieMutatie,
                               Kampioenschap, KampioenschapSporterBoog, KampioenschapTeam,
                               KampioenschapIndivKlasseLimiet, KampioenschapTeamKlasseLimiet)
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Locatie.models import WedstrijdLocatie
from Logboek.models import schrijf_in_logboek
from Site.core.background_sync import BackgroundSync
from Scheidsrechter.mutaties import scheids_mutatieverzoek_bepaal_reistijd_naar_alle_wedstrijdlocaties
from Vereniging.models import Vereniging
from types import SimpleNamespace
import datetime
import time


TEMPLATE_COMPLAAGBOND_PLANNING_LANDELIJK = 'complaagbond/planning-landelijk.dtl'
TEMPLATE_COMPLAAGBOND_WIJZIG_WEDSTRIJD = 'complaagbond/wijzig-wedstrijd.dtl'
TEMPLATE_COMPLAAGBOND_WIJZIG_LIMIETEN = 'complaagbond/wijzig-limieten.dtl'

mutatie_ping = BackgroundSync(settings.BACKGROUND_SYNC__REGIOCOMP_MUTATIES)


class PlanningView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de planning voor een competitie op het landelijke niveau """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPLAAGBOND_PLANNING_LANDELIJK
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_BKO)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelkamp_pk = int(kwargs['deelkamp_pk'][:6])  # afkappen voor de veiligheid
            deelkamp = (Kampioenschap
                        .objects
                        .select_related('competitie')
                        .get(pk=deelkamp_pk,
                             deel=DEEL_BK))
        except (KeyError, Kampioenschap.DoesNotExist):
            raise Http404('Kampioenschap niet gevonden')

        if self.rol_nu == Rol.ROL_BKO:
            if deelkamp.competitie.afstand != self.functie_nu.comp_type:
                raise Http404('Niet de beheerder')

        context['deelcomp_bk'] = deelkamp

        indiv_klasse2count = dict()
        team_klasse2count = dict()
        niet_gebruikt = dict()
        for obj in (KampioenschapSporterBoog
                    .objects
                    .filter(kampioenschap=deelkamp)
                    .filter(rank__lte=24)   # 24 = standaard limiet voor een individuele klasse
                    .exclude(rank=0)        # afgemeld
                    .select_related('indiv_klasse')):
            try:
                indiv_klasse2count[obj.indiv_klasse.pk] += 1
            except KeyError:
                indiv_klasse2count[obj.indiv_klasse.pk] = 1
        # for

        for cut in (KampioenschapIndivKlasseLimiet
                    .objects
                    .filter(kampioenschap=deelkamp)
                    .select_related('indiv_klasse')):

            try:
                if indiv_klasse2count[cut.indiv_klasse.pk] > cut.limiet:
                    indiv_klasse2count[cut.indiv_klasse.pk] = cut.limiet

            except KeyError:
                pass
        # for

        for obj in (KampioenschapTeam
                    .objects
                    .filter(kampioenschap=deelkamp)
                    # .exclude(rank=0)        # afgemeld
                    .select_related('team_klasse')):
            try:
                team_klasse2count[obj.team_klasse.pk] += 4
            except KeyError:
                team_klasse2count[obj.team_klasse.pk] = 4
        # for

        # FUTURE: standaard begrenzing aantal teams: ERE=12, rest=8

        for cut in (KampioenschapTeamKlasseLimiet
                    .objects
                    .filter(kampioenschap=deelkamp)
                    .select_related('team_klasse')):

            # vertaal aantal teams naar aantal sporters
            aantal_sporters = cut.limiet * 4

            try:
                if team_klasse2count[cut.team_klasse.pk] > aantal_sporters:
                    team_klasse2count[cut.team_klasse.pk] = aantal_sporters

            except KeyError:
                pass
        # for

        for wkl in (CompetitieIndivKlasse
                    .objects
                    .filter(competitie=deelkamp.competitie,
                            is_ook_voor_rk_bk=True)):             # verwijder regio-only klassen
            niet_gebruikt[100000 + wkl.pk] = wkl.beschrijving
        # for

        for wkl in (CompetitieTeamKlasse
                    .objects
                    .filter(competitie=deelkamp.competitie,
                            is_voor_teams_rk_bk=True)):
            niet_gebruikt[200000 + wkl.pk] = wkl.beschrijving
        # for

        # haal de BK wedstrijden op
        context['wedstrijden'] = (deelkamp.rk_bk_matches
                                  .select_related('vereniging',
                                                  'locatie')
                                  .prefetch_related('indiv_klassen',
                                                    'team_klassen')
                                  .order_by('datum_wanneer',
                                            'tijd_begin_wedstrijd'))
        for obj in context['wedstrijden']:

            obj.sporters_count = 0

            obj.wkl_namen = list()
            for wkl in obj.indiv_klassen.order_by('volgorde'):    # FUTURE: order_by zorgt voor extra database accesses
                obj.wkl_namen.append(wkl.beschrijving)
                niet_gebruikt[100000 + wkl.pk] = None

                try:
                    obj.sporters_count += indiv_klasse2count[wkl.pk]
                except KeyError:
                    # geen sporters in deze klasse
                    pass
            # for

            for wkl in obj.team_klassen.order_by('volgorde'):     # FUTURE: order_by zorgt voor extra database accesses
                obj.wkl_namen.append(wkl.beschrijving)
                niet_gebruikt[200000 + wkl.pk] = None

                try:
                    obj.sporters_count += team_klasse2count[wkl.pk]
                except KeyError:
                    pass
            # for

            obj.is_overbelast = False
            if obj.locatie:
                if deelkamp.competitie.is_indoor():
                    obj.capaciteit = obj.locatie.max_sporters_18m
                else:
                    obj.capaciteit = obj.locatie.max_sporters_25m

                if obj.capaciteit < obj.sporters_count:
                    obj.is_overbelast = True
            else:
                obj.capaciteit = '?'
        # for

        context['wkl_niet_gebruikt'] = [beschrijving for beschrijving in niet_gebruikt.values() if beschrijving]
        if len(context['wkl_niet_gebruikt']) == 0:
            del context['wkl_niet_gebruikt']

        if self.rol_nu == Rol.ROL_BKO:
            context['url_nieuwe_wedstrijd'] = reverse('CompLaagBond:planning',
                                                      kwargs={'deelkamp_pk': deelkamp.pk})

            for wedstrijd in context['wedstrijden']:
                wedstrijd.url_wijzig = reverse('CompLaagBond:wijzig-wedstrijd',
                                               kwargs={'match_pk': wedstrijd.pk})
            # for

        context['rayon_deelkamps'] = (Kampioenschap
                                      .objects
                                      .filter(deel=DEEL_RK,
                                              competitie=deelkamp.competitie)
                                      .order_by('rayon__rayon_nr',
                                                'deel'))

        comp = deelkamp.competitie

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Planning')
        )

        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Regel toevoegen' gebruikt wordt
            in de BK planning, om een nieuwe wedstrijd toe te voegen.
        """
        try:
            deelkamp_pk = int(kwargs['deelkamp_pk'][:6])  # afkappen voor de veiligheid
            deelkamp = (Kampioenschap
                        .objects
                        .select_related('competitie')
                        .get(pk=deelkamp_pk,
                             deel=DEEL_BK))
        except (ValueError, Kampioenschap.DoesNotExist):
            raise Http404('Kampioenschap niet gevonden')

        # alleen de BKO mag de planning uitbreiden
        if self.rol_nu != Rol.ROL_BKO or deelkamp.competitie.afstand != self.functie_nu.comp_type:
            raise Http404('Niet de beheerder')

        match = CompetitieMatch(
                    competitie=deelkamp.competitie,
                    datum_wanneer=deelkamp.competitie.begin_fase_P_indiv,
                    tijd_begin_wedstrijd=datetime.time(hour=10, minute=0, second=0),
                    beschrijving='BK, ' + deelkamp.competitie.beschrijving)
        match.save()

        deelkamp.rk_bk_matches.add(match)

        return HttpResponseRedirect(reverse('CompLaagBond:wijzig-wedstrijd',
                                            kwargs={'match_pk': match.pk}))


class WijzigWedstrijdView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de planning van een wedstrijd aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPLAAGBOND_WIJZIG_WEDSTRIJD
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_BKO

    @staticmethod
    def _get_wedstrijdklassen(deelkamp, match):
        """ Retourneer een lijst van individuele en team wedstrijdklassen.
            Elke klasse bevat een telling van het aantal sporters / teams
        """

        # voorkom dubbel koppelen: zoek uit welke klassen al gekoppeld zijn aan een andere wedstrijd
        match_pks = list(deelkamp.rk_bk_matches.all().values_list('pk', flat=True))
        if match.pk in match_pks:
            match_pks.remove(match.pk)

        indiv_in_use = list()       # [indiv.pk, ..]
        team_in_use = list()        # [team.pk, ..]
        for wed in (CompetitieMatch
                    .objects
                    .prefetch_related('indiv_klassen',
                                      'team_klassen')
                    .filter(pk__in=match_pks)):
            indiv_pks = list(wed.indiv_klassen.values_list('pk', flat=True))
            indiv_in_use.extend(indiv_pks)

            team_pks = list(wed.team_klassen.values_list('pk', flat=True))
            team_in_use.extend(team_pks)
        # for

        klasse2schutters = dict()
        for obj in (KampioenschapSporterBoog
                    .objects
                    .exclude(deelname=DEELNAME_NEE)         # afgemelde sporters niet tellen
                    .filter(kampioenschap=deelkamp)
                    .select_related('indiv_klasse')):
            try:
                klasse2schutters[obj.indiv_klasse.pk] += 1
            except KeyError:
                klasse2schutters[obj.indiv_klasse.pk] = 1
        # for

        # wedstrijdklassen
        wedstrijd_indiv_pks = [obj.pk for obj in match.indiv_klassen.all()]
        wkl_indiv = (CompetitieIndivKlasse
                     .objects
                     .filter(competitie=deelkamp.competitie,
                             is_ook_voor_rk_bk=True)      # verwijder regio-only klassen
                     .select_related('boogtype')
                     .order_by('volgorde')
                     .all())
        prev_boogtype = -1
        for obj in wkl_indiv:
            if prev_boogtype != obj.boogtype:
                prev_boogtype = obj.boogtype
                obj.break_before = True
            try:
                schutters = klasse2schutters[obj.pk]
                if schutters > 24:
                    schutters = 24
            except KeyError:
                schutters = 0
            obj.short_str = obj.beschrijving
            obj.schutters = schutters

            if obj.pk in indiv_in_use:
                obj.disable = True
            else:
                obj.geselecteerd = (obj.pk in wedstrijd_indiv_pks)
            obj.sel_str = "wkl_indiv_%s" % obj.pk
        # for

        klasse_count = dict()   # [klasse.pk] = count
        for klasse_pk in (KampioenschapTeam
                          .objects
                          .filter(kampioenschap=deelkamp)
                          .values_list('team_klasse__pk', flat=True)):
            try:
                klasse_count[klasse_pk] += 1
            except KeyError:
                klasse_count[klasse_pk] = 1
        # for

        wedstrijd_team_pks = [obj.pk for obj in match.team_klassen.all()]
        wkl_team = (CompetitieTeamKlasse
                    .objects
                    .filter(competitie=deelkamp.competitie,
                            is_voor_teams_rk_bk=True)
                    .order_by('volgorde'))

        for obj in wkl_team:
            obj.short_str = obj.beschrijving
            obj.sel_str = "wkl_team_%s" % obj.pk
            if obj.pk in team_in_use:
                obj.disable = True
            else:
                obj.geselecteerd = (obj.pk in wedstrijd_team_pks)

            try:
                obj.teams_count = klasse_count[obj.pk]
            except KeyError:
                obj.teams_count = 0
        # for

        return wkl_indiv, wkl_team

    @staticmethod
    def _get_dagen(deelkamp, wedstrijd):
        opt_dagen = list()
        when = min(deelkamp.competitie.begin_fase_P_indiv, deelkamp.competitie.begin_fase_P_teams)
        stop = min(deelkamp.competitie.einde_fase_P_indiv, deelkamp.competitie.einde_fase_P_teams)
        weekdag_nr = 0
        limit = 30
        while limit > 0 and when <= stop:
            obj = SimpleNamespace()
            obj.weekdag_nr = weekdag_nr
            obj.datum = when
            obj.actief = (when == wedstrijd.datum_wanneer)
            opt_dagen.append(obj)

            limit -= 1
            when += datetime.timedelta(days=1)
            weekdag_nr += 1
        # while

        # skip alle dagen tot het volgende blok
        stop = max(deelkamp.competitie.begin_fase_P_indiv, deelkamp.competitie.begin_fase_P_teams)
        while when < stop:
            when += datetime.timedelta(days=1)
            weekdag_nr += 1
        # while

        stop = max(deelkamp.competitie.einde_fase_P_indiv, deelkamp.competitie.einde_fase_P_teams)
        while limit > 0 and when <= stop:
            obj = SimpleNamespace()
            obj.weekdag_nr = weekdag_nr
            obj.datum = when
            obj.actief = (when == wedstrijd.datum_wanneer)
            opt_dagen.append(obj)

            limit -= 1
            when += datetime.timedelta(days=1)
            weekdag_nr += 1
        # while

        return opt_dagen

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            match_pk = int(kwargs['match_pk'][:6])     # afkappen voor de veiligheid
            match = (CompetitieMatch
                     .objects
                     .select_related('uitslag')
                     .prefetch_related('uitslag__scores',
                                       'indiv_klassen',
                                       'team_klassen')
                     .get(pk=match_pk))
        except (ValueError, CompetitieMatch.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        # zoek het weeknummer waarin deze wedstrijd gehouden moet worden
        deelkamps = match.kampioenschap_set.all()
        if len(deelkamps) == 0:
            raise Http404('Geen BK wedstrijd')
        deelkamp = deelkamps[0]
        comp = deelkamp.competitie
        is_25m = (comp.is_25m1pijl())

        # is dit de beheerder?
        if deelkamp.functie != self.functie_nu:
            raise Http404('Niet de beheerder')

        context['deelkamp'] = deelkamp
        context['wedstrijd'] = match

        # maak de lijst waarop de wedstrijd gehouden kan worden
        context['opt_weekdagen'] = self._get_dagen(deelkamp, match)

        match.tijd_begin_wedstrijd_str = match.tijd_begin_wedstrijd.strftime("%H:%M")
        # wedstrijd.tijd_begin_aanmelden_str = wedstrijd.tijd_begin_aanmelden.strftime("%H%M")
        # wedstrijd.tijd_einde_wedstrijd_str = wedstrijd.tijd_einde_wedstrijd.strftime("%H%M")

        verenigingen = (Vereniging
                        .objects
                        .filter(regio__is_administratief=False)
                        .prefetch_related('wedstrijdlocatie_set')
                        .order_by('ver_nr'))
        context['verenigingen'] = verenigingen

        # zet de locatie indien nog niet gezet en nu beschikbaar gekomen
        if not match.locatie:
            if match.vereniging:
                locaties = match.vereniging.wedstrijdlocatie_set.exclude(zichtbaar=False).all()
                if locaties.count() > 0:
                    match.locatie = locaties[0]
                    match.save()

        context['all_locaties'] = all_locs = list()
        for ver in verenigingen:
            for loc in ver.wedstrijdlocatie_set.exclude(zichtbaar=False):
                keep = False
                if is_25m:
                    if loc.banen_25m > 0 and (loc.discipline_indoor or loc.discipline_25m1pijl):
                        keep = True
                else:
                    if loc.discipline_indoor and loc.banen_18m > 0:
                        keep = True

                if keep:
                    all_locs.append(loc)
                    loc.ver_pk = ver.pk
                    keuze = loc.adres_oneliner()
                    if loc.notities:
                        keuze += ' (%s)' % loc.notities
                    if not keuze:
                        keuze = loc.plaats
                    if not keuze:
                        keuze = 'Locatie zonder naam (%s)' % loc.pk
                    loc.keuze_str = keuze
                    if match.locatie == loc:
                        loc.selected = True
            # for
        # for

        context['wkl_indiv'], context['wkl_team'] = self._get_wedstrijdklassen(deelkamp, match)

        context['url_opslaan'] = reverse('CompLaagBond:wijzig-wedstrijd', kwargs={'match_pk': match.pk})

        context['url_verwijderen'] = reverse('CompLaagBond:verwijder-wedstrijd',
                                             kwargs={'match_pk': match.pk})

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (reverse('CompLaagBond:planning', kwargs={'deelkamp_pk': deelkamp.pk}), 'Planning BK'),
            (None, 'Wijzig BK wedstrijd')
        )

        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Opslaan' gebruikt wordt
        """

        try:
            match_pk = int(kwargs['match_pk'][:6])     # afkappen voor de veiligheid
            match = (CompetitieMatch
                     .objects
                     .select_related('uitslag')
                     .prefetch_related('uitslag__scores')
                     .get(pk=match_pk))
        except (ValueError, CompetitieMatch.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        deelkamps = match.kampioenschap_set.all()
        if len(deelkamps) == 0:
            raise Http404('Geen BK wedstrijd')
        deelkamp = deelkamps[0]

        # is dit de beheerder?
        if deelkamp.functie != self.functie_nu:
            raise Http404('Niet de beheerder')

        comp = deelkamp.competitie
        is_25m = (comp.is_25m1pijl())

        # weekdag is een cijfer van 0 tm 6
        # aanvang bestaat uit vier cijfers, zoals 0830
        weekdag = request.POST.get('weekdag', '')[:2]           # afkappen voor de veiligheid
        aanvang = request.POST.get('aanvang', '')[:5]           # afkappen voor de veiligheid
        ver_pk = request.POST.get('ver_pk', '')[:6]             # afkappen voor de veiligheid
        loc_pk = request.POST.get('loc_pk', '')[:6]             # afkappen voor de veiligheid

        # let op: loc_pk='' is toegestaan
        if weekdag == "" or ver_pk == "" or len(aanvang) != 5 or aanvang[2] != ':':
            raise Http404('Incompleet verzoek')

        try:
            weekdag = int(weekdag)
            aanvang = int(aanvang[0:0+2] + aanvang[3:3+2])
        except (TypeError, ValueError):
            raise Http404('Geen valide verzoek')

        if weekdag < 0 or weekdag > 30 or aanvang < 0 or aanvang > 2359:
            raise Http404('Geen valide verzoek')

        # weekdag is een offset ten opzicht van de eerste toegestane BK wedstrijddag
        begin = min(comp.begin_fase_P_indiv, comp.begin_fase_P_teams)
        match.datum_wanneer = begin + datetime.timedelta(days=weekdag)

        # check dat datum_wanneer nu in de ingesteld BK periode valt
        if not ((comp.begin_fase_P_indiv <= match.datum_wanneer <= comp.einde_fase_P_indiv) or
                (comp.begin_fase_P_teams <= match.datum_wanneer <= comp.einde_fase_P_teams)):
            raise Http404('Geen valide datum')

        # vertaal aanvang naar een tijd
        uur = aanvang // 100
        minuut = aanvang - (uur * 100)
        if uur < 0 or uur > 23 or minuut < 0 or minuut > 59:
            raise Http404('Geen valide tijdstip')

        match.tijd_begin_wedstrijd = datetime.time(hour=uur, minute=minuut)

        if ver_pk == 'geen':
            match.vereniging = None
            match.locatie = None
        else:
            try:
                ver = Vereniging.objects.get(pk=ver_pk, regio__is_administratief=False)
            except (Vereniging.DoesNotExist, ValueError):
                raise Http404('Vereniging niet gevonden')

            match.vereniging = ver

            if loc_pk:
                try:
                    loc = ver.wedstrijdlocatie_set.get(pk=loc_pk)
                except WedstrijdLocatie.DoesNotExist:
                    raise Http404('Locatie niet gevonden')
            else:
                # formulier stuurt niets als er niet gekozen hoeft te worden, of als er geen locatie is
                loc = None
                for ver_loc in ver.wedstrijdlocatie_set.exclude(zichtbaar=False).all():
                    keep = False
                    if is_25m:
                        if ver_loc.banen_25m > 0 and (ver_loc.discipline_indoor or ver_loc.discipline_25m1pijl):
                            keep = True
                    else:
                        if ver_loc.discipline_indoor and ver_loc.banen_18m > 0:
                            keep = True

                    if keep:
                        loc = ver_loc
                # for

            if match.locatie != loc:
                # laat de reisafstand alvast bijwerken
                snel = str(request.POST.get('snel', ''))[:1]  # voor autotest
                scheids_mutatieverzoek_bepaal_reistijd_naar_alle_wedstrijdlocaties('Planning BK', snel == '1')

            match.locatie = loc

        match.save()

        # wedstrijdklassen
        goede_wkl_indiv_pks = list(CompetitieIndivKlasse
                                   .objects
                                   .filter(competitie=deelkamp.competitie,
                                           is_ook_voor_rk_bk=True)      # verwijder regio-only klassen
                                   .values_list('pk', flat=True))
        goede_wkl_team_pks = list(CompetitieTeamKlasse
                                  .objects
                                  .filter(competitie=deelkamp.competitie,
                                          is_voor_teams_rk_bk=True)
                                  .values_list('pk', flat=True))

        gekozen_indiv_klassen = list()
        gekozen_team_klassen = list()

        for key, value in request.POST.items():
            if key[:10] == "wkl_indiv_":
                try:
                    pk = int(key[10:10+6])          # afkappen voor de veiligheid
                except (IndexError, TypeError, ValueError):
                    pass
                else:
                    # filter slechte pk's om verder een database error te voorkomen
                    if pk in goede_wkl_indiv_pks:
                        gekozen_indiv_klassen.append(pk)

            if key[:9] == "wkl_team_":
                try:
                    pk = int(key[9:9+6])            # afkappen voor de veiligheid
                except (IndexError, TypeError, ValueError):
                    pass
                else:
                    # filter slechte pk's om verder een database error te voorkomen
                    if pk in goede_wkl_team_pks:
                        gekozen_team_klassen.append(pk)
        # for

        for obj in match.indiv_klassen.all():
            if obj.pk in gekozen_indiv_klassen:
                # was al gekozen
                gekozen_indiv_klassen.remove(obj.pk)
            else:
                # moet uitgezet worden
                match.indiv_klassen.remove(obj)
        # for

        for obj in match.team_klassen.all():
            if obj.pk in gekozen_team_klassen:
                # was al gekozen
                gekozen_team_klassen.remove(obj.pk)
            else:
                # moet uitgezet worden
                match.team_klassen.remove(obj)
        # for

        # alle nieuwe klassen toevoegen
        if len(gekozen_indiv_klassen):
            match.indiv_klassen.add(*gekozen_indiv_klassen)

        if len(gekozen_team_klassen):
            match.team_klassen.add(*gekozen_team_klassen)

        # update aantal scheidsrechters nodig
        sr_nodig = False
        for obj in match.indiv_klassen.all():
            sr_nodig |= obj.krijgt_scheids_bk
        # for
        for obj in match.team_klassen.all():
            sr_nodig |= obj.krijgt_scheids_bk
        # for

        if sr_nodig:
            match.aantal_scheids = 1
        else:
            match.aantal_scheids = 0
        match.save(update_fields=['aantal_scheids'])

        url = reverse('CompLaagBond:planning', kwargs={'deelkamp_pk': deelkamp.pk})
        return HttpResponseRedirect(url)


class WijzigLimietenView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de BKO de status van een BK selectie aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPLAAGBOND_WIJZIG_LIMIETEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_BKO

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelkamp_pk = int(kwargs['deelkamp_pk'][:6])  # afkappen voor de veiligheid
            deelkamp = (Kampioenschap
                        .objects
                        .select_related('competitie')
                        .get(pk=deelkamp_pk,
                             deel=DEEL_BK))
        except (ValueError, Kampioenschap.DoesNotExist):
            raise Http404('Kampioenschap niet gevonden')

        # controleer dat de juiste BKO aan de knoppen zit
        if self.functie_nu != deelkamp.functie:
            raise Http404('Niet de beheerder')

        comp = deelkamp.competitie
        if comp.is_25m1pijl():
            indiv_limieten = settings.COMPETITIE_25M_INDIV_LIMIETEN
            teams_limieten = settings.COMPETITIE_25M_TEAMS_LIMIETEN
        else:
            indiv_limieten = settings.COMPETITIE_18M_INDIV_LIMIETEN
            teams_limieten = settings.COMPETITIE_18M_TEAMS_LIMIETEN

        context['indiv_limieten'] = indiv_limieten
        context['teams_limieten'] = teams_limieten

        context['wkl_indiv'] = wkl_indiv = (CompetitieIndivKlasse
                                            .objects
                                            .filter(competitie=deelkamp.competitie,
                                                    is_ook_voor_rk_bk=True)
                                            .select_related('boogtype')
                                            .order_by('volgorde'))

        context['wkl_teams'] = wkl_teams = (CompetitieTeamKlasse
                                            .objects
                                            .filter(competitie=deelkamp.competitie,
                                                    is_voor_teams_rk_bk=True)
                                            .order_by('volgorde'))

        # zet de default limieten
        pk2wkl_indiv = dict()
        for wkl in wkl_indiv:
            wkl.limiet = 24     # default limiet
            wkl.sel = 'isel_%s' % wkl.pk
            pk2wkl_indiv[wkl.pk] = wkl
        # for

        pk2wkl_team = dict()
        for wkl in wkl_teams:
            # ERE klasse: 12 teams
            # overige: 8 teams
            wkl.limiet = 12 if "ERE" in wkl.beschrijving else 8
            wkl.sel = 'tsel_%s' % wkl.pk
            pk2wkl_team[wkl.pk] = wkl
        # for

        # aanvullen met de opgeslagen limieten
        for limiet in (KampioenschapIndivKlasseLimiet
                       .objects
                       .select_related('indiv_klasse')
                       .filter(kampioenschap=deelkamp,
                               indiv_klasse__in=pk2wkl_indiv.keys())):
            wkl = pk2wkl_indiv[limiet.indiv_klasse.pk]
            wkl.limiet = limiet.limiet
        # for

        for limiet in (KampioenschapTeamKlasseLimiet
                       .objects
                       .select_related('team_klasse')
                       .filter(kampioenschap=deelkamp,
                               team_klasse__in=pk2wkl_team.keys())):
            wkl = pk2wkl_team[limiet.team_klasse.pk]
            wkl.limiet = limiet.limiet
        # for

        context['url_opslaan'] = reverse('CompLaagBond:wijzig-limieten',
                                         kwargs={'deelkamp_pk': deelkamp.pk})

        comp = deelkamp.competitie
        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'BK limieten')
        )

        return context

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de gebruik op de knop OPSLAAN druk """

        try:
            deelkamp_pk = int(kwargs['deelkamp_pk'][:6])  # afkappen voor de veiligheid
            deelkamp = (Kampioenschap
                        .objects
                        .select_related('competitie')
                        .get(pk=deelkamp_pk,
                             deel=DEEL_BK))
        except (ValueError, Kampioenschap.DoesNotExist):
            raise Http404('Kampioenschap niet gevonden')

        # controleer dat de BKO aan de knoppen zit
        if self.functie_nu != deelkamp.functie:
            raise Http404('Niet de beheerder')

        comp = deelkamp.competitie
        if comp.is_25m1pijl():
            indiv_limieten = settings.COMPETITIE_25M_INDIV_LIMIETEN
            teams_limieten = settings.COMPETITIE_25M_TEAMS_LIMIETEN
        else:
            indiv_limieten = settings.COMPETITIE_18M_INDIV_LIMIETEN
            teams_limieten = settings.COMPETITIE_18M_TEAMS_LIMIETEN

        pk2ckl_indiv = dict()
        pk2ckl_team = dict()
        pk2keuze_indiv = dict()
        pk2keuze_team = dict()

        for ckl in (CompetitieIndivKlasse
                    .objects
                    .filter(competitie=comp,
                            is_ook_voor_rk_bk=True)):

            sel = 'isel_%s' % ckl.pk
            keuze = request.POST.get(sel, None)
            if keuze:
                try:
                    pk2keuze_indiv[ckl.pk] = int(keuze[:2])   # afkappen voor de veiligheid
                    pk2ckl_indiv[ckl.pk] = ckl
                except ValueError:
                    pass
                else:
                    if pk2keuze_indiv[ckl.pk] not in indiv_limieten:
                        raise Http404('Geen valide keuze voor indiv limiet')
        # for

        for ckl in (CompetitieTeamKlasse
                    .objects
                    .filter(competitie=comp,
                            is_voor_teams_rk_bk=True)):

            sel = 'tsel_%s' % ckl.pk
            keuze = request.POST.get(sel, None)
            if keuze:
                try:
                    pk2keuze_team[ckl.pk] = int(keuze[:2])   # afkappen voor de veiligheid
                    pk2ckl_team[ckl.pk] = ckl
                except ValueError:
                    pass
                else:
                    if pk2keuze_team[ckl.pk] not in teams_limieten:
                        raise Http404('Geen valide keuze voor teams limiet')
        # for

        wijzig_limiet_indiv = list()     # list of tup(indiv_klasse, nieuwe_limiet, oude_limiet)
        wijzig_limiet_team = list()      # list of tup(team_klasse, nieuwe_limiet, oude_limiet)

        for limiet in (KampioenschapIndivKlasseLimiet
                       .objects
                       .select_related('indiv_klasse')
                       .filter(kampioenschap=deelkamp,
                               indiv_klasse__in=list(pk2keuze_indiv.keys()))):

            pk = limiet.indiv_klasse.pk
            keuze = pk2keuze_indiv[pk]
            del pk2keuze_indiv[pk]

            tup = (limiet.indiv_klasse, keuze, limiet.limiet)
            wijzig_limiet_indiv.append(tup)
        # for

        for limiet in (KampioenschapTeamKlasseLimiet
                       .objects
                       .select_related('team_klasse')
                       .filter(kampioenschap=deelkamp,
                               team_klasse__in=list(pk2keuze_team.keys()))):

            pk = limiet.team_klasse.pk
            keuze = pk2keuze_team[pk]
            del pk2keuze_team[pk]

            tup = (limiet.team_klasse, keuze, limiet.limiet)
            wijzig_limiet_team.append(tup)
        # for

        # verwerk de overgebleven keuzes waar nog geen limiet voor was
        for pk, keuze in pk2keuze_indiv.items():
            try:
                indiv_klasse = pk2ckl_indiv[pk]
            except KeyError:        # pragma: no cover
                pass
            else:
                # indiv klasse
                default = 24
                tup = (indiv_klasse, keuze, default)
                wijzig_limiet_indiv.append(tup)
        # for

        # verwerk de overgebleven keuzes waar nog geen limiet voor was
        for pk, keuze in pk2keuze_team.items():
            try:
                team_klasse = pk2ckl_team[pk]
            except KeyError:        # pragma: no cover
                pass
            else:
                # ERE klasse: 12 teams
                # overige: 8 teams
                default = 12 if "ERE" in team_klasse.beschrijving else 8
                tup = (team_klasse, keuze, default)
                wijzig_limiet_team.append(tup)
        # for

        # laat opnieuw de deelnemers boven de cut bepalen en sorteer op gemiddelde
        door_account = get_account(request)
        door_str = "BKO %s" % door_account.volledige_naam()
        door_str = door_str[:149]

        mutatie = None
        for indiv_klasse, nieuwe_limiet, oude_limiet in wijzig_limiet_indiv:
            # schrijf in het logboek
            if oude_limiet != nieuwe_limiet:
                msg = "De limiet (cut) voor klasse %s van de %s is aangepast van %s naar %s." % (
                        str(indiv_klasse), str(deelkamp), oude_limiet, nieuwe_limiet)
                schrijf_in_logboek(door_account, "Competitie", msg)

                mutatie = CompetitieMutatie(mutatie=MUTATIE_KAMP_CUT,
                                            door=door_str,
                                            kampioenschap=deelkamp,
                                            indiv_klasse=indiv_klasse,
                                            cut_oud=oude_limiet,
                                            cut_nieuw=nieuwe_limiet)
                mutatie.save()
        # for

        for team_klasse, nieuwe_limiet, oude_limiet in wijzig_limiet_team:
            # schrijf in het logboek
            if oude_limiet != nieuwe_limiet:
                msg = "De limiet (cut) voor klasse %s van de %s is aangepast van %s naar %s." % (
                        str(team_klasse), str(deelkamp), oude_limiet, nieuwe_limiet)
                schrijf_in_logboek(door_account, "Competitie", msg)

                mutatie = CompetitieMutatie(mutatie=MUTATIE_KAMP_CUT,
                                            door=door_str,
                                            kampioenschap=deelkamp,
                                            team_klasse=team_klasse,
                                            cut_oud=oude_limiet,
                                            cut_nieuw=nieuwe_limiet)
                mutatie.save()
        # for

        if mutatie:
            mutatie_ping.ping()

            # wacht op verwerking door achtergrond-taak voordat we verder gaan
            snel = str(request.POST.get('snel', ''))[:1]        # voor autotest

            if snel != '1':                                     # pragma: no cover
                # wacht 3 seconden tot de mutatie uitgevoerd is
                interval = 0.2      # om steeds te verdubbelen
                total = 0.0         # om een limiet te stellen
                while not mutatie.is_verwerkt and total + interval <= 3.0:
                    time.sleep(interval)
                    total += interval   # 0.0 --> 0.2, 0.6, 1.4, 3.0, 6.2
                    interval *= 2       # 0.2 --> 0.4, 0.8, 1.6, 3.2
                    mutatie = CompetitieMutatie.objects.get(pk=mutatie.pk)
                # while

        url = reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk})

        return HttpResponseRedirect(url)


class VerwijderWedstrijdView(UserPassesTestMixin, View):

    """ Deze view laat een BK wedstrijd verwijderen """

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_BKO

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Verwijder' gebruikt wordt
        """
        try:
            match_pk = int(kwargs['match_pk'][:6])  # afkappen voor de veiligheid
            match = (CompetitieMatch
                     .objects
                     .select_related('uitslag')
                     .prefetch_related('uitslag__scores')
                     .get(pk=match_pk))
        except (ValueError, CompetitieMatch.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        deelkamps = match.kampioenschap_set.filter(deel=DEEL_BK)
        if len(deelkamps) == 0:
            raise Http404('Geen BK wedstrijd')

        deelkamp = deelkamps[0]

        # correcte beheerder?
        if deelkamp.functie != self.functie_nu:
            raise Http404('Niet de beheerder')

        # voorkom verwijderen van wedstrijden waar een uitslag aan hangt
        if match.uitslag:
            uitslag = match.uitslag
            if uitslag and (uitslag.is_bevroren or uitslag.scores.count() > 0):
                raise Http404('Uitslag mag niet meer gewijzigd worden')

        match.delete()

        url = reverse('CompLaagBond:planning', kwargs={'deelkamp_pk': deelkamp.pk})
        return HttpResponseRedirect(url)


# end of file
