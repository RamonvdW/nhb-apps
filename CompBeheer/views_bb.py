# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.db.models import F
from django.shortcuts import render, redirect
from django.utils.formats import localize
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import TemplateCompetitieIndivKlasse, TemplateCompetitieTeamKlasse
from Competitie.definities import (DEEL_RK, DEELNAME_NEE, MUTATIE_COMPETITIE_OPSTARTEN,
                                   MUTATIE_AG_VASTSTELLEN_18M, MUTATIE_AG_VASTSTELLEN_25M)
from Competitie.models import (Competitie, CompetitieMutatie,
                               RegiocompetitieSporterBoog, RegiocompetitieTeam, KampioenschapSporterBoog)
from Competitie.operations import (bepaal_startjaar_nieuwe_competitie, bepaal_klassengrenzen_indiv,
                                   bepaal_klassengrenzen_teams, competitie_klassengrenzen_vaststellen)
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige
from HistComp.models import HistCompetitie
from Logboek.models import schrijf_in_logboek
from Overig.background_sync import BackgroundSync
from Plein.menu import menu_dynamics
from Score.operations import wanneer_ag_vastgesteld
from Sporter.models import Sporter
import time


TEMPLATE_COMPETITIE_INSTELLINGEN = 'compbeheer/bb-instellingen-nieuwe-competitie.dtl'
TEMPLATE_COMPETITIE_AANMAKEN = 'compbeheer/bb-competities-aanmaken.dtl'
TEMPLATE_COMPETITIE_KLASSENGRENZEN_VASTSTELLEN = 'compbeheer/bb-klassengrenzen-vaststellen.dtl'
TEMPLATE_COMPETITIE_AG_VASTSTELLEN = 'compbeheer/bb-ag-vaststellen.dtl'
TEMPLATE_COMPETITIE_SEIZOEN_AFSLUITEN = 'compbeheer/bb-seizoen-afsluiten.dtl'
TEMPLATE_COMPETITIE_STATISTIEK = 'compbeheer/bb-statistiek.dtl'

mutatie_ping = BackgroundSync(settings.BACKGROUND_SYNC__REGIOCOMP_MUTATIES)


class InstellingenVolgendeCompetitieView(UserPassesTestMixin, TemplateView):

    """ deze view laat de defaults voor de volgende competitie zien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_INSTELLINGEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BB

    @staticmethod
    def _get_queryset_indivklassen():
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
            klasse.boogtypen_list = [boogtype.beschrijving for boogtype in klasse.team_type.boog_typen.order_by('volgorde')]
            prev = groep
        # for
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['indivklassen'] = self._get_queryset_indivklassen()
        context['teamklassen'] = self._get_queryset_teamklassen()

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (None, 'Start competitie')
        )

        menu_dynamics(self.request, context)
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
        return rol_nu == Rollen.ROL_BB

    @staticmethod
    def post(request, *args, **kwargs):
        """ deze functie handelt het http-post verzoek af
            (wat volgt uit het drukken op de knop)
            om de nieuwe competitie op te starten.
        """
        account = request.user
        jaar = bepaal_startjaar_nieuwe_competitie()

        # bescherm tegen dubbel aanmaken
        if Competitie.objects.filter(begin_jaar=jaar).count() == 0:
            seizoen = "%s/%s" % (jaar, jaar+1)
            schrijf_in_logboek(account, 'Competitie', 'Aanmaken competities %s' % seizoen)

            # voor concurrency protection, laat de achtergrondtaak de competitie aanmaken
            door_str = "BB %s" % account.volledige_naam()
            mutatie = CompetitieMutatie(mutatie=MUTATIE_COMPETITIE_OPSTARTEN,
                                        door=door_str)
            mutatie.save()

            mutatie_ping.ping()

            snel = str(request.POST.get('snel', ''))[:1]
            if snel != '1':         # pragma: no cover
                # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
                interval = 0.2      # om steeds te verdubbelen
                total = 0.0         # om een limiet te stellen
                while not mutatie.is_verwerkt and total + interval <= 3.0:
                    time.sleep(interval)
                    total += interval   # 0.0 --> 0.2, 0.6, 1.4, 3.0
                    interval *= 2       # 0.2 --> 0.4, 0.8, 1.6, 3.2
                    mutatie = CompetitieMutatie.objects.get(pk=mutatie.pk)
                # while

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
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('CompBeheer:instellingen-volgende-competitie'), 'Start competitie'),
            (None, 'Aanmaken')
        )

        menu_dynamics(self.request, context)
        return context


class AGVaststellenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan de BB de aanvangsgemiddelden vaststellen
        HistComp wordt doorzocht op bekende schutter-boog en de uitslag wordt overgenomen als AG
    """

    template_name = TEMPLATE_COMPETITIE_AG_VASTSTELLEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BB

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
        histcomps = HistCompetitie.objects.order_by('-seizoen').all()
        if len(histcomps) == 0:
            context['geen_histcomp'] = True
        else:
            context['seizoen'] = histcomps[0].seizoen

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}),
                comp.beschrijving.replace(' competitie', '')),
            (None, 'Aanvangsgemiddelden')
        )

        menu_dynamics(self.request, context)
        return render(request, self.template_name, context)

    @staticmethod
    def post(request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            --> de beheerder wil de AG's vaststellen
        """
        account = request.user
        afstand = str(kwargs['afstand'])

        if afstand == '18':
            mutatie = MUTATIE_AG_VASTSTELLEN_18M
        elif afstand == '25':
            mutatie = MUTATIE_AG_VASTSTELLEN_25M
        else:
            raise Http404('Onbekende afstand')

        # alleen toestaan als de competities in fase A is
        comps = Competitie.objects.filter(is_afgesloten=False, afstand=afstand, klassengrenzen_vastgesteld=False)
        if len(comps) != 1:
            raise Http404('Geen competitie in de juiste fase')
        comp = comps[0]

        schrijf_in_logboek(account, 'Competitie', 'Aanvangsgemiddelden vaststellen voor de %sm competitie' % afstand)

        # voor concurrency protection, laat de achtergrondtaak de competitie aanmaken
        door_str = "BB %s" % account.volledige_naam()
        mutatie = CompetitieMutatie(mutatie=mutatie,
                                    door=door_str)
        mutatie.save()

        mutatie_ping.ping()

        snel = str(request.POST.get('snel', ''))[:1]
        if snel != '1':             # pragma: no cover
            # wacht maximaal 7 seconden tot de mutatie uitgevoerd is
            total = 0         # om een limiet te stellen
            while not mutatie.is_verwerkt and total < 7:
                time.sleep(1)
                total += 1
                mutatie = CompetitieMutatie.objects.get(pk=mutatie.pk)
            # while

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
        return rol_nu == Rollen.ROL_BB

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
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}),
                comp.beschrijving.replace(' competitie', '')),
            (None, 'Klassegrenzen')
        )

        menu_dynamics(self.request, context)
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

            schrijf_in_logboek(request.user,
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
        return rol_nu == Rollen.ROL_BB

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
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (None, 'Seizoen afsluiten'),
        )

        menu_dynamics(self.request, context)
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
        for histcomp in HistCompetitie.objects.filter(seizoen=seizoen, is_openbaar=False):
            histcomp.is_openbaar = True
            histcomp.save(update_fields=['is_openbaar'])
        # for

        return HttpResponseRedirect(reverse('Competitie:kies'))


class CompetitieStatistiekView(UserPassesTestMixin, TemplateView):
    """ Deze view biedt statistiek over de competities """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_STATISTIEK
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu == Rollen.ROL_BB

    @staticmethod
    def _tel_aantallen(context, actuele_comps):
        context['toon_aantal_inschrijvingen'] = True

        context['totaal_18m_indiv'] = 0
        context['aantal_18m_teams_niet_af'] = 0

        context['totaal_25m_indiv'] = 0
        context['aantal_25m_teams_niet_af'] = 0

        aantal_18m_teams = dict()
        aantal_25m_teams = dict()
        for rayon_nr in range(1, 4+1):
            aantal_18m_teams[rayon_nr] = 0
            aantal_25m_teams[rayon_nr] = 0
        # for

        pks = list()
        for comp in actuele_comps:
            pks.append(comp.pk)
            aantal_indiv = (RegiocompetitieSporterBoog
                            .objects
                            .filter(regiocompetitie__competitie=comp)
                            .count())

            qset = RegiocompetitieTeam.objects.filter(regiocompetitie__competitie=comp).select_related('vereniging__regio__rayon')
            aantal_teams_ag_nul = qset.filter(aanvangsgemiddelde__lt=0.001).count()

            if comp.afstand == '18':
                context['totaal_18m_indiv'] = aantal_indiv
                context['aantal_18m_teams_niet_af'] = aantal_teams_ag_nul
            else:
                context['totaal_25m_indiv'] = aantal_indiv
                context['aantal_25m_teams_niet_af'] = aantal_teams_ag_nul

            for team in qset:
                rayon_nr = team.vereniging.regio.rayon.rayon_nr
                if comp.afstand == '18':
                    aantal_18m_teams[rayon_nr] += 1
                else:
                    aantal_25m_teams[rayon_nr] += 1
            # for
        # for

        context['aantal_18m_teams'] = list()
        context['aantal_25m_teams'] = list()
        context['totaal_18m_teams'] = 0
        context['totaal_25m_teams'] = 0
        for rayon_nr in range(1, 4+1):
            context['aantal_18m_teams'].append(aantal_18m_teams[rayon_nr])
            context['aantal_25m_teams'].append(aantal_25m_teams[rayon_nr])
            context['totaal_18m_teams'] += aantal_18m_teams[rayon_nr]
            context['totaal_25m_teams'] += aantal_25m_teams[rayon_nr]
        # for

        aantal_18m_rayon = dict()
        aantal_25m_rayon = dict()
        aantal_18m_regio = dict()
        aantal_25m_regio = dict()
        aantal_18m_geen_rk = dict()
        aantal_25m_geen_rk = dict()
        aantal_zelfstandig_18m_regio = dict()
        aantal_zelfstandig_25m_regio = dict()
        aantal_leden_regio = dict()

        for rayon_nr in range(1, 4+1):
            aantal_18m_rayon[rayon_nr] = 0
            aantal_25m_rayon[rayon_nr] = 0
            aantal_18m_geen_rk[rayon_nr] = 0
            aantal_25m_geen_rk[rayon_nr] = 0
        # for

        for regio_nr in range(101, 116+1):
            aantal_18m_regio[regio_nr] = 0
            aantal_25m_regio[regio_nr] = 0
            aantal_zelfstandig_18m_regio[regio_nr] = 0
            aantal_zelfstandig_25m_regio[regio_nr] = 0
            aantal_leden_regio[regio_nr] = 0
        # for

        for deelnemer in (RegiocompetitieSporterBoog
                          .objects
                          .filter(regiocompetitie__competitie__pk__in=pks)
                          .select_related('sporterboog__sporter',
                                          'sporterboog__sporter__account',
                                          'bij_vereniging__regio__rayon',
                                          'aangemeld_door',
                                          'regiocompetitie__competitie')):

            rayon_nr = deelnemer.bij_vereniging.regio.rayon.rayon_nr
            regio_nr = deelnemer.bij_vereniging.regio.regio_nr
            zelfstandig = deelnemer.aangemeld_door == deelnemer.sporterboog.sporter.account

            if deelnemer.regiocompetitie.competitie.afstand == '18':
                aantal_18m_rayon[rayon_nr] += 1
                aantal_18m_regio[regio_nr] += 1
                if not deelnemer.inschrijf_voorkeur_rk_bk:
                    aantal_18m_geen_rk[rayon_nr] += 1
                if zelfstandig:
                    aantal_zelfstandig_18m_regio[regio_nr] += 1
            else:
                aantal_25m_rayon[rayon_nr] += 1
                aantal_25m_regio[regio_nr] += 1
                if not deelnemer.inschrijf_voorkeur_rk_bk:
                    aantal_25m_geen_rk[rayon_nr] += 1
                if zelfstandig:
                    aantal_zelfstandig_25m_regio[regio_nr] += 1
        # for

        context['aantal_18m_rayon'] = list()
        context['aantal_25m_rayon'] = list()
        context['aantal_18m_geen_rk'] = list()
        context['aantal_25m_geen_rk'] = list()
        for rayon_nr in range(1, 4+1):
            context['aantal_18m_rayon'].append(aantal_18m_rayon[rayon_nr])
            context['aantal_25m_rayon'].append(aantal_25m_rayon[rayon_nr])
            context['aantal_18m_geen_rk'].append(aantal_18m_geen_rk[rayon_nr])
            context['aantal_25m_geen_rk'].append(aantal_25m_geen_rk[rayon_nr])
        # for

        context['aantal_18m_regio'] = list()
        context['aantal_25m_regio'] = list()
        for regio_nr in range(101, 116+1):
            context['aantal_18m_regio'].append(aantal_18m_regio[regio_nr])
            context['aantal_25m_regio'].append(aantal_25m_regio[regio_nr])
        # for

        qset = (RegiocompetitieSporterBoog
                .objects
                .filter(regiocompetitie__competitie__pk__in=pks)
                .select_related('sporterboog',
                                'sporterboog__sporter__account')
                .distinct('sporterboog'))

        aantal_sportersboog = qset.count()
        context['aantal_sporters'] = qset.distinct('sporterboog__sporter').count()
        context['aantal_multiboog'] = aantal_sportersboog - context['aantal_sporters']
        context['aantal_zelfstandig'] = qset.filter(aangemeld_door=F('sporterboog__sporter__account')).count()

        for sporter in Sporter.objects.select_related('bij_vereniging__regio').filter(is_actief_lid=True).exclude(bij_vereniging=None):
            regio_nr = sporter.bij_vereniging.regio.regio_nr
            if regio_nr >= 101:
                aantal_leden_regio[regio_nr] += 1
        # for

        context['perc_zelfstandig_18m_regio'] = perc_zelfstandig_18m_regio = list()
        context['perc_zelfstandig_25m_regio'] = perc_zelfstandig_25m_regio = list()
        context['perc_leden_18m_regio'] = perc_leden_18m_regio = list()
        context['perc_leden_25m_regio'] = perc_leden_25m_regio = list()
        for regio_nr in range(101, 116+1):
            aantal = aantal_18m_regio[regio_nr]
            if aantal > 0:
                perc_str = '%.1f' % ((aantal_zelfstandig_18m_regio[regio_nr] / aantal) * 100.0)
            else:
                perc_str = '0.0'
            perc_zelfstandig_18m_regio.append(perc_str)

            aantal = aantal_25m_regio[regio_nr]
            if aantal > 0:
                perc_str = '%.1f' % ((aantal_zelfstandig_25m_regio[regio_nr] / aantal) * 100.0)
            else:
                perc_str = '0.0'
            perc_zelfstandig_25m_regio.append(perc_str)

            aantal = aantal_leden_regio[regio_nr]
            if aantal > 0:
                perc_str = '%.1f' % ((aantal_18m_regio[regio_nr] / aantal) * 100.0)
                perc_leden_18m_regio.append(perc_str)

                perc_str = '%.1f' % ((aantal_25m_regio[regio_nr] / aantal) * 100.0)
                perc_leden_25m_regio.append(perc_str)
            else:
                perc_str = '0.0'
                perc_leden_18m_regio.append(perc_str)
                perc_leden_25m_regio.append(perc_str)
        # for

        if aantal_sportersboog > 0:
            context['procent_zelfstandig'] = '%.1f' % ((context['aantal_zelfstandig'] / aantal_sportersboog) * 100.0)

        for afstand in (18, 25):
            context['geplaatst_rk_%sm' % afstand] = geplaatst_rk = list()
            context['deelnemers_rk_%sm' % afstand] = deelnemers_rk = list()
            context['in_uitslag_rk_%sm' % afstand] = in_uitslag_rk = list()

            qset = (KampioenschapSporterBoog
                    .objects
                    .filter(kampioenschap__competitie__afstand=afstand,
                            kampioenschap__deel=DEEL_RK))

            totaal1 = totaal2 = totaal3 = 0
            for rayon_nr in range(1, 4+1):
                qset_rayon = qset.filter(kampioenschap__nhb_rayon__rayon_nr=rayon_nr)

                aantal = qset_rayon.count()
                geplaatst_rk.append(aantal)
                totaal1 += aantal

                qset_rayon = qset_rayon.exclude(deelname=DEELNAME_NEE)
                aantal = qset_rayon.count()
                deelnemers_rk.append(aantal)
                totaal2 += aantal

                aantal = qset_rayon.filter(result_rank__gte=1, result_rank__lt=100).count()
                in_uitslag_rk.append(aantal)

                totaal3 += aantal
            # for

            geplaatst_rk.append(totaal1)
            deelnemers_rk.append(totaal2)
            in_uitslag_rk.append(totaal3)
        # for

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        actuele_comps = list()

        for comp in (Competitie
                     .objects
                     .exclude(is_afgesloten=True)
                     .order_by('afstand',
                               'begin_jaar')):

            comp.bepaal_fase()
            comp.bepaal_openbaar(self.rol_nu)

            if comp.is_openbaar:
                if comp.fase_indiv >= 'C':
                    actuele_comps.append(comp)
                    context['seizoen'] = comp.maak_seizoen_str()
        # for

        self._tel_aantallen(context, actuele_comps)

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (None, 'Statistiek')
        )

        menu_dynamics(self.request, context)
        return context


# end of file
