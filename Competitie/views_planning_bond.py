# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie
from Plein.menu import menu_dynamics
from .models import (Competitie, CompetitieMatch,
                     LAAG_REGIO, LAAG_RK, LAAG_BK, DeelCompetitie,
                     CompetitieMutatie,
                     MUTATIE_AFSLUITEN_REGIOCOMP)


TEMPLATE_COMPETITIE_PLANNING_BOND = 'competitie/planning-landelijk.dtl'
TEMPLATE_COMPETITIE_DOORZETTEN_NAAR_RK = 'competitie/bko-doorzetten-naar-rk.dtl'
TEMPLATE_COMPETITIE_DOORZETTEN_NAAR_BK = 'competitie/bko-doorzetten-naar-bk.dtl'
TEMPLATE_COMPETITIE_DOORZETTEN_VOORBIJ_BK = 'competitie/bko-doorzetten-voorbij-bk.dtl'


class BondPlanningView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de planning voor een competitie op het landelijke niveau """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_PLANNING_BOND
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO)

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
            raise Http404('Verkeerde competitie (1)')

        if self.rol_nu == Rollen.ROL_BKO:
            if deelcomp_bk.competitie.afstand != self.functie_nu.comp_type:
                raise Http404('Verkeerde competitie (2)')

        context['deelcomp_bk'] = deelcomp_bk

        context['rayon_deelcomps'] = (DeelCompetitie
                                      .objects
                                      .filter(laag=LAAG_RK,
                                              competitie=deelcomp_bk.competitie)
                                      .order_by('nhb_rayon__rayon_nr'))

        comp = deelcomp_bk.competitie

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Planning')
        )

        menu_dynamics(self.request, context)
        return context


class DoorzettenNaarRKView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de BKO de competitie doorzetten naar de RK fase """

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
                # nog actief
                obj.status_str = "Actief"
                if obj.regio_organiseert_teamcompetitie:
                    # check hoever deze regio is met de teamcompetitie rondes
                    if obj.huidige_team_ronde < 8:
                        obj.status_str += ' (team ronde %s)' % obj.huidige_team_ronde
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

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}),
                comp.beschrijving.replace(' competitie', '')),
            (None, 'Doorzetten')
        )

        menu_dynamics(self.request, context)
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
        else:
            # bepaal de status van elk rayon
            context['rk_status'] = deelcomps = DeelCompetitie.objects.select_related('nhb_rayon').filter(competitie=comp, laag=LAAG_RK)
            for deelcomp in deelcomps:
                deelcomp.rayon_str = 'Rayon %s' % deelcomp.nhb_rayon.rayon_nr
                if deelcomp.is_afgesloten:
                    deelcomp.status_str = "Afgesloten"
                    deelcomp.status_groen = True
                else:
                    deelcomp.status_str = "Actief"

        context['comp'] = comp

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Competitie doorzetten')
        )

        menu_dynamics(self.request, context)
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


class DoorzettenVoorbijBKView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de BKO de BK wedstrijden afsluiten """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_DOORZETTEN_VOORBIJ_BK
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.functie_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
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

        # correcte beheerder?
        if comp.afstand != self.functie_nu.comp_type:
            raise PermissionDenied()

        comp.bepaal_fase()
        if comp.fase != 'R':
            raise Http404('Verkeerde competitie fase')

        context['url_doorzetten'] = reverse('Competitie:bko-doorzetten-voorbij-bk', kwargs={'comp_pk': comp.pk})

        menu_dynamics(self.request, context)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'BK afsluiten' gebruikt wordt door de BKO.
        """
        try:
            comp_pk = int(kwargs['comp_pk'][:6])  # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk,
                         is_afgesloten=False))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        # correcte beheerder?
        if comp.afstand != self.functie_nu.comp_type:
            raise PermissionDenied()

        comp.bepaal_fase()
        if comp.fase != 'R':
            raise Http404('Verkeerde competitie fase')

        comp.alle_bks_afgesloten = True
        comp.save(update_fields=['alle_bks_afgesloten'])

        return HttpResponseRedirect(reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}))


# end of file
