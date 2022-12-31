# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import (Competitie, DeelCompetitie, CompetitieMutatie, DeelKampioenschap, DEEL_RK,
                               MUTATIE_AFSLUITEN_REGIOCOMP)
from Functie.models import Rollen
from Functie.rol import rol_get_huidige, rol_get_huidige_functie
from Plein.menu import menu_dynamics


TEMPLATE_COMPETITIE_DOORZETTEN_NAAR_RK = 'compbeheer/bko-doorzetten-naar-rk.dtl'
TEMPLATE_COMPETITIE_DOORZETTEN_NAAR_BK = 'compbeheer/bko-doorzetten-naar-bk.dtl'
TEMPLATE_COMPETITIE_DOORZETTEN_VOORBIJ_BK = 'compbeheer/bko-doorzetten-voorbij-bk.dtl'


class DoorzettenNaarRKView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de BKO de competitie doorzetten naar de RK fase """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_DOORZETTEN_NAAR_RK
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_BKO

    @staticmethod
    def _get_regio_status(competitie):
        # sporters komen uit de 4 regio's van het rayon
        regio_deelcomps = (DeelCompetitie
                           .objects
                           .filter(competitie=competitie)
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
                    if obj.huidige_team_ronde <= 7:
                        obj.status_str += ' (team ronde %s)' % obj.huidige_team_ronde
                    elif obj.huidige_team_ronde == 99:
                        obj.status_str += ' / Teams klaar'
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
            context['url_doorzetten'] = reverse('CompBeheer:bko-doorzetten-naar-rk',
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
    permission_denied_message = 'Geen toegang'

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
            context['url_doorzetten'] = reverse('CompBeheer:bko-doorzetten-naar-bk',
                                                kwargs={'comp_pk': comp.pk})
        else:
            # bepaal de status van elk rayon
            context['rk_status'] = deelkamps = (DeelKampioenschap
                                                .objects
                                                .select_related('nhb_rayon')
                                                .filter(competitie=comp,
                                                        deel=DEEL_RK))
            for deelkamp in deelkamps:
                deelkamp.rayon_str = 'Rayon %s' % deelkamp.nhb_rayon.rayon_nr
                if deelkamp.is_afgesloten:
                    deelkamp.status_str = "Afgesloten"
                    deelkamp.status_groen = True
                else:
                    deelkamp.status_str = "Actief"

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
    permission_denied_message = 'Geen toegang'

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

        context['url_doorzetten'] = reverse('CompBeheer:bko-doorzetten-voorbij-bk', kwargs={'comp_pk': comp.pk})

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
