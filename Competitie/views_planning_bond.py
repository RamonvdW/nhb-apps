# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import Resolver404, reverse
from django.utils import timezone
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie
from Logboek.models import schrijf_in_logboek
from Plein.menu import menu_dynamics
from Taken.taken import maak_taak
from .models import (Competitie,
                     LAAG_REGIO, LAAG_RK, LAAG_BK, DeelCompetitie, DeelcompetitieKlasseLimiet,
                     RegioCompetitieSchutterBoog, KampioenschapSchutterBoog,
                     KampioenschapMutatie, MUTATIE_INITIEEL, DEELNAME_ONBEKEND)
from Wedstrijden.models import Wedstrijd


TEMPLATE_COMPETITIE_PLANNING_BOND = 'competitie/planning-landelijk.dtl'
TEMPLATE_COMPETITIE_DOORZETTEN_NAAR_RK = 'competitie/bko-doorzetten-naar-rk.dtl'
TEMPLATE_COMPETITIE_DOORZETTEN_NAAR_BK = 'competitie/bko-doorzetten-naar-bk.dtl'
TEMPLATE_COMPETITIE_AFSLUITEN = 'competitie/bko-afsluiten-competitie.dtl'


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


class DoorzettenNaarRKView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de BKO de competitie doorzetten naar de BR fase """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_DOORZETTEN_NAAR_RK

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BKO

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

        for obj in regio_deelcomps:
            obj.regio_str = str(obj.nhb_regio.regio_nr)
            obj.rayon_str = str(obj.nhb_regio.rayon.rayon_nr)

            if obj.is_afgesloten:
                obj.status_str = "Afgesloten"
                obj.status_groen = True
            else:
                obj.status_str = "Actief"
        # for

        return regio_deelcomps

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])  # afkappen geeft beveiliging
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk,
                         is_afgesloten=False))
        except (ValueError, Competitie.DoesNotExist):
            raise Resolver404()

        comp.zet_fase()
        if comp.fase < 'E' or comp.fase >= 'K':
            # kaartjes werd niet getoond, dus je zou hier niet moeten zijn
            raise Resolver404()

        context['comp'] = comp
        context['regio_status'] = self._get_regio_status(comp)

        if comp.fase == 'G':
            # klaar om door te zetten
            context['url_doorzetten'] = reverse('Competitie:bko-doorzetten-naar-rk',
                                                kwargs={'comp_pk': comp.pk})

        menu_dynamics(self.request, context, actief='competitie')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Doorzetten' gebruikt wordt
            om de competitie door te zetten naar de RK fase
        """
        try:
            comp_pk = int(kwargs['comp_pk'][:6])  # afkappen geeft beveiliging
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk,
                         is_afgesloten=False))
        except (ValueError, Competitie.DoesNotExist):
            raise Resolver404()

        comp.zet_fase()
        if comp.fase != 'G':
            raise Resolver404()

        # fase G garandeert dat alle regiocompetities afgesloten zijn

        self._maak_deelnemerslijst_rks(comp)

        # ga door naar de RK fase
        comp.alle_regiocompetities_afgesloten = True
        comp.save()

        return HttpResponseRedirect(reverse('Competitie:kies'))

    def _maak_deelnemerslijst_rks(self, comp):

        account = self.request.user
        door_str = "BKO %s" % account.volledige_naam()

        for deelcomp_rk in (DeelCompetitie
                            .objects
                            .select_related('nhb_rayon')
                            .filter(competitie=comp,
                                    laag=LAAG_RK)
                            .order_by('nhb_rayon__rayon_nr')):

            deelnemers = self._get_schutters_regios(comp, deelcomp_rk.nhb_rayon.rayon_nr)

            klassen = list()

            # schrijf all deze schutters in voor het RK
            # kampioenen als eerste in de lijst, daarna aflopend gesorteerd op gemiddelde
            bulk_lijst = list()
            klasse = -1
            for obj in deelnemers:
                if klasse != obj.klasse.indiv.volgorde:
                    klasse = obj.klasse.indiv.volgorde
                    klassen.append(obj.klasse)

                deelnemer = KampioenschapSchutterBoog(
                                deelcompetitie=deelcomp_rk,
                                schutterboog=obj.schutterboog,
                                klasse=obj.klasse,
                                bij_vereniging=obj.bij_vereniging,
                                gemiddelde=obj.gemiddelde,
                                kampioen_label=obj.kampioen_label)

                bulk_lijst.append(deelnemer)
                if len(bulk_lijst) > 150:       # pragma: no cover
                    KampioenschapSchutterBoog.objects.bulk_create(bulk_lijst)
                    bulk_lijst = list()
            # for

            if len(bulk_lijst) > 0:
                KampioenschapSchutterBoog.objects.bulk_create(bulk_lijst)
            del bulk_lijst

            deelcomp_rk.heeft_deelnemerslijst = True
            deelcomp_rk.save()

            # laat de lijsten sorteren en de volgorde bepalen
            KampioenschapMutatie(mutatie=MUTATIE_INITIEEL,
                                 door=door_str,
                                 deelcompetitie=deelcomp_rk).save()

            # stuur de RKO een taak ('ter info')
            rko_namen = list()
            functie_rko = deelcomp_rk.functie
            now = timezone.now()
            taak_deadline = now
            taak_tekst = "Ter info: De deelnemerslijst voor jouw Rayonkampioenschappen zijn zojuist vastgesteld door de BKO"
            taak_log = "[%s] Taak aangemaakt" % now

            for account in functie_rko.accounts.all():
                # maak een taak aan voor deze BKO
                maak_taak(toegekend_aan=account,
                          deadline=taak_deadline,
                          aangemaakt_door=self.request.user,
                          beschrijving=taak_tekst,
                          handleiding_pagina="",
                          log=taak_log,
                          deelcompetitie=deelcomp_rk)
                rko_namen.append(account.volledige_naam())
            # for

            # schrijf in het logboek
            msg = "De deelnemerslijst voor de Rayonkampioenschappen in %s is zojuist vastgesteld." % str(deelcomp_rk.nhb_rayon)
            msg += '\nDe volgende beheerders zijn geïnformeerd via een taak: %s' % ", ".join(rko_namen)
            schrijf_in_logboek(self.request.user, "Competitie", msg)
        # for

    @staticmethod
    def _get_schutters_regios(competitie, rayon_nr):
        """ geeft een lijst met deelnemers terug
            en een totaal-status van de onderliggende regiocompetities: alles afgesloten?
        """

        # schutter moeten uit LAAG_REGIO gehaald worden, uit de 4 regio's van het rayon
        pks = list()
        for deelcomp in (DeelCompetitie
                         .objects
                         .filter(laag=LAAG_REGIO,
                                 competitie=competitie,
                                 nhb_regio__rayon__rayon_nr=rayon_nr)):
            pks.append(deelcomp.pk)
        # for

        deelnemers = (RegioCompetitieSchutterBoog
                      .objects
                      .select_related('klasse__indiv',
                                      'bij_vereniging__regio',
                                      'schutterboog__nhblid')
                      .exclude(schutterboog__nhblid__bij_vereniging=None)   # moet nu lid zijn bij een vereniging
                      .filter(deelcompetitie__in=pks,
                              aantal_scores__gte=6,
                              klasse__indiv__niet_voor_rk_bk=False)         # skip aspiranten
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
            rank += 1
            deelnemer.volgorde = rank
            deelnemer.deelname = DEELNAME_ONBEKEND

            regio_nr = deelnemer.bij_vereniging.regio.regio_nr
            if regio_nr not in regios:
                regios.append(regio_nr)
                deelnemer.kampioen_label = "Kampioen regio %s" % regio_nr
                tup = (regio_nr, deelnemer)
                kampioenen.append(tup)
                deelnemers.pop(nr)
            else:
                # alle schutters overnemen als potentiële reserveschutter
                deelnemer.kampioen_label = ""
                nr += 1
        # while

        if len(kampioenen):
            kampioenen.sort(reverse=True)       # hoogste regionummer bovenaan
            for _, kampioen in kampioenen:
                deelnemers.insert(insert_at, kampioen)
                insert_at += 1
            # for

        return deelnemers


class DoorzettenNaarBKView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de BKO de competitie doorzetten naar de BK fase """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_DOORZETTEN_NAAR_BK

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BKO

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])  # afkappen geeft beveiliging
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk,
                         is_afgesloten=False))
        except (ValueError, Competitie.DoesNotExist):
            raise Resolver404()

        comp.zet_fase()
        if comp.fase < 'M' or comp.fase >= 'P':
            raise Resolver404()

        if comp.fase == 'N':
            # klaar om door te zetten
            context['url_doorzetten'] = reverse('Competitie:bko-doorzetten-naar-bk',
                                                kwargs={'comp_pk': comp.pk})

        context['comp'] = comp

        menu_dynamics(self.request, context, actief='competitie')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Regel toevoegen' gebruikt wordt
            in de RK planning, om een nieuwe wedstrijd toe te voegen.
        """

        try:
            comp_pk = int(kwargs['comp_pk'][:6])  # afkappen geeft beveiliging
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk,
                         is_afgesloten=False))
        except (ValueError, Competitie.DoesNotExist):
            raise Resolver404()

        comp.zet_fase()
        if comp.fase != 'N':
            raise Resolver404()

        # FUTURE: implementeer doorzetten

        return HttpResponseRedirect(reverse('Competitie:kies'))


class VerwijderWedstrijdView(UserPassesTestMixin, View):

    """ Deze view laat een BK wedstrijd verwijderen """

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BKO

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Verwijder' gebruikt wordt
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

        plan = wedstrijd.wedstrijdenplan_set.all()[0]
        try:
            deelcomp = DeelCompetitie.objects.get(plan=plan, laag=LAAG_BK)
        except DeelCompetitie.DoesNotExist:
            raise Resolver404()

        # correcte beheerder?
        _, functie_nu = rol_get_huidige_functie(self.request)
        if deelcomp.functie != functie_nu:
            raise Resolver404()

        # voorkom verwijderen van wedstrijden waar een uitslag aan hangt
        if wedstrijd.uitslag:
            uitslag = wedstrijd.uitslag
            if uitslag and (uitslag.is_bevroren or uitslag.scores.count() > 0):
                raise Resolver404()

        wedstrijd.delete()

        url = reverse('Competitie:bond-planning', kwargs={'deelcomp_pk': deelcomp.pk})
        return HttpResponseRedirect(url)


# class CompetitieAfsluitenView(UserPassesTestMixin, TemplateView):
#
#     """ Met deze view kan de BKO de competitie afsluiten """
#
#     # class variables shared by all instances
#     template_name = TEMPLATE_COMPETITIE_AFSLUITEN
#
#     def test_func(self):
#         """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
#         rol_nu = rol_get_huidige(self.request)
#         return rol_nu == Rollen.ROL_BKO
#
#     def handle_no_permission(self):
#         """ gebruiker heeft geen toegang --> redirect naar het plein """
#         return HttpResponseRedirect(reverse('Plein:plein'))
#
#     def get_context_data(self, **kwargs):
#         """ called by the template system to get the context data for the template """
#         context = super().get_context_data(**kwargs)
#
#         try:
#             comp_pk = int(kwargs['comp_pk'][:6])  # afkappen geeft beveiliging
#             comp = (Competitie
#                     .objects
#                     .get(pk=comp_pk,
#                          is_afgesloten=False))
#         except (ValueError, Competitie.DoesNotExist):
#             raise Resolver404()
#
#         comp.zet_fase()
#         if comp.fase < 'R' or comp.fase >= 'Z':
#             raise Resolver404()
#
#         menu_dynamics(self.request, context, actief='competitie')
#         return context
#
#     def post(self, request, *args, **kwargs):
#         """ Deze functie wordt aangeroepen als de knop 'Regel toevoegen' gebruikt wordt
#             in de RK planning, om een nieuwe wedstrijd toe te voegen.
#         """
#         try:
#             comp_pk = int(kwargs['comp_pk'][:6])  # afkappen geeft beveiliging
#             comp = (Competitie
#                     .objects
#                     .get(pk=comp_pk,
#                          is_afgesloten=False))
#         except (ValueError, Competitie.DoesNotExist):
#             raise Resolver404()
#
#         comp.zet_fase()
#         if comp.fase < 'R' or comp.fase >= 'Z':
#             raise Resolver404()
#
#         return HttpResponseRedirect(reverse('Competitie:kies'))


# end of file
