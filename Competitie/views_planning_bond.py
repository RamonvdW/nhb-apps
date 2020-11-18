# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import Resolver404, reverse
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige
from Logboek.models import schrijf_in_logboek
from Plein.menu import menu_dynamics
from Taken.models import Taak
from .models import (Competitie,
                     LAAG_REGIO, LAAG_RK, LAAG_BK, DeelCompetitie,
                     RegioCompetitieSchutterBoog, KampioenschapSchutterBoog)


TEMPLATE_COMPETITIE_DOORZETTEN_NAAR_RK = 'competitie/bko-doorzetten-naar-rk.dtl'
TEMPLATE_COMPETITIE_DOORZETTEN_NAAR_BK = 'competitie/bko-doorzetten-naar-bk.dtl'
TEMPLATE_COMPETITIE_AFSLUITEN = 'competitie/bko-afsluiten-competitie.dtl'


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

        if comp.fase == 'G':
            # klaar om door te zetten
            context['url_doorzetten'] = reverse('Competitie:bko-doorzetten-naar-rk',
                                                kwargs={'comp_pk': comp.pk})

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
        if comp.fase != 'G':
            raise Resolver404()

        # fase G garandeert dat alle regiocompetities afgesloten zijn

        self._maak_deelnemerslijst_rks(comp)

        # ga door naar de RK fase
        comp.alle_regiocompetities_afgesloten = True
        comp.save()

        return HttpResponseRedirect(reverse('Competitie:overzicht'))

    def _maak_deelnemerslijst_rks(self, comp):
        for deelcomp_rk in (DeelCompetitie
                            .objects
                            .select_related('nhb_rayon')
                            .filter(competitie=comp,
                                    laag=LAAG_RK)
                            .order_by('nhb_rayon__rayon_nr')):

            deelnemers = self._get_schutters_regios(comp, deelcomp_rk.nhb_rayon.rayon_nr)

            # schrijf all deze schutters in voor het RK
            # kampioenen als eerste in de lijst, daarna aflopend gesorteerd op gemiddelde
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

            # stuur de RKO een taak ('ter info')
            rko_namen = list()
            functie_rko = deelcomp_rk.functie
            now = timezone.now()
            taak_deadline = now
            taak_tekst = "Ter info: De deelnemerslijst voor jouw Rayonkampioenschappen zijn zojuist vastgesteld door de BKO"
            taak_log = "[%s] Taak aangemaakt" % now

            for account in functie_rko.accounts.all():
                # maak een taak aan voor deze BKO
                taak = Taak(toegekend_aan=account,
                            deadline=taak_deadline,
                            aangemaakt_door=self.request.user,
                            beschrijving=taak_tekst,
                            handleiding_pagina="",
                            log=taak_log,
                            deelcompetitie=deelcomp_rk)
                taak.save()
                rko_namen.append(account.volledige_naam())
            # for

            # schrijf in het logboek
            msg = "De deelnemerslijst voor de Rayonkampioenschappen in %s is zojuist vastgesteld." % str(deelcomp_rk.nhb_rayon)
            msg += '\nDe volgende beheerders zijn geïnformeerd via een taak: %s' % ", ".join(rko_namen)
            schrijf_in_logboek(self.request.user, "Competitie", msg)
        # for

    def _get_schutters_regios(self, competitie, rayon_nr):
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
                      .filter(deelcompetitie__in=pks,
                              aantal_scores__gte=6,
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

        return HttpResponseRedirect(reverse('Competitie:overzicht'))


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
#         return HttpResponseRedirect(reverse('Competitie:overzicht'))


# end of file
