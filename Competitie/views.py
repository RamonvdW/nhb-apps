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
from Account.models import Account
from Account.rol import rol_is_BKO, rol_is_RKO, rol_is_bestuurder, rol_get_deelcompetitie
from BasisTypen.models import TeamType, TeamTypeBoog, BoogType, LeeftijdsKlasse, WedstrijdKlasse, \
                              WedstrijdKlasseBoog, WedstrijdKlasseLeeftijd
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from NhbStructuur.models import NhbLid
from .models import models_bepaal_startjaar_nieuwe_competitie, competitie_aanmaken, maak_competitieklasse_indiv, \
                    Competitie, ZERO, FavorieteBestuurders, add_favoriete_bestuurder, drop_favoriete_bestuurder, \
                    DeelCompetitie
from .forms import FavorieteBestuurdersForm, WijzigFavorieteBestuurdersForm, KoppelBestuurdersForm


TEMPLATE_COMPETITIE_OVERZICHT = 'competitie/overzicht.dtl'
TEMPLATE_COMPETITIE_OVERZICHT_BESTUURDER = 'competitie/overzicht-bestuurder.dtl'
TEMPLATE_COMPETITIE_INSTELLINGEN = 'competitie/instellingen-nieuwe-competitie.dtl'
TEMPLATE_COMPETITIE_AANMAKEN = 'competitie/competities-aanmaken.dtl'
TEMPLATE_COMPETITIE_KLASSEGRENZEN = 'competitie/klassegrenzen-vaststellen.dtl'
TEMPLATE_COMPETITIE_BEHEER_FAVORIETEN = 'competitie/beheer-favorieten.dtl'
TEMPLATE_COMPETITIE_KOPPEL_BESTUURDERS_OVERZICHT = 'competitie/koppel-bestuurders-overzicht.dtl'
TEMPLATE_COMPETITIE_KOPPEL_BESTUURDERS_WIJZIG = 'competitie/koppel-bestuurders-wijzig.dtl'


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
                obj.wijzig_url = reverse('Competitie:toon-competitie-bestuurders', kwargs={'comp_pk': obj.id})
            # for

            # als er nog geen competitie is voor het huidige jaar, geeft de BKO dan de optie om deze op te starten
            if rol_is_BKO(self.request):
                beginjaar = models_bepaal_startjaar_nieuwe_competitie()
                context['bko_kan_competitie_aanmaken'] = (len(objs.filter(begin_jaar=beginjaar)) == 0)
                if context['bko_kan_competitie_aanmaken']:
                    context['nieuwe_seizoen'] = "%s/%s" % (beginjaar, beginjaar+1)
                context['bko_kan_rko_koppelen'] = True
                context['bko__kan_klassegrenzen_vaststellen'] = True
            elif rol_is_RKO(self.request):
                context['rko_kan_rcl_koppelen'] = True
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
            form.full_clean()       # vult cleaned_data
            # form is altijd valid, dus niet nodig om is_valid aan te roepen

            account_pk = form.cleaned_data.get('add_favoriet')
            if account_pk:
                add_favoriete_bestuurder(request.user, account_pk)

            account_pk = form.cleaned_data.get('drop_favoriet')
            if account_pk:
                drop_favoriete_bestuurder(request.user, account_pk)

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
        self.form.full_clean()      # vult cleaned_data
        # formulier is altijd goed, dus niet nodig om is_valid te gebruiken

        zoekterm = self.form.cleaned_data['zoekterm']

        if len(zoekterm) >= 2:      # minimaal twee tekens van de naam/nummer
            self.have_searched = True
            self.get_zoekterm = zoekterm
            fav_accounts = FavorieteBestuurders.objects.filter(zelf=self.request.user).values_list('favoriet__pk', flat=True)
            return Account.objects.exclude(pk__in=fav_accounts).\
                                   exclude(nhblid__is_actief_lid=False).\
                                   annotate(hele_naam=Concat('nhblid__voornaam', Value(' '), 'nhblid__achternaam')).\
                                   filter(
                                        Q(username__icontains=zoekterm) |       # dekt ook nhb_nr
                                        Q(nhblid__voornaam__icontains=zoekterm) |
                                        Q(nhblid__achternaam__icontains=zoekterm) |
                                        Q(hele_naam__icontains=zoekterm)).order_by('nhblid__nhb_nr')[:50]

        self.have_searched = False
        self.zoekterm = ""
        return None

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        context['have_searched'] = self.have_searched
        context['zoekterm'] = self.get_zoekterm
        context['favoriete_bestuurders'] = FavorieteBestuurders.objects.filter(zelf=self.request.user)
        menu_dynamics(self.request, context, actief='competitie')
        return context


class KoppelBestuurdersOntvangWijzigingView(View):

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """
        raise Resolver404()

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Registreer knop.
        """

        url = reverse('Competitie:overzicht')

        if rol_is_bestuurder(request):
            # zoek de huidige bestuurders erbij
            fav_bestuurders = FavorieteBestuurders.objects.filter(zelf=self.request.user)
            form = KoppelBestuurdersForm(request.POST, fav_bestuurders=fav_bestuurders)
            if form.is_valid():
                # zoek de DeelCompetitie erbij
                try:
                    deelcompetitie = DeelCompetitie.objects.get(pk=form.cleaned_data.get('deelcomp_pk'))
                except DeelCompetitie.DoesNotExist:
                    raise Resolver404()

                functie = deelcompetitie.functies.all()[0]

                # gooi alle gekoppelde bestuurders weg
                functie.user_set.clear()

                # koppel de gekozen bestuurders (oud en nieuw)
                for obj in fav_bestuurders:
                    is_gekozen = form.cleaned_data.get('bestuurder_%s' % obj.favoriet.pk)
                    if is_gekozen:
                        # voeg het account toe aan de functie
                        functie.user_set.add(obj.favoriet)
                # for

                url = reverse('Competitie:toon-competitie-bestuurders', kwargs={'comp_pk': deelcompetitie.competitie.pk})
            #else:
            #    print("form is not valid: %s" % repr(form.errors))

        return HttpResponseRedirect(url)


def bestuurder_context_str(account):
    if account.nhblid:
        lid = account.nhblid
        if lid.bij_vereniging:
            ver = lid.bij_vereniging
            descr = "rayon %s, regio %s, vereniging %s %s" % (ver.regio.rayon.rayon_nr,
                                                              ver.regio.regio_nr,
                                                              ver.nhb_nr,
                                                              ver.naam)
        else:
            descr = "geen vereniging"
    else:
        descr = "geen lid"

    return descr


class KoppelBestuurderDeelCompetitieView(UserPassesTestMixin, ListView):

    """ Via deze view kan de gebruiker een bestuurder kiezen voor een deelcompetitie.
        Keuze komt uit de lijst met favoriete bestuurders.
    """

    template_name = TEMPLATE_COMPETITIE_KOPPEL_BESTUURDERS_WIJZIG

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_is_bestuurder(self.request)

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        try:
            self.deelcompetitie = DeelCompetitie.objects.get(pk=self.kwargs['deelcomp_pk'])
        except DeelCompetitie.DoesNotExist:
            # verkeerd comp_id
            raise Resolver404()

        functie = self.deelcompetitie.functies.all()[0]
        huidige_bestuurders = functie.user_set.all()

        # lijst van favoriete bestuurders waar uit gekozen kan worden
        # marker de bestuurders die nu gekoppeld zijn
        fav_bestuurders = FavorieteBestuurders.objects.filter(zelf=self.request.user)
        for obj in fav_bestuurders:
            obj.form_index = "bestuurder_%s" % obj.favoriet.pk
            obj.is_gekozen_bestuurder = len(huidige_bestuurders.filter(pk=obj.favoriet.pk)) > 0
            obj.beschrijving = bestuurder_context_str(obj.favoriet)
            # for
        # for
        return fav_bestuurders

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['deelcompetitie'] = self.deelcompetitie
        context['rol_str'] = self.deelcompetitie.get_rol_str()
        context['formulier_url'] = reverse('Competitie:wijzig-deelcomp-bestuurders')
        context['terug_url'] = reverse('Competitie:toon-competitie-bestuurders', kwargs={'comp_pk': self.deelcompetitie.competitie.pk})
        menu_dynamics(self.request, context, actief='competitie')
        return context


class KoppelBestuurdersCompetitieView(UserPassesTestMixin, ListView):

    """ Via deze view worden de huidige gekozen bestuurders voor een competitie getoond
        en kan de gebruiker, aan de hand van de rol, kiezen om er een te wijzigen.
    """

    template_name = TEMPLATE_COMPETITIE_KOPPEL_BESTUURDERS_OVERZICHT

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_is_bestuurder(self.request)

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        deelcomp = None
        if rol_is_BKO(self.request):
            wijzigbare_laag = 'RK'
        elif rol_is_RKO(self.request):
            wijzigbare_laag = 'Regio'
            deelcomp = rol_get_deelcompetitie(self.request)
        else:
            # niets te zoeken hier - los het netjes op
            return HttpResponseRedirect(reverse('Competitie:overzicht'))

        try:
            self.competitie = Competitie.objects.get(pk=self.kwargs['comp_pk'])
        except Competitie.DoesNotExist:
            # verkeerd comp_id
            raise Resolver404()

        deelcompetities = list()
        for obj in DeelCompetitie.objects.filter(competitie=self.competitie).order_by('-laag', 'nhb_rayon__rayon_nr', 'nhb_regio__regio_nr'):
            if obj.laag == "BK":
                continue    # skip

            obj.rol_str = obj.get_rol_str()

            if obj.laag == wijzigbare_laag:
                if deelcomp is None or obj.nhb_regio.rayon == deelcomp.nhb_rayon:
                    obj.wijzig_url = reverse('Competitie:kies-deelcomp-bestuurder', kwargs={'deelcomp_pk': obj.pk})

            functie = obj.functies.all()[0]
            obj.bestuurders = functie.user_set.all()

            deelcompetities.append(obj)
        # for
        return deelcompetities

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['competitie'] = self.competitie

        # heeft deze gebruiker al favoriete bestuurders?
        if len(FavorieteBestuurders.objects.filter(zelf=self.request.user)) == 0:
            context['kies_favleden_url'] = reverse('Competitie:beheerfavorieten')

        menu_dynamics(self.request, context, actief='competitie')
        return context

# end of file
