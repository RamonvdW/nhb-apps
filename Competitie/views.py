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
from BasisTypen.models import BoogType, LeeftijdsKlasse
from Plein.menu import menu_dynamics
from Logboek.models import schrijf_in_logboek
from Functie.models import Functie
from Functie.rol import Rollen, rol_get_huidige_functie, rol_get_beschrijving, rol_get_huidige
from BasisTypen.models import IndivWedstrijdklasse, TeamWedstrijdklasse, MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from NhbStructuur.models import NhbLid, NhbVereniging
from Schutter.models import SchutterBoog
from Score.models import Score, ScoreHist, zoek_meest_recente_automatisch_vastgestelde_ag
from .models import Competitie, AG_NUL, AG_LAAGSTE_NIET_NUL, CompetitieKlasse, DeelCompetitie,\
                    competitie_aanmaken, maak_competitieklasse_indiv, RegioCompetitieSchutterBoog
from datetime import date


TEMPLATE_COMPETITIE_OVERZICHT = 'competitie/overzicht.dtl'
TEMPLATE_COMPETITIE_OVERZICHT_CWZ = 'competitie/overzicht-cwz.dtl'
TEMPLATE_COMPETITIE_OVERZICHT_BEHEERDER = 'competitie/overzicht-beheerder.dtl'
TEMPLATE_COMPETITIE_INSTELLINGEN = 'competitie/instellingen-nieuwe-competitie.dtl'
TEMPLATE_COMPETITIE_AANMAKEN = 'competitie/competities-aanmaken.dtl'
TEMPLATE_COMPETITIE_KLASSEGRENZEN = 'competitie/klassegrenzen-vaststellen.dtl'
TEMPLATE_COMPETITIE_LIJST_VERENIGINGEN = 'competitie/lijst-verenigingen.dtl'
TEMPLATE_COMPETITIE_AANGEMELD_REGIO = 'competitie/lijst-aangemeld-regio.dtl'
TEMPLATE_COMPETITIE_AG_VASTSTELLEN = 'competitie/ag-vaststellen.dtl'

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
        if CompetitieKlasse.objects.filter(competitie=comp).count() == 0:
            # A1 = aanvangsgemiddelden en klassegrenzen zijn vastgesteld
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
            objs = Competitie.objects.filter(is_afgesloten=False).order_by('begin_jaar', 'afstand')
        elif functie_nu:
            # toon de competitie waar de functie een rol in heeft
            for deelcomp in DeelCompetitie.objects.filter(is_afgesloten=False, functie=functie_nu):
                objs.append(deelcomp.competitie)
            # for

        context['object_list'] = objs
        context['have_active_comps'] = len(objs) > 0

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
            context['bb_kan_competitie_aanmaken'] = (objs.filter(begin_jaar=beginjaar).count() == 0)

            if context['bb_kan_ag_vaststellen']:
                # zoek uit wanneer dit voor het laatste gedaan is
                datum = zoek_meest_recente_automatisch_vastgestelde_ag()
                if datum:
                    context['bb_ag_nieuwste_datum'] = datum

        return context, TEMPLATE_COMPETITIE_OVERZICHT_BEHEERDER

    def _get_competitie_overzicht_cwz(self, request):
        context = dict()
        self._get_competities(context, Rollen.ROL_CWZ)
        return context, TEMPLATE_COMPETITIE_OVERZICHT_CWZ

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
        elif rol_nu == Rollen.ROL_CWZ:
            context, template = self._get_competitie_overzicht_cwz(request)
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
        objs = IndivWedstrijdklasse.objects.\
                        filter(buiten_gebruik=False).\
                        order_by('volgorde').\
                        select_related('boogtype')
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
        objs = TeamWedstrijdklasse.objects.\
                        filter(buiten_gebruik=False).\
                        order_by('volgorde')
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
            datum = date(year=now.year, month=now.month, day=now.day)

            # doorloop alle individuele histcomp records die bij dit seizoen horen
            for obj in HistCompetitieIndividueel.objects.\
                            select_related('histcompetitie').\
                            filter(histcompetitie__seizoen=seizoen):
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

        if rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO):
            # toon de landelijke lijst
            objs = NhbVereniging.objects.all().exclude(regio__regio_nr=100).order_by('regio__regio_nr', 'nhb_nr')
            if rol_nu == Rollen.ROL_IT:
                for obj in objs:
                    obj.aantal_leden = NhbLid.objects.filter(bij_vereniging=obj).count()
                # for
            return objs

        if rol_nu == Rollen.ROL_RKO:
            # toon de lijst van verenigingen in het rayon van de RKO
            # het rayonnummer is verkrijgbaar via de deelcompetitie van de functie
            return NhbVereniging.objects.filter(regio__rayon=functie.nhb_rayon).exclude(regio__regio_nr=100).order_by('regio__regio_nr', 'nhb_nr')

        # (rol_nu == Rollen.ROL_RCL)
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

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['toon_rayon'] = True
        context['toon_regio'] = True

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        context['huidige_rol'] = rol_get_beschrijving(self.request)

        if rol_nu == Rollen.ROL_IT:
            context['toon_ledental'] = True

        if rol_nu == Rollen.ROL_RKO:
            context['toon_rayon'] = False

        if rol_nu == Rollen.ROL_RCL:
            context['toon_rayon'] = False
            context['toon_regio'] = False
            context['toon_cwzs'] = True

        menu_dynamics(self.request, context, actief='competitie')
        return context


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

        context['object_list'] = RegioCompetitieSchutterBoog.objects.\
                                        select_related('klasse', 'klasse__indiv', 'deelcompetitie', 'schutterboog', 'schutterboog__nhblid', 'schutterboog__nhblid__bij_vereniging').\
                                        filter(deelcompetitie__competitie=comp_pk).\
                                        order_by('klasse__indiv__volgorde', 'aanvangsgemiddelde')

        volgorde = -1
        for obj in context['object_list']:
            if volgorde != obj.klasse.indiv.volgorde:
                obj.nieuwe_klasse = True
                volgorde = obj.klasse.indiv.volgorde
        # for

        menu_dynamics(self.request, context, actief='competitie')
        return context


class KlassegrenzenAGView(UserPassesTestMixin, TemplateView):

    """ deze view laat de aanvangsgemiddelden voor de volgende competitie zien,
        aan de hand van de al vastgestelde aanvangsgemiddelden
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
        for wedstrklasse in IndivWedstrijdklasse.objects.\
                                    select_related('boogtype').\
                                    filter(buiten_gebruik=False).\
                                    order_by('volgorde'):
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
            for score in Score.objects.\
                    select_related('schutterboog', 'schutterboog__boogtype', 'schutterboog__nhblid').\
                    filter(is_ag=True, afstand_meter=afstand, schutterboog__boogtype=boogtype):
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


# end of file
