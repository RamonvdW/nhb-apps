# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import Resolver404, reverse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie
from NhbStructuur.models import NhbCluster, NhbVereniging
from Wedstrijden.models import Wedstrijd, WedstrijdenPlan, WedstrijdLocatie
from .models import (LAAG_REGIO, LAAG_RK, LAAG_BK,
                     DeelCompetitie, DeelcompetitieRonde, maak_deelcompetitie_ronde)
from types import SimpleNamespace
import datetime


TEMPLATE_COMPETITIE_PLANNING_RAYON = 'competitie/planning-rayon.dtl'
TEMPLATE_COMPETITIE_WIJZIG_WEDSTRIJD_RAYON = 'competitie/wijzig-wedstrijd-rk.dtl'


# python strftime: 0=sunday, 6=saturday
# wij rekenen het verschil ten opzicht van maandag in de week
WEEK_DAGEN = ( (0, 'Maandag'),
               (1, 'Dinsdag'),
               (2, 'Woensdag'),
               (3, 'Donderdag'),
               (4, 'Vrijdag'),
               (5, 'Zaterdag'),
               (6, 'Zondag'))

JA_NEE = {False: 'Nee', True: 'Ja'}


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

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen geeft beveiliging
            deelcomp_rk = (DeelCompetitie
                           .objects
                           .select_related('competitie', 'nhb_rayon')
                           .get(pk=deelcomp_pk, laag=LAAG_RK))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Resolver404()

        context['deelcomp_rk'] = deelcomp_rk
        context['rayon'] = deelcomp_rk.nhb_rayon

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        # maak het plan aan, als deze nog niet aanwezig was
        if not deelcomp_rk.plan:
            deelcomp_rk.plan = WedstrijdenPlan()
            deelcomp_rk.plan.save()
            deelcomp_rk.save()

        # haal de RK wedstrijden op
        context['wedstrijden_rk'] = (deelcomp_rk.plan.wedstrijden
                                     .select_related('vereniging')
                                     .order_by('datum_wanneer',
                                               'tijd_begin_wedstrijd'))

        if rol_nu == Rollen.ROL_RKO and functie_nu.nhb_rayon == deelcomp_rk.nhb_rayon:
            context['url_nieuwe_wedstrijd'] = reverse('Competitie:rayon-planning',
                                                      kwargs={'deelcomp_pk': deelcomp_rk.pk})

            for wedstrijd in context['wedstrijden_rk']:
                wedstrijd.url_wijzig = reverse('Competitie:wijzig-rayon-wedstrijd',
                                               kwargs={'wedstrijd_pk': wedstrijd.pk})
            # for

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

        # zoek het aantal regiowedstrijden erbij
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

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Regel toevoegen' gebruikt wordt
            in de RK planning, om een nieuwe wedstrijd toe te voegen.
        """
        # alleen de RKO mag de planning uitbreiden
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        if rol_nu != Rollen.ROL_RKO:
            raise Resolver404()

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen geeft beveiliging
            deelcomp_rk = (DeelCompetitie
                           .objects
                           .select_related('competitie', 'nhb_regio')
                           .get(pk=deelcomp_pk,
                                laag=LAAG_RK,                          # moet voor RK zijn
                                nhb_rayon=functie_nu.nhb_rayon))       # moet juiste rayon zijn
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Resolver404()

        # maak het plan aan, als deze nog niet aanwezig was
        if not deelcomp_rk.plan:
            deelcomp_rk.plan = WedstrijdenPlan()
            deelcomp_rk.plan.save()
            deelcomp_rk.save()

        wedstrijd = Wedstrijd()
        wedstrijd.datum_wanneer = deelcomp_rk.competitie.rk_eerste_wedstrijd
        wedstrijd.tijd_begin_aanmelden = datetime.time(hour=0, minute=0, second=0)
        wedstrijd.tijd_begin_wedstrijd = wedstrijd.tijd_begin_aanmelden
        wedstrijd.tijd_einde_wedstrijd = wedstrijd.tijd_begin_aanmelden
        wedstrijd.save()

        deelcomp_rk.plan.wedstrijden.add(wedstrijd)

        return HttpResponseRedirect(reverse('Competitie:wijzig-rayon-wedstrijd',
                                            kwargs={'wedstrijd_pk': wedstrijd.pk}))


class WijzigRayonWedstrijdView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de planning van een wedstrijd aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_WIJZIG_WEDSTRIJD_RAYON

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_RKO

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        _, functie_nu = rol_get_huidige_functie(self.request)

        try:
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])     # afkappen geeft beveiliging
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('uitslag')
                         .prefetch_related('uitslag__scores')
                         .get(pk=wedstrijd_pk))
        except (ValueError, Wedstrijd.DoesNotExist):
            raise Resolver404()

        # zoek het weeknummer waarin deze wedstrijd gehouden moet worden
        plan = wedstrijd.wedstrijdenplan_set.all()[0]
        deelcomp_rk = plan.deelcompetitie_set.all()[0]

        # is dit de beheerder?
        if deelcomp_rk.functie != functie_nu:
            raise Resolver404()

        context['deelcomp_rk'] = deelcomp_rk
        context['wedstrijd'] = wedstrijd

        # maak de lijst waarop de wedstrijd gehouden kan worden
        context['opt_weekdagen'] = opt_weekdagen = list()
        when = deelcomp_rk.competitie.rk_eerste_wedstrijd
        stop = deelcomp_rk.competitie.rk_laatste_wedstrijd
        weekdag_nr = 0
        limit = 30
        while limit > 0 and when <= stop:
            obj = SimpleNamespace()
            obj.weekdag_nr = weekdag_nr
            obj.datum = when
            obj.actief = (when == wedstrijd.datum_wanneer)
            opt_weekdagen.append(obj)

            limit -= 1
            when += datetime.timedelta(days=1)
            weekdag_nr += 1
        # while

        wedstrijd.tijd_begin_wedstrijd_str = wedstrijd.tijd_begin_wedstrijd.strftime("%H:%M")
        # wedstrijd.tijd_begin_aanmelden_str = wedstrijd.tijd_begin_aanmelden.strftime("%H%M")
        # wedstrijd.tijd_einde_wedstrijd_str = wedstrijd.tijd_einde_wedstrijd.strftime("%H%M")

        verenigingen = NhbVereniging.objects.filter(regio__rayon=deelcomp_rk.nhb_rayon,
                                                    regio__is_administratief=False)
        context['verenigingen'] = verenigingen

        if not wedstrijd.vereniging:
            if verenigingen.count() > 0:
                wedstrijd.vereniging = verenigingen[0]
                wedstrijd.save()

        if not wedstrijd.locatie:
            if wedstrijd.vereniging:
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

        context['url_terug'] = reverse('Competitie:rayon-planning', kwargs={'deelcomp_pk': deelcomp_rk.pk})
        context['url_opslaan'] = reverse('Competitie:wijzig-rayon-wedstrijd', kwargs={'wedstrijd_pk': wedstrijd.pk})

        context['url_verwijderen'] = reverse('Competitie:verwijder-wedstrijd',
                                             kwargs={'wedstrijd_pk': wedstrijd.pk})

        menu_dynamics(self.request, context, actief='competitie')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Opslaan' gebruikt wordt
        """

        _, functie_nu = rol_get_huidige_functie(self.request)

        try:
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])     # afkappen geeft beveiliging
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('uitslag')
                         .prefetch_related('uitslag__scores')
                         .get(pk=wedstrijd_pk))
        except (ValueError, Wedstrijd.DoesNotExist):
            raise Resolver404()

        plan = wedstrijd.wedstrijdenplan_set.all()[0]
        deelcomp_rk = plan.deelcompetitie_set.all()[0]

        # is dit de beheerder?
        if deelcomp_rk.functie != functie_nu:
            raise Resolver404()

        competitie = deelcomp_rk.competitie

        # weekdag is een cijfer van 0 tm 6
        # aanvang bestaat uit vier cijfers, zoals 0830
        weekdag = request.POST.get('weekdag', '')[:2]     # afkappen = veiligheid
        aanvang = request.POST.get('aanvang', '')[:5]
        nhbver_pk = request.POST.get('nhbver_pk', '')[:6]
        if weekdag == "" or nhbver_pk == "" or len(aanvang) != 5 or aanvang[2] != ':':
            raise Resolver404()

        try:
            weekdag = int(weekdag)
            aanvang = int(aanvang[0:0+2] + aanvang[3:3+2])
        except (TypeError, ValueError):
            raise Resolver404()

        if weekdag < 0 or weekdag > 30 or aanvang < 0 or aanvang > 2359:
            raise Resolver404()

        # weekdag is een offset ten opzicht van de eerste toegestane RK wedstrijddag
        wedstrijd.datum_wanneer = deelcomp_rk.competitie.rk_eerste_wedstrijd + datetime.timedelta(days=weekdag)

        # check dat datum_wanneer nu in de ingesteld RK periode valt
        if not (competitie.rk_eerste_wedstrijd <= wedstrijd.datum_wanneer <= competitie.rk_laatste_wedstrijd):
            raise Resolver404()

        # vertaal aanvang naar een tijd
        uur = aanvang // 100
        minuut = aanvang - (uur * 100)
        if uur < 0 or uur > 23 or minuut < 0 or minuut > 59:
            raise Resolver404()

        wedstrijd.tijd_begin_wedstrijd = datetime.time(hour=uur, minute=minuut)

        try:
            nhbver = NhbVereniging.objects.get(pk=nhbver_pk)
        except NhbVereniging.DoesNotExist:
            raise Resolver404()

        # check dat nhbver een van de aangeboden verenigingen is
        if nhbver.regio.rayon != deelcomp_rk.nhb_rayon or nhbver.regio.is_administratief:
            raise Resolver404()

        wedstrijd.vereniging = nhbver

        locaties = nhbver.wedstrijdlocatie_set.all()
        if locaties.count() > 0:
            wedstrijd.locatie = locaties[0]
        else:
            wedstrijd.locatie = None
        wedstrijd.save()

        url = reverse('Competitie:rayon-planning', kwargs={'deelcomp_pk': deelcomp_rk.pk})
        return HttpResponseRedirect(url)


# end of file
