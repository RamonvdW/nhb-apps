# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils import timezone
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige_functie
from BasisTypen.models import LeeftijdsKlasse, MAXIMALE_LEEFTIJD_JEUGD
from NhbStructuur.models import NhbLid
from Schutter.models import SchutterBoog


TEMPLATE_LEDENLIJST = 'vereniging/ledenlijst.dtl'
TEMPLATE_LEDEN_VOORKEUREN = 'vereniging/leden-voorkeuren.dtl'


class LedenLijstView(UserPassesTestMixin, ListView):

    """ Deze view laat de HWL zijn ledenlijst zien """

    # class variables shared by all instances
    template_name = TEMPLATE_LEDENLIJST

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        _, functie_nu = rol_get_huidige_functie(self.request)
        return functie_nu and functie_nu.rol in ('SEC', 'HWL', 'WL')

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        huidige_jaar = timezone.now().year  # TODO: check for correctness in last hours of the year (due to timezone)
        jeugdgrens = huidige_jaar - MAXIMALE_LEEFTIJD_JEUGD
        self._huidige_jaar = huidige_jaar

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        qset = NhbLid.objects.filter(bij_vereniging=functie_nu.nhb_ver)

        objs = list()

        prev_lkl = None
        prev_wedstrijdleeftijd = 0

        # sorteer op geboorte jaar en daarna naam
        for obj in (NhbLid
                    .objects
                    .filter(bij_vereniging=functie_nu.nhb_ver)
                    .filter(geboorte_datum__year__gte=jeugdgrens)
                    .order_by('-geboorte_datum__year', 'achternaam', 'voornaam')):

            # de wedstrijdleeftijd voor dit hele jaar
            wedstrijdleeftijd = huidige_jaar - obj.geboorte_datum.year
            obj.leeftijd = wedstrijdleeftijd

            # de wedstrijdklasse voor dit hele jaar
            if wedstrijdleeftijd == prev_wedstrijdleeftijd:
                obj.leeftijdsklasse = prev_lkl
            else:
                obj.leeftijdsklasse = LeeftijdsKlasse.objects.filter(
                                max_wedstrijdleeftijd__gte=wedstrijdleeftijd,
                                geslacht='M').order_by('max_wedstrijdleeftijd')[0]
                prev_lkl = obj.leeftijdsklasse
                prev_wedstrijdleeftijd = wedstrijdleeftijd

            objs.append(obj)
        # for

        # volwassenen
        # sorteer op naam
        for obj in (NhbLid
                    .objects
                    .filter(bij_vereniging=functie_nu.nhb_ver)
                    .filter(geboorte_datum__year__lt=jeugdgrens)
                    .order_by('achternaam', 'voornaam')):
            obj.leeftijdsklasse = None

            if not obj.is_actief_lid:
                obj.leeftijd = huidige_jaar - obj.geboorte_datum.year

            objs.append(obj)
        # for

        # zoek de laatste-inlog bij elk lid
        for nhblid in objs:
            # HWL mag de voorkeuren van de schutters aanpassen
            if rol_nu == Rollen.ROL_HWL:
                nhblid.wijzig_url = reverse('Schutter:voorkeuren-nhblid', kwargs={'nhblid_pk': nhblid.pk})

            if nhblid.account:
                nhblid.laatste_inlog = nhblid.account.last_login
            else:
                nhblid.geen_inlog = 1
        # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        context['nhb_ver'] = functie_nu.nhb_ver

        # splits the ledenlijst op in jeugd, senior en inactief
        jeugd = list()
        senior = list()
        inactief = list()
        for obj in context['object_list']:
            if not obj.is_actief_lid:
                inactief.append(obj)
            elif obj.leeftijdsklasse:
                jeugd.append(obj)
            else:
                senior.append(obj)
        # for

        context['leden_jeugd'] = jeugd
        context['leden_senior'] = senior
        context['leden_inactief'] = inactief
        context['wedstrijdklasse_jaar'] = self._huidige_jaar
        context['toon_wijzig_kolom'] = (rol_nu == Rollen.ROL_HWL)

        menu_dynamics(self.request, context, actief='vereniging')
        return context


class LedenVoorkeurenView(LedenLijstView):

    """ Deze view laat de HWL de voorkeuren van de zijn leden aanpassen
        en geeft de SEC en WL inzicht in de voorkeuren
    """

    # NOTE: UserPassesTestMixin wordt gedaan door LedenLijstView

    # class variables shared by all instances
    template_name = TEMPLATE_LEDEN_VOORKEUREN

    def get_queryset(self):
        objs = super().get_queryset()

        nhblid_dict = dict()
        for nhblid in objs:
            nhblid.wedstrijdbogen = list()
            nhblid_dict[nhblid.nhb_nr] = nhblid
        # for

        # zoek de bogen informatie bij elk lid
        for schutterboog in (SchutterBoog
                             .objects
                             .filter(voor_wedstrijd=True)
                             .select_related('nhblid', 'boogtype')
                             .only('nhblid__nhb_nr', 'boogtype__beschrijving')):
            try:
                nhblid = nhblid_dict[schutterboog.nhblid.nhb_nr]
            except KeyError:
                # nhblid niet van deze vereniging
                pass
            else:
                nhblid.wedstrijdbogen.append(schutterboog.boogtype.beschrijving)
        # for

        return objs


# end of file
