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
from Wedstrijden.models import Wedstrijd
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
WEEK_DAGEN = ( (0, 'Maandag'),
               (1, 'Dinsdag'),
               (2, 'Woensdag'),
               (3, 'Donderdag'),
               (4, 'Vrijdag'),
               (5, 'Zaterdag'),
               (6, 'Zondag'))


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

        deelcomp_pk = kwargs['deelcomp_pk'][:6]     # afkappen geeft beveiliging
        try:
            deelcomp_bk = (DeelCompetitie
                           .objects
                           .select_related('competitie')
                           .get(pk=deelcomp_pk))
        except DeelCompetitie.DoesNotExist:
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

        if rol_nu == Rollen.ROL_BKO:
            deelcomp_bk = DeelCompetitie.objects.get(laag=LAAG_BK,
                                                     competitie=deelcomp_rk.competitie)
            context['url_bond'] = reverse('Competitie:bond-planning', kwargs={'deelcomp_pk': deelcomp_bk.pk})

        context['regio_deelcomps'] = (DeelCompetitie
                                      .objects
                                      .filter(laag=LAAG_REGIO,
                                              competitie=deelcomp_rk.competitie,
                                              nhb_regio__rayon=deelcomp_rk.nhb_rayon)
                                      .order_by('nhb_regio__regio_nr'))

        menu_dynamics(self.request, context, actief='competitie')
        return context


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

        deelcomp_pk = kwargs['deelcomp_pk'][:6]     # afkappen geeft beveiliging
        try:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_regio', 'nhb_regio__rayon')
                        .get(pk=deelcomp_pk))
        except DeelCompetitie.DoesNotExist:
            raise Resolver404()

        if deelcomp.laag != LAAG_REGIO:
            raise Resolver404()

        context['deelcomp'] = deelcomp
        context['regio'] = deelcomp.nhb_regio

        context['rondes'] = (DeelcompetitieRonde
                             .objects
                             .filter(deelcompetitie=deelcomp, cluster=None)
                             .order_by('week_nr'))

        for ronde in context['rondes']:
            ronde.wedstrijd_count = ronde.plan.wedstrijden.count()
        # for

        # alleen de RCL mag de planning uitbreiden
        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rollen.ROL_RCL and context['rondes'].count() < 10:
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

        menu_dynamics(self.request, context, actief='competitie')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Regel toevoegen' gebruikt wordt
        """

        # alleen de RCL mag de planning uitbreiden
        rol_nu = rol_get_huidige(self.request)
        if rol_nu != Rollen.ROL_RCL:
            raise Resolver404()

        deelcomp_pk = kwargs['deelcomp_pk'][:6]     # afkappen geeft beveiliging
        try:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_regio')
                        .get(pk=deelcomp_pk))
        except DeelCompetitie.DoesNotExist:
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

        cluster_pk = kwargs['cluster_pk'][:6]     # afkappen geeft beveiliging
        try:
            cluster = (NhbCluster
                       .objects
                       .select_related('regio', 'regio__rayon')
                       .get(pk=cluster_pk))
        except NhbCluster.DoesNotExist:
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

        context['rondes'] = (DeelcompetitieRonde
                             .objects
                             .filter(deelcompetitie=deelcomp,
                                     cluster=cluster)
                             .order_by('week_nr'))

        for ronde in context['rondes']:
            ronde.wedstrijd_count = ronde.plan.wedstrijden.count()
        # for

        # alleen de RCL mag de planning uitbreiden
        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rollen.ROL_RCL and context['rondes'].count() < 10:
            context['url_nieuwe_week'] = reverse('Competitie:regio-cluster-planning',
                                                 kwargs={'cluster_pk': cluster.pk})

        context['terug_url'] = reverse('Competitie:regio-planning',
                                       kwargs={'deelcomp_pk': deelcomp.pk})

        menu_dynamics(self.request, context, actief='competitie')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Regel toevoegen' gebruikt wordt
        """

        # alleen de RCL mag de planning uitbreiden
        rol_nu = rol_get_huidige(self.request)
        if rol_nu != Rollen.ROL_RCL:
            raise Resolver404()

        cluster_pk = kwargs['cluster_pk'][:6]     # afkappen geeft beveiliging
        try:
            cluster = (NhbCluster
                       .objects
                       .select_related('regio', 'regio__rayon')
                       .get(pk=cluster_pk))
        except NhbCluster.DoesNotExist:
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

    # let op: week nummers zijn 0-based in strptime!
    when = datetime.datetime.strptime("%s-%s-1" % (jaar, week_nr-1), "%Y-%W-%w")   # 1 = maandag

    return datetime.date(year=when.year, month=when.month, day=when.day)


class RegioRondePlanningView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de planning van een ronde in een regio """

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

        ronde_pk = kwargs['ronde_pk'][:6]     # afkappen geeft beveiliging
        try:
            ronde = (DeelcompetitieRonde
                     .objects
                     .select_related('deelcompetitie__competitie',
                                     'deelcompetitie__nhb_regio__rayon',
                                     'cluster__regio')
                     .get(pk=ronde_pk))
        except DeelcompetitieRonde.DoesNotExist:
            raise Resolver404()

        context['ronde'] = ronde

        context['wedstrijden'] = (ronde.plan.wedstrijden
                                  .order_by('datum_wanneer', 'tijd_begin_wedstrijd')
                                  .select_related('vereniging'))

        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rollen.ROL_RCL:
            context['url_nieuwe_wedstrijd'] = reverse('Competitie:regio-ronde-planning',
                                                      kwargs={'ronde_pk': ronde.pk})

            for wedstrijd in context['wedstrijden']:
                wedstrijd.url_wijzig = reverse('Competitie:wijzig-wedstrijd', kwargs={'wedstrijd_pk': wedstrijd.pk})
            # for

        start_week = 37
        eind_week = 11+1
        if ronde.deelcompetitie.competitie.afstand == '18':
            eind_week = 50+1
        jaar = ronde.deelcompetitie.competitie.begin_jaar

        context['opt_week_nrs'] = opt_week_nrs = list()
        while start_week != eind_week:
            when = competitie_week_nr_to_date(jaar, start_week)
            obj = SimpleNamespace()
            obj.week_nr = start_week
            obj.choice_name = start_week
            obj.maandag = when
            obj.actief = (start_week == ronde.week_nr)
            opt_week_nrs.append(obj)

            if start_week >= 53:
                start_week = 1
                jaar += 1
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

        rol_nu = rol_get_huidige(self.request)
        if rol_nu != Rollen.ROL_RCL:
            context['readonly'] = True

        menu_dynamics(self.request, context, actief='competitie')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Regel toevoegen' gebruikt wordt
            en als op de knop Opslaan wordt gedrukt voor de ronde parameters
        """

        ronde_pk = kwargs['ronde_pk'][:6]     # afkappen geeft beveiliging
        try:
            ronde = DeelcompetitieRonde.objects.get(pk=ronde_pk)
        except DeelcompetitieRonde.DoesNotExist:
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
            if week_nr < 1 or week_nr > 53 or (week_nr > 11 and week_nr < 37):
                # geen valide week nummer
                raise Resolver404()

            beschrijving = request.POST.get('ronde_naam', '')
            ronde.beschrijving = beschrijving[:20]  # afkappen, anders werkt save niet

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

            if ronde.cluster:
                next_url = reverse('Competitie:regio-cluster-planning',
                                    kwargs={'cluster_pk': ronde.cluster.pk})
            else:
                next_url = reverse('Competitie:regio-planning',
                                    kwargs={'deelcomp_pk': ronde.deelcompetitie.pk})
        else:
            # voeg een wedstrijd toe
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

        wedstrijd_pk = kwargs['wedstrijd_pk'][:6]     # afkappen geeft beveiliging
        try:
            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd_pk)
        except Wedstrijd.DoesNotExist:
            raise Resolver404()

        mag_wijzigen, mag_verwijderen = plan_wedstrijd_rechten(self.request, wedstrijd)
        if not mag_wijzigen:
            raise Resolver404()

        # zoek het weeknummer waarin deze wedstrijd gehouden moet worden
        plan = wedstrijd.wedstrijdenplan_set.all()[0]
        ronde = DeelcompetitieRonde.objects.get(plan=plan)

        context['wedstrijd'] = wedstrijd
        context['ronde'] = ronde
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

            when = when + datetime.timedelta(days=1)
        # for

        wedstrijd.tijd_begin_wedstrijd_str = wedstrijd.tijd_begin_wedstrijd.strftime("%H:%M")
        # wedstrijd.tijd_begin_aanmelden_str = wedstrijd.tijd_begin_aanmelden.strftime("%H%M")
        # wedstrijd.tijd_einde_wedstrijd_str = wedstrijd.tijd_einde_wedstrijd.strftime("%H%M")

        if ronde.cluster:
            verenigingen = ronde.cluster.nhbvereniging_set.all()
        else:
            verenigingen = ronde.deelcompetitie.nhb_regio.nhbvereniging_set.all()
        context['verenigingen'] = verenigingen

        context['url_terug'] = reverse('Competitie:regio-ronde-planning', kwargs={'ronde_pk': ronde.pk})
        context['url_opslaan'] = reverse('Competitie:wijzig-wedstrijd', kwargs={'wedstrijd_pk': wedstrijd.pk})

        if mag_verwijderen:     # pragma: no branch
            context['url_verwijderen'] = reverse('Competitie:verwijder-wedstrijd', kwargs={'wedstrijd_pk': wedstrijd.pk})

        menu_dynamics(self.request, context, actief='competitie')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Opslaan' gebruikt wordt
        """
        wedstrijd_pk = kwargs['wedstrijd_pk'][:6]     # afkappen geeft beveiliging
        try:
            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd_pk)
        except Wedstrijd.DoesNotExist:
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

        if weekdag < 0 or weekdag > 6 or aanvang < 800 or aanvang > 2200:
            raise Resolver404()

        # bepaal de begin datum van de ronde-week
        when = competitie_week_nr_to_date(jaar, ronde.week_nr)
        # voeg nu de offset toe uit de weekdag
        when += datetime.timedelta(days=weekdag)

        # vertaal aanvang naar een tijd
        hour = aanvang // 100
        min = aanvang - (hour * 100)
        if hour < 8 or hour > 22 or min < 0 or min > 59:
            raise Resolver404()

        try:
            nhbver = NhbVereniging.objects.get(pk=nhbver_pk)
        except NhbVereniging.DoesNotExist:
            raise Resolver404()

        wedstrijd.datum_wanneer = when
        wedstrijd.tijd_begin_wedstrijd = datetime.time(hour=hour, minute=min)
        wedstrijd.vereniging = nhbver
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
        wedstrijd_pk = kwargs['wedstrijd_pk'][:6]     # afkappen geeft beveiliging
        try:
            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd_pk)
        except Wedstrijd.DoesNotExist:
            raise Resolver404()

        _, mag_verwijderen = plan_wedstrijd_rechten(request, wedstrijd)
        if not mag_verwijderen:
            raise Resolver404()

        plan = wedstrijd.wedstrijdenplan_set.all()[0]
        ronde = DeelcompetitieRonde.objects.get(plan=plan)
        url = reverse('Competitie:regio-ronde-planning', kwargs={'ronde_pk': ronde.pk})

        wedstrijd.delete()

        return HttpResponseRedirect(url)

# end of file
