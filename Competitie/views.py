# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import Resolver404, reverse
from django.views.generic import TemplateView, ListView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.utils import timezone
from Plein.menu import menu_dynamics
from Logboek.models import schrijf_in_logboek
from Functie.models import Functie
from Functie.rol import Rollen, rol_get_huidige_functie, rol_get_beschrijving, rol_get_huidige
from BasisTypen.models import TeamType, TeamTypeBoog, WedstrijdKlasse, LeeftijdsKlasse, \
                              WedstrijdKlasseBoog, WedstrijdKlasseLeeftijd, MAXIMALE_LEEFTIJD_JEUGD
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from NhbStructuur.models import NhbLid, NhbVereniging
from Schutter.models import SchutterBoog
from .models import Competitie, ZERO, CompetitieWedstrijdKlasse, DeelCompetitie,\
                    competitie_aanmaken, maak_competitieklasse_indiv
from datetime import date


TEMPLATE_COMPETITIE_OVERZICHT = 'competitie/overzicht.dtl'
TEMPLATE_COMPETITIE_OVERZICHT_CWZ = 'competitie/overzicht-cwz.dtl'
TEMPLATE_COMPETITIE_OVERZICHT_BEHEERDER = 'competitie/overzicht-beheerder.dtl'
TEMPLATE_COMPETITIE_INSTELLINGEN = 'competitie/instellingen-nieuwe-competitie.dtl'
TEMPLATE_COMPETITIE_AANMAKEN = 'competitie/competities-aanmaken.dtl'
TEMPLATE_COMPETITIE_KLASSEGRENZEN = 'competitie/klassegrenzen-vaststellen.dtl'
TEMPLATE_COMPETITIE_LIJST_VERENIGINGEN = 'competitie/lijst-verenigingen.dtl'
TEMPLATE_COMPETITIE_LEDENLIJST = 'competitie/ledenlijst.dtl'
TEMPLATE_COMPETITIE_CWZ_SCHUTTERSBOOG_AANMELDEN = 'competitie/cwz-schutters-boog-aanmelden.dtl'
TEMPLATE_COMPETITIE_CWZ_SCHUTTER_BOGEN_INSTELLEN = 'competitie/cwz-schutter-bogen-kiezen.dtl'

JA_NEE = {False: 'Nee', True: 'Ja'}


def models_bepaal_startjaar_nieuwe_competitie():
    """ bepaal het start jaar van de nieuwe competitie """
    return timezone.now().year


def zet_fase(comp):
    # fase A was totdat dit object gemaakt werd

    now = timezone.now()
    now = date(year=now.year, month=now.month, day=now.day)

    if now < comp.begin_aanmeldingen:
        # zijn de wedstrijdklassen vastgesteld?
        if len(CompetitieWedstrijdKlasse.objects.filter(competitie=comp)) == 0:
            # A1 = competitie is aangemaakt
            comp.fase = 'A1'
            return

        # A2 = klassengrenzen zijn bepaald
        comp.fase = 'A2'
        return

    # B = open voor inschrijvingen
    if now < comp.einde_aanmeldingen:
        comp.fase = 'B'
        return

    # C = aanmaken teams; gesloten voor individuele inschrijvingen
    if now < comp.einde_teamvorming:
        comp.fase = 'C'
        return

    # D = aanmaken poules en afronden wedstrijdschema's
    if now < comp.eerste_wedstrijd:
        comp.fase = 'D'
        return

    # E = Begin wedstrijden
    comp.fase = 'E'


class CompetitieOverzichtView(View):
    """ Deze view biedt de landingpage vanuit het menu aan """

    # class variables shared by all instances
    # (none)

    @staticmethod
    def _get_competitie_overzicht_beheerder(request):
        context = dict()

        rol_nu, functie_nu = rol_get_huidige_functie(request)

        context['huidige_rol'] = rol_get_beschrijving(request)

        context['toon_functies'] = rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO)

        # kies de competities om het tijdschema van de tonen
        objs = list()
        if rol_nu == Rollen.ROL_BB:
            # toon alle competities
            objs = Competitie.objects.filter(is_afgesloten=False).order_by('begin_jaar', 'afstand')
        elif functie_nu:
            # toon de competitie waar de functie een rol in heeft
            for deelcomp in DeelCompetitie.objects.filter(is_afgesloten=False, functie=functie_nu):
                objs.append(deelcomp.competitie)
            # for

        context['object_list'] = objs
        context['have_active_comps'] = (len(objs) > 0)

        # kies de competities waarvoor de beheerder getoond kunnen worden
        for obj in objs:
            zet_fase(obj)
            obj.is_afgesloten_str = JA_NEE[obj.is_afgesloten]
        # for

        if rol_nu == Rollen.ROL_BB:
            context['rol_is_bb'] = True
            # als er nog geen competitie is voor het huidige jaar, geeft de BB dan de optie om deze op te starten
            beginjaar = models_bepaal_startjaar_nieuwe_competitie()
            context['nieuwe_seizoen'] = "%s/%s" % (beginjaar, beginjaar+1)
            context['bb_kan_competitie_aanmaken'] = (len(objs.filter(begin_jaar=beginjaar)) == 0)

        return context, TEMPLATE_COMPETITIE_OVERZICHT_BEHEERDER

    @staticmethod
    def _get_competitie_overzicht_cwz(request):
        context = dict()
        return context, TEMPLATE_COMPETITIE_OVERZICHT_CWZ

    @staticmethod
    def _get_competitie_overzicht_schutter():
        context = dict()
        return context, TEMPLATE_COMPETITIE_OVERZICHT

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """

        rol_nu = rol_get_huidige(self.request)
        if rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL):
            context, template = self._get_competitie_overzicht_beheerder(request)
        elif rol_nu == Rollen.ROL_CWZ:
            context, template = self._get_competitie_overzicht_cwz(request)
        else:
            context, template = self._get_competitie_overzicht_schutter()

        menu_dynamics(self.request, context, actief='competitie')
        return render(request, template, context)


class InstellingenVolgendeCompetitieView(UserPassesTestMixin, ListView):

    """ deze view laat de defaults voor de volgende competitie zien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_INSTELLINGEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BB

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    @staticmethod
    def _get_queryset_teamtypen():
        objs = TeamType.objects.all()
        for teamtype in objs:
            boogtypen = [obj.boogtype.afkorting for obj in TeamTypeBoog.objects.select_related('boogtype').filter(teamtype=teamtype)]
            teamtype.boogtypen = "+".join(boogtypen)
        # for
        return objs

    @staticmethod
    def _get_queryset_indivklassen():
        objs = WedstrijdKlasse.objects.filter(is_voor_teams=False, buiten_gebruik=False)
        prev = "-"
        for klasse in objs:
            klasse.separate_before = not klasse.beschrijving.startswith(prev)
            if klasse.beschrijving[-4:] == 'jaar':
                prev = klasse.beschrijving[:-10]    # aspiranten hebben suffix "11-12 jaar"
            else:
                prev = klasse.beschrijving[:-1]     # klasse nummer 1..6

            # add boogtypen
            boogtypen = [obj.boogtype.afkorting for obj in WedstrijdKlasseBoog.objects.select_related('boogtype').filter(wedstrijdklasse=klasse)]
            klasse.boogtypen = "+".join(boogtypen)

            # add leeftijdsklassen
            leeftijden = [obj.leeftijdsklasse.afkorting for obj in WedstrijdKlasseLeeftijd.objects.select_related('leeftijdsklasse').filter(wedstrijdklasse=klasse)]
            klasse.leeftijden = "+".join(leeftijden)
        # for
        return objs

    def _get_queryset_teamklassen(self):
        objs = WedstrijdKlasse.objects.filter(is_voor_teams=True, buiten_gebruik=False)
        prev = "-"
        for klasse in objs:
            klasse.separate_before = not klasse.beschrijving.startswith(prev)
            prev = klasse.beschrijving[:-3]     # "ERE" is de langste suffix

            # add boogtypen
            boogtypen = [obj.boogtype.afkorting for obj in WedstrijdKlasseBoog.objects.select_related('boogtype').filter(wedstrijdklasse=klasse)]
            klasse.boogtypen = "+".join(boogtypen)
        # for
        return objs

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        self.teamtypen = self._get_queryset_teamtypen()
        self.indivklassen = self._get_queryset_indivklassen()
        self.teamklassen = self._get_queryset_teamklassen()
        return None

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['teamtypen'] = self.teamtypen
        context['indivklassen'] = self.indivklassen
        context['teamklassen'] = self.teamklassen
        menu_dynamics(self.request, context, actief='competitie')
        return context


class CompetitieAanmakenView(UserPassesTestMixin, TemplateView):

    """ deze view laat de BKO een nieuwe competitie opstarten """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_AANMAKEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BB

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def post(self, request, *args, **kwargs):
        """ deze functie handelt het http-post verzoek af
            (wat volgt uit het drukken op de knop)
            om de nieuwe competitie op te starten.
        """
        jaar = models_bepaal_startjaar_nieuwe_competitie()
        seizoen = "%s/%s" % (jaar, jaar+1)
        schrijf_in_logboek(request.user, 'Competitie', 'Aanmaken competities %s' % seizoen)
        competitie_aanmaken(jaar)
        return redirect('Competitie:overzicht')

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        jaar = models_bepaal_startjaar_nieuwe_competitie()
        context['seizoen'] = "%s/%s" % (jaar, jaar+1)
        menu_dynamics(self.request, context, actief='competitie')
        return context


class KlassegrenzenView(UserPassesTestMixin, TemplateView):

    """ deze view laat de aanvangemiddelden voor de volgende competitie zien,
        aan de hand van de historische competitie data
        De BKO kan deze bevestigen, waarna ze aan de competitie toegevoegd worden
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_KLASSEGRENZEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BB

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def _get_targets(self):
        """ Retourneer een data structuur met daarin voor alle wedstrijdklassen
            de toegestande boogtypen en leeftijden

            out: target = dict() met [ (min_age, max_age, tuple(bogen)) ] = list(wedstrijdklassen)

            Voorbeeld: { (21,150,('R','BB','IB','LB')): [obj1, obj2, etc.],
                         (21,150,('C')): [obj10, obj11],
                         (14,17),('C')): [obj20, obj21]  }
                    Waarbij obj* = WedstrijdKlasse object
        """
        targets = dict()        # [ (min_age, max_age, tuple(bogen)) ] = list(wedstrijdklassen)
        for wedstrklasse in WedstrijdKlasse.objects.filter(is_voor_teams=False, buiten_gebruik=False):

            # zoek de minimale en maximaal toegestane leeftijden voor deze wedstrijdklasse
            age_min = 999
            age_max = 0
            for obj in WedstrijdKlasseLeeftijd.objects.filter(wedstrijdklasse=wedstrklasse):
                lkl = obj.leeftijdsklasse
                age_min = min(lkl.min_wedstrijdleeftijd, age_min)
                age_max = max(lkl.max_wedstrijdleeftijd, age_max)
            # for

            # verzamel alle toegestane boogsoorten voor deze wedstrijdklasse
            bogen = list()
            for obj in WedstrijdKlasseBoog.objects.filter(wedstrijdklasse=wedstrklasse):
                if obj.boogtype.afkorting not in bogen:
                    bogen.append(obj.boogtype.afkorting)
            # for

            tup = (age_min, age_max, tuple(bogen))
            if tup not in targets:
                targets[tup] = list()
            targets[tup].append(wedstrklasse)
        # for
        return targets

    def _get_queryset(self, afstand):
        """ called by the template system to get the queryset or list of objects for the template """

        # bepaal het jaar waarin de wedstrijdleeftijd bepaald moet worden
        # dit is het huidige jaar + 1
        jaar = 1 + models_bepaal_startjaar_nieuwe_competitie()
        self.wedstrijdjaar = jaar

        if len(HistCompetitie.objects.all()) < 1:
            # geen historische competitiedata aanwezig
            self.seizoen = "FOUT - GEEN DATA AANWEZIG"
            return list()

        # bepaal 'het vorige seizoen'
        # seizoen = '20xx-20yy'
        self.seizoen = HistCompetitie.objects.distinct('seizoen').order_by('-seizoen')[0].seizoen

        # eenmalig de wedstrijdleeftijd van elke schutter berekenen
        schutternr2age = dict()     # [ nhb_nr ] = age
        for lid in NhbLid.objects.all():
            schutternr2age[lid.nhb_nr] = lid.bereken_wedstrijdleeftijd(jaar)
        # for

        # creeer de resultatenlijst
        objs = list()
        histcomps = HistCompetitie.objects.filter(seizoen=self.seizoen, comp_type=afstand, is_team=False)
        targets = self._get_targets()   # wedstrijdklassen vs leeftijd + bogen

        for tup, wedstrklassen in targets.items():
            min_age, max_age, bogen = tup
            wedstrklassen.sort(key=lambda kl: kl.beschrijving)     # forceer de juiste volgorde

            # zoek alle schutters uit de vorige competitie die hier in passen (boog, leeftijd)
            gemiddelden = list()
            for indiv in HistCompetitieIndividueel.objects.filter(histcompetitie__in=histcomps):
                if indiv.boogtype in bogen:
                    age = schutternr2age[indiv.schutter_nr]
                    if min_age <= age and age <= max_age:
                        gemiddelden.append(indiv.gemiddelde)
            # for

            if len(gemiddelden):
                gemiddelden.sort(reverse=True)  # in-place sort, highest to lowest
                count = len(gemiddelden)        # aantal schutters
                aantal = len(wedstrklassen)     # aantal groepen
                step = int(count / aantal)      # omlaag afgerond = OK voor grote groepen
                pos = 0
                for klasse in wedstrklassen[:-1]:
                    pos += step
                    ag = gemiddelden[pos]
                    res = {'beschrijving': klasse.beschrijving,
                           'count' : step,
                           'ag': ag,
                           'wedstrkl_obj': klasse}
                    objs.append(res)
                # for
                # laatste klasse krijgt 0,000 als AG
                klasse = wedstrklassen[-1]
                res = {'beschrijving': klasse.beschrijving,
                       'count' : count - (aantal - 1) * step,
                       'ag': ZERO,
                       'wedstrkl_obj': klasse}
                objs.append(res)
            else:
                # geen historische gemiddelden
                # zet alles op 0,000 - dit geeft een beetje een rommeltje als er meerdere klassen zijn
                for klasse in wedstrklassen:
                    res = {'beschrijving': klasse.beschrijving,
                           'count': 0,
                           'ag': ZERO,
                           'wedstrkl_obj': klasse}
                    objs.append(res)
                # for
        # for
        objs2 = sorted(objs, key=lambda k: k['beschrijving'])
        return objs2

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        context = super().get_context_data(**kwargs)

        afstand = kwargs['afstand']
        context['afstand'] = afstand

        objs = Competitie.objects.filter(afstand=afstand, is_afgesloten=False)
        if len(objs) == 0:
            # onverwachts here
            return redirect('Plein:plein')
        obj = objs[0]
        context['comp_str'] = obj.beschrijving

        context['object_list'] = self._get_queryset(afstand)
        context['seizoen'] = self.seizoen
        context['wedstrijdjaar'] = self.wedstrijdjaar

        menu_dynamics(self.request, context, actief='competitie')
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            --> de beheerder wil deze klassegrenzen vaststellen
        """
        afstand = kwargs['afstand']
        # TODO: pk doorgeven via het formulier?
        objs = Competitie.objects.filter(afstand=afstand, is_afgesloten=False)
        if len(objs) > 0:
            comp = objs[0]
            schrijf_in_logboek(request.user, 'Competitie', 'Klassegrenzen bevestigd voor %s' % comp.beschrijving)
            # haal dezelfde data op als voor de GET request
            for obj in self._get_queryset(afstand):
                klasse = obj['wedstrkl_obj']
                maak_competitieklasse_indiv(comp, klasse, obj['ag'])
            # for
        return redirect('Competitie:overzicht')


class LijstVerenigingenView(UserPassesTestMixin, ListView):

    """ Via deze view worden kan een BKO, RKO of RCL
          de lijst van verenigingen zien, in zijn werkgebied
    """

    template_name = TEMPLATE_COMPETITIE_LIJST_VERENIGINGEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        rol_nu, functie = rol_get_huidige_functie(self.request)

        if rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO):
            # toon de landelijke lijst
            return NhbVereniging.objects.all().exclude(regio__regio_nr=100).order_by('regio__regio_nr', 'nhb_nr')

        if rol_nu == Rollen.ROL_RKO:
            # toon de lijst van verenigingen in het rayon van de RKO
            # het rayonnummer is verkrijgbaar via de deelcompetitie van de functie
            return NhbVereniging.objects.filter(regio__rayon=functie.nhb_rayon).exclude(regio__regio_nr=100).order_by('regio__regio_nr', 'nhb_nr')

        if rol_nu == Rollen.ROL_RCL:
            # toon de lijst van verenigingen in de regio van de RCL
            # het regionummer is verkrijgbaar via de deelcompetitie van de functie
            objs = NhbVereniging.objects.filter(regio=functie.nhb_regio)
            for obj in objs:
                try:
                    functie_cwz = Functie.objects.get(rol='CWZ', nhb_ver=obj)
                except Functie.DoesNotExist:
                    obj.cwzs = list()
                else:
                    obj.cwzs = functie_cwz.accounts.all()
            # for
            return objs

        # waarom hier?
        raise Resolver404()

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['toon_rayon'] = True
        context['toon_regio'] = True

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        context['huidige_rol'] = rol_get_beschrijving(self.request)

        if rol_nu == Rollen.ROL_RKO:
            context['toon_rayon'] = False

        if rol_nu == Rollen.ROL_RCL:
            context['toon_rayon'] = False
            context['toon_regio'] = False
            context['toon_cwzs'] = True

        menu_dynamics(self.request, context, actief='competitie')
        return context


class LedenLijstView(UserPassesTestMixin, ListView):

    """ Deze view laat de CWZ zijn ledenlijst zien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_LEDENLIJST

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        _, functie_nu = rol_get_huidige_functie(self.request)
        return functie_nu and functie_nu.rol == "CWZ"

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar Competitie scherm """
        return HttpResponseRedirect(reverse('Competitie:overzicht'))

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        huidige_jaar = timezone.now().year  # TODO: check for correctness in last hours of the year (due to timezone)
        jeugdgrens = huidige_jaar - MAXIMALE_LEEFTIJD_JEUGD
        self._huidige_jaar = huidige_jaar

        _, functie_nu = rol_get_huidige_functie(self.request)
        qset = NhbLid.objects.filter(bij_vereniging=functie_nu.nhb_ver)
        objs = list()

        # sorteer op geboorte jaar en daarna naam
        for obj in qset.filter(geboorte_datum__year__gte=jeugdgrens).order_by('-geboorte_datum__year', 'achternaam', 'voornaam'):
            objs.append(obj)

            # de wedstrijdleeftijd voor dit hele jaar
            wedstrijdleeftijd = huidige_jaar - obj.geboorte_datum.year
            obj.leeftijd = wedstrijdleeftijd

            # de wedstrijdklasse voor dit hele jaar
            obj.leeftijdsklasse = LeeftijdsKlasse.objects.filter(
                            max_wedstrijdleeftijd__gte=wedstrijdleeftijd,
                            geslacht='M').order_by('max_wedstrijdleeftijd')[0]
        # for

        # volwassenen
        # sorteer op naam
        for obj in qset.filter(geboorte_datum__year__lt=jeugdgrens).order_by('achternaam', 'voornaam'):
            objs.append(obj)
            obj.leeftijdsklasse = None

            if not obj.is_actief_lid:
                obj.leeftijd = huidige_jaar - obj.geboorte_datum.year
        # for
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

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

        menu_dynamics(self.request, context, actief='competitie')
        return context


class SchutterBogenInstellenView(UserPassesTestMixin, ListView):

    """ Deze view laat de CWZ de boven van een lid instellen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_CWZ_SCHUTTER_BOGEN_INSTELLEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        _, functie_nu = rol_get_huidige_functie(self.request)
        return functie_nu and functie_nu.rol == "CWZ"

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar Competitie scherm """
        return HttpResponseRedirect(reverse('Competitie:overzicht'))

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        huidige_jaar = timezone.now().year  # TODO: check for correctness in last hours of the year (due to timezone)
        jeugdgrens = huidige_jaar - MAXIMALE_LEEFTIJD_JEUGD
        self._huidige_jaar = huidige_jaar

        _, functie_nu = rol_get_huidige_functie(self.request)
        qset = NhbLid.objects.filter(bij_vereniging=functie_nu.nhb_ver)
        objs = list()

        # jeugd
        # sorteer op geboorte jaar en daarna naam
        for obj in qset.filter(geboorte_datum__year__gte=jeugdgrens).order_by('-geboorte_datum__year', 'achternaam', 'voornaam'):
            objs.append(obj)

            # de wedstrijdleeftijd voor dit hele jaar
            wedstrijdleeftijd = huidige_jaar - obj.geboorte_datum.year
            obj.leeftijd = wedstrijdleeftijd

            # de wedstrijdklasse voor dit hele jaar
            obj.leeftijdsklasse = LeeftijdsKlasse.objects.filter(
                            max_wedstrijdleeftijd__gte=wedstrijdleeftijd,
                            geslacht='M').order_by('max_wedstrijdleeftijd')[0]
        # for

        # volwassenen
        # sorteer op naam
        for obj in qset.filter(geboorte_datum__year__lt=jeugdgrens).order_by('achternaam', 'voornaam'):
            objs.append(obj)
            obj.leeftijdsklasse = None

            if not obj.is_actief_lid:
                obj.leeftijd = huidige_jaar - obj.geboorte_datum.year
        # for
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

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

        menu_dynamics(self.request, context, actief='competitie')
        return context


class SchuttersBoogAanmeldenView(UserPassesTestMixin, ListView):

    """ Deze view laat de CWZ schutters van zijn vereniging aanmelden voor de competitie """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_CWZ_SCHUTTERSBOOG_AANMELDEN

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._huidige_jaar = timezone.now().year  # TODO: check for correctness in last hours of the year (due to timezone)
        self._jeugdgrens = self._huidige_jaar - MAXIMALE_LEEFTIJD_JEUGD

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        _, functie_nu = rol_get_huidige_functie(self.request)
        return functie_nu and functie_nu.rol == "CWZ"

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar Competitie scherm """
        return HttpResponseRedirect(reverse('Competitie:overzicht'))

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        _, functie_nu = rol_get_huidige_functie(self.request)
        qset = NhbLid.objects.filter(bij_vereniging=functie_nu.nhb_ver)
        objs = list()

        # jeugd
        # sorteer op geboorte jaar en daarna naam
        for obj in qset.filter(geboorte_datum__year__gte=self._jeugdgrens).order_by('-geboorte_datum__year', 'achternaam', 'voornaam'):
            objs.append(obj)

            # de wedstrijdleeftijd voor dit hele jaar
            wedstrijdleeftijd = self._huidige_jaar - obj.geboorte_datum.year
            obj.leeftijd = wedstrijdleeftijd

            # de wedstrijdklasse voor dit hele jaar
            obj.leeftijdsklasse = LeeftijdsKlasse.objects.filter(
                            max_wedstrijdleeftijd__gte=wedstrijdleeftijd,
                            geslacht='M').order_by('max_wedstrijdleeftijd')[0]

            for obj in SchutterBoog.objects.filter(account=obj.account):
                pass
            obj.bogen = "?"
        # for

        # volwassenen
        # sorteer op naam
        for obj in qset.filter(geboorte_datum__year__lt=self._jeugdgrens).order_by('achternaam', 'voornaam'):
            objs.append(obj)
            obj.leeftijdsklasse = None

            if not obj.is_actief_lid:
                obj.leeftijd = self._huidige_jaar - obj.geboorte_datum.year
        # for
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

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

        menu_dynamics(self.request, context, actief='competitie')
        return context


# end of file
