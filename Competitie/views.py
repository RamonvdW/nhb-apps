# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import Resolver404, reverse
from django.views.generic import TemplateView, ListView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.utils import timezone
from django.shortcuts import redirect
from Plein.menu import menu_dynamics
from Logboek.models import schrijf_in_logboek
from Account.rol import rol_is_BKO, rol_is_bestuurder
from BasisTypen.models import TeamType, TeamTypeBoog, BoogType, LeeftijdsKlasse, WedstrijdKlasse, \
                              WedstrijdKlasseBoog, WedstrijdKlasseLeeftijd
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from NhbStructuur.models import NhbLid
from .models import models_bepaal_startjaar_nieuwe_competitie, competitie_aanmaken, maak_competitieklasse_indiv, \
                    Competitie, ZERO, FavorieteBestuurders, add_favoriete_bestuurder, drop_favoriete_bestuurder
from .forms import FavorieteBestuurdersForm, WijzigFavorieteBestuurdersForm


TEMPLATE_COMPETITIE_OVERZICHT = 'competitie/overzicht.dtl'
TEMPLATE_COMPETITIE_OVERZICHT_BESTUURDER = 'competitie/overzicht-bestuurder.dtl'
TEMPLATE_COMPETITIE_INSTELLINGEN = 'competitie/instellingen-nieuwe-competitie.dtl'
TEMPLATE_COMPETITIE_AANMAKEN = 'competitie/competities-aanmaken.dtl'
TEMPLATE_COMPETITIE_KLASSEGRENZEN = 'competitie/klassegrenzen-vaststellen.dtl'
TEMPLATE_COMPETITIE_BEHEER_FAVORIETEN = 'competitie/beheer-favorieten.dtl'


JA_NEE = {False: 'Nee', True: 'Ja'}


class InstellingenVolgendeCompetitieView(UserPassesTestMixin, ListView):

    """ deze view laat de defaults voor de volgende competitie zien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_INSTELLINGEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        res = rol_is_BKO(self.request)
        return res

    def _get_queryset_teamtypen(self):
        objs = TeamType.objects.all()
        for teamtype in objs:
            boogtypen = [obj.boogtype.afkorting for obj in TeamTypeBoog.objects.select_related('boogtype').filter(teamtype=teamtype)]
            teamtype.boogtypen = "+".join(boogtypen)
        # for
        return objs

    def _get_queryset_indivklassen(self):
        objs = WedstrijdKlasse.objects.filter(is_voor_teams=False)
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
        objs = WedstrijdKlasse.objects.filter(is_voor_teams=True)
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
        res = rol_is_BKO(self.request)
        return res

    def post(self, request, *args, **kwargs):
        """ deze functie handelt het http-post verzoek af
            (wat volgt uit het drukken op de knop)
            om de nieuwe competitie op te starten.
        """
        jaar = models_bepaal_startjaar_nieuwe_competitie()
        seizoen = "%s/%s" % (jaar, jaar+1)
        schrijf_in_logboek(request.user, 'Competitie', 'Aanmaken competities %s' % seizoen)
        competitie_aanmaken()
        return redirect('Plein:plein')

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
        res = rol_is_BKO(self.request)
        return res

    def _get_targets(self):
        targets = dict()        # [ (min_age, max_age, tuple(bogen)) ] = list(wedstrijdklassen)
        for wedstrklasse in WedstrijdKlasse.objects.filter(is_voor_teams=False):
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
                # helaas op beschrijving, want we matchen met
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

        # creeer de resultatenlijst
        objs = list()
        histcomps = HistCompetitie.objects.filter(seizoen=self.seizoen, comp_type=afstand, is_team=False)
        targets = self._get_targets()

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
                count = len(gemiddelden)
                aantal = len(wedstrklassen)     # aantal groepen
                step = int(count / aantal)      # omlaag afgerond = OK voor grote groepen
                pos = 0
                for klasse in wedstrklassen[:-1]:
                    pos += step
                    ag = gemiddelden[pos]
                    res = {'beschrijving': klasse.beschrijving, 'count' : step, 'ag': ag, 'wedstrkl_obj': klasse}
                    objs.append(res)
                # for
                # laatste klasse krijgt 0,000 als AG
                klasse = wedstrklassen[-1]
                res = {'beschrijving': klasse.beschrijving, 'count' : count - (aantal - 1) * step, 'ag': ZERO, 'wedstrkl_obj': klasse}
                objs.append(res)
            else:
                # geen historische gemiddelden
                # zet alles op 0,000 - dit geeft een beetje een rommeltje als er meerdere klassen zijn
                for klasse in wedstrklassen:
                    res = {'beschrijving': klasse.beschrijving, 'count': 0, 'ag': ZERO, 'wedstrkl_obj': klasse}
                    objs.append(res)
                # for
        # for
        return objs

    def get(self, request, *args, **kwargs):
        context = super().get_context_data(**kwargs)

        afstand = kwargs['afstand']
        context['afstand'] = afstand

        objs = Competitie.objects.filter(afstand=afstand)
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
        afstand = kwargs['afstand']
        objs = Competitie.objects.filter(afstand=afstand)
        if len(objs) > 0:
            comp = objs[0]
            schrijf_in_logboek(request.user, 'Competitie', 'Klassegrenzen bevestigd voor %s' % comp.beschrijving)
            for obj in self._get_queryset(afstand):
                klasse = obj['wedstrkl_obj']
                maak_competitieklasse_indiv(comp, klasse, obj['ag'])
            # for
        return redirect('Plein:plein')


class CompetitieOverzichtView(View):
    """ Deze view biedt de landingpage vanuit het menu aan
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_OVERZICHT

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """

        context = dict()

        if rol_is_bestuurder(self.request):
            template = TEMPLATE_COMPETITIE_OVERZICHT_BESTUURDER

            context['kan_favorieten_beheren'] = True

            objs = Competitie.objects.filter(is_afgesloten=False).order_by('begin_jaar', 'afstand')
            context['object_list'] = objs
            context['have_active_comps'] = (len(objs) > 0)

            for obj in objs:
                obj.zet_fase()
                obj.is_afgesloten_str = JA_NEE[obj.is_afgesloten]
            # for

            # als er nog geen competitie is voor het huidige jaar, geeft de BKO dan de optie om deze op te starten
            if rol_is_BKO(self.request):
                beginjaar = models_bepaal_startjaar_nieuwe_competitie()
                context['bko_kan_competitie_aanmaken'] = (len(objs.filter(begin_jaar=beginjaar)) == 0)
                if context['bko_kan_competitie_aanmaken']:
                    context['nieuwe_seizoen'] = "%s/%s" % (beginjaar, beginjaar+1)
        else:
            template = TEMPLATE_COMPETITIE_OVERZICHT

        menu_dynamics(self.request, context, actief='competitie')
        return render(request, template, context)


class WijzigFavorieteBestuurdersView(View):

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """
        raise Resolver404()

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Registreer knop.
        """
        if rol_is_bestuurder(request):
            form = WijzigFavorieteBestuurdersForm(request.POST)
            if form.is_valid():
                nhb_nr = form.cleaned_data.get('add_nhb_nr')
                if nhb_nr:
                    add_favoriete_bestuurder(request.user, nhb_nr)
                else:
                    nhb_nr = form.cleaned_data.get('drop_nhb_nr')
                    if nhb_nr:
                        drop_favoriete_bestuurder(request.user, nhb_nr)

        return HttpResponseRedirect(reverse('Competitie:beheerfavorieten'))


class BeheerFavorieteBestuurdersView(UserPassesTestMixin, ListView):

    """ Via deze view kunnen bestuurders hun lijst met favoriete NHB leden beheren """

    template_name = TEMPLATE_COMPETITIE_BEHEER_FAVORIETEN

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.form = FavorieteBestuurdersForm()
        self.get_zoekterm = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_is_bestuurder(self.request)

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        # retourneer een QuerySet voor de template
        # onthoud zaken in de object instantie

        # haal de GET parameters uit de request
        self.form = FavorieteBestuurdersForm(self.request.GET)

        self.have_searched = False

        if self.form.is_valid():
            self.get_zoekterm = self.form.cleaned_data['zoekterm']

            if self.get_zoekterm:
                zoekterm = self.get_zoekterm
                self.have_searched = True
                fav_nhb_nrs = FavorieteBestuurders.objects.filter(zelf=self.request.user).values_list('favlid__nhb_nr', flat=True)
                return NhbLid.objects.exclude(is_actief_lid=False).\
                                      exclude(nhb_nr__in=fav_nhb_nrs).\
                                      annotate(hele_naam=Concat('voornaam', Value(' '), 'achternaam')).\
                                      filter(
                                            Q(nhb_nr__contains=zoekterm) |
                                            Q(voornaam__icontains=zoekterm) |
                                            Q(achternaam__icontains=zoekterm) |
                                            Q(hele_naam__icontains=zoekterm)).\
                                       order_by('nhb_nr')[:50]

        return None

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        context['have_searched'] = self.have_searched
        context['zoekterm'] = self.get_zoekterm
        fav_nhb_nrs = FavorieteBestuurders.objects.filter(zelf=self.request.user).values_list('favlid__nhb_nr', flat=True)
        context['huidige_lijst'] = NhbLid.objects.filter(nhb_nr__in=fav_nhb_nrs)
        menu_dynamics(self.request, context, actief='competitie')
        return context


# end of file
