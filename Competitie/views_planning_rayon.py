# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import Resolver404, reverse
from django.utils import timezone
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import IndivWedstrijdklasse
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie
from Logboek.models import schrijf_in_logboek
from NhbStructuur.models import NhbCluster, NhbVereniging
from Plein.menu import menu_dynamics
from Taken.models import Taak
from Wedstrijden.models import Wedstrijd, WedstrijdenPlan, WedstrijdLocatie
from .models import (LAAG_REGIO, LAAG_RK, LAAG_BK, DeelCompetitie, DeelcompetitieRonde,
                     CompetitieKlasse, RegioCompetitieSchutterBoog, KampioenschapSchutterBoog)
from types import SimpleNamespace
import datetime


TEMPLATE_COMPETITIE_PLANNING_RAYON = 'competitie/planning-rayon.dtl'
TEMPLATE_COMPETITIE_WIJZIG_WEDSTRIJD_RAYON = 'competitie/wijzig-wedstrijd-rk.dtl'
TEMPLATE_COMPETITIE_LIJST_RK = 'competitie/lijst-rk.dtl'
TEMPLATE_COMPETITIE_LIJST_RK_CONTACT = 'competitie/lijst-rk-contact.dtl'
TEMPLATE_COMPETITIE_WIJZIG_STATUS_RK_SCHUTTER = 'competitie/wijzig-status-rk-deelnemer.dtl'

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

        klasse2schutters = dict()
        for obj in (KampioenschapSchutterBoog
                    .objects
                    .filter(deelcompetitie=deelcomp_rk)
                    .select_related('klasse')):
            try:
                klasse2schutters[obj.klasse.indiv.pk] += 1
            except KeyError:
                klasse2schutters[obj.klasse.indiv.pk] = 1
        # for

        # haal de RK wedstrijden op
        context['wedstrijden_rk'] = (deelcomp_rk.plan.wedstrijden
                                     .select_related('vereniging')
                                     .prefetch_related('indiv_klassen',
                                                       'team_klassen')
                                     .order_by('datum_wanneer',
                                               'tijd_begin_wedstrijd'))
        for obj in context['wedstrijden_rk']:
            obj.klassen_count = obj.indiv_klassen.count() + obj.team_klassen.count()
            obj.schutters_count = 0

            for klasse in obj.indiv_klassen.all():
                try:
                    obj.schutters_count += klasse2schutters[klasse.pk]
                except KeyError:
                    # geen schutters in deze klasse
                    pass
            # for
        # for

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

    @staticmethod
    def _get_wedstrijdklassen(deelcomp_rk, wedstrijd):
        klasse2schutters = dict()
        for obj in (KampioenschapSchutterBoog
                    .objects
                    .filter(deelcompetitie=deelcomp_rk)
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
                     .filter(competitie=deelcomp_rk.competitie,
                             indiv__is_onbekend=False,
                             team=None)
                     .select_related('indiv__boogtype')
                     .order_by('indiv__volgorde')
                     .all())
        prev_boogtype = wkl_indiv[0].indiv.boogtype
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
            obj.sel_str = "wkl_indiv_%s" % obj.indiv.pk
            obj.geselecteerd = (obj.indiv.pk in wedstrijd_indiv_pks)
        # for

        wedstrijd_team_pks = [obj.pk for obj in wedstrijd.team_klassen.all()]
        wkl_team = (CompetitieKlasse
                    .objects
                    .filter(competitie=deelcomp_rk.competitie,
                            indiv=None)
                    .order_by('indiv__volgorde')
                    .all())
        for obj in wkl_team:
            obj.short_str = obj.team.beschrijving
            obj.sel_str = "wkl_team_%s" % obj.team.pk
            obj.geselecteerd = (obj.team.pk in wedstrijd_team_pks)
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

        _, functie_nu = rol_get_huidige_functie(self.request)

        try:
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])     # afkappen geeft beveiliging
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('uitslag')
                         .prefetch_related('uitslag__scores',
                                           'indiv_klassen',
                                           'team_klassen')
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
        context['opt_weekdagen'] = self._get_dagen(deelcomp_rk, wedstrijd)

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

        context['wkl_indiv'], context['wkl_team'] = self._get_wedstrijdklassen(deelcomp_rk, wedstrijd)

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

        gekozen_klassen = list()
        for key, value in request.POST.items():
            if key[:10] == "wkl_indiv_":
                try:
                    pk = int(key[10:10+6])
                except (IndexError, TypeError, ValueError):
                    pass
                else:
                    gekozen_klassen.append(pk)
        # for

        niet_meer_gekozen = list()
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

        url = reverse('Competitie:rayon-planning', kwargs={'deelcomp_pk': deelcomp_rk.pk})
        return HttpResponseRedirect(url)


class LijstRkSchuttersView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de (kandidaat) schutters van en RK zien,
        met mogelijkheid voor de RKO om deze te bevestigen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_LIJST_RK

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_RKO

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    @staticmethod
    def _get_regio_status(competitie):
        # schutter moeten uit LAAG_REGIO gehaald worden, uit de 4 regio's van het rayon
        regio_deelcomps = (DeelCompetitie
                           .objects
                           .filter(laag=LAAG_REGIO,
                                   competitie=competitie)
                           .select_related('nhb_regio',
                                           'nhb_regio__rayon')
                           .order_by('nhb_regio__regio_nr'))

        alles_afgesloten = True
        for obj in regio_deelcomps:
            obj.regio_str = str(obj.nhb_regio.regio_nr)
            obj.rayon_str = str(obj.nhb_regio.rayon.rayon_nr)

            if obj.is_afgesloten:
                obj.status_str = "Afgesloten"
                obj.status_groen = True
            else:
                alles_afgesloten = False
                obj.status_str = "Actief"
        # for

        return alles_afgesloten, regio_deelcomps

    def _get_schutters_regios(self, competitie, rayon_nr):
        """ geeft een lijst met deelnemers terug
            en een totaal-status van de onderliggende regiocompetities: alles afgesloten?
        """
        alles_afgesloten = True
        pks = list()

        # schutter moeten uit LAAG_REGIO gehaald worden, uit de 4 regio's van het rayon
        for deelcomp in (DeelCompetitie
                         .objects
                         .filter(laag=LAAG_REGIO,
                                 competitie=competitie,
                                 nhb_regio__rayon__rayon_nr=rayon_nr)):
            if not deelcomp.is_afgesloten:
                alles_afgesloten = False

            pks.append(deelcomp.pk)
        # for

        deelnemers = (RegioCompetitieSchutterBoog
                      .objects
                      .select_related('klasse__indiv',
                                      'bij_vereniging__regio',
                                      'schutterboog__nhblid')
                      .filter(deelcompetitie__in=pks,
                              aantal_scores__gte=3,         # TODO: gte=6
                              schutterboog__nhblid__is_actief_lid=True)     # verwijdert uitgeschreven leden
                      .order_by('klasse__indiv__volgorde',      # groepeer per klasse
                                '-gemiddelde'))                 # aflopend gemiddelde

        # markeer de regiokampioenen
        klasse = -1
        regios = list()     # bijhouden welke kampioenen we al gemarkeerd hebben
        kampioenen = list()
        deelnemers = list(deelnemers)
        nr = 0
        insert_at = 0
        rank = 0
        while nr < len(deelnemers):
            deelnemer = deelnemers[nr]

            if klasse != deelnemer.klasse.indiv.volgorde:
                klasse = deelnemer.klasse.indiv.volgorde
                if len(kampioenen):
                    kampioenen.sort()
                    for _, kampioen in kampioenen:
                        deelnemers.insert(insert_at, kampioen)
                        insert_at += 1
                        nr += 1
                    # for
                kampioenen = list()
                regios = list()
                insert_at = nr
                rank = 0

            # fake een paar velden uit KampioenschapSchutterBoog
            deelnemer.is_afgemeld = False
            deelnemer.deelname_bevestigd = False

            rank += 1
            deelnemer.volgorde = rank

            regio_nr = deelnemer.bij_vereniging.regio.regio_nr
            if regio_nr not in regios:
                regios.append(regio_nr)
                deelnemer.kampioen_label = "Kampioen regio %s" % regio_nr
                tup = (regio_nr, deelnemer)
                kampioenen.append(tup)
                deelnemers.pop(nr)
            else:
                if rank <= 48:
                    deelnemer.kampioen_label = ""
                    nr += 1
                else:
                    # verwijder deze schutter uit de lijst
                    deelnemers.pop(nr)
        # while

        if len(kampioenen):
            kampioenen.sort(reverse=True)       # hoogste regionummer bovenaan
            for _, kampioen in kampioenen:
                deelnemers.insert(insert_at, kampioen)
                insert_at += 1
            # for

        return deelnemers, alles_afgesloten

    def _get_schutters_rk(self, deelcomp_rk):
        deelnemers = (KampioenschapSchutterBoog
                      .objects
                      .select_related('deelcompetitie',
                                      'klasse__indiv',
                                      'schutterboog__nhblid',
                                      'bij_vereniging')
                      .filter(deelcompetitie=deelcomp_rk)
                      .order_by('klasse__indiv__volgorde',  # groepeer per klasse
                                '-kampioen_label',          # hoogste regio nummer boven (anders leeg boven)
                                '-gemiddelde'))             # aflopend gemiddelde
        return deelnemers

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # er zijn 3 situaties:
        # 1) regiocompetities zijn nog niet afgesloten --> verwijst naar pagina tussenstand rayon
        # 2) deelnemers voor RK zijn nog niet vastgesteld --> toon lijst + knop om akkoord te geven
        # 3) deelnemers voor RK zijn vastgesteld --> toon lijst

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen geeft beveiliging
            deelcomp_rk = (DeelCompetitie
                           .objects
                           .select_related('competitie', 'nhb_rayon')
                           .get(pk=deelcomp_pk, laag=LAAG_RK))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Resolver404()

        # controleer dat de juiste RKO aan de knoppen zit
        _, functie_nu = rol_get_huidige_functie(self.request)
        if functie_nu != deelcomp_rk.functie:
            raise Resolver404()     # niet de juiste RKO

        alles_afgesloten, regio_status = self._get_regio_status(deelcomp_rk.competitie)
        context['regio_status'] = regio_status

        context['deelcomp_rk'] = deelcomp_rk

        if not deelcomp_rk.heeft_deelnemerslijst:
            deelnemers, alles_afgesloten = self._get_schutters_regios(deelcomp_rk.competitie,
                                                                      deelcomp_rk.nhb_rayon.rayon_nr)
            if not alles_afgesloten:
                # situatie 1)
                context['url_tussenstand'] = reverse('Competitie:tussenstand-rayon-n',
                                                     kwargs={'afstand': deelcomp_rk.competitie.afstand,
                                                             'comp_boog': 'r',
                                                             'rayon_nr': deelcomp_rk.nhb_rayon.rayon_nr})
                deelnemers = list()
            else:
                # situatie 2)
                context['url_bevestig_rk_schutters'] = reverse('Competitie:lijst-rk',
                                                               kwargs={'deelcomp_pk': deelcomp_rk.pk})
        else:
            # situatie 3)
            deelnemers = self._get_schutters_rk(deelcomp_rk)

            for deelnemer in deelnemers:
                deelnemer.url_wijzig = reverse('Competitie:wijzig-status-rk-deelnemer',
                                               kwargs={'deelnemer_pk': deelnemer.pk})
            # for

        klasse = -1
        rank = 0
        aantal_afgemeld = 0
        aantal_bevestigd = 0
        aantal_onbekend = 0
        aantal_klassen = 0
        for deelnemer in deelnemers:
            deelnemer.break_klasse = (klasse != deelnemer.klasse.indiv.volgorde)
            if deelnemer.break_klasse:
                if klasse != -1:
                    aantal_klassen += 1
                deelnemer.klasse_str = deelnemer.klasse.indiv.beschrijving
                klasse = deelnemer.klasse.indiv.volgorde
                rank = 0

            lid = deelnemer.schutterboog.nhblid
            deelnemer.naam_str = "[%s] %s" % (lid.nhb_nr, lid.volledige_naam())
            deelnemer.ver_str = str(deelnemer.bij_vereniging)

            deelnemer.rank = 0
            if not deelnemer.is_afgemeld:
                rank += 1
                deelnemer.rank = rank

            if rank > 24:
                deelnemer.is_reserve = True

            # tel het aantal deelnemers
            if deelnemer.volgorde <= 24+8:
                if deelnemer.is_afgemeld:
                    aantal_afgemeld += 1
                elif deelnemer.deelname_bevestigd:
                    aantal_bevestigd += 1
                else:
                    aantal_onbekend += 1
        # for

        context['deelnemers'] = deelnemers
        context['aantal_klassen'] = aantal_klassen

        if deelcomp_rk.heeft_deelnemerslijst:
            context['aantal_afgemeld'] = aantal_afgemeld
            context['aantal_onbekend'] = aantal_onbekend
            context['aantal_bevestigd'] = aantal_bevestigd

            context['url_contact'] = reverse('Competitie:lijst-rk-contact',
                                             kwargs={'deelcomp_pk': deelcomp_rk.pk})

        menu_dynamics(self.request, context, actief='competitie')
        return context

    def post(self, request, *args, **kwargs):

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen geeft beveiliging
            deelcomp_rk = (DeelCompetitie
                           .objects
                           .select_related('competitie', 'nhb_rayon')
                           .get(pk=deelcomp_pk, laag=LAAG_RK))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Resolver404()

        # controleer dat de juiste RKO aan de knoppen zit
        _, functie_nu = rol_get_huidige_functie(self.request)
        if functie_nu != deelcomp_rk.functie:
            raise Resolver404()     # niet de juiste RKO

        if not deelcomp_rk.heeft_deelnemerslijst:
            deelnemers, alles_afgesloten = self._get_schutters_regios(deelcomp_rk.competitie,
                                                                      deelcomp_rk.nhb_rayon.rayon_nr)
            if not alles_afgesloten:
                raise Resolver404()

            # schrijf all deze schutters in voor het RK
            # kampioenen zitten als eerste in de lijst, daarna aflopend gesorteerd op gemiddelde
            bulk_lijst = list()
            klasse = -1
            volgorde = 0
            for obj in deelnemers:
                if klasse != obj.klasse.indiv.volgorde:
                    klasse = obj.klasse.indiv.volgorde
                    volgorde = 0

                volgorde += 1

                deelnemer = KampioenschapSchutterBoog(
                                deelcompetitie=deelcomp_rk,
                                schutterboog=obj.schutterboog,
                                klasse=obj.klasse,
                                bij_vereniging=obj.bij_vereniging,
                                volgorde=volgorde,
                                gemiddelde=obj.gemiddelde,
                                kampioen_label=obj.kampioen_label)

                bulk_lijst.append(deelnemer)
                if len(bulk_lijst) > 500:
                    KampioenschapSchutterBoog.objects.bulk_create(bulk_lijst)
                    bulk_lijst = list()
            # for

            if len(bulk_lijst) > 0:
                KampioenschapSchutterBoog.objects.bulk_create(bulk_lijst)
            del bulk_lijst

            deelcomp_rk.heeft_deelnemerslijst = True
            deelcomp_rk.save()

            # zoek het bijbehorende BK op
            deelcomp_bk = DeelCompetitie.objects.get(competitie=deelcomp_rk.competitie,
                                                     laag=LAAG_BK)

            # stuur elke RKO een taak ('ter info')
            bko_namen = list()
            functie_bko = deelcomp_bk.functie
            now = timezone.now()
            taak_deadline = now
            taak_tekst = "Ter info: De deelnemerslijst voor de Rayonkampioenschappen in %s zijn zojuist vastgesteld door RKO %s" % (str(deelcomp_rk.nhb_rayon), request.user.volledige_naam())
            taak_log = "[%s] Taak aangemaakt" % now

            for account in functie_bko.accounts.all():
                # maak een taak aan voor deze BKO
                taak = Taak(toegekend_aan=account,
                            deadline=taak_deadline,
                            aangemaakt_door=request.user,
                            beschrijving=taak_tekst,
                            handleiding_pagina="",
                            log=taak_log,
                            deelcompetitie=deelcomp_bk)
                taak.save()
                bko_namen.append(account.volledige_naam())
            # for

            # schrijf in het logboek
            msg = "De deelnemerslijst voor de Rayonkampioenschappen in %s is zojuist vastgesteld." % str(deelcomp_rk.nhb_rayon)
            msg += '\nDe volgende beheerders zijn geïnformeerd via een taak: %s' % ", ".join(bko_namen)
            schrijf_in_logboek(request.user, "Competitie", msg)

        return HttpResponseRedirect(reverse('Competitie:overzicht'))


class WijzigStatusRkSchutterView(TemplateView):

    """ Deze view laat de RKO de status van een RK schutters aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_WIJZIG_STATUS_RK_SCHUTTER

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

        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen geeft beveiliging
            deelnemer = (KampioenschapSchutterBoog
                         .objects
                         .select_related('deelcompetitie__competitie',
                                         'deelcompetitie__nhb_rayon',
                                         'schutterboog__nhblid',
                                         'bij_vereniging')
                         .get(pk=deelnemer_pk))
        except (ValueError, KampioenschapSchutterBoog.DoesNotExist):
            raise Resolver404()

        # controleer dat de juiste RKO aan de knoppen zit
        _, functie_nu = rol_get_huidige_functie(self.request)
        if functie_nu != deelnemer.deelcompetitie.functie:
            raise Resolver404()     # niet de juiste RKO

        lid = deelnemer.schutterboog.nhblid
        deelnemer.naam_str = "[%s] %s" % (lid.nhb_nr, lid.volledige_naam())
        deelnemer.ver_str = str(deelnemer.bij_vereniging)

        context['deelnemer'] = deelnemer

        context['url_wijzig'] = reverse('Competitie:wijzig-status-rk-deelnemer',
                                        kwargs={'deelnemer_pk': deelnemer.pk})

        context['url_terug'] = reverse('Competitie:lijst-rk',
                                       kwargs={'deelcomp_pk': deelnemer.deelcompetitie.pk})

        menu_dynamics(self.request, context, actief='competitie')
        return context

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de gebruik op de knop OPSLAAN druk """
        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen geeft beveiliging
            deelnemer = (KampioenschapSchutterBoog
                         .objects
                         .select_related('deelcompetitie__competitie')
                         .get(pk=deelnemer_pk))
        except (ValueError, KampioenschapSchutterBoog.DoesNotExist):
            raise Resolver404()

        bevestig = request.POST.get('bevestig', '')
        afmelden = request.POST.get('afmelden', '')

        _, functie_nu = rol_get_huidige_functie(self.request)
        if functie_nu != deelnemer.deelcompetitie.functie:
            raise Resolver404()     # niet de juiste RKO

        if bevestig == "1":
            if not deelnemer.deelname_bevestigd:
                deelnemer.deelname_bevestigd = True
                deelnemer.is_afgemeld = False
                deelnemer.save()
        elif afmelden == "1":
            if not deelnemer.is_afgemeld:
                deelnemer.deelname_bevestigd = False
                deelnemer.is_afgemeld = True
                deelnemer.save()

        return HttpResponseRedirect(reverse('Competitie:lijst-rk',
                                            kwargs={'deelcomp_pk': deelnemer.deelcompetitie.pk}))


class LijstRkContactgegevensView(UserPassesTestMixin, TemplateView):
    """ Deze view laat de contactgegevens zien van de RK schutters """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_LIJST_RK_CONTACT

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

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen geeft beveiliging
            deelcomp_rk = (DeelCompetitie
                           .objects
                           .select_related('competitie', 'nhb_rayon')
                           .get(pk=deelcomp_pk, laag=LAAG_RK))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Resolver404()

        # controleer dat de juiste RKO aan de knoppen zit
        _, functie_nu = rol_get_huidige_functie(self.request)
        if functie_nu != deelcomp_rk.functie:
            raise Resolver404()     # niet de juiste RKO

        if not deelcomp_rk.heeft_deelnemerslijst:
            raise Resolver404()     # zou hier niet moeten komen

        context['deelcomp_rk'] = deelcomp_rk

        deelnemers = (KampioenschapSchutterBoog
                      .objects
                      .filter(deelcompetitie=deelcomp_rk)
                      .select_related('deelcompetitie',
                                      'klasse__indiv',
                                      'schutterboog__nhblid',
                                      'bij_vereniging')
                      .order_by('klasse__indiv__volgorde',  # groepeer per klasse
                                '-kampioen_label',          # hoogste regio nummer boven (anders leeg boven)
                                '-gemiddelde'))             # aflopend gemiddelde

        klasse = -1
        rank = 0
        per_ver = list()
        for deelnemer in deelnemers:
            if klasse != deelnemer.klasse.indiv.volgorde:
                klasse = deelnemer.klasse.indiv.volgorde
                rank = 0

            lid = deelnemer.schutterboog.nhblid
            deelnemer.naam_str = "[%s] %s" % (lid.nhb_nr, lid.volledige_naam())
            deelnemer.ver_str = str(deelnemer.bij_vereniging)

            if lid.email == "":
                deelnemer.geen_email = True

            if not deelnemer.is_afgemeld:
                rank += 1
                if rank > 24:
                    deelnemer.is_reserve = True

                if not deelnemer.deelname_bevestigd:
                    tup = (deelnemer.bij_vereniging.nhb_nr, lid.nhb_nr, deelnemer)
                    per_ver.append(tup)
        # for

        # opnieuw sorteren, op vereniging
        per_ver.sort(key=lambda tup: tup[0:0+2])

        context['deelnemers'] = contacten = [obj for _,_,obj in per_ver]

        ver = -1
        for obj in contacten:
            if ver != obj.bij_vereniging.nhb_nr:
                ver = obj.bij_vereniging.nhb_nr
                obj.break_ver = True

                obj.ver_email = ""

                functies = obj.bij_vereniging.functie_set.filter(rol='HWL')
                if len(functies) > 0:
                    functie = functies[0]
                    if functie.bevestigde_email:
                        obj.ver_email = functie.bevestigde_email
                        obj.ver_rol = 'Hoofdwedstrijdleider'

                if obj.ver_email == "":
                    functies = obj.bij_vereniging.functie_set.filter(rol='SEC')
                    if len(functies) > 0:
                        functie = functies[0]
                        if functie.bevestigde_email:
                            obj.ver_email = functie.bevestigde_email
                            obj.ver_rol = 'Secretaris'

        # for

        menu_dynamics(self.request, context, actief='competitie')
        return context


# end of file
