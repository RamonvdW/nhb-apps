# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView, View
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import Account
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie
from Logboek.models import schrijf_in_logboek
from NhbStructuur.models import NhbCluster, NhbVereniging
from Taken.taken import maak_taak
from Wedstrijden.models import CompetitieWedstrijd, WedstrijdLocatie
from .models import (LAAG_REGIO, LAAG_RK, LAAG_BK, INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_2,
                     DeelCompetitie, DeelcompetitieRonde,
                     CompetitieKlasse, RegioCompetitieSchutterBoog)
from .operations import maak_deelcompetitie_ronde
from .menu import menu_dynamics_competitie
from types import SimpleNamespace
import datetime


TEMPLATE_COMPETITIE_PLANNING_REGIO = 'competitie/planning-regio.dtl'
TEMPLATE_COMPETITIE_PLANNING_REGIO_METHODE1 = 'competitie/planning-regio-methode1.dtl'
TEMPLATE_COMPETITIE_PLANNING_REGIO_CLUSTER = 'competitie/planning-regio-cluster.dtl'
TEMPLATE_COMPETITIE_PLANNING_REGIO_RONDE = 'competitie/planning-regio-ronde.dtl'
TEMPLATE_COMPETITIE_PLANNING_REGIO_RONDE_METHODE1 = 'competitie/planning-regio-ronde-methode1.dtl'
TEMPLATE_COMPETITIE_WIJZIG_WEDSTRIJD = 'competitie/wijzig-wedstrijd.dtl'
TEMPLATE_COMPETITIE_AFSLUITEN_REGIOCOMP = 'competitie/rcl-afsluiten-regiocomp.dtl'


# python strftime: 0=sunday, 6=saturday
# wij rekenen het verschil ten opzicht van maandag in de week
WEEK_DAGEN = ((0, 'Maandag'),
              (1, 'Dinsdag'),
              (2, 'Woensdag'),
              (3, 'Donderdag'),
              (4, 'Vrijdag'),
              (5, 'Zaterdag'),
              (6, 'Zondag'))

JA_NEE = {False: 'Nee', True: 'Ja'}


def planning_sorteer_weeknummers(rondes):
    # sorteer op week nummer
    # en ondersteun dat meerdere rondes hetzelfde nummer hebben
    nr2rondes = dict()      # [week nr] = [ronde, ronde, ..]
    nrs = list()
    for ronde in rondes:
        nr = ronde.week_nr
        if nr < 26:
            nr += 100
        if nr not in nrs:
            nrs.append(nr)
        try:
            nr2rondes[nr].append(ronde)
        except KeyError:
            nr2rondes[nr] = [ronde]
    # for
    nrs.sort()
    nieuw = list()
    for nr in nrs:
        nieuw.extend(nr2rondes[nr])
    # for
    return nieuw


class RegioPlanningView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de planning voor een competitie in een regio """

    # class variables shared by all instances
    template1 = TEMPLATE_COMPETITIE_PLANNING_REGIO
    template2 = TEMPLATE_COMPETITIE_PLANNING_REGIO_METHODE1
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL)

    def _get_methode_1(self, context, deelcomp):
        self.template_name = self.template2

        context['handleiding_planning_regio_url'] = reverse('Handleiding:Planning_Regio')

        # zoek de regio planning op
        regio_ronde = None
        for ronde in (DeelcompetitieRonde
                      .objects
                      .filter(deelcompetitie=deelcomp,
                              cluster=None)
                      .order_by('beschrijving')):
            if not ronde.is_voor_import_oude_programma():
                regio_ronde = ronde
                break
        # for

        if not regio_ronde:
            # maak de enige ronde automatisch aan
            regio_ronde = maak_deelcompetitie_ronde(deelcomp, cluster=None)
            regio_ronde.week_nr = 0
            regio_ronde.beschrijving = "Alle regio wedstrijden"
            regio_ronde.save()

        regio_ronde.wedstrijden_count = regio_ronde.plan.wedstrijden.count()
        regio_ronde.url = reverse('Competitie:regio-methode1-planning',
                                  kwargs={'ronde_pk': regio_ronde.pk})
        context['regio_ronde'] = regio_ronde

        # zorg dat de clusters een ronde hebben
        for cluster in (NhbCluster
                        .objects
                        .filter(regio=deelcomp.nhb_regio,
                                gebruik=deelcomp.competitie.afstand)
                        .prefetch_related('nhbvereniging_set',
                                          'deelcompetitieronde_set')
                        .select_related('regio')
                        .order_by('letter')):

            if cluster.nhbvereniging_set.count() > 0:
                # maak de enige ronde automatisch aan
                if cluster.deelcompetitieronde_set.count() == 0:
                    maak_deelcompetitie_ronde(deelcomp, cluster)
        # for

        # zoek de bruikbare clusters
        context['clusters'] = clusters = list()
        for cluster in (NhbCluster
                        .objects
                        .filter(regio=deelcomp.nhb_regio,
                                gebruik=deelcomp.competitie.afstand)
                        .prefetch_related('nhbvereniging_set',
                                          'deelcompetitieronde_set')
                        .select_related('regio')
                        .order_by('letter')):

            if cluster.nhbvereniging_set.count() > 0:
                ronde = cluster.deelcompetitieronde_set.all()[0]
                cluster.wedstrijden_count = ronde.plan.wedstrijden.count()
                cluster.ronde_url = reverse('Competitie:regio-methode1-planning',
                                            kwargs={'ronde_pk': ronde.pk})

                clusters.append(cluster)
        # for

    def _get_methode_2_3(self, context, deelcomp, mag_wijzigen):
        self.template_name = self.template1
        context['handleiding_planning_regio_url'] = reverse('Handleiding:Planning_Regio')

        rondes = planning_sorteer_weeknummers(
                                DeelcompetitieRonde
                                .objects
                                .filter(deelcompetitie=deelcomp,
                                        cluster=None)
                                .order_by('beschrijving'))

        context['rondes'] = list()
        context['rondes_import'] = list()
        for ronde in rondes:
            ronde.wedstrijd_count = ronde.plan.wedstrijden.count()
            if ronde.is_voor_import_oude_programma():
                context['rondes_import'].append(ronde)
            else:
                context['rondes'].append(ronde)
        # for

        if mag_wijzigen and len(context['rondes']) < 10:
            context['url_nieuwe_week'] = reverse('Competitie:regio-planning',
                                                 kwargs={'deelcomp_pk': deelcomp.pk})

        # zoek de bruikbare clusters
        clusters = (NhbCluster
                    .objects
                    .filter(regio=deelcomp.nhb_regio,
                            gebruik=deelcomp.competitie.afstand)
                    .prefetch_related('nhbvereniging_set', 'deelcompetitieronde_set')
                    .select_related('regio')
                    .order_by('letter'))
        context['clusters'] = list()
        for cluster in clusters:
            if cluster.nhbvereniging_set.count() > 0:
                context['clusters'].append(cluster)
                # tel het aantal rondes voor dit cluster
                cluster.ronde_count = cluster.deelcompetitieronde_set.count()
                cluster.url_bekijk = reverse('Competitie:regio-cluster-planning',
                                             kwargs={'cluster_pk': cluster.pk,
                                                     'deelcomp_pk': deelcomp.pk})
        # for
        if len(context['clusters']) > 0:
            context['show_clusters'] = True

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen geeft beveiliging
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie',
                                        'nhb_regio',
                                        'nhb_regio__rayon')
                        .get(pk=deelcomp_pk,
                             laag=LAAG_REGIO))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        context['deelcomp'] = deelcomp
        context['regio'] = deelcomp.nhb_regio

        mag_wijzigen = (self.rol_nu == Rollen.ROL_RCL and self.functie_nu.nhb_regio == deelcomp.nhb_regio)

        if deelcomp.inschrijf_methode == INSCHRIJF_METHODE_1:
            self._get_methode_1(context, deelcomp)
            context['inschrijfmethode'] = '1 (keuze sporter)'
        else:
            self._get_methode_2_3(context, deelcomp, mag_wijzigen)

            if deelcomp.inschrijf_methode == INSCHRIJF_METHODE_2:
                context['inschrijfmethode'] = '2 (wedstrijdklasse naar locatie)'
            else:
                context['inschrijfmethode'] = '3 (sporter voorkeur dagdeel)'

        if self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO):
            rayon = DeelCompetitie.objects.get(laag=LAAG_RK,
                                               competitie=deelcomp.competitie,
                                               nhb_rayon=deelcomp.nhb_regio.rayon)
            context['url_rayon'] = reverse('Competitie:rayon-planning',
                                           kwargs={'deelcomp_pk': rayon.pk})

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp.competitie.pk)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Regel toevoegen' gebruikt wordt
            in de regioplanning, om een nieuwe ronde toe te voegen.
        """
        # alleen de RCL mag de planning uitbreiden
        if self.rol_nu != Rollen.ROL_RCL:
            raise PermissionDenied()

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen geeft beveiliging
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_regio')
                        .get(pk=deelcomp_pk, laag=LAAG_REGIO, nhb_regio=self.functie_nu.nhb_regio))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        if deelcomp.inschrijf_methode == INSCHRIJF_METHODE_1:
            # inschrijfmethode 1 heeft maar 1 ronde en die wordt automatisch aangemaakt
            raise Http404('Verkeerde inschrijfmethode')

        ronde = maak_deelcompetitie_ronde(deelcomp=deelcomp)  # checkt ook maximum aantal toegestaan
        if ronde:
            # nieuwe ronde is aangemaakt
            next_url = reverse('Competitie:regio-ronde-planning', kwargs={'ronde_pk': ronde.pk})
        else:
            # er kan geen ronde meer bij
            # TODO: nette melding geven
            next_url = reverse('Competitie:regio-planning', kwargs={'deelcomp_pk': deelcomp.pk})

        return HttpResponseRedirect(next_url)


class RegioClusterPlanningView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de planning voor een competitie in een regio """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_PLANNING_REGIO_CLUSTER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            cluster_pk = int(kwargs['cluster_pk'][:6])  # afkappen geeft beveiliging
            cluster = (NhbCluster
                       .objects
                       .select_related('regio', 'regio__rayon')
                       .get(pk=cluster_pk))
        except (ValueError, NhbCluster.DoesNotExist):
            raise Http404('Cluster niet gevonden')

        context['cluster'] = cluster
        context['regio'] = cluster.regio

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])     # afkappen geeft beveiliging
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(pk=deelcomp_pk))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        context['deelcomp'] = deelcomp

        context['rondes'] = planning_sorteer_weeknummers(
                                DeelcompetitieRonde
                                .objects
                                .filter(deelcompetitie=deelcomp,
                                        cluster=cluster))

        for ronde in context['rondes']:
            ronde.wedstrijd_count = ronde.plan.wedstrijden.count()
        # for

        # alleen de RCL mag de planning uitbreiden
        if self.rol_nu == Rollen.ROL_RCL and len(context['rondes']) < 10:
            context['url_nieuwe_week'] = reverse('Competitie:regio-cluster-planning',
                                                 kwargs={'deelcomp_pk': deelcomp.pk,
                                                         'cluster_pk': cluster.pk})

        context['terug_url'] = reverse('Competitie:regio-planning',
                                       kwargs={'deelcomp_pk': deelcomp.pk})

        context['handleiding_planning_regio_url'] = reverse('Handleiding:Planning_Regio')

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp.competitie.pk)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Regel toevoegen' gebruikt wordt
        """

        # alleen de RCL mag de planning uitbreiden
        if self.rol_nu != Rollen.ROL_RCL:
            raise PermissionDenied()

        try:
            cluster_pk = int(kwargs['cluster_pk'][:6])  # afkappen geeft beveiliging
            cluster = (NhbCluster
                       .objects
                       .select_related('regio', 'regio__rayon')
                       .get(pk=cluster_pk))
        except (ValueError, NhbCluster.DoesNotExist):
            raise Http404('Cluster niet gevonden')

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])     # afkappen geeft beveiliging
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(pk=deelcomp_pk))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        ronde = maak_deelcompetitie_ronde(deelcomp=deelcomp, cluster=cluster)

        next_url = reverse('Competitie:regio-ronde-planning', kwargs={'ronde_pk': ronde.pk})

        return HttpResponseRedirect(next_url)


def competitie_week_nr_to_date(jaar, week_nr):
    # de competitie begin na de zomer
    # dus als het weeknummer voor de zomer valt, dan is het in het volgende jaar
    if week_nr <= 26:
        jaar += 1

    # conversie volgen ISO 8601
    # details: https://docs.python.org/3/library/datetime.html
    # %G = jaar
    # %V = met maandag als eerste dag van de week + week 1 bevat 4 januari
    # %u = dag van de week met 1=maandag
    when = datetime.datetime.strptime("%s-%s-1" % (jaar, week_nr), "%G-%V-%u")
    when2 = datetime.date(year=when.year, month=when.month, day=when.day)
    return when2


class RegioRondePlanningView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de planning van een ronde in een regio of cluster in de regio """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_PLANNING_REGIO_RONDE
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            ronde_pk = int(kwargs['ronde_pk'][:6])  # afkappen geeft beveiliging
            ronde = (DeelcompetitieRonde
                     .objects
                     .select_related('deelcompetitie__competitie',
                                     'deelcompetitie__nhb_regio__rayon',
                                     'cluster__regio')
                     .get(pk=ronde_pk))
        except (ValueError, DeelcompetitieRonde.DoesNotExist):
            raise Http404('Ronde niet gevonden')

        context['ronde'] = ronde
        context['vaste_beschrijving'] = is_import = ronde.is_voor_import_oude_programma()

        context['ronde_opslaan_url'] = reverse('Competitie:regio-ronde-planning',
                                               kwargs={'ronde_pk': ronde.pk})

        context['wedstrijden'] = (ronde.plan.wedstrijden
                                  .select_related('vereniging',
                                                  'locatie')
                                  .prefetch_related('indiv_klassen')
                                  .order_by('datum_wanneer',
                                            'tijd_begin_wedstrijd'))

        if self.rol_nu == Rollen.ROL_RCL and not is_import:
            context['url_nieuwe_wedstrijd'] = reverse('Competitie:regio-ronde-planning',
                                                      kwargs={'ronde_pk': ronde.pk})

            for wedstrijd in context['wedstrijden']:
                # TODO: vanaf welke datum dit niet meer aan laten passen?
                wedstrijd.url_wijzig = reverse('Competitie:regio-wijzig-wedstrijd',
                                               kwargs={'wedstrijd_pk': wedstrijd.pk})
            # for

            context['url_verwijderen'] = context['ronde_opslaan_url']
            context['heeft_wedstrijden'] = context['wedstrijden'].count() > 0

        start_week = settings.COMPETITIES_START_WEEK
        eind_week = settings.COMPETITIE_25M_LAATSTE_WEEK
        if ronde.deelcompetitie.competitie.afstand == '18':
            eind_week = settings.COMPETITIE_18M_LAATSTE_WEEK
        eind_week += 1  # de hele week mag nog gebruikt worden
        begin_jaar = ronde.deelcompetitie.competitie.begin_jaar

        last_week_in_year = 52
        when_wk53 = competitie_week_nr_to_date(begin_jaar, 53)
        when_wk1 = competitie_week_nr_to_date(begin_jaar, 1)
        if when_wk53 != when_wk1:
            # wk53 does exist
            last_week_in_year = 53

        context['opt_week_nrs'] = opt_week_nrs = list()

        while start_week != eind_week:
            when = competitie_week_nr_to_date(begin_jaar, start_week)
            obj = SimpleNamespace()
            obj.week_nr = start_week
            obj.choice_name = start_week
            obj.maandag = when
            obj.actief = (start_week == ronde.week_nr)
            opt_week_nrs.append(obj)

            if start_week >= last_week_in_year:
                start_week = 1
                # let op: begin_jaar niet aanpassen (dat doen competitie_week_nr_to_date)
            else:
                start_week += 1
        # while

        if ronde.cluster:
            terug_url = reverse('Competitie:regio-cluster-planning',
                                kwargs={'cluster_pk': ronde.cluster.pk,
                                        'deelcomp_pk': ronde.deelcompetitie.pk})
        else:
            terug_url = reverse('Competitie:regio-planning',
                                kwargs={'deelcomp_pk': ronde.deelcompetitie.pk})
        context['terug_url'] = terug_url

        context['heeft_wkl'] = heeft_wkl = (ronde.deelcompetitie.inschrijf_methode == INSCHRIJF_METHODE_2 and
                                            not ronde.is_voor_import_oude_programma())

        klasse2schutters = dict()
        niet_gebruikt = dict()
        if heeft_wkl:
            for obj in (RegioCompetitieSchutterBoog
                        .objects
                        .filter(deelcompetitie=ronde.deelcompetitie)
                        .select_related('klasse__indiv')):
                try:
                    klasse2schutters[obj.klasse.indiv.pk] += 1
                except KeyError:
                    klasse2schutters[obj.klasse.indiv.pk] = 1
            # for

            for wkl in (CompetitieKlasse
                        .objects
                        .select_related('indiv', 'team')
                        .filter(competitie=ronde.deelcompetitie.competitie)):
                if wkl.indiv:
                    niet_gebruikt[100000 + wkl.indiv.pk] = wkl.indiv.beschrijving
                if wkl.team:
                    niet_gebruikt[200000 + wkl.team.pk] = wkl.team.beschrijving
            # for

        for wedstrijd in context['wedstrijden']:
            wedstrijd.aantal_schutters = 0
            if heeft_wkl:
                for wkl in wedstrijd.indiv_klassen.order_by('volgorde'):
                    try:
                        wedstrijd.aantal_schutters += klasse2schutters[wkl.pk]
                    except KeyError:        # pragma: no cover
                        # geen schutters in deze klasse
                        pass

                    niet_gebruikt[100000 + wkl.pk] = None
                # for

                # FUTURE: team klassen toevoegen
        # for

        context['wkl_niet_gebruikt'] = [beschrijving for beschrijving in niet_gebruikt.values() if beschrijving]
        if len(context['wkl_niet_gebruikt']) == 0:
            del context['wkl_niet_gebruikt']

        if self.rol_nu != Rollen.ROL_RCL:
            context['readonly'] = True

        menu_dynamics_competitie(self.request, context, comp_pk=ronde.deelcompetitie.competitie.pk)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Wedstrijd toevoegen' gebruikt wordt
            en als op de knop Instellingen Opslaan wordt gedrukt voor de ronde parameters
        """

        try:
            ronde_pk = int(kwargs['ronde_pk'][:6])  # afkappen geeft beveiliging
            ronde = (DeelcompetitieRonde
                     .objects
                     .select_related('deelcompetitie__competitie')
                     .get(pk=ronde_pk))
        except (ValueError, DeelcompetitieRonde.DoesNotExist):
            raise Http404('Ronde niet gevonden')

        # alleen de RCL mag een wedstrijd toevoegen
        if self.rol_nu != Rollen.ROL_RCL:
            raise PermissionDenied()

        if request.POST.get('verwijder_ronde', None):
            # de ronde moet verwijderd worden
            # controleer nog een keer dat er geen wedstrijden aan hangen
            if ronde.plan.wedstrijden.count() > 0:
                raise Http404('Wedstrijden aanwezig')

            next_url = reverse('Competitie:regio-planning',
                               kwargs={'deelcomp_pk': ronde.deelcompetitie.pk})

            ronde.delete()

            return HttpResponseRedirect(next_url)

        week_nr = request.POST.get('ronde_week_nr', None)
        if week_nr:
            # het was de Opslaan knop
            try:
                week_nr = int(week_nr)
            except (TypeError, ValueError):
                raise Http404('Geen valide week nummer')

            # sanity-check op ronde nummer
            if week_nr < 1 or week_nr > 53:
                # geen valide week nummer
                raise Http404('Geen valide week nummer')

            eind_week = settings.COMPETITIE_25M_LAATSTE_WEEK
            if ronde.deelcompetitie.competitie.afstand == '18':
                eind_week = settings.COMPETITIE_18M_LAATSTE_WEEK

            if eind_week < settings.COMPETITIES_START_WEEK:
                # typisch voor 25m: week 11..37 mogen niet
                if eind_week < week_nr < settings.COMPETITIES_START_WEEK:
                    raise Http404('Geen valide week nummer')
            else:
                # typisch voor 18m: week 37..50 mogen, verder niet
                if week_nr > eind_week or week_nr < settings.COMPETITIES_START_WEEK:
                    raise Http404('Geen valide week nummer')

            beschrijving = request.POST.get('ronde_naam', '')

            if not ronde.is_voor_import_oude_programma():
                # is niet voor import, dus beschrijving mag aangepast worden
                oude_beschrijving = ronde.beschrijving
                ronde.beschrijving = beschrijving[:40]  # afkappen, anders werkt save niet
                if ronde.is_voor_import_oude_programma():
                    # poging tot beschrijving die niet mag / problemen gaat geven
                    # herstel de oude beschrijving
                    ronde.beschrijving = oude_beschrijving

            if ronde.week_nr != week_nr:
                # nieuw week nummer
                # reken uit hoeveel het verschil is
                jaar = ronde.deelcompetitie.competitie.begin_jaar
                when1 = competitie_week_nr_to_date(jaar, ronde.week_nr)
                when2 = competitie_week_nr_to_date(jaar, week_nr)

                diff = when2 - when1

                # pas de datum van alle wedstrijden met evenveel aan
                for wedstrijd in ronde.plan.wedstrijden.all():
                    wedstrijd.datum_wanneer += diff
                    wedstrijd.save()
                # for

                ronde.week_nr = week_nr

            ronde.save()

            # werk de beschrijvingen van alle wedstrijden bij
            comp_str = ronde.deelcompetitie.competitie.beschrijving
            for obj in ronde.plan.wedstrijden.all():
                new_str = "%s - %s" % (comp_str, ronde.beschrijving)
                if obj.beschrijving != new_str:
                    obj.beschrijving = new_str
                    obj.save()
            # for

            if ronde.cluster:
                next_url = reverse('Competitie:regio-cluster-planning',
                                   kwargs={'cluster_pk': ronde.cluster.pk,
                                           'deelcomp_pk': ronde.deelcompetitie.pk})
            else:
                next_url = reverse('Competitie:regio-planning',
                                   kwargs={'deelcomp_pk': ronde.deelcompetitie.pk})
        else:
            # voeg een wedstrijd toe

            # niet toestaan op import rondes
            if ronde.is_voor_import_oude_programma():
                raise PermissionDenied()

            jaar = ronde.deelcompetitie.competitie.begin_jaar
            wedstrijd = CompetitieWedstrijd()
            wedstrijd.datum_wanneer = competitie_week_nr_to_date(jaar, ronde.week_nr)
            wedstrijd.tijd_begin_aanmelden = datetime.time(hour=0, minute=0, second=0)
            wedstrijd.tijd_begin_wedstrijd = wedstrijd.tijd_begin_aanmelden
            wedstrijd.tijd_einde_wedstrijd = wedstrijd.tijd_begin_aanmelden
            wedstrijd.save()

            ronde.plan.wedstrijden.add(wedstrijd)

            # laat de nieuwe wedstrijd meteen wijzigen
            next_url = reverse('Competitie:regio-wijzig-wedstrijd',
                               kwargs={'wedstrijd_pk': wedstrijd.pk})

        return HttpResponseRedirect(next_url)


class RegioRondePlanningMethode1View(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de Methode 1 planning weer van een regio of cluster in de regio """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_PLANNING_REGIO_RONDE_METHODE1
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            ronde_pk = int(kwargs['ronde_pk'][:6])  # afkappen geeft beveiliging
            ronde = (DeelcompetitieRonde
                     .objects
                     .select_related('deelcompetitie__competitie',
                                     'deelcompetitie__nhb_regio__rayon',
                                     'cluster__regio')
                     .get(pk=ronde_pk))
        except (ValueError, DeelcompetitieRonde.DoesNotExist):
            raise Http404('Ronde niet gevonden')

        context['ronde'] = ronde

        wedstrijden = (ronde.plan.wedstrijden
                       .select_related('vereniging')
                       .order_by('datum_wanneer',
                                 'tijd_begin_wedstrijd'))
        context['wedstrijden'] = wedstrijden

        # er zijn minder wedstrijden dan deelnemers
        for wedstrijd in wedstrijden:
            wedstrijd.aantal_aanmeldingen = wedstrijd.regiocompetitieschutterboog_set.count()
        # for

        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rollen.ROL_RCL:
            context['url_nieuwe_wedstrijd'] = reverse('Competitie:regio-methode1-planning',
                                                      kwargs={'ronde_pk': ronde.pk})

            for wedstrijd in wedstrijden:
                # TODO: vanaf welke datum dit niet meer aan laten passen?
                wedstrijd.url_wijzig = reverse('Competitie:regio-wijzig-wedstrijd',
                                               kwargs={'wedstrijd_pk': wedstrijd.pk})
            # for

        terug_url = reverse('Competitie:regio-planning',
                            kwargs={'deelcomp_pk': ronde.deelcompetitie.pk})
        context['terug_url'] = terug_url

        if self.rol_nu != Rollen.ROL_RCL:
            context['readonly'] = True

        menu_dynamics_competitie(self.request, context, comp_pk=ronde.deelcompetitie.competitie.pk)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Wedstrijd toevoegen' gebruikt wordt
            en als op de knop Instellingen Opslaan wordt gedrukt voor de ronde parameters
        """

        try:
            ronde_pk = int(kwargs['ronde_pk'][:6])  # afkappen geeft beveiliging
            ronde = (DeelcompetitieRonde
                     .objects
                     .select_related('deelcompetitie__competitie')
                     .get(pk=ronde_pk))
        except (ValueError, DeelcompetitieRonde.DoesNotExist):
            raise Http404('Ronde niet gevonden')

        # alleen de RCL mag een wedstrijd toevoegen
        if self.rol_nu != Rollen.ROL_RCL:
            raise PermissionDenied()

        # voeg een wedstrijd toe
        jaar = ronde.deelcompetitie.competitie.begin_jaar
        wedstrijd = CompetitieWedstrijd()
        wedstrijd.datum_wanneer = competitie_week_nr_to_date(jaar, settings.COMPETITIES_START_WEEK)
        wedstrijd.tijd_begin_aanmelden = datetime.time(hour=0, minute=0, second=0)
        wedstrijd.tijd_begin_wedstrijd = wedstrijd.tijd_begin_aanmelden
        wedstrijd.tijd_einde_wedstrijd = wedstrijd.tijd_begin_aanmelden
        wedstrijd.save()

        ronde.plan.wedstrijden.add(wedstrijd)

        # laat de nieuwe wedstrijd meteen wijzigen
        next_url = reverse('Competitie:regio-wijzig-wedstrijd',
                           kwargs={'wedstrijd_pk': wedstrijd.pk})

        return HttpResponseRedirect(next_url)


class WijzigWedstrijdView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de planning van een wedstrijd aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_WIJZIG_WEDSTRIJD
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_RCL

    @staticmethod
    def _get_wedstrijdklassen(deelcomp, wedstrijd):
        klasse2schutters = dict()
        for obj in (RegioCompetitieSchutterBoog
                    .objects
                    .filter(deelcompetitie=deelcomp)
                    .select_related('klasse')):
            try:
                klasse2schutters[obj.klasse.indiv.pk] += 1
            except KeyError:
                klasse2schutters[obj.klasse.indiv.pk] = 1
        # for

        # wedstrijdklassen
        wedstrijd_indiv_pks = [obj.pk for obj in wedstrijd.indiv_klassen.all()]
        wkl_indiv = (CompetitieKlasse
                     .objects
                     .filter(competitie=deelcomp.competitie,
                             team=None)
                     .select_related('indiv__boogtype')
                     .order_by('indiv__volgorde')
                     .all())
        prev_boogtype = -1
        for obj in wkl_indiv:
            if prev_boogtype != obj.indiv.boogtype:
                prev_boogtype = obj.indiv.boogtype
                obj.break_before = True
            try:
                schutters = klasse2schutters[obj.indiv.pk]
            except KeyError:
                schutters = 0
            obj.short_str = obj.indiv.beschrijving
            obj.schutters = schutters
            obj.sel_str = "wkl_indiv_%s" % obj.indiv.pk
            obj.geselecteerd = (obj.indiv.pk in wedstrijd_indiv_pks)
        # for

        wedstrijd_team_pks = [obj.pk for obj in wedstrijd.team_klassen.all()]
        wkl_team = (CompetitieKlasse
                    .objects
                    .filter(competitie=deelcomp.competitie,
                            indiv=None)
                    .order_by('indiv__volgorde')
                    .all())
        for obj in wkl_team:
            obj.short_str = obj.team.beschrijving
            obj.sel_str = "wkl_team_%s" % obj.team.pk
            obj.geselecteerd = (obj.team.pk in wedstrijd_team_pks)
        # for

        return wkl_indiv, wkl_team

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])  # afkappen geeft beveiliging
            wedstrijd = (CompetitieWedstrijd
                         .objects
                         .select_related('uitslag')
                         .prefetch_related('uitslag__scores')
                         .get(pk=wedstrijd_pk))
        except (ValueError, CompetitieWedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        plan = wedstrijd.competitiewedstrijdenplan_set.all()[0]
        ronde = (DeelcompetitieRonde
                 .objects
                 .select_related('deelcompetitie',
                                 'deelcompetitie__competitie',
                                 'deelcompetitie__nhb_regio')
                 .get(plan=plan))

        if ronde.is_voor_import_oude_programma():
            raise PermissionDenied()

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        if ronde.deelcompetitie.functie != functie_nu:
            # mag niet wijzigen
            raise PermissionDenied()

        context['competitie'] = comp = ronde.deelcompetitie.competitie
        is_25m = (comp.afstand == '25')

        context['regio'] = ronde.deelcompetitie.nhb_regio
        context['ronde'] = ronde
        context['wedstrijd'] = wedstrijd

        if ronde.deelcompetitie.inschrijf_methode == INSCHRIJF_METHODE_1:
            jaar = ronde.deelcompetitie.competitie.begin_jaar
            week = settings.COMPETITIES_START_WEEK
            context['datum_eerste'] = competitie_week_nr_to_date(jaar, week)

            if ronde.deelcompetitie.competitie.afstand == '18':
                week = settings.COMPETITIE_18M_LAATSTE_WEEK + 1
            else:
                week = settings.COMPETITIE_25M_LAATSTE_WEEK + 1
            week += 1
            if week < settings.COMPETITIES_START_WEEK:
                jaar += 1
            context['datum_laatste'] = competitie_week_nr_to_date(jaar, week)  # TODO: moet 1 dag eerder?
        else:
            # laat een dag van de week kiezen

            # zoek het weeknummer waarin deze wedstrijd gehouden moet worden
            context['opt_weekdagen'] = opt_weekdagen = list()

            # bepaal de weekdag uit de huidige wedstrijd datum
            jaar = ronde.deelcompetitie.competitie.begin_jaar
            when = competitie_week_nr_to_date(jaar, ronde.week_nr)
            ronde.maandag = when

            verschil = wedstrijd.datum_wanneer - when
            dag_nr = verschil.days

            for weekdag_nr, weekdag_naam in WEEK_DAGEN:
                obj = SimpleNamespace()
                obj.weekdag_nr = weekdag_nr
                obj.weekdag_naam = weekdag_naam
                obj.datum = when
                obj.actief = (dag_nr == weekdag_nr)
                opt_weekdagen.append(obj)

                when += datetime.timedelta(days=1)
            # for

        wedstrijd.tijd_begin_wedstrijd_str = wedstrijd.tijd_begin_wedstrijd.strftime("%H:%M")
        # wedstrijd.tijd_begin_aanmelden_str = wedstrijd.tijd_begin_aanmelden.strftime("%H%M")
        # wedstrijd.tijd_einde_wedstrijd_str = wedstrijd.tijd_einde_wedstrijd.strftime("%H%M")

        if ronde.cluster:
            verenigingen = ronde.cluster.nhbvereniging_set.order_by('ver_nr')
        else:
            verenigingen = ronde.deelcompetitie.nhb_regio.nhbvereniging_set.order_by('ver_nr')
        context['verenigingen'] = verenigingen

        if not wedstrijd.vereniging and verenigingen.count() > 0:
            wedstrijd.vereniging = verenigingen[0]
            wedstrijd.save()

        if not wedstrijd.locatie and wedstrijd.vereniging:
            # alle binnen accommodaties hebben discipline_indoor=True
            # externe locaties met dezelfde discipline komen ook mee
            locaties = wedstrijd.vereniging.wedstrijdlocatie_set.filter(discipline_indoor=True)

            if is_25m:
                # neem ook externe locaties mee met discipline=25m1pijl
                locaties_25m1p = wedstrijd.vereniging.wedstrijdlocatie_set.filter(discipline_25m1pijl=True)
                locaties = locaties.union(locaties_25m1p)

            if locaties.count() > 0:
                wedstrijd.locatie = locaties[0]     # pak een default
                # maak een slimmere keuze
                for locatie in locaties:
                    if is_25m:
                        if locatie.banen_25m > 0:
                            wedstrijd.locatie = locatie
                    else:
                        if locatie.banen_18m > 0:
                            wedstrijd.locatie = locatie
                # for
                wedstrijd.save()
        del obj

        context['all_locaties'] = all_locs = list()
        pks = [ver.pk for ver in verenigingen]
        for ver in (NhbVereniging
                    .objects
                    .prefetch_related('wedstrijdlocatie_set')
                    .filter(pk__in=pks)):
            for loc in ver.wedstrijdlocatie_set.all():
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
                    keuze = loc.adres.replace('\n', ', ')
                    if loc.notities:
                        keuze += ' (%s)' % loc.notities
                    loc.keuze_str = keuze
            # for
        # for

        context['heeft_wkl'] = heeft_wkl = (ronde.deelcompetitie.inschrijf_methode == INSCHRIJF_METHODE_2)
        if heeft_wkl:
            context['wkl_indiv'], context['wkl_team'] = self._get_wedstrijdklassen(ronde.deelcompetitie, wedstrijd)

        context['url_opslaan'] = reverse('Competitie:regio-wijzig-wedstrijd', kwargs={'wedstrijd_pk': wedstrijd.pk})

        if ronde.deelcompetitie.inschrijf_methode == INSCHRIJF_METHODE_1:
            context['url_terug'] = reverse('Competitie:regio-methode1-planning',
                                           kwargs={'ronde_pk': ronde.pk})
        else:
            context['url_terug'] = reverse('Competitie:regio-ronde-planning',
                                           kwargs={'ronde_pk': ronde.pk})

        uitslag = wedstrijd.uitslag
        if uitslag and (uitslag.is_bevroren or uitslag.scores.count()):
            context['kan_niet_verwijderen'] = True
        else:
            context['url_verwijderen'] = reverse('Competitie:regio-verwijder-wedstrijd',
                                                 kwargs={'wedstrijd_pk': wedstrijd.pk})

        menu_dynamics_competitie(self.request, context, comp_pk=context['competitie'].pk)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Opslaan' gebruikt wordt
        """

        try:
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])  # afkappen geeft beveiliging
            wedstrijd = CompetitieWedstrijd.objects.get(pk=wedstrijd_pk)
        except (ValueError, CompetitieWedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        plan = wedstrijd.competitiewedstrijdenplan_set.all()[0]
        ronde = (DeelcompetitieRonde
                 .objects
                 .select_related('deelcompetitie',
                                 'deelcompetitie__competitie',
                                 'deelcompetitie__nhb_regio')
                 .get(plan=plan))

        if ronde.is_voor_import_oude_programma():
            raise PermissionDenied()

        deelcomp = ronde.deelcompetitie

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        if deelcomp.functie != functie_nu:
            # mag niet wijzigen
            raise PermissionDenied()

        nhbver_pk = request.POST.get('nhbver_pk', '')[:6]       # afkappen voor de veiligheid
        loc_pk = request.POST.get('loc_pk', '')[:6]             # afkappen voor de veiligheid
        aanvang = request.POST.get('aanvang', '')[:5]           # afkappen voor de veiligheid

        if nhbver_pk == "" or len(aanvang) != 5 or aanvang[2] != ':':
            raise Http404('Geen valide verzoek')

        try:
            nhbver = NhbVereniging.objects.get(pk=nhbver_pk)
        except (NhbVereniging.DoesNotExist, ValueError):
            raise Http404('Vereniging niet gevonden')

        if loc_pk:
            try:
                loc = nhbver.wedstrijdlocatie_set.get(pk=loc_pk)
            except WedstrijdLocatie.DoesNotExist:
                raise Http404('Geen valide verzoek')
        else:
            # formulier stuurt niets als er niet gekozen hoeft te worden
            loc = None
            locs = nhbver.wedstrijdlocatie_set.all()
            if locs.count() == 1:
                loc = locs[0]       # de enige keuze

        try:
            aanvang = int(aanvang[0:0+2] + aanvang[3:3+2])
        except (TypeError, ValueError):
            raise Http404('Geen valide verzoek')

        # vertaal aanvang naar een tijd
        uur = aanvang // 100
        minuut = aanvang - (uur * 100)
        if uur < 0 or uur > 23 or minuut < 0 or minuut > 59:
            raise Http404('Geen valide tijdstip')

        if deelcomp.inschrijf_methode == INSCHRIJF_METHODE_1:
            wanneer = request.POST.get('wanneer', None)
            if not wanneer:
                raise Http404('Verzoek is niet compleet')

            try:
                datum_p = datetime.datetime.strptime(wanneer, '%Y-%m-%d')
            except ValueError:
                raise Http404('Geen valide datum')

            when = datum_p.date()
        else:
            # weekdag is een cijfer van 0 tm 6
            # aanvang bestaat uit vier cijfers, zoals 0830
            weekdag = request.POST.get('weekdag', '')[:1]     # afkappen = veiligheid
            if weekdag == "":
                raise Http404('Geen valide weekdag')

            try:
                weekdag = int(weekdag)
            except (TypeError, ValueError):
                raise Http404('Geen valide weekdag')

            if weekdag < 0 or weekdag > 6:
                raise Http404('Geen valide weekdag')

            # bepaal de begin datum van de ronde-week
            jaar = ronde.deelcompetitie.competitie.begin_jaar
            when = competitie_week_nr_to_date(jaar, ronde.week_nr)
            # voeg nu de offset toe uit de weekdag
            when += datetime.timedelta(days=weekdag)

        wedstrijd.datum_wanneer = when
        wedstrijd.tijd_begin_wedstrijd = datetime.time(hour=uur, minute=minuut)
        wedstrijd.vereniging = nhbver
        wedstrijd.locatie = loc
        wedstrijd.save()

        wkl_indiv, wkl_team = self._get_wedstrijdklassen(ronde.deelcompetitie, wedstrijd)
        indiv_pks = [wkl.indiv.pk for wkl in wkl_indiv]

        gekozen_klassen = list()
        for key, value in request.POST.items():
            if key[:10] == "wkl_indiv_":
                try:
                    pk = int(key[10:10+6])
                except (IndexError, TypeError, ValueError):
                    raise Http404('Geen valide klasse')
                else:
                    if pk not in indiv_pks:
                        # unsupported number
                        raise Http404('Geen valide klasse')
                    gekozen_klassen.append(pk)
        # for

        for obj in wedstrijd.indiv_klassen.all():
            if obj.pk in gekozen_klassen:
                # was al gekozen
                gekozen_klassen.remove(obj.pk)
            else:
                # moet uitgezet worden
                wedstrijd.indiv_klassen.remove(obj)
        # for

        # alle nieuwe klassen toevoegen
        if len(gekozen_klassen):
            wedstrijd.indiv_klassen.add(*gekozen_klassen)

        if deelcomp.inschrijf_methode == INSCHRIJF_METHODE_1:
            url = reverse('Competitie:regio-methode1-planning',
                          kwargs={'ronde_pk': ronde.pk})
        else:
            url = reverse('Competitie:regio-ronde-planning',
                          kwargs={'ronde_pk': ronde.pk})

        return HttpResponseRedirect(url)


class VerwijderWedstrijdView(UserPassesTestMixin, View):

    """ Deze view laat een Regio wedstrijd verwijderen """

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_RCL

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Verwijder' gebruikt wordt
        """
        try:
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])  # afkappen geeft beveiliging
            wedstrijd = (CompetitieWedstrijd
                         .objects
                         .select_related('uitslag')
                         .prefetch_related('uitslag__scores')
                         .get(pk=wedstrijd_pk))
        except (ValueError, CompetitieWedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        plan = wedstrijd.competitiewedstrijdenplan_set.all()[0]
        try:
            ronde = DeelcompetitieRonde.objects.get(plan=plan,
                                                    deelcompetitie__laag=LAAG_REGIO)
        except DeelcompetitieRonde.DoesNotExist:
            raise Http404('Ronde niet gevonden')

        deelcomp = ronde.deelcompetitie

        # correcte beheerder?
        if deelcomp.functie != self.functie_nu:
            raise PermissionDenied()

        # voorkom verwijderen van wedstrijden waar een uitslag aan hangt
        if wedstrijd.uitslag:
            uitslag = wedstrijd.uitslag
            if uitslag and (uitslag.is_bevroren or uitslag.scores.count() > 0):
                raise Http404('Uitslag mag niet meer gewijzigd worden')

        wedstrijd.delete()

        if deelcomp.inschrijf_methode == INSCHRIJF_METHODE_1:
            url = reverse('Competitie:regio-methode1-planning',
                          kwargs={'ronde_pk': ronde.pk})
        else:
            url = reverse('Competitie:regio-ronde-planning',
                          kwargs={'ronde_pk': ronde.pk})

        return HttpResponseRedirect(url)


class AfsluitenRegiocompView(UserPassesTestMixin, TemplateView):

    """ Deze view kan de RCL een regiocompetitie afsluiten """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_AFSLUITEN_REGIOCOMP
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

        if not deelcomp.is_afgesloten:
            deelcomp.competitie.bepaal_fase()
            if deelcomp.competitie.fase == 'F':
                context['url_afsluiten'] = reverse('Competitie:afsluiten-regiocomp',
                                                   kwargs={'deelcomp_pk': deelcomp.pk})

        context['url_terug'] = reverse('Competitie:overzicht',
                                       kwargs={'comp_pk': deelcomp.competitie.pk})

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp.competitie.pk)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Afsluiten' gebruikt wordt door de RCL """

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen geeft beveiliging
            deelcomp = DeelCompetitie.objects.get(pk=deelcomp_pk,
                                                  laag=LAAG_REGIO)
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        if deelcomp.functie != self.functie_nu:
            # niet de beheerder
            raise PermissionDenied()

        if not deelcomp.is_afgesloten:

            deelcomp.competitie.bepaal_fase()
            if deelcomp.competitie.fase != 'F':
                # nog niet mogelijk om af te sluiten
                raise Http404('Verkeerde competitie fase')

            deelcomp.is_afgesloten = True
            deelcomp.save()

            # maak het bericht voor een taak aan de RKO's en BKO's
            account = request.user
            ter_info_namen = list()
            now = timezone.now()
            taak_deadline = now
            assert isinstance(account, Account)
            taak_tekst = "Ter info: De regiocompetitie %s is zojuist afgesloten door RCL %s" % (
                            str(deelcomp), account.volledige_naam())
            taak_tekst += "\nAls RKO kan je onder Competitie, Planning Rayon de status van elke regio zien."
            taak_log = "[%s] Taak aangemaakt" % now

            # stuur elke RKO een taak ('ter info')
            deelcomp_rk = DeelCompetitie.objects.get(competitie=deelcomp.competitie,
                                                     laag=LAAG_RK,
                                                     nhb_rayon=deelcomp.nhb_regio.rayon)
            functie_rko = deelcomp_rk.functie
            for account in functie_rko.accounts.all():
                # maak een taak aan voor deze RKO
                maak_taak(toegekend_aan=account,
                          deadline=taak_deadline,
                          aangemaakt_door=request.user,
                          beschrijving=taak_tekst,
                          handleiding_pagina="",
                          log=taak_log,
                          deelcompetitie=deelcomp_rk)
                ter_info_namen.append(account.volledige_naam())
            # for

            # stuur elke BKO een taak ('ter info')
            deelcomp_bk = DeelCompetitie.objects.get(is_afgesloten=False,
                                                     competitie=deelcomp.competitie,
                                                     laag=LAAG_BK)
            functie_bko = deelcomp_bk.functie
            for account in functie_bko.accounts.all():
                # maak een taak aan voor deze BKO
                maak_taak(toegekend_aan=account,
                          deadline=taak_deadline,
                          aangemaakt_door=request.user,
                          beschrijving=taak_tekst,
                          handleiding_pagina="",
                          log=taak_log,
                          deelcompetitie=deelcomp_bk)
                ter_info_namen.append(account.volledige_naam())
            # for

            # schrijf in het logboek
            msg = "Deelcompetitie '%s' is afgesloten" % str(deelcomp)
            msg += '\nDe volgende beheerders zijn geïnformeerd via een taak: %s' % ", ".join(ter_info_namen)
            schrijf_in_logboek(request.user, "Competitie", msg)

        url = reverse('Competitie:kies')
        return HttpResponseRedirect(url)


# end of file
