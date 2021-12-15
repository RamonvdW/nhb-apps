# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie
from Plein.menu import menu_dynamics
from .models import (Competitie,
                     LAAG_REGIO, LAAG_RK, LAAG_BK, DeelCompetitie,
                     CompetitieMutatie,
                     MUTATIE_AFSLUITEN_REGIOCOMP)
from Wedstrijden.models import CompetitieWedstrijd


TEMPLATE_COMPETITIE_PLANNING_BOND = 'competitie/planning-landelijk.dtl'
TEMPLATE_COMPETITIE_DOORZETTEN_NAAR_RK = 'competitie/bko-doorzetten-naar-rk.dtl'
TEMPLATE_COMPETITIE_DOORZETTEN_NAAR_BK = 'competitie/bko-doorzetten-naar-bk.dtl'
TEMPLATE_COMPETITIE_AFSLUITEN = 'competitie/bko-afsluiten-competitie.dtl'


class BondPlanningView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de planning voor een competitie op het landelijke niveau """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_PLANNING_BOND
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen voor de veiligheid
            deelcomp_bk = (DeelCompetitie
                           .objects
                           .select_related('competitie')
                           .get(pk=deelcomp_pk))
        except (KeyError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        if deelcomp_bk.laag != LAAG_BK:
            raise Http404('Verkeerde competitie')

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
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_BKO

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
            comp_pk = int(kwargs['comp_pk'][:6])  # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk,
                         is_afgesloten=False))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        if comp.afstand != self.functie_nu.comp_type:
            raise Http404('Verkeerde competitie')

        comp.bepaal_fase()
        if comp.fase < 'E' or comp.fase >= 'K':
            # kaartjes werd niet getoond, dus je zou hier niet moeten zijn
            raise Http404('Verkeerde competitie fase')

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
            comp_pk = int(kwargs['comp_pk'][:6])  # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk,
                         is_afgesloten=False))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        if comp.fase != 'G':
            raise Http404('Verkeerde competitie fase')

        # fase G garandeert dat alle regiocompetities afgesloten zijn

        # vraag de achtergrond taak alle stappen van het afsluiten uit te voeren
        # dit voorkomt ook race conditions / dubbel uitvoeren
        account = self.request.user
        door_str = "BKO %s" % account.volledige_naam()

        CompetitieMutatie(mutatie=MUTATIE_AFSLUITEN_REGIOCOMP,
                          door=door_str,
                          competitie=comp).save()

        return HttpResponseRedirect(reverse('Competitie:kies'))


class DoorzettenNaarBKView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de BKO de competitie doorzetten naar de BK fase """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_DOORZETTEN_NAAR_BK
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BKO

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])  # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk,
                         is_afgesloten=False))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        if comp.fase < 'M' or comp.fase >= 'P':
            raise Http404('Verkeerde competitie fase')

        if comp.fase == 'N':
            # klaar om door te zetten
            context['url_doorzetten'] = reverse('Competitie:bko-doorzetten-naar-bk',
                                                kwargs={'comp_pk': comp.pk})

        context['comp'] = comp

        menu_dynamics(self.request, context, actief='competitie')
        return context

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Regel toevoegen' gebruikt wordt
            in de RK planning, om een nieuwe wedstrijd toe te voegen.
        """

        try:
            comp_pk = int(kwargs['comp_pk'][:6])  # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk,
                         is_afgesloten=False))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        if comp.fase != 'N':
            raise Http404('Verkeerde competitie fase')

        # FUTURE: implementeer doorzetten

        return HttpResponseRedirect(reverse('Competitie:kies'))


class VerwijderWedstrijdView(UserPassesTestMixin, View):

    """ Deze view laat een BK wedstrijd verwijderen """

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_BKO

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
            deelcomp = DeelCompetitie.objects.get(plan=plan, laag=LAAG_BK)
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

        url = reverse('Competitie:bond-planning', kwargs={'deelcomp_pk': deelcomp.pk})
        return HttpResponseRedirect(url)


# class CompetitieAfsluitenView(UserPassesTestMixin, TemplateView):
#
#     """ Met deze view kan de BKO de competitie afsluiten """
#
#     # class variables shared by all instances
#     template_name = TEMPLATE_COMPETITIE_AFSLUITEN
#     raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
#
#     def test_func(self):
#         """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
#         rol_nu = rol_get_huidige(self.request)
#         return rol_nu == Rollen.ROL_BKO
#
#     def get_context_data(self, **kwargs):
#         """ called by the template system to get the context data for the template """
#         context = super().get_context_data(**kwargs)
#
#         try:
#             comp_pk = int(kwargs['comp_pk'][:6])  # afkappen voor de veiligheid
#             comp = (Competitie
#                     .objects
#                     .get(pk=comp_pk,
#                          is_afgesloten=False))
#         except (ValueError, Competitie.DoesNotExist):
#             raise Http404('Competitie niet gevonden')
#
#         comp.zet_fase()
#         if comp.fase < 'R' or comp.fase >= 'Z':
#             raise Http404('Verkeerde competitie fase')
#
#         menu_dynamics(self.request, context, actief='competitie')
#         return context
#
#     def post(self, request, *args, **kwargs):
#         """ Deze functie wordt aangeroepen als de knop 'Regel toevoegen' gebruikt wordt
#             in de RK planning, om een nieuwe wedstrijd toe te voegen.
#         """
#         try:
#             comp_pk = int(kwargs['comp_pk'][:6])  # afkappen voor de veiligheid
#             comp = (Competitie
#                     .objects
#                     .get(pk=comp_pk,
#                          is_afgesloten=False))
#         except (ValueError, Competitie.DoesNotExist):
#             raise Http404('Competitie niet gevonden')
#
#         comp.zet_fase()
#         if comp.fase < 'R' or comp.fase >= 'Z':
#             raise Http404('Verkeerde competitie fase)
#
#         return HttpResponseRedirect(reverse('Competitie:kies'))


# end of file
