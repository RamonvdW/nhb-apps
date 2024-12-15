# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.definities import MAXIMALE_LEEFTIJD_JEUGD, ORGANISATIE_KHSN
from BasisTypen.models import Leeftijdsklasse
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Sporter.models import Sporter, SporterBoog

TEMPLATE_LEDENLIJST = 'vereniging/ledenlijst.dtl'
TEMPLATE_LEDEN_VOORKEUREN = 'vereniging/leden-voorkeuren.dtl'


class LedenLijstView(UserPassesTestMixin, ListView):

    """ Deze view laat de HWL zijn ledenlijst zien """

    # class variables shared by all instances
    template_name = TEMPLATE_LEDENLIJST
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'
    kruimel = 'Ledenlijst'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None
        self.huidige_jaar = 0
        self.mag_wijzigen = False

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        self.mag_wijzigen = self.rol_nu in (Rol.ROL_SEC, Rol.ROL_HWL)
        return self.functie_nu and self.functie_nu.rol in ('SEC', 'HWL', 'WL')

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        # pak het huidige jaar na conversie naar lokale tijdzone
        # zodat dit ook goed gaat in de laatste paar uren van het jaar
        now = timezone.now()  # is in UTC
        now = timezone.localtime(now)  # convert to active timezone (say Europe/Amsterdam)
        huidige_jaar = now.year
        jeugdgrens = huidige_jaar - MAXIMALE_LEEFTIJD_JEUGD
        self.huidige_jaar = huidige_jaar

        # deel 1: jeugd

        lkls = list()
        for lkl in (Leeftijdsklasse  # pragma: no branch
                    .objects
                    .filter(organisatie=ORGANISATIE_KHSN,
                            min_wedstrijdleeftijd=0)    # exclude veel van de senioren klassen
                    .order_by('volgorde')):             # aspirant eerst

            lkls.append(lkl)
        # for

        prev_lkl = None
        prev_wedstrijdleeftijd = 0
        objs = list()

        # sorteer op geboorte jaar en daarna naam
        for obj in (Sporter
                    .objects
                    .filter(bij_vereniging=self.functie_nu.vereniging)
                    .filter(geboorte_datum__year__gte=jeugdgrens)
                    .select_related('account')
                    .order_by('-geboorte_datum__year',
                              'achternaam',
                              'voornaam')):

            # de wedstrijdleeftijd voor dit hele jaar, gebruik WA methode
            wedstrijdleeftijd = obj.bereken_wedstrijdleeftijd_wa(huidige_jaar)
            obj.leeftijd = wedstrijdleeftijd
            obj.is_jeugd = True

            # de wedstrijdklasse voor dit hele jaar
            if wedstrijdleeftijd == prev_wedstrijdleeftijd:
                obj.leeftijdsklasse = prev_lkl
            else:
                obj.leeftijdsklasse = None      # fallback
                for lkl in lkls:                                            # pragma: no branch
                    if lkl.leeftijd_is_compatible(wedstrijdleeftijd):
                        obj.leeftijdsklasse = lkl
                        # stop op de eerste match: aspirant, cadet, junior, senior
                        break
                # for

                prev_lkl = obj.leeftijdsklasse
                prev_wedstrijdleeftijd = wedstrijdleeftijd

            objs.append(obj)
        # for

        # deel 2: volwassenen

        lkls = list()
        for lkl in (Leeftijdsklasse  # pragma: no branch
                    .objects.filter(organisatie=ORGANISATIE_KHSN,
                                    max_wedstrijdleeftijd=0)    # skip jeugd klassen
                    .order_by('-volgorde')):                    # volgorde: veteraan, master, senior

            lkls.append(lkl)
        # for

        # volwassenen: sorteer op naam
        prev_lkl = None
        prev_wedstrijdleeftijd = 0
        for obj in (Sporter
                    .objects
                    .filter(bij_vereniging=self.functie_nu.vereniging)
                    .filter(geboorte_datum__year__lt=jeugdgrens)
                    .select_related('account')
                    .order_by('achternaam',
                              'voornaam')):

            # de wedstrijdleeftijd voor dit hele jaar, gebruik WA methode
            wedstrijdleeftijd = obj.bereken_wedstrijdleeftijd_wa(huidige_jaar)
            obj.is_jeugd = False

            # de wedstrijdklasse voor dit hele jaar
            if wedstrijdleeftijd == prev_wedstrijdleeftijd:
                obj.leeftijdsklasse = prev_lkl
            else:
                obj.leeftijdsklasse = None      # fallback
                for lkl in lkls:                                            # pragma: no branch
                    if lkl.leeftijd_is_compatible(wedstrijdleeftijd):
                        obj.leeftijdsklasse = lkl
                        # stop op de eerste match: veteraan, master, senior
                        break
                # for

                prev_lkl = obj.leeftijdsklasse
                prev_wedstrijdleeftijd = wedstrijdleeftijd

            if not obj.is_actief_lid:
                obj.leeftijd = huidige_jaar - obj.geboorte_datum.year

            objs.append(obj)
        # for

        # zoek de laatste-inlog bij elk lid
        for sporter in objs:
            # voorkeuren van de sporters aanpassen
            if self.mag_wijzigen:
                sporter.wijzig_url = reverse('Sporter:voorkeuren-sporter',
                                             kwargs={'sporter_pk': sporter.pk})

            if sporter.account:
                if sporter.account.last_login:
                    sporter.laatste_inlog = sporter.account.last_login
                else:
                    sporter.geen_inlog = 2
            else:
                sporter.geen_inlog = 1
        # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['ver'] = self.functie_nu.vereniging

        # splits the ledenlijst op in jeugd, senior en inactief
        jeugd = list()
        senior = list()
        inactief = list()
        for obj in context['object_list']:
            if not obj.is_actief_lid:
                inactief.append(obj)
            elif obj.is_jeugd:
                jeugd.append(obj)
            else:
                senior.append(obj)
        # for

        context['leden_jeugd'] = jeugd
        context['leden_senior'] = senior
        context['leden_inactief'] = inactief
        context['wedstrijdklasse_jaar'] = self.huidige_jaar
        context['toon_wijzig_kolom'] = self.rol_nu in (Rol.ROL_SEC, Rol.ROL_HWL)

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (None, self.kruimel)
        )

        return context


class LedenVoorkeurenView(LedenLijstView):

    """ Deze view laat de HWL de voorkeuren van de zijn leden aanpassen
        en geeft de SEC en WL inzicht in de voorkeuren
    """

    # NOTE: UserPassesTestMixin wordt gedaan door LedenLijstView

    # class variables shared by all instances
    template_name = TEMPLATE_LEDEN_VOORKEUREN
    kruimel = 'Voorkeuren leden'

    def get_queryset(self):
        objs = super().get_queryset()

        sporter_dict = dict()
        for sporter in objs:
            sporter.wedstrijdbogen = list()
            sporter_dict[sporter.lid_nr] = sporter
        # for

        # zoek de bogen informatie bij elk lid
        for sporterboog in (SporterBoog
                            .objects
                            .filter(voor_wedstrijd=True)
                            .select_related('sporter',
                                            'boogtype')
                            .only('sporter__lid_nr',
                                  'boogtype__beschrijving')):
            try:
                sporter = sporter_dict[sporterboog.sporter.lid_nr]
            except KeyError:
                # sporter is niet van deze vereniging
                pass
            else:
                sporter.wedstrijdbogen.append(sporterboog.boogtype.beschrijving)
        # for

        return objs


# end of file
