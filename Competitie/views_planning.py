# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import Resolver404, reverse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige
from NhbStructuur.models import NhbCluster, NhbVereniging
from Wedstrijden.models import Wedstrijd, WedstrijdenPlan, WedstrijdLocatie
from .models import (LAAG_REGIO, LAAG_RK, LAAG_BK,
                     DeelCompetitie, DeelcompetitieRonde, maak_deelcompetitie_ronde)
from types import SimpleNamespace
import datetime


TEMPLATE_COMPETITIE_PLANNING_REGIO_RONDE = 'competitie/planning-regio-ronde.dtl'
TEMPLATE_COMPETITIE_PLANNING_REGIO_CLUSTER = 'competitie/planning-regio-cluster.dtl'
TEMPLATE_COMPETITIE_PLANNING_REGIO = 'competitie/planning-regio.dtl'
TEMPLATE_COMPETITIE_PLANNING_RAYON = 'competitie/planning-rayon.dtl'
TEMPLATE_COMPETITIE_PLANNING_BOND = 'competitie/planning-landelijk.dtl'
TEMPLATE_COMPETITIE_WIJZIG_WEDSTRIJD = 'competitie/wijzig-wedstrijd.dtl'


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


class BondPlanningView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de planning voor een competitie op het landelijke niveau """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_PLANNING_BOND

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen geeft beveiliging
            deelcomp_bk = (DeelCompetitie
                           .objects
                           .select_related('competitie')
                           .get(pk=deelcomp_pk))
        except (KeyError, DeelCompetitie.DoesNotExist):
            raise Resolver404()

        if deelcomp_bk.laag != LAAG_BK:
            raise Resolver404()

        context['deelcomp_bk'] = deelcomp_bk

        context['rayon_deelcomps'] = (DeelCompetitie
                                      .objects
                                      .filter(laag=LAAG_RK,
                                              competitie=deelcomp_bk.competitie)
                                      .order_by('nhb_rayon__rayon_nr'))

        menu_dynamics(self.request, context, actief='competitie')
        return context


class RayonPlanningView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de planning voor een competitie in een rayon """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_PLANNING_RAYON

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        deelcomp_pk = kwargs['deelcomp_pk'][:6]     # afkappen geeft beveiliging
        try:
            deelcomp_rk = (DeelCompetitie
                           .objects
                           .select_related('competitie', 'nhb_rayon')
                           .get(pk=deelcomp_pk))
        except DeelCompetitie.DoesNotExist:
            raise Resolver404()

        if deelcomp_rk.laag != LAAG_RK:
            raise Resolver404()

        rol_nu = rol_get_huidige(self.request)

        context['deelcomp_rk'] = deelcomp_rk
        context['rayon'] = deelcomp_rk.nhb_rayon

        if rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO):
            deelcomp_bk = DeelCompetitie.objects.get(laag=LAAG_BK,
                                                     competitie=deelcomp_rk.competitie)
            context['url_bond'] = reverse('Competitie:bond-planning',
                                          kwargs={'deelcomp_pk': deelcomp_bk.pk})

        deelcomps = (DeelCompetitie
                     .objects
                     .filter(laag=LAAG_REGIO,
                             competitie=deelcomp_rk.competitie,
                             nhb_regio__rayon=deelcomp_rk.nhb_rayon)
                     .order_by('nhb_regio__regio_nr'))
        context['regio_deelcomps'] = deelcomps

        # zoek het aantal wedstrijden erbij
        for deelcomp in deelcomps:
            plan_pks = (DeelcompetitieRonde
                        .objects
                        .filter(deelcompetitie=deelcomp)
                        .values_list('plan__pk', flat=True))
            deelcomp.rondes_count = len(plan_pks)
            deelcomp.wedstrijden_count = 0
            for plan in (WedstrijdenPlan
                         .objects
                         .filter(pk__in=plan_pks)
                         .prefetch_related('wedstrijden')):
                deelcomp.wedstrijden_count += plan.wedstrijden.count()
            # for
        # for

        menu_dynamics(self.request, context, actief='competitie')
        return context


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
    template_name = TEMPLATE_COMPETITIE_PLANNING_REGIO

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen geeft beveiliging
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_regio', 'nhb_regio__rayon')
                        .get(pk=deelcomp_pk, laag=LAAG_REGIO))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Resolver404()

        context['deelcomp'] = deelcomp
        context['regio'] = deelcomp.nhb_regio

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

        # alleen de RCL mag de planning uitbreiden
        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rollen.ROL_RCL and len(context['rondes']) < 10:
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
        # for
        if len(context['clusters']) > 0:
            context['show_clusters'] = True

        if rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO):
            rayon = DeelCompetitie.objects.get(laag=LAAG_RK,
                                               competitie=deelcomp.competitie,
                                               nhb_rayon=deelcomp.nhb_regio.rayon)
            context['url_rayon'] = reverse('Competitie:rayon-planning',
                                           kwargs={'deelcomp_pk': rayon.pk})

        context['handleiding_planning_regio_url'] = reverse('Handleiding:Planning_Regio')

        menu_dynamics(self.request, context, actief='competitie')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Regel toevoegen' gebruikt wordt
            in de regioplanning, om een nieuwe ronde toe te voegen.
        """
        # alleen de RCL mag de planning uitbreiden
        rol_nu = rol_get_huidige(self.request)
        if rol_nu != Rollen.ROL_RCL:
            raise Resolver404()

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen geeft beveiliging
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_regio')
                        .get(pk=deelcomp_pk, laag=LAAG_REGIO, nhb_regio=functie_nu.nhb_regio))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Resolver404()

        if deelcomp.laag != LAAG_REGIO:
            raise Resolver404()

        ronde = maak_deelcompetitie_ronde(deelcomp=deelcomp)
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

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

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
            raise Resolver404()

        context['cluster'] = cluster
        context['regio'] = cluster.regio

        try:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(laag=LAAG_REGIO,
                             nhb_regio=cluster.regio,
                             competitie__afstand=cluster.gebruik))
        except DeelCompetitie.DoesNotExist:
            raise Resolver404()

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
        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rollen.ROL_RCL and len(context['rondes']) < 10:
            context['url_nieuwe_week'] = reverse('Competitie:regio-cluster-planning',
                                                 kwargs={'cluster_pk': cluster.pk})

        context['terug_url'] = reverse('Competitie:regio-planning',
                                       kwargs={'deelcomp_pk': deelcomp.pk})

        context['handleiding_planning_regio_url'] = reverse('Handleiding:Planning_Regio')

        menu_dynamics(self.request, context, actief='competitie')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Regel toevoegen' gebruikt wordt
        """

        # alleen de RCL mag de planning uitbreiden
        rol_nu = rol_get_huidige(self.request)
        if rol_nu != Rollen.ROL_RCL:
            raise Resolver404()

        try:
            cluster_pk = int(kwargs['cluster_pk'][:6])  # afkappen geeft beveiliging
            cluster = (NhbCluster
                       .objects
                       .select_related('regio', 'regio__rayon')
                       .get(pk=cluster_pk))
        except (ValueError, NhbCluster.DoesNotExist):
            raise Resolver404()

        try:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(laag=LAAG_REGIO,
                             nhb_regio=cluster.regio,
                             competitie__afstand=cluster.gebruik))
        except DeelCompetitie.DoesNotExist:
            raise Resolver404()

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

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

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
            raise Resolver404()

        context['ronde'] = ronde
        context['vaste_beschrijving'] = is_import = ronde.is_voor_import_oude_programma()

        context['wedstrijden'] = (ronde.plan.wedstrijden
                                  .order_by('datum_wanneer', 'tijd_begin_wedstrijd')
                                  .select_related('vereniging'))

        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rollen.ROL_RCL and not is_import:
            context['url_nieuwe_wedstrijd'] = reverse('Competitie:regio-ronde-planning',
                                                      kwargs={'ronde_pk': ronde.pk})

            for wedstrijd in context['wedstrijden']:
                # TODO: vanaf welke datum dit niet meer aan laten passen?
                wedstrijd.url_wijzig = reverse('Competitie:wijzig-wedstrijd',
                                               kwargs={'wedstrijd_pk': wedstrijd.pk})
            # for

        start_week = 37
        eind_week = 11+1
        if ronde.deelcompetitie.competitie.afstand == '18':
            eind_week = 50+1
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
                                kwargs={'cluster_pk': ronde.cluster.pk})
        else:
            terug_url = reverse('Competitie:regio-planning',
                                kwargs={'deelcomp_pk': ronde.deelcompetitie.pk})
        context['terug_url'] = terug_url

        context['ronde_opslaan_url'] = reverse('Competitie:regio-ronde-planning',
                                               kwargs={'ronde_pk': ronde.pk})

        # uitslagen invoeren
        if rol_nu == Rollen.ROL_RCL:
            context['mag_uitslag_invoeren'] = True

        for wedstrijd in context['wedstrijden']:
            heeft_uitslag = (wedstrijd.uitslag and wedstrijd.uitslag.scores.count() > 0)
            if heeft_uitslag:
                wedstrijd.url_uitslag_bekijken = reverse('Competitie:wedstrijd-bekijk-uitslag',
                                                         kwargs={'wedstrijd_pk': wedstrijd.pk})

            # geef RCL de mogelijkheid om te scores aan te passen
            # de HWL/WL krijgen deze link vanuit Vereniging::Wedstrijden
            if rol_nu == Rollen.ROL_RCL and not is_import:
                if heeft_uitslag:
                    wedstrijd.url_uitslag_controleren = reverse('Competitie:wedstrijd-uitslag-controleren',
                                                                kwargs={'wedstrijd_pk': wedstrijd.pk})
                else:
                    # TODO: knop pas beschikbaar maken op wedstrijddatum tot datum+N
                    wedstrijd.url_uitslag_invoeren = reverse('Competitie:wedstrijd-uitslag-invoeren',
                                                             kwargs={'wedstrijd_pk': wedstrijd.pk})
        # for

        rol_nu = rol_get_huidige(self.request)
        if rol_nu != Rollen.ROL_RCL:
            context['readonly'] = True

        menu_dynamics(self.request, context, actief='competitie')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Regel toevoegen' gebruikt wordt
            en als op de knop Instellingen Opslaan wordt gedrukt voor de ronde parameters
        """

        try:
            ronde_pk = int(kwargs['ronde_pk'][:6])  # afkappen geeft beveiliging
            ronde = (DeelcompetitieRonde
                     .objects
                     .select_related('deelcompetitie__competitie')
                     .get(pk=ronde_pk))
        except (ValueError, DeelcompetitieRonde.DoesNotExist):
            raise Resolver404()

        # alleen de RCL mag een wedstrijd toevoegen
        rol_nu = rol_get_huidige(self.request)
        if rol_nu != Rollen.ROL_RCL:
            raise Resolver404()

        # print("RegioRondePlanningView::post kwargs=%s, items=%s" % (repr(kwargs), repr([(key, value) for key,value in request.POST.items()])))

        week_nr = request.POST.get('ronde_week_nr', None)
        if week_nr:
            # het was de Opslaan knop
            try:
                week_nr = int(week_nr)
            except (TypeError, ValueError):
                raise Resolver404()

            # sanity-check op ronde nummer
            if week_nr < 1 or week_nr > 53 or (11 < week_nr < 37):
                # geen valide week nummer
                raise Resolver404()

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
                                   kwargs={'cluster_pk': ronde.cluster.pk})
            else:
                next_url = reverse('Competitie:regio-planning',
                                   kwargs={'deelcomp_pk': ronde.deelcompetitie.pk})
        else:
            # voeg een wedstrijd toe

            # niet toestaan op import rondes
            if ronde.is_voor_import_oude_programma():
                raise Resolver404()

            jaar = ronde.deelcompetitie.competitie.begin_jaar
            wedstrijd = Wedstrijd()
            wedstrijd.datum_wanneer = competitie_week_nr_to_date(jaar, ronde.week_nr)
            wedstrijd.tijd_begin_aanmelden = datetime.time(hour=0, minute=0, second=0)
            wedstrijd.tijd_begin_wedstrijd = wedstrijd.tijd_begin_aanmelden
            wedstrijd.tijd_einde_wedstrijd = wedstrijd.tijd_begin_aanmelden
            wedstrijd.save()

            ronde.plan.wedstrijden.add(wedstrijd)

            # laat de nieuwe wedstrijd meteen wijzigen
            next_url = reverse('Competitie:wijzig-wedstrijd', kwargs={'wedstrijd_pk': wedstrijd.pk})

        return HttpResponseRedirect(next_url)


def plan_wedstrijd_rechten(request, wedstrijd):
    """ Retourneert:
            mag_wijzigen, mag_verwijderen
    """
    rol_nu = rol_get_huidige(request)
    if rol_nu in (Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL):
        # TODO: error handling
        plan = wedstrijd.wedstrijdenplan_set.all()[0]
        ronde = DeelcompetitieRonde.objects.get(plan=plan)
        laag = ronde.deelcompetitie.laag

        if rol_nu == Rollen.ROL_BKO and laag == LAAG_BK:
            return True, True

        if rol_nu == Rollen.ROL_RKO and laag == LAAG_RK:
            return True, True

        if rol_nu == Rollen.ROL_RCL and laag == LAAG_REGIO:
            return True, True

    return False, False


class WijzigWedstrijdView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de planning van een wedstrijd aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_WIJZIG_WEDSTRIJD

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])  # afkappen geeft beveiliging
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('uitslag')
                         .prefetch_related('uitslag__scores')
                         .get(pk=wedstrijd_pk))
        except (ValueError, Wedstrijd.DoesNotExist):
            raise Resolver404()

        mag_wijzigen, mag_verwijderen = plan_wedstrijd_rechten(self.request, wedstrijd)
        if not mag_wijzigen:
            raise Resolver404()

        # zoek het weeknummer waarin deze wedstrijd gehouden moet worden
        plan = wedstrijd.wedstrijdenplan_set.all()[0]
        ronde = DeelcompetitieRonde.objects.get(plan=plan)

        context['wedstrijd'] = wedstrijd
        context['ronde'] = ronde

        if ronde.is_voor_import_oude_programma():
            raise Resolver404()

        context['regio'] = ronde.deelcompetitie.nhb_regio
        context['competitie'] = competitie = ronde.deelcompetitie.competitie

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
            verenigingen = ronde.cluster.nhbvereniging_set.all()
        else:
            verenigingen = ronde.deelcompetitie.nhb_regio.nhbvereniging_set.all()
        context['verenigingen'] = verenigingen

        if not wedstrijd.vereniging and verenigingen.count() > 0:
            wedstrijd.vereniging = verenigingen[0]
            wedstrijd.save()

        if not wedstrijd.locatie and wedstrijd.vereniging:
            locaties = wedstrijd.vereniging.wedstrijdlocatie_set.all()
            if locaties.count() > 0:
                wedstrijd.locatie = locaties[0]
                wedstrijd.save()

        context['locaties'] = locaties = dict()
        pks = [ver.pk for ver in verenigingen]
        for obj in WedstrijdLocatie.objects.filter(verenigingen__pk__in=pks):
            for ver in obj.verenigingen.all():
                locaties[str(ver.pk)] = obj.adres   # nhb_nr --> adres
            # for
        # for

        context['url_terug'] = reverse('Competitie:regio-ronde-planning', kwargs={'ronde_pk': ronde.pk})
        context['url_opslaan'] = reverse('Competitie:wijzig-wedstrijd', kwargs={'wedstrijd_pk': wedstrijd.pk})

        if mag_verwijderen:     # pragma: no branch
            uitslag = wedstrijd.uitslag
            if uitslag and (uitslag.is_bevroren or uitslag.scores.count()):
                context['kan_niet_verwijderen'] = True
            else:
                context['url_verwijderen'] = reverse('Competitie:verwijder-wedstrijd',
                                                     kwargs={'wedstrijd_pk': wedstrijd.pk})

        menu_dynamics(self.request, context, actief='competitie')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Opslaan' gebruikt wordt
        """

        try:
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])  # afkappen geeft beveiliging
            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd_pk)
        except (ValueError, Wedstrijd.DoesNotExist):
            raise Resolver404()

        plan = wedstrijd.wedstrijdenplan_set.all()[0]
        ronde = DeelcompetitieRonde.objects.get(plan=plan)
        jaar = ronde.deelcompetitie.competitie.begin_jaar

        mag_wijzigen, _ = plan_wedstrijd_rechten(request, wedstrijd)
        if not mag_wijzigen:
            raise Resolver404()

        # weekdag is een cijfer van 0 tm 6
        # aanvang bestaat uit vier cijfers, zoals 0830
        weekdag = request.POST.get('weekdag', '')[:1]     # afkappen = veiligheid
        aanvang = request.POST.get('aanvang', '')[:5]
        nhbver_pk = request.POST.get('nhbver_pk', '')[:6]
        if weekdag == "" or nhbver_pk == "" or len(aanvang) != 5 or aanvang[2] != ':':
            raise Resolver404()

        try:
            weekdag = int(weekdag)
            aanvang = int(aanvang[0:0+2] + aanvang[3:3+2])
        except (TypeError, ValueError):
            raise Resolver404()

        if weekdag < 0 or weekdag > 6 or aanvang < 0 or aanvang > 2359:
            raise Resolver404()

        # bepaal de begin datum van de ronde-week
        when = competitie_week_nr_to_date(jaar, ronde.week_nr)
        # voeg nu de offset toe uit de weekdag
        when += datetime.timedelta(days=weekdag)

        # vertaal aanvang naar een tijd
        uur = aanvang // 100
        minuut = aanvang - (uur * 100)
        if uur < 0 or uur > 23 or minuut < 0 or minuut > 59:
            raise Resolver404()

        try:
            nhbver = NhbVereniging.objects.get(pk=nhbver_pk)
        except NhbVereniging.DoesNotExist:
            raise Resolver404()

        wedstrijd.datum_wanneer = when
        wedstrijd.tijd_begin_wedstrijd = datetime.time(hour=uur, minute=minuut)
        wedstrijd.vereniging = nhbver

        locaties = nhbver.wedstrijdlocatie_set.all()
        if locaties.count() > 0:
            wedstrijd.locatie = locaties[0]
        else:
            wedstrijd.locatie = None
        wedstrijd.save()

        url = reverse('Competitie:regio-ronde-planning', kwargs={'ronde_pk': ronde.pk})
        return HttpResponseRedirect(url)


class VerwijderWedstrijdView(UserPassesTestMixin, View):

    """ Deze view laat een wedstrijd verwijderen """

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Opslaan' gebruikt wordt
        """
        try:
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])  # afkappen geeft beveiliging
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('uitslag')
                         .prefetch_related('uitslag__scores')
                         .get(pk=wedstrijd_pk))
        except (ValueError, Wedstrijd.DoesNotExist):
            raise Resolver404()

        _, mag_verwijderen = plan_wedstrijd_rechten(request, wedstrijd)

        if mag_verwijderen:
            uitslag = wedstrijd.uitslag
            if uitslag and (uitslag.is_bevroren or uitslag.scores.count()):
                mag_verwijderen = False

        if not mag_verwijderen:
            raise Resolver404()

        plan = wedstrijd.wedstrijdenplan_set.all()[0]
        ronde = DeelcompetitieRonde.objects.get(plan=plan)
        url = reverse('Competitie:regio-ronde-planning', kwargs={'ronde_pk': ronde.pk})

        wedstrijd.delete()

        return HttpResponseRedirect(url)

# end of file
