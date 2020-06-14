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
from BasisTypen.models import BoogType
from Plein.menu import menu_dynamics
from Logboek.models import schrijf_in_logboek
from Functie.rol import Rollen, rol_get_huidige_functie, rol_get_beschrijving, rol_get_huidige
from BasisTypen.models import (IndivWedstrijdklasse, TeamWedstrijdklasse,
                               MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT)
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from NhbStructuur.models import NhbLid, NhbRegio, NhbCluster, NhbVereniging
from Schutter.models import SchutterBoog
from Score.models import Score, ScoreHist, zoek_meest_recente_automatisch_vastgestelde_ag
from Wedstrijden.models import WedstrijdLocatie, Wedstrijd
from .models import (AG_NUL, AG_LAAGSTE_NIET_NUL, LAAG_REGIO, LAAG_RK, LAAG_BK,
                     Competitie, competitie_aanmaken,
                     CompetitieKlasse, maak_competitieklasse_indiv,
                     DeelCompetitie, DeelcompetitieRonde, maak_deelcompetitie_ronde,
                     RegioCompetitieSchutterBoog)
from types import SimpleNamespace
import datetime


TEMPLATE_COMPETITIE_OVERZICHT = 'competitie/overzicht.dtl'
TEMPLATE_COMPETITIE_OVERZICHT_HWL = 'competitie/overzicht-hwl.dtl'
TEMPLATE_COMPETITIE_OVERZICHT_BEHEERDER = 'competitie/overzicht-beheerder.dtl'
TEMPLATE_COMPETITIE_INSTELLINGEN = 'competitie/instellingen-nieuwe-competitie.dtl'
TEMPLATE_COMPETITIE_AANMAKEN = 'competitie/competities-aanmaken.dtl'
TEMPLATE_COMPETITIE_KLASSEGRENZEN_VASTSTELLEN = 'competitie/klassegrenzen-vaststellen.dtl'
TEMPLATE_COMPETITIE_KLASSEGRENZEN_TONEN = 'competitie/klassegrenzen-tonen.dtl'
TEMPLATE_COMPETITIE_AANGEMELD_REGIO = 'competitie/lijst-aangemeld-regio.dtl'
TEMPLATE_COMPETITIE_AG_VASTSTELLEN = 'competitie/ag-vaststellen.dtl'
TEMPLATE_COMPETITIE_INFO_COMPETITIE = 'competitie/info-competitie.dtl'
TEMPLATE_COMPETITIE_WIJZIG_DATUMS = 'competitie/wijzig-datums.dtl'
TEMPLATE_COMPETITIE_PLANNING_REGIO_RONDE = 'competitie/planning-regio-ronde.dtl'
TEMPLATE_COMPETITIE_PLANNING_REGIO_CLUSTER = 'competitie/planning-regio-cluster.dtl'
TEMPLATE_COMPETITIE_PLANNING_REGIO = 'competitie/planning-regio.dtl'
TEMPLATE_COMPETITIE_PLANNING_RAYON = 'competitie/planning-rayon.dtl'
TEMPLATE_COMPETITIE_PLANNING_BOND = 'competitie/planning-landelijk.dtl'
TEMPLATE_COMPETITIE_WIJZIG_WEDSTRIJD = 'competitie/wijzig-wedstrijd.dtl'


JA_NEE = {False: 'Nee', True: 'Ja'}

# python strftime: 0=sunday, 6=saturday
# wij rekenen het verschil ten opzicht van maandag in de week
WEEK_DAGEN = ( (0, 'Maandag'),
               (1, 'Dinsdag'),
               (2, 'Woensdag'),
               (3, 'Donderdag'),
               (4, 'Vrijdag'),
               (5, 'Zaterdag'),
               (6, 'Zondag'))


def models_bepaal_startjaar_nieuwe_competitie():
    """ bepaal het start jaar van de nieuwe competitie """
    return timezone.now().year


def zet_fase(comp):
    # fase A was totdat dit object gemaakt werd

    now = timezone.now()
    now = datetime.date(year=now.year, month=now.month, day=now.day)

    if now < comp.begin_aanmeldingen:
        # zijn de wedstrijdklassen vastgesteld?
        if CompetitieKlasse.objects.filter(competitie=comp).count() == 0:
            # A1 = aanvangsgemiddelden en klassegrenzen zijn vastgesteld
            comp.fase = 'A1'
            return

        # A2 = klassegrenzen zijn bepaald
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
    """ Deze view biedt de landing page vanuit het menu aan """

    # class variables shared by all instances
    # (none)

    def _get_competities(self, context, rol_nu):
        comps = Competitie.objects.filter(is_afgesloten=False).order_by('begin_jaar', 'afstand')
        for comp in comps:
            comp.url_inschrijvingen = reverse('Competitie:lijst-regio', kwargs={'comp_pk': comp.pk})
            zet_fase(comp)
            if comp.fase == 'A1' and rol_nu == Rollen.ROL_BB:
                context['bb_kan_ag_vaststellen'] = True
        # for
        context['competities'] = comps

    def _get_competitie_overzicht_beheerder(self, request):
        context = dict()

        rol_nu, functie_nu = rol_get_huidige_functie(request)

        context['huidige_rol'] = rol_get_beschrijving(request)
        context['toon_functies'] = rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO)
        context['bb_kan_ag_vaststellen'] = False

        self._get_competities(context, rol_nu)

        # kies de competities om het tijdschema van de tonen
        objs = list()
        if rol_nu == Rollen.ROL_BB:
            # toon alle competities
            objs = (Competitie
                    .objects
                    .filter(is_afgesloten=False)
                    .order_by('begin_jaar', 'afstand'))
        elif functie_nu:
            # toon de competitie waar de functie een rol in heeft
            for deelcomp in (DeelCompetitie
                             .objects
                             .filter(is_afgesloten=False,
                                     functie=functie_nu)):
                objs.append(deelcomp.competitie)
            # for

        context['object_list'] = objs
        context['have_active_comps'] = len(objs) > 0

        # kies de competities waarvoor de beheerder getoond kunnen worden
        for obj in objs:
            zet_fase(obj)
            obj.is_afgesloten_str = JA_NEE[obj.is_afgesloten]       # TODO: wordt niet gebruikt
        # for

        if rol_nu == Rollen.ROL_BB:
            context['rol_is_bb'] = True
            # als er nog geen competitie is voor het huidige jaar, geeft de BB dan de optie om deze op te starten
            beginjaar = models_bepaal_startjaar_nieuwe_competitie()
            context['nieuwe_seizoen'] = "%s/%s" % (beginjaar, beginjaar+1)
            context['bb_kan_competitie_aanmaken'] = (0 == objs.filter(begin_jaar=beginjaar).count())

            if context['bb_kan_ag_vaststellen']:
                # zoek uit wanneer dit voor het laatste gedaan is
                datum = zoek_meest_recente_automatisch_vastgestelde_ag()
                if datum:
                    context['bb_ag_nieuwste_datum'] = datum

            context['show_wijzig_datums'] = True
            for obj in objs:
                obj.url_wijzig_datums = reverse('Competitie:wijzig-datums', kwargs={'comp_pk': obj.pk})
            # for

        if rol_nu == Rollen.ROL_RCL:
            context['planning_deelcomp'] = (DeelCompetitie
                                            .objects
                                            .filter(laag=LAAG_REGIO,
                                                    nhb_regio=functie_nu.nhb_regio,
                                                    competitie__afstand=functie_nu.comp_type)
                                            .select_related('nhb_regio', 'competitie'))
            for obj in context['planning_deelcomp']:
                obj.titel = 'Planning Regio'
                obj.tekst = 'Planning voor %s voor de %s.' % (obj.nhb_regio.naam, obj.competitie.beschrijving)
                obj.url = reverse('Competitie:regio-planning', kwargs={'deelcomp_pk': obj.pk})
            # for

        elif rol_nu == Rollen.ROL_RKO:
            context['planning_deelcomp'] = (DeelCompetitie
                                            .objects
                                            .filter(laag=LAAG_RK,
                                                    nhb_rayon=functie_nu.nhb_rayon,
                                                    competitie__afstand=functie_nu.comp_type)
                                            .select_related('nhb_rayon', 'competitie'))
            for obj in context['planning_deelcomp']:
                obj.titel = 'Planning %s' % obj.nhb_rayon.naam
                obj.tekst = 'Planning voor %s voor de %s.' % (obj.nhb_rayon.naam, obj.competitie.beschrijving)
                obj.url = reverse('Competitie:rayon-planning', kwargs={'deelcomp_pk': obj.pk})
            # for

        elif rol_nu == Rollen.ROL_BKO:
            context['planning_deelcomp'] = (DeelCompetitie
                                            .objects
                                            .filter(laag=LAAG_BK,
                                                    competitie__afstand=functie_nu.comp_type)
                                            .select_related('competitie'))
            for obj in context['planning_deelcomp']:
                obj.titel = 'Planning %sm' % obj.competitie.afstand
                obj.tekst = 'Landelijke planning voor de %s.' % obj.competitie.beschrijving
                obj.url = reverse('Competitie:bond-planning', kwargs={'deelcomp_pk': obj.pk})
            # for

        return context, TEMPLATE_COMPETITIE_OVERZICHT_BEHEERDER

    def _get_competitie_overzicht_hwl(self, request):
        context = dict()
        self._get_competities(context, Rollen.ROL_HWL)

        rol_nu, functie_nu = rol_get_huidige_functie(request)

        context['planning_deelcomp'] = (DeelCompetitie
                                        .objects
                                        .filter(laag=LAAG_REGIO,
                                                nhb_regio=functie_nu.nhb_ver.regio))

        return context, TEMPLATE_COMPETITIE_OVERZICHT_HWL

    @staticmethod
    def _get_competitie_overzicht_schutter():
        # let op! Niet alleen voor schutter, maar ook voor gebruiker/anon
        context = dict()
        return context, TEMPLATE_COMPETITIE_OVERZICHT

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """

        rol_nu = rol_get_huidige(self.request)
        if rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL):
            context, template = self._get_competitie_overzicht_beheerder(request)
        elif rol_nu == Rollen.ROL_HWL:
            context, template = self._get_competitie_overzicht_hwl(request)
        else:
            context, template = self._get_competitie_overzicht_schutter()

        menu_dynamics(self.request, context, actief='competitie')
        return render(request, template, context)


class InstellingenVolgendeCompetitieView(UserPassesTestMixin, TemplateView):

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
    def _get_queryset_indivklassen():
        objs = (IndivWedstrijdklasse
                .objects
                .filter(buiten_gebruik=False)
                .order_by('volgorde')
                .select_related('boogtype'))
        prev = 0
        for klasse in objs:
            groep = klasse.volgorde // 10
            klasse.separate_before = groep != prev
            klasse.lkl_list = [lkl.beschrijving for lkl in klasse.leeftijdsklassen.only('beschrijving').all()]
            prev = groep
        # for
        return objs

    @staticmethod
    def _get_queryset_teamklassen():
        objs = (TeamWedstrijdklasse
                .objects
                .filter(buiten_gebruik=False)
                .order_by('volgorde'))
        prev = 0
        for klasse in objs:
            groep = klasse.volgorde // 10
            klasse.separate_before = groep != prev
            klasse.boogtypen_list = [boogtype.beschrijving for boogtype in klasse.boogtypen.only('beschrijving', 'volgorde').order_by('volgorde')]
            prev = groep
        # for
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['indivklassen'] = self._get_queryset_indivklassen()
        context['teamklassen'] = self._get_queryset_teamklassen()
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

        # beveiliging tegen dubbel aanmaken
        if Competitie.objects.filter(is_afgesloten=False).order_by('begin_jaar', 'afstand').count() == 0:
            seizoen = "%s/%s" % (jaar, jaar+1)
            schrijf_in_logboek(request.user, 'Competitie', 'Aanmaken competities %s' % seizoen)
            competitie_aanmaken(jaar)

        return redirect('Competitie:overzicht')

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        jaar = models_bepaal_startjaar_nieuwe_competitie()
        context['seizoen'] = "%s/%s" % (jaar, jaar+1)

        # beveiliging tegen dubbel aanmaken
        if Competitie.objects.filter(is_afgesloten=False).order_by('begin_jaar', 'afstand').count() > 0:
            context['bestaat_al'] = True

        menu_dynamics(self.request, context, actief='competitie')
        return context


class AGVaststellenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan de BB de aanvangsgemiddelden vaststellen
        HistComp wordt doorzocht op bekende schutter-boog en de uitslag wordt overgenomen als AG
    """

    template_name = TEMPLATE_COMPETITIE_AG_VASTSTELLEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        if rol_nu != Rollen.ROL_BB:
            return False

        # alleen toestaan als een van de competities in fase A1 is
        kan_ag_vaststellen = False
        for comp in Competitie.objects.filter(is_afgesloten=False):
            zet_fase(comp)
            if comp.fase == 'A1':
                kan_ag_vaststellen = True
        # for
        return kan_ag_vaststellen

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        context = super().get_context_data(**kwargs)

        # zoek uit wat de meest recente HistComp is
        histcomps = HistCompetitie.objects.order_by('-seizoen').all()
        if len(histcomps) == 0:
            context['geen_histcomp'] = True
        else:
            context['seizoen'] = histcomps[0].seizoen

        menu_dynamics(self.request, context, actief='competitie')
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            --> de beheerder wil de AG's vaststellen
        """
        # zoek uit wat de meest recente HistComp is
        histcomps = HistCompetitie.objects.order_by('-seizoen').all()
        if len(histcomps) > 0:
            seizoen = histcomps[0].seizoen

            schrijf_in_logboek(request.user, 'Competitie', 'Aanvangsgemiddelden vastgesteld met uitslag seizoen %s' % seizoen)

            # het eindjaar van de competitie was bepalend voor de klasse
            # daarmee kunnen we bepalen of de schutter aspirant was
            eindjaar = int(seizoen.split('/')[1])

            # maak een cache aan van boogtype
            boogtype_dict = dict()  # [afkorting] = BoogType
            for obj in BoogType.objects.all():
                boogtype_dict[obj.afkorting] = obj
            # for

            # maak een cache aan van nhb leden
            # we filteren hier niet op inactieve leden
            nhblid_dict = dict()  # [nhb_nr] = NhbLid
            for obj in NhbLid.objects.all():
                nhblid_dict[obj.nhb_nr] = obj
            # for

            # maak een cache aan van schutter-boog
            schutterboog_cache = dict()     # [schutter_nr, boogtype_afkorting] = SchutterBoog
            for schutterboog in SchutterBoog.objects.select_related('nhblid', 'boogtype'):
                tup = (schutterboog.nhblid.nhb_nr, schutterboog.boogtype.afkorting)
                schutterboog_cache[tup] = schutterboog
            # for

            # verwijder alle bestaande aanvangsgemiddelden
            Score.objects.filter(is_ag=True, afstand_meter=18).all().delete()
            Score.objects.filter(is_ag=True, afstand_meter=25).all().delete()
            bulk_score = list()

            now = timezone.now()
            datum = datetime.date(year=now.year, month=now.month, day=now.day)

            # doorloop alle individuele histcomp records die bij dit seizoen horen
            for obj in (HistCompetitieIndividueel
                        .objects
                        .select_related('histcompetitie')
                        .filter(histcompetitie__seizoen=seizoen)):
                afstand_meter = int(obj.histcompetitie.comp_type)
                if obj.gemiddelde > AG_NUL and obj.boogtype in boogtype_dict:
                    # haal het schutterboog record op, of maak een nieuwe aan
                    try:
                        tup = (obj.schutter_nr, obj.boogtype)
                        schutterboog = schutterboog_cache[tup]
                    except KeyError:
                        # nieuw record nodig
                        schutterboog = SchutterBoog()
                        schutterboog.boogtype = boogtype_dict[obj.boogtype]
                        schutterboog.voor_wedstrijd = True

                        try:
                            schutterboog.nhblid = nhblid_dict[obj.schutter_nr]
                        except KeyError:
                            # geen lid meer - skip
                            schutterboog = None
                        else:
                            schutterboog.save()
                    else:
                        if not schutterboog.voor_wedstrijd:
                            schutterboog.voor_wedstrijd = True
                            schutterboog.save()

                    if schutterboog:
                        # aspiranten schieten op een grotere kaart en altijd op 18m
                        # daarom AG van aspirant niet overnemen als deze cadet wordt
                        # aangezien er maar 1 klasse is, is het AG niet nodig
                        # voorbeeld: eindjaar = 2019
                        #       geboortejaar = 2006 --> leeftijd was 13, dus aspirant
                        #       geboortejaar = 2005 --> leeftijd was 14, dus cadet
                        was_aspirant = (eindjaar - schutterboog.nhblid.geboorte_datum.year) <= MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT

                        # zoek het score record erbij
                        if not was_aspirant:
                            # eerste aanvangsgemiddelde voor deze afstand
                            waarde = int(obj.gemiddelde * 1000)

                            score = Score(schutterboog=schutterboog,
                                          is_ag=True,
                                          waarde=waarde,
                                          afstand_meter=afstand_meter)
                            bulk_score.append(score)

                            if len(bulk_score) >= 500:
                                Score.objects.bulk_create(bulk_score)
                                bulk_score = list()
            # for

            if len(bulk_score) > 0:
                Score.objects.bulk_create(bulk_score)
            del bulk_score

            # maak nu alle ScoreHist entries in 1x aan
            bulk_scorehist = list()
            notitie = "Uitslag competitie seizoen %s" % seizoen
            for score in Score.objects.all():
                scorehist = ScoreHist(score=score,
                                      oude_waarde=0,
                                      nieuwe_waarde=score.waarde,
                                      datum=datum,
                                      door_account=None,
                                      notitie=notitie)
                bulk_scorehist.append(scorehist)

                if len(bulk_scorehist) > 250:
                    ScoreHist.objects.bulk_create(bulk_scorehist)
                    bulk_scorehist = list()
            # for
            if len(bulk_scorehist) > 0:
                ScoreHist.objects.bulk_create(bulk_scorehist)

        return redirect('Competitie:overzicht')


class LijstAangemeldRegioView(TemplateView):

    """ Toon een lijst van SchutterBoog die aangemeld zijn voor de regiocompetitie """

    template_name = TEMPLATE_COMPETITIE_AANGEMELD_REGIO

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        comp_pk = kwargs['comp_pk']

        try:
            context['competitie'] = Competitie.objects.get(pk=comp_pk)
        except Competitie.DoesNotExist:
            raise Resolver404()

        context['object_list'] = (RegioCompetitieSchutterBoog
                                  .objects
                                  .select_related('klasse', 'klasse__indiv', 'deelcompetitie', 'schutterboog', 'schutterboog__nhblid', 'schutterboog__nhblid__bij_vereniging')
                                  .filter(deelcompetitie__competitie=comp_pk)
                                  .order_by('klasse__indiv__volgorde', 'aanvangsgemiddelde'))

        volgorde = -1
        for obj in context['object_list']:
            if volgorde != obj.klasse.indiv.volgorde:
                obj.nieuwe_klasse = True
                volgorde = obj.klasse.indiv.volgorde
        # for

        menu_dynamics(self.request, context, actief='competitie')
        return context


class KlassegrenzenVaststellenView(UserPassesTestMixin, TemplateView):

    """ deze view laat de klassengrenzen voor de volgende competitie zien,
        aan de hand van de al vastgestelde aanvangsgemiddelden
        De BKO kan deze bevestigen, waarna ze aan de competitie toegevoegd worden
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_KLASSEGRENZEN_VASTSTELLEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BB

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    @staticmethod
    def _get_targets():
        """ Retourneer een data structuur met daarin voor alle wedstrijdklassen
            de toegestane boogtypen en leeftijden

            out: target = dict() met [ (min_age, max_age, boogtype, heeft_onbekend) ] = list(IndivWedstrijdklasse)

            Voorbeeld: { (21,150,'R',True ): [obj1, obj2, etc.],
                         (21,150,'C',True ): [obj10, obj11],
                         (14, 17,'C',False): [obj20,]  }
        """
        targets = dict()        # [ (min_age, max_age, boogtype) ] = list(wedstrijdklassen)
        for wedstrklasse in (IndivWedstrijdklasse
                             .objects
                             .select_related('boogtype')
                             .filter(buiten_gebruik=False)
                             .order_by('volgorde')):
            # zoek de minimale en maximaal toegestane leeftijden voor deze wedstrijdklasse
            age_min = 999
            age_max = 0
            for lkl in wedstrklasse.leeftijdsklassen.all():
                age_min = min(lkl.min_wedstrijdleeftijd, age_min)
                age_max = max(lkl.max_wedstrijdleeftijd, age_max)
            # for

            tup = (age_min, age_max, wedstrklasse.boogtype)
            if tup not in targets:
                targets[tup] = list()
            targets[tup].append(wedstrklasse)
        # for

        targets2 = dict()
        for tup, wedstrklassen in targets.items():
            age_min, age_max, boogtype = tup
            # print("age=%s..%s, boogtype=%s, wkl=%s, %s" % (age_min, age_max, boogtype.afkorting, repr(wedstrklassen), wedstrklassen[-1].is_onbekend))
            tup = (age_min, age_max, boogtype, wedstrklassen[-1].is_onbekend)
            targets2[tup] = wedstrklassen
        # for
        return targets2

    def _get_queryset(self, afstand):
        """ called by the template system to get the queryset or list of objects for the template """

        # bepaal het jaar waarin de wedstrijdleeftijd bepaald moet worden
        # dit is het huidige jaar + 1
        self.wedstrijdjaar = jaar = 1 + models_bepaal_startjaar_nieuwe_competitie()

        # eenmalig de wedstrijdleeftijd van elke nhblid berekenen
        schutternr2age = dict()     # [ nhb_nr ] = age
        for lid in NhbLid.objects.all():
            schutternr2age[lid.nhb_nr] = lid.bereken_wedstrijdleeftijd(jaar)
        # for

        # wedstrijdklassen vs leeftijd + bogen
        targets = self._get_targets()

        # creëer de resultatenlijst
        objs = list()
        for tup, wedstrklassen in targets.items():
            min_age, max_age, boogtype, heeft_klasse_onbekend = tup

            # zoek alle schutters-boog die hier in passen (boog, leeftijd)
            gemiddelden = list()
            for score in (Score
                          .objects
                          .select_related('schutterboog', 'schutterboog__boogtype', 'schutterboog__nhblid')
                          .filter(is_ag=True, afstand_meter=afstand, schutterboog__boogtype=boogtype)):
                age = schutternr2age[score.schutterboog.nhblid.nhb_nr]
                if min_age <= age <= max_age:
                    gemiddelden.append(score.waarde)        # is AG*1000
            # for

            if len(gemiddelden):
                gemiddelden.sort(reverse=True)  # in-place sort, highest to lowest
                count = len(gemiddelden)        # aantal schutters
                aantal = len(wedstrklassen)     # aantal groepen
                if heeft_klasse_onbekend:
                    stop = -2
                    aantal -= 1
                else:
                    stop = -1
                step = int(count / aantal)      # omlaag afgerond = OK voor grote groepen
                pos = 0
                for klasse in wedstrklassen[:stop]:
                    pos += step
                    ag = gemiddelden[pos] / 1000        # conversie Score naar AG met 3 decimale
                    res = {'beschrijving': klasse.beschrijving,
                           'count': step,
                           'ag': ag,
                           'wedstrkl_obj': klasse,
                           'volgorde': klasse.volgorde}
                    objs.append(res)
                # for

                # laatste klasse krijgt speciaal AG
                klasse = wedstrklassen[stop]
                ag = AG_LAAGSTE_NIET_NUL if heeft_klasse_onbekend else AG_NUL
                res = {'beschrijving': klasse.beschrijving,
                       'count': count - (aantal - 1) * step,
                       'ag': ag,
                       'wedstrkl_obj': klasse,
                       'volgorde': klasse.volgorde}
                objs.append(res)

                # klasse onbekend met AG=0.000
                if heeft_klasse_onbekend:
                    klasse = wedstrklassen[-1]
                    res = {'beschrijving': klasse.beschrijving,
                           'count': 0,
                           'ag': AG_NUL,
                           'wedstrkl_obj': klasse,
                           'volgorde': klasse.volgorde}
                    objs.append(res)
            else:
                # geen historische gemiddelden
                # zet ag op 0,001 als er een klasse onbekend is, anders op 0,000
                ag = AG_LAAGSTE_NIET_NUL if heeft_klasse_onbekend else AG_NUL
                for klasse in wedstrklassen:
                    if klasse.is_onbekend:  # is de laatste klasse
                        ag = AG_NUL
                    res = {'beschrijving': klasse.beschrijving,
                           'count': 0,
                           'ag': ag,
                           'wedstrkl_obj': klasse,
                           'volgorde': klasse.volgorde}
                    objs.append(res)
                # for
        # for
        objs2 = sorted(objs, key=lambda k: k['volgorde'])
        return objs2

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        context = super().get_context_data(**kwargs)

        # stukje input beveiliging: begrens tot 2 tekens getal (18/25)
        afstand_str = kwargs['afstand'][:2]
        try:
            afstand = int(afstand_str)
        except ValueError:
            raise Resolver404()

        objs = Competitie.objects.filter(afstand=afstand_str, is_afgesloten=False)
        if objs.count() == 0:
            # onverwachts here
            raise Resolver404()
        obj = objs[0]

        if obj.competitieklasse_set.count() != 0:
            context['al_vastgesteld'] = True
        else:
            context['object_list'] = self._get_queryset(afstand)
            context['wedstrijdjaar'] = self.wedstrijdjaar

        context['comp_str'] = obj.beschrijving
        context['afstand'] = afstand_str

        menu_dynamics(self.request, context, actief='competitie')
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            --> de beheerder wil deze klassegrenzen vaststellen
        """
        afstand_str = kwargs['afstand']
        try:
            afstand = int(afstand_str)
        except ValueError:
            raise Resolver404()

        objs = Competitie.objects.filter(afstand=afstand_str, is_afgesloten=False)
        if objs.count() > 0:
            comp = objs[0]

            if comp.competitieklasse_set.count() != 0:
                # onverwachts here
                raise Resolver404()

            # haal dezelfde data op als voor de GET request
            for obj in self._get_queryset(afstand):
                maak_competitieklasse_indiv(comp, obj['wedstrkl_obj'], obj['ag'])
            # for

            schrijf_in_logboek(request.user, 'Competitie', 'Klassegrenzen bevestigd voor %s' % comp.beschrijving)

        return redirect('Competitie:overzicht')


class KlassegrenzenTonenView(ListView):

    """ deze view laat de vastgestelde aanvangsgemiddelden voor de volgende competitie zien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_KLASSEGRENZEN_TONEN

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        objs = list()
        if CompetitieKlasse.objects.filter(team=None).count() == 0:
            return objs

        indiv_dict = dict()     # [indiv.pk] = IndivWedstrijdklasse
        for obj in IndivWedstrijdklasse.objects.order_by('volgorde'):
            indiv_dict[obj.pk] = obj
            objs.append(obj)
        # for

        for obj in CompetitieKlasse.objects.filter(team=None).select_related('competitie', 'indiv'):
            indiv = indiv_dict[obj.indiv.pk]
            min_ag = obj.min_ag
            if min_ag != AG_NUL:
                if obj.competitie.afstand == '18':
                    indiv.min_ag18 = obj.min_ag
                else:
                    indiv.min_ag25 = obj.min_ag
        # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context, actief='competitie')
        return context


class InfoCompetitieView(TemplateView):

    """ Django class-based view voor de Competitie Info """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_INFO_COMPETITIE

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['regios'] = (NhbRegio
                             .objects
                             .filter(is_administratief=False)
                             .select_related('rayon')
                             .order_by('regio_nr'))

        account = self.request.user
        if account and account.is_authenticated:
            if account.nhblid_set.count() > 0:
                nhblid = account.nhblid_set.all()[0]
                nhb_ver = nhblid.bij_vereniging
                if nhb_ver:
                    context['mijn_vereniging'] = nhb_ver
                    for obj in context['regios']:
                        if obj == nhb_ver.regio:
                            obj.mijn_regio = True
                    # for

        context['klassen_count'] = IndivWedstrijdklasse.objects.exclude(is_onbekend=True).count()

        menu_dynamics(self.request, context, actief='competitie')
        return context


class WijzigDatumsView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor het wijzigen van de competitie datums """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_WIJZIG_DATUMS

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BB

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        comp_pk = kwargs['comp_pk'][:6]     # afkappen geeft beveiliging
        try:
            competitie = Competitie.objects.get(pk=comp_pk)
        except Competitie.DoesNotExist:
            raise Resolver404()

        context['competitie'] = competitie
        competitie.datum1 = competitie.begin_aanmeldingen
        competitie.datum2 = competitie.einde_aanmeldingen
        competitie.datum3 = competitie.einde_teamvorming
        competitie.datum4 = competitie.eerste_wedstrijd

        context['wijzig_url'] = reverse('Competitie:wijzig-datums', kwargs={'comp_pk': competitie.pk})

        menu_dynamics(self.request, context, actief='competitie')
        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            --> de beheerder wil deze klassegrenzen vaststellen
        """
        comp_pk = kwargs['comp_pk'][:6]     # afkappen geeft beveiliging
        try:
            competitie = Competitie.objects.get(pk=comp_pk)
        except Competitie.DoesNotExist:
            raise Resolver404()

        datum1 = request.POST.get('datum1', None)
        datum2 = request.POST.get('datum2', None)
        datum3 = request.POST.get('datum3', None)
        datum4 = request.POST.get('datum4', None)

        # alle vier datums zijn verplicht
        if not (datum1 and datum2 and datum3 and datum4):
            raise Resolver404()

        try:
            datum1 = datetime.datetime.strptime(datum1, '%Y-%m-%d')
            datum2 = datetime.datetime.strptime(datum2, '%Y-%m-%d')
            datum3 = datetime.datetime.strptime(datum3, '%Y-%m-%d')
            datum4 = datetime.datetime.strptime(datum4, '%Y-%m-%d')
        except ValueError:
            raise Resolver404()

        competitie.begin_aanmeldingen = datum1.date()
        competitie.einde_aanmeldingen = datum2.date()
        competitie.einde_teamvorming = datum3.date()
        competitie.eerste_wedstrijd = datum4.date()
        competitie.save()

        return HttpResponseRedirect(reverse('Competitie:overzicht'))


class BondPlanningView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de planning voor een competitie op het landelijke niveau """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_PLANNING_BOND

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        deelcomp_pk = kwargs['deelcomp_pk'][:6]     # afkappen geeft beveiliging
        try:
            deelcomp_bk = (DeelCompetitie
                           .objects
                           .select_related('competitie')
                           .get(pk=deelcomp_pk))
        except DeelCompetitie.DoesNotExist:
            raise Resolver404()

        if deelcomp_bk.laag != LAAG_BK:
            raise Resolver404()

        context['deelcomp_bk'] = deelcomp_bk

        context['rayon_deelcomps'] = (DeelCompetitie
                                      .objects
                                      .filter(laag=LAAG_RK,
                                              competitie=deelcomp_bk.competitie)
                                      .order_by('nhb_rayon__rayon_nr'))

        menu_dynamics(self.request, context, actief='competitie')
        return context


class RayonPlanningView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de planning voor een competitie in een rayon """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_PLANNING_RAYON

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        deelcomp_pk = kwargs['deelcomp_pk'][:6]     # afkappen geeft beveiliging
        try:
            deelcomp_rk = (DeelCompetitie
                           .objects
                           .select_related('competitie', 'nhb_rayon')
                           .get(pk=deelcomp_pk))
        except DeelCompetitie.DoesNotExist:
            raise Resolver404()

        if deelcomp_rk.laag != LAAG_RK:
            raise Resolver404()

        rol_nu = rol_get_huidige(self.request)

        context['deelcomp_rk'] = deelcomp_rk
        context['rayon'] = deelcomp_rk.nhb_rayon

        if rol_nu == Rollen.ROL_BKO:
            deelcomp_bk = DeelCompetitie.objects.get(laag=LAAG_BK,
                                                     competitie=deelcomp_rk.competitie)
            context['url_bond'] = reverse('Competitie:bond-planning', kwargs={'deelcomp_pk': deelcomp_bk.pk})

        context['regio_deelcomps'] = (DeelCompetitie
                                      .objects
                                      .filter(laag=LAAG_REGIO,
                                              competitie=deelcomp_rk.competitie,
                                              nhb_regio__rayon=deelcomp_rk.nhb_rayon)
                                      .order_by('nhb_regio__regio_nr'))

        menu_dynamics(self.request, context, actief='competitie')
        return context


class RegioPlanningView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de planning voor een competitie in een regio """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_PLANNING_REGIO

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        deelcomp_pk = kwargs['deelcomp_pk'][:6]     # afkappen geeft beveiliging
        try:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_regio', 'nhb_regio__rayon')
                        .get(pk=deelcomp_pk))
        except DeelCompetitie.DoesNotExist:
            raise Resolver404()

        if deelcomp.laag != LAAG_REGIO:
            raise Resolver404()

        context['deelcomp'] = deelcomp
        context['regio'] = deelcomp.nhb_regio

        context['rondes'] = (DeelcompetitieRonde
                             .objects
                             .filter(deelcompetitie=deelcomp, cluster=None)
                             .order_by('week_nr'))

        for ronde in context['rondes']:
            ronde.wedstrijd_count = ronde.plan.wedstrijden.count()
        # for

        # alleen de RCL mag de planning uitbreiden
        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rollen.ROL_RCL and context['rondes'].count() < 10:
            context['url_nieuwe_week'] = reverse('Competitie:regio-planning',
                                                 kwargs={'deelcomp_pk': deelcomp.pk})

        # zoek de bruikbare clusters
        clusters = (NhbCluster
                    .objects
                    .filter(regio=deelcomp.nhb_regio,
                            gebruik=deelcomp.competitie.afstand)
                    .prefetch_related('nhbvereniging_set', 'deelcompetitieronde_set')
                    .select_related('regio')
                    .order_by('letter'))
        context['clusters'] = list()
        for cluster in clusters:
            if cluster.nhbvereniging_set.count() > 0:
                context['clusters'].append(cluster)
                # tel het aantal rondes voor dit cluster
                cluster.ronde_count = cluster.deelcompetitieronde_set.count()
        # for
        if len(context['clusters']) > 0:
            context['show_clusters'] = True

        if rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO):
            rayon = DeelCompetitie.objects.get(laag=LAAG_RK,
                                               competitie=deelcomp.competitie,
                                               nhb_rayon=deelcomp.nhb_regio.rayon)
            context['url_rayon'] = reverse('Competitie:rayon-planning',
                                           kwargs={'deelcomp_pk': rayon.pk})

        menu_dynamics(self.request, context, actief='competitie')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Regel toevoegen' gebruikt wordt
        """

        # alleen de RCL mag de planning uitbreiden
        rol_nu = rol_get_huidige(self.request)
        if rol_nu != Rollen.ROL_RCL:
            raise Resolver404()

        deelcomp_pk = kwargs['deelcomp_pk'][:6]     # afkappen geeft beveiliging
        try:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_regio')
                        .get(pk=deelcomp_pk))
        except DeelCompetitie.DoesNotExist:
            raise Resolver404()

        if deelcomp.laag != LAAG_REGIO:
            raise Resolver404()

        ronde = maak_deelcompetitie_ronde(deelcomp=deelcomp)

        next_url = reverse('Competitie:regio-ronde-planning', kwargs={'ronde_pk': ronde.pk})

        return HttpResponseRedirect(next_url)


class RegioClusterPlanningView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de planning voor een competitie in een regio """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_PLANNING_REGIO_CLUSTER

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        cluster_pk = kwargs['cluster_pk'][:6]     # afkappen geeft beveiliging
        try:
            cluster = (NhbCluster
                       .objects
                       .select_related('regio', 'regio__rayon')
                       .get(pk=cluster_pk))
        except NhbCluster.DoesNotExist:
            raise Resolver404()

        context['cluster'] = cluster
        context['regio'] = cluster.regio

        try:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(laag=LAAG_REGIO,
                             nhb_regio=cluster.regio,
                             competitie__afstand=cluster.gebruik))
        except DeelCompetitie.DoesNotExist:
            raise Resolver404()

        context['deelcomp'] = deelcomp

        context['rondes'] = (DeelcompetitieRonde
                             .objects
                             .filter(deelcompetitie=deelcomp,
                                     cluster=cluster)
                             .order_by('week_nr'))

        for ronde in context['rondes']:
            ronde.wedstrijd_count = ronde.plan.wedstrijden.count()
        # for

        # alleen de RCL mag de planning uitbreiden
        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rollen.ROL_RCL and context['rondes'].count() < 10:
            context['url_nieuwe_week'] = reverse('Competitie:regio-cluster-planning',
                                                 kwargs={'cluster_pk': cluster.pk})

        context['terug_url'] = reverse('Competitie:regio-planning',
                                       kwargs={'deelcomp_pk': deelcomp.pk})

        menu_dynamics(self.request, context, actief='competitie')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Regel toevoegen' gebruikt wordt
        """

        # alleen de RCL mag de planning uitbreiden
        rol_nu = rol_get_huidige(self.request)
        if rol_nu != Rollen.ROL_RCL:
            raise Resolver404()

        cluster_pk = kwargs['cluster_pk'][:6]     # afkappen geeft beveiliging
        try:
            cluster = (NhbCluster
                       .objects
                       .select_related('regio', 'regio__rayon')
                       .get(pk=cluster_pk))
        except NhbCluster.DoesNotExist:
            raise Resolver404()

        try:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(laag=LAAG_REGIO,
                             nhb_regio=cluster.regio,
                             competitie__afstand=cluster.gebruik))
        except DeelCompetitie.DoesNotExist:
            raise Resolver404()

        ronde = maak_deelcompetitie_ronde(deelcomp=deelcomp, cluster=cluster)

        next_url = reverse('Competitie:regio-ronde-planning', kwargs={'ronde_pk': ronde.pk})

        return HttpResponseRedirect(next_url)


def competitie_week_nr_to_date(jaar, week_nr):
    # de competitie begin na de zomer
    # dus als het weeknummer voor de zomer valt, dan is het in het volgende jaar
    if week_nr <= 26:
        jaar += 1

    # let op: week nummers zijn 0-based in strptime!
    when = datetime.datetime.strptime("%s-%s-1" % (jaar, week_nr-1), "%Y-%W-%w")   # 1 = maandag

    return datetime.date(year=when.year, month=when.month, day=when.day)


class RegioRondePlanningView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de planning van een ronde in een regio """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_PLANNING_REGIO_RONDE

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        ronde_pk = kwargs['ronde_pk'][:6]     # afkappen geeft beveiliging
        try:
            ronde = (DeelcompetitieRonde
                     .objects
                     .select_related('deelcompetitie__competitie',
                                     'deelcompetitie__nhb_regio__rayon',
                                     'cluster__regio')
                     .get(pk=ronde_pk))
        except DeelcompetitieRonde.DoesNotExist:
            raise Resolver404()

        context['ronde'] = ronde

        context['wedstrijden'] = (ronde.plan.wedstrijden
                                  .order_by('datum_wanneer', 'tijd_begin_aanmelden')
                                  .select_related('vereniging'))

        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rollen.ROL_RCL:
            context['url_nieuwe_wedstrijd'] = reverse('Competitie:regio-ronde-planning',
                                                      kwargs={'ronde_pk': ronde.pk})

            for wedstrijd in context['wedstrijden']:
                wedstrijd.url_wijzig = reverse('Competitie:wijzig-wedstrijd', kwargs={'wedstrijd_pk': wedstrijd.pk})
            # for

        start_week = 37
        eind_week = 11+1
        if ronde.deelcompetitie.competitie.afstand == '18':
            eind_week = 50+1
        jaar = ronde.deelcompetitie.competitie.begin_jaar

        context['opt_week_nrs'] = opt_week_nrs = list()
        while start_week != eind_week:
            when = competitie_week_nr_to_date(jaar, start_week)
            obj = SimpleNamespace()
            obj.week_nr = start_week
            obj.choice_name = start_week
            obj.maandag = when
            obj.actief = (start_week == ronde.week_nr)
            opt_week_nrs.append(obj)

            if start_week >= 53:
                start_week = 1
                jaar += 1
            else:
                start_week += 1
        # while

        if ronde.cluster:
            terug_url = reverse('Competitie:regio-cluster-planning',
                                kwargs={'cluster_pk': ronde.cluster.pk})
        else:
            terug_url = reverse('Competitie:regio-planning',
                                kwargs={'deelcomp_pk': ronde.deelcompetitie.pk})
        context['terug_url'] = terug_url

        context['ronde_opslaan_url'] = reverse('Competitie:regio-ronde-planning',
                                               kwargs={'ronde_pk': ronde.pk})

        rol_nu = rol_get_huidige(self.request)
        if rol_nu != Rollen.ROL_RCL:
            context['readonly'] = True

        menu_dynamics(self.request, context, actief='competitie')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Regel toevoegen' gebruikt wordt
            en als op de knop Opslaan wordt gedrukt voor de ronde parameters
        """

        ronde_pk = kwargs['ronde_pk'][:6]     # afkappen geeft beveiliging
        try:
            ronde = DeelcompetitieRonde.objects.get(pk=ronde_pk)
        except DeelcompetitieRonde.DoesNotExist:
            raise Resolver404()

        # alleen de RCL mag een wedstrijd toevoegen
        rol_nu = rol_get_huidige(self.request)
        if rol_nu != Rollen.ROL_RCL:
            raise Resolver404()

        # print("RegioRondePlanningView::post kwargs=%s, items=%s" % (repr(kwargs), repr([(key, value) for key,value in request.POST.items()])))

        week_nr = request.POST.get('ronde_week_nr', None)
        if week_nr:
            # het was de Opslaan knop
            try:
                week_nr = int(week_nr)
            except (TypeError, ValueError):
                raise Resolver404()

            # sanity-check op ronde nummer
            if week_nr < 1 or week_nr > 53 or (week_nr > 11 and week_nr < 37):
                # geen valide week nummer
                raise Resolver404()

            beschrijving = request.POST.get('ronde_naam', '')
            ronde.beschrijving = beschrijving[:20]  # afkappen, anders werkt save niet

            if ronde.week_nr != week_nr:
                # nieuw week nummer
                # reken uit hoeveel het verschil is
                jaar = ronde.deelcompetitie.competitie.begin_jaar
                when1 = competitie_week_nr_to_date(jaar, ronde.week_nr)
                when2 = competitie_week_nr_to_date(jaar, week_nr)

                diff = when2 - when1

                # pas de datum van alle wedstrijden met evenveel aan
                for wedstrijd in ronde.plan.wedstrijden.all():
                    wedstrijd.datum_wanneer += diff
                    wedstrijd.save()
                # for

                ronde.week_nr = week_nr

            ronde.save()

            if ronde.cluster:
                next_url = reverse('Competitie:regio-cluster-planning',
                                    kwargs={'cluster_pk': ronde.cluster.pk})
            else:
                next_url = reverse('Competitie:regio-planning',
                                    kwargs={'deelcomp_pk': ronde.deelcompetitie.pk})
        else:
            # voeg een wedstrijd toe
            jaar = ronde.deelcompetitie.competitie.begin_jaar
            wedstrijd = Wedstrijd()
            wedstrijd.datum_wanneer = competitie_week_nr_to_date(jaar, ronde.week_nr)
            wedstrijd.tijd_begin_aanmelden = datetime.time(hour=0, minute=0, second=0)
            wedstrijd.tijd_begin_wedstrijd = wedstrijd.tijd_begin_aanmelden
            wedstrijd.tijd_einde_wedstrijd = wedstrijd.tijd_begin_aanmelden
            wedstrijd.save()

            ronde.plan.wedstrijden.add(wedstrijd)

            # laat de nieuwe wedstrijd meteen wijzigen
            next_url = reverse('Competitie:wijzig-wedstrijd', kwargs={'wedstrijd_pk': wedstrijd.pk})

        return HttpResponseRedirect(next_url)


class WijzigWedstrijdView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de planning van een wedstrijd aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_WIJZIG_WEDSTRIJD

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        wedstrijd_pk = kwargs['wedstrijd_pk'][:6]     # afkappen geeft beveiliging
        try:
            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd_pk)
        except Wedstrijd.DoesNotExist:
            raise Resolver404()

        context['wedstrijd'] = wedstrijd

        # zoek het weeknummer waarin deze wedstrijd gehouden moet worden
        plan = wedstrijd.wedstrijdenplan_set.all()[0]
        ronde = DeelcompetitieRonde.objects.get(plan=plan)

        context['ronde'] = ronde
        context['regio'] = ronde.deelcompetitie.nhb_regio
        context['competitie'] = competitie = ronde.deelcompetitie.competitie

        context['opt_weekdagen'] = opt_weekdagen = list()

        # bepaal de weekdag uit de huidige wedstrijd datum
        jaar = ronde.deelcompetitie.competitie.begin_jaar
        when = competitie_week_nr_to_date(jaar, ronde.week_nr)
        ronde.maandag = when

        verschil = wedstrijd.datum_wanneer - when
        dag_nr = verschil.days

        for weekdag_nr, weekdag_naam in WEEK_DAGEN:
            obj = SimpleNamespace()
            obj.weekdag_nr = weekdag_nr
            obj.weekdag_naam = weekdag_naam
            obj.datum = when
            obj.actief = (dag_nr == weekdag_nr)
            opt_weekdagen.append(obj)

            when = when + datetime.timedelta(days=1)
        # for

        wedstrijd.tijd_begin_wedstrijd_str = wedstrijd.tijd_begin_wedstrijd.strftime("%H:%M")
        # wedstrijd.tijd_begin_aanmelden_str = wedstrijd.tijd_begin_aanmelden.strftime("%H%M")
        # wedstrijd.tijd_einde_wedstrijd_str = wedstrijd.tijd_einde_wedstrijd.strftime("%H%M")

        if ronde.cluster:
            verenigingen = ronde.cluster.nhbvereniging_set.all()
        else:
            verenigingen = ronde.deelcompetitie.nhb_regio.nhbvereniging_set.all()
        context['verenigingen'] = verenigingen

        context['url_opslaan'] = reverse('Competitie:wijzig-wedstrijd', kwargs={'wedstrijd_pk': wedstrijd.pk})
        context['url_terug'] = reverse('Competitie:regio-ronde-planning', kwargs={'ronde_pk': ronde.pk})

        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Opslaan' gebruikt wordt
        """
        wedstrijd_pk = kwargs['wedstrijd_pk'][:6]     # afkappen geeft beveiliging
        try:
            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd_pk)
        except Wedstrijd.DoesNotExist:
            raise Resolver404()

        # print("WijzigWedstrijdView::post kwargs=%s, items=%s" % (repr(kwargs), repr([(key, value) for key, value in request.POST.items()])))

        # alleen de RCL mag een wedstrijd wijzigen
        # TODO: laat de WL de overige datums aanpassen
        rol_nu = rol_get_huidige(self.request)
        if rol_nu != Rollen.ROL_RCL:
            raise Resolver404()

        # weekdag is een cijfer van 0 tm 6
        # aanvang bestaat uit vier cijfers, zoals 0830
        weekdag = request.POST.get('weekdag', '')[:1]     # afkappen = veiligheid
        aanvang = request.POST.get('aanvang', '')[:5]
        nhbver_pk = request.POST.get('nhbver_pk', '')[:6]
        if weekdag == "" or nhbver_pk == "" or len(aanvang) != 5 or aanvang[2] != ':':
            raise Resolver404()

        try:
            weekdag = int(weekdag)
            aanvang = int(aanvang[0:0+2] + aanvang[3:3+2])
        except (TypeError, ValueError):
            raise Resolver404()

        if weekdag < 0 or weekdag > 6 or aanvang < 800 or aanvang > 2200:
            raise Resolver404()

        # bepaal de begin datum van de ronde-week
        plan = wedstrijd.wedstrijdenplan_set.all()[0]
        ronde = DeelcompetitieRonde.objects.get(plan=plan)
        jaar = ronde.deelcompetitie.competitie.begin_jaar
        when = competitie_week_nr_to_date(jaar, ronde.week_nr)
        # voeg nu de offset toe uit de weekdag
        when += datetime.timedelta(days=weekdag)

        # vertaal aanvang naar een tijd
        hour = aanvang // 100
        min = aanvang - (hour * 100)
        if hour < 8 or hour > 22 or min < 0 or min > 59:
            raise Resolver404()

        try:
            nhbver = NhbVereniging.objects.get(pk=nhbver_pk)
        except NhbVereniging.DoesNotExist:
            raise Resolver404()

        wedstrijd.datum_wanneer = when
        wedstrijd.tijd_begin_wedstrijd = datetime.time(hour=hour, minute=min)
        wedstrijd.vereniging = nhbver
        wedstrijd.save()

        url = reverse('Competitie:regio-ronde-planning', kwargs={'ronde_pk': ronde.pk})
        return HttpResponseRedirect(url)

# end of file
