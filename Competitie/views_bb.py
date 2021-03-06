# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import Resolver404, reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.utils import timezone
from django.conf import settings
from BasisTypen.models import BoogType
from BasisTypen.models import (IndivWedstrijdklasse, TeamWedstrijdklasse,
                               MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT)
from Functie.rol import Rollen, rol_get_huidige
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Logboek.models import schrijf_in_logboek
from NhbStructuur.models import NhbLid
from Plein.menu import menu_dynamics
from Schutter.models import SchutterBoog
from Score.models import Score, ScoreHist, zoek_meest_recente_automatisch_vastgestelde_ag
from django.utils.formats import localize
from .models import (AG_NUL, AG_LAAGSTE_NIET_NUL,
                     Competitie, competitie_aanmaken, CompetitieKlasse)
from .menu import menu_dynamics_competitie
import datetime


TEMPLATE_COMPETITIE_INSTELLINGEN = 'competitie/bb-instellingen-nieuwe-competitie.dtl'
TEMPLATE_COMPETITIE_AANMAKEN = 'competitie/bb-competities-aanmaken.dtl'
TEMPLATE_COMPETITIE_KLASSEGRENZEN_VASTSTELLEN = 'competitie/bb-klassegrenzen-vaststellen.dtl'
TEMPLATE_COMPETITIE_KLASSEGRENZEN_TONEN = 'competitie/klassegrenzen-tonen.dtl'
TEMPLATE_COMPETITIE_AANGEMELD_REGIO = 'competitie/lijst-aangemeld-regio.dtl'
TEMPLATE_COMPETITIE_AG_VASTSTELLEN = 'competitie/bb-ag-vaststellen.dtl'
TEMPLATE_COMPETITIE_INFO_COMPETITIE = 'competitie/info-competitie.dtl'
TEMPLATE_COMPETITIE_WIJZIG_DATUMS = 'competitie/bb-wijzig-datums.dtl'


def models_bepaal_startjaar_nieuwe_competitie():
    """ bepaal het start jaar van de nieuwe competitie """
    return timezone.now().year


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
        objs = (TeamWedstrijdklasse
                .objects
                .filter(buiten_gebruik=False)
                .prefetch_related('boogtypen')
                .order_by('volgorde'))
        prev = 0
        for klasse in objs:
            groep = klasse.volgorde // 10
            klasse.separate_before = groep != prev
            klasse.boogtypen_list = [boogtype.beschrijving for boogtype in klasse.boogtypen.order_by('volgorde')]
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

    @staticmethod
    def post(request, *args, **kwargs):
        """ deze functie handelt het http-post verzoek af
            (wat volgt uit het drukken op de knop)
            om de nieuwe competitie op te starten.
        """
        jaar = models_bepaal_startjaar_nieuwe_competitie()

        # beveiliging tegen dubbel aanmaken
        if Competitie.objects.filter(begin_jaar=jaar).count() == 0:
            seizoen = "%s/%s" % (jaar, jaar+1)
            schrijf_in_logboek(request.user, 'Competitie', 'Aanmaken competities %s' % seizoen)
            competitie_aanmaken(jaar)

        return redirect('Competitie:kies')

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        jaar = models_bepaal_startjaar_nieuwe_competitie()
        context['seizoen'] = "%s/%s" % (jaar, jaar+1)

        # beveiliging tegen dubbel aanmaken
        if Competitie.objects.filter(begin_jaar=jaar).count() > 0:
            context['bestaat_al'] = True

        menu_dynamics_competitie(self.request, context)
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

        # alleen toestaan als een van de competities in fase A is
        kan_ag_vaststellen = False
        for comp in Competitie.objects.filter(is_afgesloten=False):
            if not comp.klassegrenzen_vastgesteld:
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

        context['aantal_scores_18'] = settings.COMPETITIE_18M_MINIMUM_SCORES_VOOR_AG
        context['aantal_scores_25'] = settings.COMPETITIE_25M_MINIMUM_SCORES_VOOR_AG

        menu_dynamics(self.request, context, actief='competitie')
        return render(request, self.template_name, context)

    @staticmethod
    def post(request, *args, **kwargs):
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

            minimum_aantal_scores = {18: settings.COMPETITIE_18M_MINIMUM_SCORES_VOOR_AG,
                                     25: settings.COMPETITIE_25M_MINIMUM_SCORES_VOOR_AG}

            # doorloop alle individuele histcomp records die bij dit seizoen horen
            for obj in (HistCompetitieIndividueel
                        .objects
                        .select_related('histcompetitie')
                        .filter(histcompetitie__seizoen=seizoen)):
                afstand_meter = int(obj.histcompetitie.comp_type)

                if (obj.gemiddelde > AG_NUL
                        and obj.boogtype in boogtype_dict
                        and obj.tel_aantal_scores() >= minimum_aantal_scores[afstand_meter]):

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
                            # zet het nieuwe record in de cache, anders krijgen we dupes
                            tup = (schutterboog.nhblid.nhb_nr, schutterboog.boogtype.afkorting)
                            schutterboog_cache[tup] = schutterboog
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
                            # aanvangsgemiddelde voor deze afstand
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
                                      door_account=None,
                                      notitie=notitie)
                bulk_scorehist.append(scorehist)

                if len(bulk_scorehist) > 250:
                    ScoreHist.objects.bulk_create(bulk_scorehist)
                    bulk_scorehist = list()
            # for
            if len(bulk_scorehist) > 0:
                ScoreHist.objects.bulk_create(bulk_scorehist)

        return redirect('Competitie:kies')


class KlassegrenzenVaststellenView(UserPassesTestMixin, TemplateView):

    """ deze view laat de klassengrenzen voor de volgende competitie zien,
        aan de hand van de al vastgestelde aanvangsgemiddelden
        De BB kan deze bevestigen, waarna ze aan de competitie toegevoegd worden
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
                             .prefetch_related('leeftijdsklassen')
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

    def _get_queryset(self, comp):
        # bepaal het jaar waarin de wedstrijdleeftijd bepaald moet worden
        # dat is het tweede jaar van de competitie, waarin de BK gehouden wordt
        jaar = comp.begin_jaar + 1

        # eenmalig de wedstrijdleeftijd van elke nhblid berekenen
        schutternr2age = dict()     # [ nhb_nr ] = age
        for lid in NhbLid.objects.all():
            schutternr2age[lid.nhb_nr] = lid.bereken_wedstrijdleeftijd(jaar)
        # for

        # haal de scores 1x op per boogtype
        boogtype2ags = dict()        # [boogtype.afkorting] = scores
        for boogtype in BoogType.objects.all():
            boogtype2ags[boogtype.afkorting] = (Score
                                                .objects
                                                .select_related('schutterboog',
                                                                'schutterboog__boogtype',
                                                                'schutterboog__nhblid')
                                                .filter(is_ag=True,
                                                        afstand_meter=comp.afstand,
                                                        schutterboog__boogtype=boogtype))
        # for

        # wedstrijdklassen vs leeftijd + bogen
        targets = self._get_targets()

        # creëer de resultatenlijst
        objs = list()
        for tup, wedstrklassen in targets.items():
            min_age, max_age, boogtype, heeft_klasse_onbekend = tup

            # zoek alle schutters-boog die hier in passen (boog, leeftijd)
            gemiddelden = list()
            for score in boogtype2ags[boogtype.afkorting]:
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

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen geeft beveiliging
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Resolver404()

        context['comp'] = comp

        if comp.klassegrenzen_vastgesteld:
            context['al_vastgesteld'] = True
        else:
            context['object_list'] = self._get_queryset(comp)
            context['wedstrijdjaar'] = comp.begin_jaar + 1

        datum = zoek_meest_recente_automatisch_vastgestelde_ag()
        if datum:
            context['bb_ag_nieuwste_datum'] = localize(datum.date())

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            --> de beheerder wil deze klassegrenzen vaststellen
        """

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen geeft beveiliging
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Resolver404()

        if not comp.klassegrenzen_vastgesteld:
            bulk = list()

            # haal dezelfde data op als voor de GET request
            for obj in self._get_queryset(comp):
                compkl = CompetitieKlasse(competitie=comp,
                                          indiv=obj['wedstrkl_obj'],
                                          min_ag=obj['ag'])
                bulk.append(compkl)
            # for

            CompetitieKlasse.objects.bulk_create(bulk)

            comp.klassegrenzen_vastgesteld = True
            comp.save()

            schrijf_in_logboek(request.user,
                               'Competitie',
                               'Klassegrenzen vastgesteld voor %s' % comp.beschrijving)

        return redirect('Competitie:kies')


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

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen geeft beveiliging
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Resolver404()

        context['comp'] = comp

        context['wijzig_url'] = reverse('Competitie:wijzig-datums',
                                        kwargs={'comp_pk': comp.pk})

        comp.datum1 = comp.begin_aanmeldingen
        comp.datum2 = comp.einde_aanmeldingen
        comp.datum3 = comp.einde_teamvorming
        comp.datum4 = comp.eerste_wedstrijd
        comp.datum5 = comp.laatst_mogelijke_wedstrijd
        comp.datum6 = comp.rk_eerste_wedstrijd
        comp.datum7 = comp.rk_laatste_wedstrijd
        comp.datum8 = comp.bk_eerste_wedstrijd
        comp.datum9 = comp.bk_laatste_wedstrijd

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return context

    @staticmethod
    def post(request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            --> de beheerder wil deze klassegrenzen vaststellen
        """
        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen geeft beveiliging
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Resolver404()

        datums = list()
        for datum_nr in range(9):
            datum_s = request.POST.get('datum%s' % (datum_nr + 1), None)
            if not datum_s:
                # alle datums zijn verplicht
                raise Resolver404()

            try:
                datum_p = datetime.datetime.strptime(datum_s, '%Y-%m-%d')
            except ValueError:
                raise Resolver404()

            datums.append(datum_p.date())
        # for

        datums.insert(0, None)      # dummy
        comp.begin_aanmeldingen = datums[1]
        comp.einde_aanmeldingen = datums[2]
        comp.einde_teamvorming = datums[3]
        comp.eerste_wedstrijd = datums[4]
        comp.laatst_mogelijke_wedstrijd = datums[5]
        comp.rk_eerste_wedstrijd = datums[6]
        comp.rk_laatste_wedstrijd = datums[7]
        comp.bk_eerste_wedstrijd = datums[8]
        comp.bk_laatste_wedstrijd = datums[9]
        comp.save()

        return HttpResponseRedirect(reverse('Competitie:overzicht',
                                            kwargs={'comp_pk': comp.pk}))

# end of file
