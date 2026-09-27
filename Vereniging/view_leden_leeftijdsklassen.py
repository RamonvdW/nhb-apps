# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.definities import (MAXIMALE_LEEFTIJD_JEUGD,
                                   GESLACHT_MAN, GESLACHT_VROUW, GESLACHT_ANDERS, GESLACHT_ALLE,
                                   ORGANISATIE_WA, ORGANISATIE_IFAA, ORGANISATIE_KHSN,
                                   BOOGTYPE_AFKORTING_RECURVE)
from BasisTypen.models import Leeftijdsklasse, TemplateCompetitieIndivKlasse
from Functie.rol import rol_get_huidige_functie
from Sporter.models import Sporter, SporterVoorkeuren

TEMPLATE_LEDEN_LEEFTIJDSKLASSEN = 'vereniging/leden-leeftijdsklassen.dtl'


class LedenLeeftijdsklassenView(UserPassesTestMixin, ListView):

    """ Deze view laat de HWL zijn ledenlijst zien """

    # class variables shared by all instances
    template_name = TEMPLATE_LEDEN_LEEFTIJDSKLASSEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

        # pak het huidige jaar na conversie naar lokale tijdzone
        # zodat dit ook goed gaat in de laatste paar uren van het jaar
        now = timezone.now()  # is in UTC
        now = timezone.localtime(now)  # convert to active timezone (say Europe/Amsterdam)
        self.huidige_jaar = now.year
        self.huidige_maand = now.month

        seizoen_begin_jaar = self.huidige_jaar
        if self.huidige_maand <= 6:
            seizoen_begin_jaar -= 1
        self.seizoen = '%s/%s' % (seizoen_begin_jaar, seizoen_begin_jaar+1)

        # WA zijn 8 leeftijdsklassen: M/V x onder18, onder21, senior, 50+
        self.lkls_wa = list(Leeftijdsklasse
                            .objects
                            .filter(organisatie=ORGANISATIE_WA)
                            .order_by('volgorde'))

        # IFAA zijn 12 leeftijdsklassen: M/V x welpen, junioren, jongvolwassen, volwassen, veteraren, senioren
        self.lkls_ifaa = list(Leeftijdsklasse
                              .objects
                              .filter(organisatie=ORGANISATIE_IFAA)
                              .order_by('volgorde'))

        # KHSN is WA plus: M/V x onder12, onder14, .., 60+, veteranen (in buckets van 5 jaar)
        #                  en gemengde klassen (M+V)
        self.lkls_khsn = list(Leeftijdsklasse
                              .objects
                              .filter(organisatie=ORGANISATIE_KHSN)
                              .order_by('volgorde'))

        # bondscompetitie
        lkl_pks = list()
        for ckl in (TemplateCompetitieIndivKlasse
                    .objects
                    .prefetch_related('leeftijdsklassen')
                    .filter(gebruik_18m=True,
                            boogtype__afkorting=BOOGTYPE_AFKORTING_RECURVE)):

            for lkl in ckl.leeftijdsklassen.all():
                pk = lkl.pk
                if pk not in lkl_pks:
                    lkl_pks.append(pk)
            # for
        # for

        alle_lkl = list()
        for lkl in (Leeftijdsklasse
                    .objects
                    .filter(pk__in=lkl_pks)
                    .order_by('-volgorde')):     # oudste klasse eerst (jongste optie overschrijf oudere)

            if lkl.max_wedstrijdleeftijd == 0:
                lkl.max_wedstrijdleeftijd = 125

            # volgende leeftijdsklasse gaat verder waar deze ophoudt
            alle_lkl.append(lkl)
        # for

        # maak de look-up tabel
        self.lkls_comp_leeftijd2tekst = dict()  # [leeftijd] = beschrijving

        for lkl in alle_lkl:
            for leeftijd in range(lkl.min_wedstrijdleeftijd, lkl.max_wedstrijdleeftijd + 1):
                beschrijving = lkl.beschrijving

                if lkl.wedstrijd_geslacht == GESLACHT_ALLE:
                    self.lkls_comp_leeftijd2tekst[(leeftijd, GESLACHT_MAN)] = beschrijving
                    self.lkls_comp_leeftijd2tekst[(leeftijd, GESLACHT_VROUW)] = beschrijving
                    self.lkls_comp_leeftijd2tekst[(leeftijd, GESLACHT_ANDERS)] = beschrijving
                else:
                    self.lkls_comp_leeftijd2tekst[(leeftijd, lkl.wedstrijd_geslacht)] = beschrijving
            # for
        # for

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.functie_nu.rol in ('SEC', 'HWL', 'WL', 'LA')

    def _zet_lkl_wa(self, lid: Sporter):
        # de wedstrijdleeftijd voor dit hele jaar, gebruik WA methode
        wedstrijdleeftijd = lid.bereken_wedstrijdleeftijd_wa(self.huidige_jaar)
        # lid.leeftijd = wedstrijdleeftijd

        # de wedstrijdklasse voor dit hele jaar
        lkls = list()
        for lkl in self.lkls_wa:
            if lkl.wedstrijd_geslacht == lid.geslacht:
                if lkl.leeftijd_is_compatible(wedstrijdleeftijd):
                    if lkl.beschrijving not in lkls:
                        lkls.append(lkl.beschrijving)
        # for

        lid.lkl_wa = "\n".join(lkls) or '**X'

    def _zet_lkl_ifaa(self, lid: Sporter):
        leeftijd = self.huidige_jaar - lid.geboorte_datum.year

        matches = list()
        for lkl in self.lkls_ifaa:
            if lkl.wedstrijd_geslacht == GESLACHT_ALLE or lkl.wedstrijd_geslacht == lid.geslacht:
                match = ''

                # tot verjaardag lid
                if lkl.min_wedstrijdleeftijd <= leeftijd:
                    if lkl.max_wedstrijdleeftijd == 0 or leeftijd <= lkl.max_wedstrijdleeftijd:
                        match = lkl.beschrijving

                # vanaf verjaardag lid
                if not match:
                    leeftijd += 1
                    if lkl.min_wedstrijdleeftijd <= leeftijd:
                        if lkl.max_wedstrijdleeftijd == 0 or leeftijd <= lkl.max_wedstrijdleeftijd:
                            match = lkl.beschrijving

                if match and match not in matches:
                    matches.append(match)
        # for

        lid.lkl_ifaa = "\n".join(matches) or '**X'

    def _zet_lkl_khsn(self, lid: Sporter):
        # de wedstrijdleeftijd voor dit hele jaar, gebruik WA methode
        wedstrijdleeftijd = lid.bereken_wedstrijdleeftijd_wa(self.huidige_jaar)
        # lid.leeftijd = wedstrijdleeftijd

        # de wedstrijdklasse voor dit hele jaar
        lkls = list()
        for lkl in self.lkls_khsn:
            if lkl.wedstrijd_geslacht == GESLACHT_ALLE or lkl.wedstrijd_geslacht == lid.geslacht:
                if lkl.leeftijd_is_compatible(wedstrijdleeftijd):
                    if lkl.beschrijving not in lkls:
                        lkls.append(lkl.beschrijving)
        # for

        lid.lkl_khsn = "\n".join(lkls)

    def _zet_lkl_comp(self, lid: Sporter):
        # bondscompetitie heeft gender-neutrale klassen, behalve voor Onder 12 en Onder 14
        # de meeste sporters met geslacht 'anders' zullen dus in een gender-neutrale klasse komen
        # een jonge sporter met geslacht 'anders' die nog geen wedstrijdgeslacht gekozen heeft,
        # die moeten we dus forceren in een van de klasse.
        geslacht = lid.geslacht
        if geslacht == GESLACHT_ANDERS:
            geslacht = GESLACHT_MAN

        eerste_jaar = self.huidige_jaar
        if self.huidige_maand <= 6:
            # toon voor seizoen vorig-jaar/dit-jaar
            eerste_jaar -= 1
        else:
            # toon voor seizoen dit-jaar/volgend-jaar
            pass

        wedstrijdleeftijd = eerste_jaar - lid.geboorte_datum.year
        wedstrijdleeftijd += 1  # neem 2e jaar van de competitie

        lid.lkl_comp = self.lkls_comp_leeftijd2tekst[(wedstrijdleeftijd, geslacht)]

    def get_queryset(self):
        """ retourneer twee lijsten met Sporters: jeugd en senioren
            in elke object zijn de lkl_* velden toegevoegd
        """

        objs = list()

        # doe 1 grote query van sportervoorkeuren
        lidnr2voorkeuren = dict()
        for voorkeuren in (SporterVoorkeuren
                           .objects
                           .select_related('sporter')
                           .filter(sporter__bij_vereniging=self.functie_nu.vereniging)):
            lidnr2voorkeuren[voorkeuren.sporter.lid_nr] = voorkeuren
        # for

        # sorteer op geboorte jaar en daarna naam
        for lid in (Sporter
                    .objects
                    .filter(bij_vereniging=self.functie_nu.vereniging,
                            is_actief_lid=True)
                    .select_related('account')
                    .order_by('-geboorte_datum__year',
                              'achternaam',
                              'voornaam')):

            if lid.geslacht == GESLACHT_ANDERS:
                voorkeuren = lidnr2voorkeuren.get(lid.lid_nr, None)
                if voorkeuren:
                    assert isinstance(voorkeuren, SporterVoorkeuren)
                    if voorkeuren.wedstrijd_geslacht_gekozen:
                        lid.geslacht = voorkeuren.wedstrijd_geslacht

            self._zet_lkl_wa(lid)
            self._zet_lkl_ifaa(lid)
            self._zet_lkl_khsn(lid)
            self._zet_lkl_comp(lid)

            objs.append(lid)
        # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['ver'] = self.functie_nu.vereniging
        context['seizoen'] = self.seizoen

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (None, 'Leeftijdsklassen')
        )

        return context


# end of file
