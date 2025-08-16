# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.shortcuts import render, redirect
from django.utils.formats import localize
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from BasisTypen.models import TemplateCompetitieIndivKlasse, TemplateCompetitieTeamKlasse
from Competitie.models import Competitie
from Competitie.operations import (bepaal_startjaar_nieuwe_competitie, bepaal_klassengrenzen_indiv,
                                   bepaal_klassengrenzen_teams, competitie_klassengrenzen_vaststellen)
from CompBeheer.operations.maak_mutatie import maak_mutatie_competitie_opstarten, maak_mutatie_ag_vaststellen
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from HistComp.models import HistCompSeizoen
from Logboek.models import schrijf_in_logboek
from Score.operations import wanneer_ag_vastgesteld

TEMPLATE_COMPETITIE_INSTELLINGEN = 'compbeheer/bb-instellingen-nieuwe-competitie.dtl'
TEMPLATE_COMPETITIE_AANMAKEN = 'compbeheer/bb-competities-aanmaken.dtl'
TEMPLATE_COMPETITIE_KLASSENGRENZEN_VASTSTELLEN = 'compbeheer/bb-klassengrenzen-vaststellen.dtl'
TEMPLATE_COMPETITIE_AG_VASTSTELLEN = 'compbeheer/bb-ag-vaststellen.dtl'
TEMPLATE_COMPETITIE_SEIZOEN_AFSLUITEN = 'compbeheer/bb-seizoen-afsluiten.dtl'


class InstellingenVolgendeCompetitieView(UserPassesTestMixin, TemplateView):

    """ deze view laat de defaults voor de volgende competitie zien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_INSTELLINGEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_BB

    @staticmethod
    def _get_queryset_indiv_klassen():
        objs = (TemplateCompetitieIndivKlasse
                .objects
                .select_related('boogtype')
                .prefetch_related('leeftijdsklassen')
                .order_by('volgorde'))
        prev = 0
        for klasse in objs:
            groep = klasse.volgorde // 10
            klasse.separate_before = groep != prev
            klasse.lkl_list = [lkl.beschrijving for lkl in klasse.leeftijdsklassen.all()]
            prev = groep
        # for
        return objs

    @staticmethod
    def _get_queryset_teamklassen():
        objs = (TemplateCompetitieTeamKlasse
                .objects
                .select_related('team_type')
                .prefetch_related('team_type__boog_typen')
                .order_by('volgorde'))
        prev = 0
        for klasse in objs:
            groep = klasse.volgorde // 10
            klasse.separate_before = groep != prev
            klasse.boogtypen_list = [boogtype.beschrijving for boogtype in (klasse
                                                                            .team_type
                                                                            .boog_typen
                                                                            .order_by('volgorde'))]
            prev = groep
        # for
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['indiv_klassen'] = self._get_queryset_indiv_klassen()
        context['teamklassen'] = self._get_queryset_teamklassen()

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (None, 'Start competitie')
        )

        return context


class CompetitieAanmakenView(UserPassesTestMixin, TemplateView):

    """ deze view laat de BB een nieuwe competitie opstarten """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_AANMAKEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_BB

    @staticmethod
    def post(request, *args, **kwargs):
        """ deze functie handelt het http-post verzoek af
            (wat volgt uit het drukken op de knop)
            om de nieuwe competitie op te starten.
        """
        account = get_account(request)
        jaar = bepaal_startjaar_nieuwe_competitie()

        snel = str(request.POST.get('snel', ''))[:1]

        # bescherm tegen dubbel aanmaken
        if Competitie.objects.filter(begin_jaar=jaar).count() == 0:
            seizoen = "%s/%s" % (jaar, jaar+1)
            schrijf_in_logboek(account, 'Competitie', 'Aanmaken competities %s' % seizoen)

            # voor concurrency protection, laat de achtergrondtaak de competitie aanmaken
            door_str = "BB %s" % account.volledige_naam()
            door_str = door_str[:149]
            maak_mutatie_competitie_opstarten(door_str, snel == '1')

        return redirect('Competitie:kies')

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        jaar = bepaal_startjaar_nieuwe_competitie()
        context['seizoen'] = "%s/%s" % (jaar, jaar+1)

        # feedback als competitie al aangemaakt is
        if Competitie.objects.filter(begin_jaar=jaar).count() > 0:
            context['bestaat_al'] = True

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:instellingen-volgende-competitie'), 'Start competitie'),
            (None, 'Aanmaken')
        )

        return context


class AGVaststellenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan de BB de aanvangsgemiddelden vaststellen
        HistComp wordt doorzocht op bekende sporterboog en de uitslag wordt overgenomen als AG
    """

    template_name = TEMPLATE_COMPETITIE_AG_VASTSTELLEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_BB

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        context = super().get_context_data(**kwargs)

        afstand = str(kwargs['afstand'])

        if afstand == '18':
            aantal_scores = settings.COMPETITIE_18M_MINIMUM_SCORES_VOOR_AG
        elif afstand == '25':
            aantal_scores = settings.COMPETITIE_25M_MINIMUM_SCORES_VOOR_AG
        else:
            raise Http404('Onbekende afstand')

        # alleen toestaan als de competities in fase A is
        comps = Competitie.objects.filter(is_afgesloten=False, afstand=afstand, klassengrenzen_vastgesteld=False)
        if len(comps) != 1:
            raise Http404('Geen competitie in de juiste fase')
        comp = comps[0]

        context['afstand'] = afstand
        context['aantal_scores'] = aantal_scores

        context['url_vaststellen'] = reverse('CompBeheer:ag-vaststellen-afstand',
                                             kwargs={'afstand': afstand})

        # zoek uit wat de meest recente HistComp is
        histcomps = HistCompSeizoen.objects.order_by('-seizoen').all()
        if len(histcomps) == 0:
            context['geen_histcomp'] = True
        else:
            context['seizoen'] = histcomps[0].seizoen

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}),
                comp.beschrijving.replace(' competitie', '')),
            (None, 'Aanvangsgemiddelden')
        )

        return render(request, self.template_name, context)

    @staticmethod
    def post(request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            --> de beheerder wil de AG's vaststellen
        """
        account = get_account(request)
        afstand = str(kwargs['afstand'])

        # alleen toestaan als de competities in fase A is
        comps = Competitie.objects.filter(is_afgesloten=False, afstand=afstand, klassengrenzen_vastgesteld=False)
        if len(comps) != 1:
            raise Http404('Geen competitie in de juiste fase')
        comp = comps[0]

        schrijf_in_logboek(account, 'Competitie', 'Aanvangsgemiddelden vaststellen voor de %sm competitie' % afstand)

        snel = str(request.POST.get('snel', ''))[:1]

        # voor concurrency protection, laat de achtergrondtaak de competitie aanmaken
        door_str = "BB %s" % account.volledige_naam()
        door_str = door_str[:149]
        maak_mutatie_ag_vaststellen(comp, door_str, snel == '1')

        return redirect('CompBeheer:overzicht', comp_pk=comp.pk)


class KlassengrenzenVaststellenView(UserPassesTestMixin, TemplateView):

    """ deze view laat de klassengrenzen voor de volgende competitie zien,
        aan de hand van de al vastgestelde aanvangsgemiddelden
        De BB kan deze bevestigen, waarna ze aan de competitie toegevoegd worden
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_KLASSENGRENZEN_VASTSTELLEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_BB

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen voor de veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        context['comp'] = comp

        if comp.klassengrenzen_vastgesteld:
            context['al_vastgesteld'] = True
        else:
            context['klassengrenzen_indiv'] = bepaal_klassengrenzen_indiv(comp)
            context['klassengrenzen_teams'] = bepaal_klassengrenzen_teams(comp)
            context['wedstrijdjaar'] = comp.begin_jaar + 1

        datum = wanneer_ag_vastgesteld(comp.afstand)
        if datum:
            context['bb_ag_nieuwste_datum'] = localize(datum.date())
        else:
            context['bb_ag_nieuwste_datum'] = '????'

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Klassengrenzen')
        )

        return render(request, self.template_name, context)

    @staticmethod
    def post(request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            --> de beheerder wil deze klassengrenzen vaststellen
        """

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen voor de veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        if not comp.klassengrenzen_vastgesteld:
            competitie_klassengrenzen_vaststellen(comp)

            account_log = get_account(request)
            schrijf_in_logboek(account_log,
                               'Competitie',
                               'Klassengrenzen vastgesteld voor %s' % comp.beschrijving)

        return redirect('CompBeheer:overzicht', comp_pk=comp.pk)


class SeizoenAfsluitenView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de BKO de competitie afsluiten """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_SEIZOEN_AFSLUITEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_BB

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        begin_jaar = None
        comps = list()      # af te sluiten competities
        for comp in (Competitie
                     .objects
                     .exclude(is_afgesloten=True)
                     .order_by('afstand',
                               'begin_jaar')):      # laagste jaar eerst --> oudste competitie eerst

            if begin_jaar is None or comp.begin_jaar == begin_jaar:
                begin_jaar = comp.begin_jaar
                comp.bepaal_fase()
                comps.append(comp)
        # for

        if len(comps) == 0:
            raise Http404('Geen competitie gevonden')

        context['seizoen'] = '%s/%s' % (begin_jaar, begin_jaar + 1)
        context['comps'] = comps

        context['url_afsluiten'] = reverse('CompBeheer:bb-seizoen-afsluiten')
        for comp in comps:
            if comp.fase_indiv != 'Q' or comp.fase_teams != 'Q':
                context['url_afsluiten'] = None
        # for

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (None, 'Seizoen afsluiten'),
        )

        return context

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Seizoen afsluiten' gebruikt wordt door de BKO.
        """

        begin_jaar = None
        comps = list()      # af te sluiten competities
        for comp in (Competitie
                     .objects
                     .exclude(is_afgesloten=True)
                     .order_by('afstand',
                               'begin_jaar')):      # laagste jaar eerst --> oudste competitie eerst

            if begin_jaar is None or comp.begin_jaar == begin_jaar:
                begin_jaar = comp.begin_jaar
                comp.bepaal_fase()
                comps.append(comp)
        # for

        if len(comps) == 0:
            raise Http404('Geen competitie gevonden')

        for comp in comps:
            if comp.fase_indiv != 'Q' or comp.fase_teams != 'Q':
                raise Http404('Alle competities nog niet in fase Q')
        # for

        for comp in comps:
            comp.is_afgesloten = True
            comp.save(update_fields=['is_afgesloten'])
        # for

        # maak de HistComp uitslagen openbaar voor dit seizoen
        seizoen = '%s/%s' % (comps[0].begin_jaar, comps[0].begin_jaar + 1)
        HistCompSeizoen.objects.filter(seizoen=seizoen, is_openbaar=False).update(is_openbaar=True)

        return HttpResponseRedirect(reverse('Competitie:kies'))


# end of file
