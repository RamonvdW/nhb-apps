# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.views.generic import TemplateView, View
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import (LAAG_REGIO, LAAG_RK, LAAG_BK, INSCHRIJF_METHODE_1, DeelCompetitie,
                               CompetitieKlasse, DeelcompetitieKlasseLimiet, DeelcompetitieRonde,
                               KampioenschapSchutterBoog, KampioenschapTeam, CompetitieMutatie,
                               MUTATIE_CUT, DEELNAME_NEE)
from Competitie.menu import menu_dynamics_competitie
from Functie.rol import Rollen, rol_get_huidige_functie
from Handleiding.views import reverse_handleiding
from Logboek.models import schrijf_in_logboek
from NhbStructuur.models import NhbVereniging
from Overig.background_sync import BackgroundSync
from Wedstrijden.models import CompetitieWedstrijd, CompetitieWedstrijdenPlan, WedstrijdLocatie
from types import SimpleNamespace
import datetime
import time


TEMPLATE_COMPRAYON_PLANNING = 'comprayon/planning-rayon.dtl'
TEMPLATE_COMPRAYON_WIJZIG_WEDSTRIJD = 'comprayon/wijzig-wedstrijd-rk.dtl'
TEMPLATE_COMPRAYON_LIJST_RK = 'comprayon/rko-rk-selectie.dtl'
TEMPLATE_COMPRAYON_WIJZIG_STATUS_RK_SCHUTTER = 'comprayon/wijzig-status-rk-deelnemer.dtl'
TEMPLATE_COMPRAYON_WIJZIG_LIMIETEN_RK = 'comprayon/wijzig-limieten-rk.dtl'

mutatie_ping = BackgroundSync(settings.BACKGROUND_SYNC__REGIOCOMP_MUTATIES)


class RayonPlanningView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de planning voor een competitie in een rayon """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_PLANNING
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            rk_deelcomp_pk = int(kwargs['rk_deelcomp_pk'][:6])  # afkappen voor de veiligheid
            deelcomp_rk = (DeelCompetitie
                           .objects
                           .select_related('competitie', 'nhb_rayon')
                           .get(pk=rk_deelcomp_pk, laag=LAAG_RK))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        context['deelcomp_rk'] = deelcomp_rk
        context['rayon'] = deelcomp_rk.nhb_rayon

        # maak het plan aan, als deze nog niet aanwezig was
        if not deelcomp_rk.plan:
            deelcomp_rk.plan = CompetitieWedstrijdenPlan()
            deelcomp_rk.plan.save()
            deelcomp_rk.save()

        klasse2schutters = dict()
        niet_gebruikt = dict()
        for obj in (KampioenschapSchutterBoog
                    .objects
                    .select_related('klasse__indiv')
                    .filter(deelcompetitie=deelcomp_rk)
                    .select_related('klasse')):
            try:
                klasse2schutters[obj.klasse.indiv.pk] += 1
            except KeyError:
                klasse2schutters[obj.klasse.indiv.pk] = 1
        # for

        for wkl in (CompetitieKlasse
                    .objects
                    .exclude(indiv__niet_voor_rk_bk=True)
                    .select_related('indiv', 'team')
                    .filter(competitie=deelcomp_rk.competitie)):
            if wkl.indiv:
                niet_gebruikt[100000 + wkl.indiv.pk] = wkl.indiv.beschrijving
            if wkl.team:
                if wkl.is_voor_teams_rk_bk:
                    niet_gebruikt[200000 + wkl.team.pk] = wkl.team.beschrijving
        # for

        # haal de RK wedstrijden op
        context['wedstrijden_rk'] = (deelcomp_rk.plan.wedstrijden
                                     .select_related('vereniging')
                                     .prefetch_related('indiv_klassen',
                                                       'team_klassen')
                                     .order_by('datum_wanneer',
                                               'tijd_begin_wedstrijd'))
        for obj in context['wedstrijden_rk']:

            obj.schutters_count = 0

            obj.wkl_namen = list()
            for wkl in obj.indiv_klassen.order_by('volgorde'):
                obj.wkl_namen.append(wkl.beschrijving)
                niet_gebruikt[100000 + wkl.pk] = None

                try:
                    obj.schutters_count += klasse2schutters[wkl.pk]
                except KeyError:
                    # geen schutters in deze klasse
                    pass
            # for

            for wkl in obj.team_klassen.order_by('volgorde'):
                obj.wkl_namen.append(wkl.beschrijving)
                niet_gebruikt[200000 + wkl.pk] = None

                # TODO: aantal teams vaststellen per klasse
                aantal_teams = 0
                obj.schutters_count += 4 * aantal_teams
            # for

        # for

        context['wkl_niet_gebruikt'] = [beschrijving for beschrijving in niet_gebruikt.values() if beschrijving]
        if len(context['wkl_niet_gebruikt']) == 0:
            del context['wkl_niet_gebruikt']

        if self.rol_nu == Rollen.ROL_RKO and self.functie_nu.nhb_rayon == deelcomp_rk.nhb_rayon:
            context['url_nieuwe_wedstrijd'] = reverse('CompRayon:rayon-planning',
                                                      kwargs={'rk_deelcomp_pk': deelcomp_rk.pk})

            for wedstrijd in context['wedstrijden_rk']:
                wedstrijd.url_wijzig = reverse('CompRayon:rayon-wijzig-wedstrijd',
                                               kwargs={'wedstrijd_pk': wedstrijd.pk})
            # for

        if self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO):
            deelcomp_bk = DeelCompetitie.objects.get(laag=LAAG_BK,
                                                     competitie=deelcomp_rk.competitie)
            context['url_bond'] = reverse('Competitie:bond-planning',
                                          kwargs={'deelcomp_pk': deelcomp_bk.pk})

        deelcomps = (DeelCompetitie
                     .objects
                     .select_related('nhb_regio')
                     .filter(laag=LAAG_REGIO,
                             competitie=deelcomp_rk.competitie,
                             nhb_regio__rayon=deelcomp_rk.nhb_rayon)
                     .order_by('nhb_regio__regio_nr'))
        context['regio_deelcomps'] = deelcomps

        # zoek het aantal regiowedstrijden erbij
        for deelcomp in deelcomps:
            plan_pks = (DeelcompetitieRonde
                        .objects
                        .exclude(beschrijving__contains=' oude programma')
                        .filter(deelcompetitie=deelcomp)
                        .values_list('plan__pk', flat=True))
            if deelcomp.inschrijf_methode == INSCHRIJF_METHODE_1:
                deelcomp.rondes_count = "-"
            else:
                deelcomp.rondes_count = len(plan_pks)
            deelcomp.wedstrijden_count = 0
            for plan in (CompetitieWedstrijdenPlan
                         .objects
                         .prefetch_related('wedstrijden')
                         .filter(pk__in=plan_pks)):
                deelcomp.wedstrijden_count += plan.wedstrijden.count()
            # for
        # for

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp_rk.competitie.pk)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Regel toevoegen' gebruikt wordt
            in de RK planning, om een nieuwe wedstrijd toe te voegen.
        """
        # alleen de RKO mag de planning uitbreiden
        if self.rol_nu != Rollen.ROL_RKO:
            raise PermissionDenied()

        try:
            rk_deelcomp_pk = int(kwargs['rk_deelcomp_pk'][:6])  # afkappen voor de veiligheid
            deelcomp_rk = (DeelCompetitie
                           .objects
                           .select_related('competitie', 'nhb_regio')
                           .get(pk=rk_deelcomp_pk,
                                laag=LAAG_RK,                          # moet voor RK zijn
                                nhb_rayon=self.functie_nu.nhb_rayon))  # moet juiste rayon zijn
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        # maak het plan aan, als deze nog niet aanwezig was
        if not deelcomp_rk.plan:
            deelcomp_rk.plan = CompetitieWedstrijdenPlan()
            deelcomp_rk.plan.save()
            deelcomp_rk.save()

        wedstrijd = CompetitieWedstrijd()
        wedstrijd.datum_wanneer = deelcomp_rk.competitie.rk_eerste_wedstrijd
        wedstrijd.tijd_begin_aanmelden = datetime.time(hour=10, minute=0, second=0)
        wedstrijd.tijd_begin_wedstrijd = wedstrijd.tijd_begin_aanmelden
        wedstrijd.tijd_einde_wedstrijd = wedstrijd.tijd_begin_aanmelden
        wedstrijd.save()

        deelcomp_rk.plan.wedstrijden.add(wedstrijd)

        return HttpResponseRedirect(reverse('CompRayon:rayon-wijzig-wedstrijd',
                                            kwargs={'wedstrijd_pk': wedstrijd.pk}))


class WijzigRayonWedstrijdView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de planning van een wedstrijd aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_WIJZIG_WEDSTRIJD
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_RKO

    @staticmethod
    def _get_wedstrijdklassen(deelcomp_rk, wedstrijd):
        """ Geef een lijst van individuele en team wedstrijdklassen terug.
            Elke klasse bevat een telling van het aantal sporters / teams
        """

        # voorkom dubbel koppelen: zoek uit welke klassen al gekoppeld zijn aan een andere wedstrijd
        alle_deelcomp_rk_plan_pks = DeelCompetitie.objects.filter(laag=LAAG_RK).values_list('plan__pk', flat=True)
        wedstrijd_pks = list()
        for plan in CompetitieWedstrijdenPlan.objects.prefetch_related('wedstrijden').filter(pk__in=alle_deelcomp_rk_plan_pks):
            pks = list(plan.wedstrijden.all().values_list('pk', flat=True))
            wedstrijd_pks.extend(pks)
        # for
        del alle_deelcomp_rk_plan_pks
        if wedstrijd.pk in wedstrijd_pks:
            wedstrijd_pks.remove(wedstrijd.pk)

        indiv_in_use = list()       # [indiv.pk, ..]
        team_in_use = list()        # [team.pk, ..]
        for wed in CompetitieWedstrijd.objects.prefetch_related('indiv_klassen', 'team_klassen').filter(pk__in=wedstrijd_pks):
            indiv_pks = list(wed.indiv_klassen.values_list('pk', flat=True))
            indiv_in_use.extend(indiv_pks)

            team_pks = list(wed.team_klassen.values_list('pk', flat=True))
            team_in_use.extend(team_pks)
        # for

        klasse2schutters = dict()
        for obj in (KampioenschapSchutterBoog
                    .objects
                    .exclude(deelname=DEELNAME_NEE)         # afgemelde schutters niet tellen
                    .filter(deelcompetitie=deelcomp_rk)
                    .select_related('klasse',
                                    'klasse__indiv')):
            try:
                klasse2schutters[obj.klasse.indiv.pk] += 1
            except KeyError:
                klasse2schutters[obj.klasse.indiv.pk] = 1
        # for

        # wedstrijdklassen
        wedstrijd_indiv_pks = [obj.pk for obj in wedstrijd.indiv_klassen.all()]
        wkl_indiv = (CompetitieKlasse
                     .objects
                     .exclude(indiv__niet_voor_rk_bk=True)      # verwijder regio-only klassen
                     .filter(competitie=deelcomp_rk.competitie,
                             team=None)
                     .select_related('indiv',
                                     'indiv__boogtype')
                     .order_by('indiv__volgorde')
                     .all())
        prev_boogtype = -1
        for obj in wkl_indiv:
            if prev_boogtype != obj.indiv.boogtype:
                prev_boogtype = obj.indiv.boogtype
                obj.break_before = True
            try:
                schutters = klasse2schutters[obj.indiv.pk]
                if schutters > 24:
                    schutters = 24
            except KeyError:
                schutters = 0
            obj.short_str = obj.indiv.beschrijving
            obj.schutters = schutters

            if obj.indiv.pk in indiv_in_use:
                obj.disable = True
            else:
                obj.geselecteerd = (obj.indiv.pk in wedstrijd_indiv_pks)
            obj.sel_str = "wkl_indiv_%s" % obj.indiv.pk
        # for

        klasse_count = dict()   # [klasse.pk] = count
        for klasse_pk in (KampioenschapTeam
                          .objects
                          .filter(deelcompetitie=deelcomp_rk)
                          .values_list('klasse__pk', flat=True)):
            try:
                klasse_count[klasse_pk] += 1
            except KeyError:
                klasse_count[klasse_pk] = 1
        # for

        wedstrijd_team_pks = [obj.pk for obj in wedstrijd.team_klassen.all()]
        wkl_team = (CompetitieKlasse
                    .objects
                    .filter(competitie=deelcomp_rk.competitie,
                            indiv=None,
                            is_voor_teams_rk_bk=True)
                    .select_related('team')
                    .order_by('team__volgorde'))

        for obj in wkl_team:
            obj.short_str = obj.team.beschrijving
            obj.sel_str = "wkl_team_%s" % obj.team.pk
            if obj.team.pk in team_in_use:
                obj.disable = True
            else:
                obj.geselecteerd = (obj.team.pk in wedstrijd_team_pks)

            try:
                obj.teams_count = klasse_count[obj.pk]
            except KeyError:
                obj.teams_count = 0
        # for

        return wkl_indiv, wkl_team

    @staticmethod
    def _get_dagen(deelcomp_rk, wedstrijd):
        opt_dagen = list()
        when = deelcomp_rk.competitie.rk_eerste_wedstrijd
        stop = deelcomp_rk.competitie.rk_laatste_wedstrijd
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

        return opt_dagen

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])     # afkappen voor de veiligheid
            wedstrijd = (CompetitieWedstrijd
                         .objects
                         .select_related('uitslag')
                         .prefetch_related('uitslag__scores',
                                           'indiv_klassen',
                                           'team_klassen')
                         .get(pk=wedstrijd_pk))
        except (ValueError, CompetitieWedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        # zoek het weeknummer waarin deze wedstrijd gehouden moet worden
        plan = wedstrijd.competitiewedstrijdenplan_set.all()[0]
        deelcomp_rk = plan.deelcompetitie_set.all()[0]

        # is dit de beheerder?
        if deelcomp_rk.functie != self.functie_nu:
            raise PermissionDenied()

        context['deelcomp_rk'] = deelcomp_rk
        context['wedstrijd'] = wedstrijd

        # maak de lijst waarop de wedstrijd gehouden kan worden
        context['opt_weekdagen'] = self._get_dagen(deelcomp_rk, wedstrijd)

        wedstrijd.tijd_begin_wedstrijd_str = wedstrijd.tijd_begin_wedstrijd.strftime("%H:%M")
        # wedstrijd.tijd_begin_aanmelden_str = wedstrijd.tijd_begin_aanmelden.strftime("%H%M")
        # wedstrijd.tijd_einde_wedstrijd_str = wedstrijd.tijd_einde_wedstrijd.strftime("%H%M")

        verenigingen = NhbVereniging.objects.filter(regio__rayon=deelcomp_rk.nhb_rayon,
                                                    regio__is_administratief=False)
        context['verenigingen'] = verenigingen

        # forceer een eerste vereniging
        # if not wedstrijd.vereniging:
        #     if verenigingen.count() > 0:
        #         wedstrijd.vereniging = verenigingen[0]
        #         wedstrijd.save()

        # zet de wedstrijdlocatie indien nog niet gezet en nu beschikbaar gekomen
        if not wedstrijd.locatie:
            if wedstrijd.vereniging:
                locaties = wedstrijd.vereniging.wedstrijdlocatie_set.all()
                if locaties.count() > 0:
                    wedstrijd.locatie = locaties[0]
                    wedstrijd.save()

        context['locaties'] = locaties = dict()
        pks = [ver.pk for ver in verenigingen]
        for obj in WedstrijdLocatie.objects.prefetch_related('verenigingen').filter(verenigingen__pk__in=pks):
            for ver in obj.verenigingen.all():
                locaties[str(ver.pk)] = obj.adres   # ver_nr --> adres
            # for
        # for

        context['wkl_indiv'], context['wkl_team'] = self._get_wedstrijdklassen(deelcomp_rk, wedstrijd)

        context['url_terug'] = reverse('CompRayon:rayon-planning', kwargs={'rk_deelcomp_pk': deelcomp_rk.pk})
        context['url_opslaan'] = reverse('CompRayon:rayon-wijzig-wedstrijd', kwargs={'wedstrijd_pk': wedstrijd.pk})

        context['url_verwijderen'] = reverse('CompRayon:rayon-verwijder-wedstrijd',
                                             kwargs={'wedstrijd_pk': wedstrijd.pk})

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp_rk.competitie.pk)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Opslaan' gebruikt wordt
        """

        try:
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])     # afkappen voor de veiligheid
            wedstrijd = (CompetitieWedstrijd
                         .objects
                         .select_related('uitslag')
                         .prefetch_related('uitslag__scores')
                         .get(pk=wedstrijd_pk))
        except (ValueError, CompetitieWedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        plan = wedstrijd.competitiewedstrijdenplan_set.all()[0]
        deelcomp_rk = plan.deelcompetitie_set.all()[0]

        # is dit de beheerder?
        if deelcomp_rk.functie != self.functie_nu:
            raise PermissionDenied()

        competitie = deelcomp_rk.competitie

        # weekdag is een cijfer van 0 tm 6
        # aanvang bestaat uit vier cijfers, zoals 0830
        weekdag = request.POST.get('weekdag', '')[:2]     # afkappen voor de veiligheid
        aanvang = request.POST.get('aanvang', '')[:5]
        nhbver_pk = request.POST.get('nhbver_pk', '')[:6]
        if weekdag == "" or nhbver_pk == "" or len(aanvang) != 5 or aanvang[2] != ':':
            raise Http404('Incompleet verzoek')

        try:
            weekdag = int(weekdag)
            aanvang = int(aanvang[0:0+2] + aanvang[3:3+2])
        except (TypeError, ValueError):
            raise Http404('Geen valide verzoek')

        if weekdag < 0 or weekdag > 30 or aanvang < 0 or aanvang > 2359:
            raise Http404('Geen valide verzoek')

        # weekdag is een offset ten opzicht van de eerste toegestane RK wedstrijddag
        wedstrijd.datum_wanneer = deelcomp_rk.competitie.rk_eerste_wedstrijd + datetime.timedelta(days=weekdag)

        # check dat datum_wanneer nu in de ingesteld RK periode valt
        if not (competitie.rk_eerste_wedstrijd <= wedstrijd.datum_wanneer <= competitie.rk_laatste_wedstrijd):
            raise Http404('Geen valide datum')

        # vertaal aanvang naar een tijd
        uur = aanvang // 100
        minuut = aanvang - (uur * 100)
        if uur < 0 or uur > 23 or minuut < 0 or minuut > 59:
            raise Http404('Geen valide tijdstip')

        wedstrijd.tijd_begin_wedstrijd = datetime.time(hour=uur, minute=minuut)

        if nhbver_pk == 'geen':
            wedstrijd.vereniging = None
            wedstrijd.locatie = None
        else:
            try:
                nhbver = NhbVereniging.objects.get(pk=nhbver_pk)
            except (NhbVereniging.DoesNotExist, ValueError):
                raise Http404('Vereniging niet gevonden')

            # check dat nhbver een van de aangeboden verenigingen is
            if nhbver.regio.rayon != deelcomp_rk.nhb_rayon or nhbver.regio.is_administratief:
                raise Http404('Geen valide rayon')

            wedstrijd.vereniging = nhbver

            locaties = nhbver.wedstrijdlocatie_set.all()
            if locaties.count() > 0:
                wedstrijd.locatie = locaties[0]
            else:
                wedstrijd.locatie = None

        wedstrijd.save()

        gekozen_indiv_klassen = list()
        gekozen_team_klassen = list()

        for key, value in request.POST.items():
            if key[:10] == "wkl_indiv_":
                try:
                    pk = int(key[10:10+6])          # afkappen voor de veiligheid
                except (IndexError, TypeError, ValueError):
                    pass
                else:
                    gekozen_indiv_klassen.append(pk)

            if key[:9] == "wkl_team_":
                try:
                    pk = int(key[9:9+6])            # afkappen voor de veiligheid
                except (IndexError, TypeError, ValueError):
                    pass
                else:
                    gekozen_team_klassen.append(pk)
        # for

        for obj in wedstrijd.indiv_klassen.all():
            if obj.pk in gekozen_indiv_klassen:
                # was al gekozen
                gekozen_indiv_klassen.remove(obj.pk)
            else:
                # moet uitgezet worden
                wedstrijd.indiv_klassen.remove(obj)
        # for

        for obj in wedstrijd.team_klassen.all():
            if obj.pk in gekozen_team_klassen:
                # was al gekozen
                gekozen_team_klassen.remove(obj.pk)
            else:
                # moet uitgezet worden
                wedstrijd.team_klassen.remove(obj)
        # for

        # alle nieuwe klassen toevoegen
        if len(gekozen_indiv_klassen):
            wedstrijd.indiv_klassen.add(*gekozen_indiv_klassen)

        if len(gekozen_team_klassen):
            wedstrijd.team_klassen.add(*gekozen_team_klassen)

        url = reverse('CompRayon:rayon-planning', kwargs={'rk_deelcomp_pk': deelcomp_rk.pk})
        return HttpResponseRedirect(url)


class RayonLimietenView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de RKO de status van een RK selectie aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_WIJZIG_LIMIETEN_RK
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_RKO

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            rk_deelcomp_pk = int(kwargs['rk_deelcomp_pk'][:6])  # afkappen voor de veiligheid
            deelcomp_rk = (DeelCompetitie
                           .objects
                           .select_related('competitie')
                           .get(pk=rk_deelcomp_pk,
                                laag=LAAG_RK))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        # controleer dat de juiste RKO aan de knoppen zit
        if self.functie_nu != deelcomp_rk.functie:
            raise PermissionDenied()     # niet de juiste RKO

        context['wkl_indiv'] = wkl_indiv = (CompetitieKlasse
                                            .objects
                                            .exclude(indiv__niet_voor_rk_bk=True)
                                            .filter(competitie=deelcomp_rk.competitie,
                                                    team=None)
                                            .select_related('indiv__boogtype')
                                            .order_by('indiv__volgorde'))

        context['wkl_teams'] = wkl_teams = (CompetitieKlasse
                                            .objects
                                            .filter(competitie=deelcomp_rk.competitie,
                                                    is_voor_teams_rk_bk=True,
                                                    indiv=None)
                                            .order_by('team__volgorde'))

        # zet de default limieten
        pk2wkl = dict()
        for wkl in wkl_indiv:
            wkl.limiet = 24     # default limiet
            wkl.sel = 'sel_%s' % wkl.pk
            pk2wkl[wkl.pk] = wkl
        # for

        for wkl in wkl_teams:
            # ERE klasse: 12 teams
            # overige: 8 teams
            wkl.limiet = 12 if "ERE" in wkl.team.beschrijving else 8
            wkl.sel = 'sel_%s' % wkl.pk
            pk2wkl[wkl.pk] = wkl
        # for

        # aanvullen met de opgeslagen limieten
        for limiet in (DeelcompetitieKlasseLimiet
                       .objects
                       .select_related('klasse')
                       .filter(deelcompetitie=deelcomp_rk,
                               klasse__in=pk2wkl.keys())):
            wkl = pk2wkl[limiet.klasse.pk]
            wkl.limiet = limiet.limiet
        # for

        context['url_opslaan'] = reverse('CompRayon:rayon-limieten',
                                         kwargs={'rk_deelcomp_pk': deelcomp_rk.pk})

        context['url_terug'] = reverse('Competitie:kies')

        context['wiki_rk_schutters'] = reverse_handleiding(self.request, settings.HANDLEIDING_RK_SELECTIE)

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp_rk.competitie.pk)
        return context

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de gebruik op de knop OPSLAAN druk """

        try:
            rk_deelcomp_pk = int(kwargs['rk_deelcomp_pk'][:6])  # afkappen voor de veiligheid
            deelcomp_rk = (DeelCompetitie
                           .objects
                           .select_related('competitie')
                           .get(pk=rk_deelcomp_pk,
                                laag=LAAG_RK))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        # controleer dat de juiste RKO aan de knoppen zit
        if self.functie_nu != deelcomp_rk.functie:
            raise PermissionDenied()     # niet de juiste RKO

        pk2ckl = dict()
        pk2keuze = dict()

        for ckl in (CompetitieKlasse
                    .objects
                    .exclude(indiv__niet_voor_rk_bk=True)
                    .filter(competitie=deelcomp_rk.competitie,
                            team=None)):

            sel = 'sel_%s' % ckl.pk
            keuze = request.POST.get(sel, None)
            if keuze:
                try:
                    pk2keuze[ckl.pk] = int(keuze[:2])   # afkappen voor de veiligheid
                    pk2ckl[ckl.pk] = ckl
                except ValueError:
                    pass
                else:
                    if pk2keuze[ckl.pk] not in (24, 20, 16, 12, 8, 4):
                        raise Http404('Geen valide keuze')
        # for

        for ckl in (CompetitieKlasse
                    .objects
                    .filter(competitie=deelcomp_rk.competitie,
                            is_voor_teams_rk_bk=True,
                            indiv=None)):

            sel = 'sel_%s' % ckl.pk
            keuze = request.POST.get(sel, None)
            if keuze:
                try:
                    pk2keuze[ckl.pk] = int(keuze[:2])   # afkappen voor de veiligheid
                    pk2ckl[ckl.pk] = ckl
                except ValueError:
                    pass
                else:
                    if pk2keuze[ckl.pk] not in (12, 10, 8, 6, 4):
                        raise Http404('Geen valide keuze')
        # for

        wijzig_limiet = list()     # list of tup(klasse, nieuwe_limiet, oude_limiet)

        for limiet in (DeelcompetitieKlasseLimiet
                       .objects
                       .select_related('klasse')
                       .filter(deelcompetitie=deelcomp_rk,
                               klasse__in=list(pk2keuze.keys()))):
            pk = limiet.klasse.pk
            keuze = pk2keuze[pk]
            del pk2keuze[pk]

            tup = (limiet.klasse, keuze, limiet.limiet)
            wijzig_limiet.append(tup)
        # for

        # verwerk de overgebleven keuzes waar nog geen limiet voor was
        for pk, keuze in pk2keuze.items():
            klasse = pk2ckl[pk]
            if klasse.indiv:
                default = 24
                tup = (klasse, keuze, default)
                wijzig_limiet.append(tup)
            else:
                # ERE klasse: 12 teams
                # overige: 8 teams
                default = 12 if "ERE" in klasse.team.beschrijving else 8
                tup = (klasse, keuze, default)
                wijzig_limiet.append(tup)
        # for

        # laat opnieuw de deelnemers boven de cut bepalen en sorteer op gemiddelde
        account = request.user
        door_str = "RKO %s" % account.volledige_naam()

        mutatie = None
        for klasse, nieuwe_limiet, oude_limiet in wijzig_limiet:
            # schrijf in het logboek
            if oude_limiet != nieuwe_limiet:
                msg = "De limiet (cut) voor klasse %s van de %s is aangepast van %s naar %s." % (
                        str(klasse), str(deelcomp_rk), oude_limiet, nieuwe_limiet)
                schrijf_in_logboek(self.request.user, "Competitie", msg)

                mutatie = CompetitieMutatie(mutatie=MUTATIE_CUT,
                                            door=door_str,
                                            deelcompetitie=deelcomp_rk,
                                            klasse=klasse,
                                            cut_oud=oude_limiet,
                                            cut_nieuw=nieuwe_limiet)
                mutatie.save()
        # for

        if mutatie:
            mutatie_ping.ping()

            # wacht op verwerking door achtergrond-taak voordat we verder gaan
            snel = str(request.POST.get('snel', ''))[:1]        # voor autotest

            if snel != '1':
                # wacht 3 seconden tot de mutatie uitgevoerd is
                interval = 0.2      # om steeds te verdubbelen
                total = 0.0         # om een limiet te stellen
                while not mutatie.is_verwerkt and total + interval <= 3.0:
                    time.sleep(interval)
                    total += interval   # 0.0 --> 0.2, 0.6, 1.4, 3.0, 6.2
                    interval *= 2       # 0.2 --> 0.4, 0.8, 1.6, 3.2
                    mutatie = CompetitieMutatie.objects.get(pk=mutatie.pk)
                # while

        return HttpResponseRedirect(reverse('Competitie:kies'))


class VerwijderWedstrijdView(UserPassesTestMixin, View):

    """ Deze view laat een RK wedstrijd verwijderen """

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_RKO

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Verwijder' gebruikt wordt
        """
        try:
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])  # afkappen voor de veiligheid
            wedstrijd = (CompetitieWedstrijd
                         .objects
                         .select_related('uitslag')
                         .prefetch_related('uitslag__scores')
                         .get(pk=wedstrijd_pk))
        except (ValueError, CompetitieWedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        plan = wedstrijd.competitiewedstrijdenplan_set.all()[0]
        try:
            deelcomp = DeelCompetitie.objects.get(plan=plan, laag=LAAG_RK)
        except DeelCompetitie.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        # correcte beheerder?
        if deelcomp.functie != self.functie_nu:
            raise PermissionDenied()

        # voorkom verwijderen van wedstrijden waar een uitslag aan hangt
        if wedstrijd.uitslag:
            uitslag = wedstrijd.uitslag
            if uitslag and (uitslag.is_bevroren or uitslag.scores.count() > 0):
                raise Http404('Uitslag mag niet meer gewijzigd worden')

        wedstrijd.delete()

        url = reverse('CompRayon:rayon-planning', kwargs={'rk_deelcomp_pk': deelcomp.pk})
        return HttpResponseRedirect(url)


# end of file
