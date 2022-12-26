# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.shortcuts import render, redirect
from django.utils.formats import localize
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import TemplateCompetitieIndivKlasse, TemplateCompetitieTeamKlasse
from Competitie.models import (Competitie, DeelCompetitie, CompetitieMutatie, LAAG_REGIO, LAAG_RK, LAAG_BK,
                               MUTATIE_COMPETITIE_OPSTARTEN, MUTATIE_AG_VASTSTELLEN_18M, MUTATIE_AG_VASTSTELLEN_25M,
                               MUTATIE_AFSLUITEN_REGIOCOMP)
from Competitie.operations import (bepaal_startjaar_nieuwe_competitie, bepaal_klassengrenzen_indiv,
                                   bepaal_klassengrenzen_teams, competitie_klassengrenzen_vaststellen)
from Functie.models import Rollen
from Functie.rol import rol_get_huidige, rol_get_huidige_functie
from HistComp.models import HistCompetitie
from Logboek.models import schrijf_in_logboek
from Overig.background_sync import BackgroundSync
from Plein.menu import menu_dynamics
from Score.operations import wanneer_ag_vastgesteld
import datetime
import time


TEMPLATE_COMPETITIE_INSTELLINGEN = 'compbeheer/bb-instellingen-nieuwe-competitie.dtl'
TEMPLATE_COMPETITIE_AANMAKEN = 'compbeheer/bb-competities-aanmaken.dtl'
TEMPLATE_COMPETITIE_KLASSENGRENZEN_VASTSTELLEN = 'compbeheer/bb-klassengrenzen-vaststellen.dtl'
TEMPLATE_COMPETITIE_AANGEMELD_REGIO = 'competitie/lijst-aangemeld-regio.dtl'
TEMPLATE_COMPETITIE_AG_VASTSTELLEN = 'compbeheer/bb-ag-vaststellen.dtl'
TEMPLATE_COMPETITIE_WIJZIG_DATUMS = 'compbeheer/bb-wijzig-datums.dtl'
TEMPLATE_COMPETITIE_SEIZOEN_AFSLUITEN = 'compbeheer/bb-seizoen-afsluiten.dtl'
TEMPLATE_COMPETITIE_DOORZETTEN_NAAR_RK = 'compbeheer/bko-doorzetten-naar-rk.dtl'
TEMPLATE_COMPETITIE_DOORZETTEN_NAAR_BK = 'compbeheer/bko-doorzetten-naar-bk.dtl'
TEMPLATE_COMPETITIE_DOORZETTEN_VOORBIJ_BK = 'compbeheer/bko-doorzetten-voorbij-bk.dtl'

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
                .filter(buiten_gebruik=False)
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
                .filter(buiten_gebruik=False)
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

    """ deze view laat de BKO een nieuwe competitie opstarten """

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
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}),
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

        return redirect('Competitie:overzicht', comp_pk=comp.pk)


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
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}),
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

        return redirect('Competitie:overzicht', comp_pk=comp.pk)


class WijzigDatumsView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor het wijzigen van de competitie datums """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_WIJZIG_DATUMS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BB

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen voor de veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        context['comp'] = comp

        context['wijzig_url'] = reverse('CompBeheer:wijzig-datums',
                                        kwargs={'comp_pk': comp.pk})

        comp.datum1 = comp.begin_aanmeldingen
        comp.datum2 = comp.einde_aanmeldingen
        comp.datum3 = comp.einde_teamvorming
        comp.datum4 = comp.eerste_wedstrijd
        comp.datum5 = comp.laatst_mogelijke_wedstrijd
        comp.datum6 = comp.datum_klassengrenzen_rk_bk_teams
        comp.datum7 = comp.rk_eerste_wedstrijd
        comp.datum8 = comp.rk_laatste_wedstrijd
        comp.datum9 = comp.bk_eerste_wedstrijd
        comp.datum10 = comp.bk_laatste_wedstrijd

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}),
                comp.beschrijving.replace(' competitie', '')),
            (None, 'Zet datums'),
        )

        menu_dynamics(self.request, context)
        return context

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

        datums = list()
        for datum_nr in range(10):
            datum_s = request.POST.get('datum%s' % (datum_nr + 1), None)
            if not datum_s:
                # alle datums zijn verplicht
                raise Http404('Verplichte parameter ontbreekt')

            try:
                datum_p = datetime.datetime.strptime(datum_s, '%Y-%m-%d')
            except ValueError:
                raise Http404('Geen valide datum')

            datums.append(datum_p.date())
        # for

        oud_einde_teamvorming = comp.einde_teamvorming

        datums.insert(0, None)      # dummy
        comp.begin_aanmeldingen = datums[1]
        comp.einde_aanmeldingen = datums[2]
        comp.einde_teamvorming = datums[3]
        comp.eerste_wedstrijd = datums[4]
        comp.laatst_mogelijke_wedstrijd = datums[5]
        comp.datum_klassengrenzen_rk_bk_teams = datums[6]
        comp.rk_eerste_wedstrijd = datums[7]
        comp.rk_laatste_wedstrijd = datums[8]
        comp.bk_eerste_wedstrijd = datums[9]
        comp.bk_laatste_wedstrijd = datums[10]
        comp.save()

        # pas ook de deelcompetities aan
        for deelcomp in (DeelCompetitie
                         .objects
                         .filter(competitie=comp,
                                 laag=LAAG_REGIO)):

            # volg mee met wijzigingen in de competitie datums
            # neem ook meteen template datums mee (2001-01-01)
            if deelcomp.einde_teams_aanmaken == oud_einde_teamvorming or deelcomp.einde_teams_aanmaken.year < comp.begin_jaar:
                deelcomp.einde_teams_aanmaken = comp.einde_teamvorming
                deelcomp.save(update_fields=['einde_teams_aanmaken'])
        # for

        return HttpResponseRedirect(reverse('Competitie:overzicht',
                                            kwargs={'comp_pk': comp.pk}))


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
            if comp.fase != 'S':
                context['url_afsluiten'] = None
        # for

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (None, 'Seizoen afsluiten'),
        )

        menu_dynamics(self.request, context)
        return context

    def post(self, request, *args, **kwargs):
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
            if comp.fase != 'S':
                raise Http404('Alle competities nog niet in fase S')
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
