# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import Resolver404, reverse
from django.views.generic import TemplateView, ListView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.utils import timezone
from django.shortcuts import redirect
from Plein.menu import menu_dynamics
from Logboek.models import schrijf_in_logboek
from Account.models import Account
from Account.rol import Rollen, rol_get_huidige, rol_get_huidige_functie, rol_get_beschrijving,\
                        rol_is_BB, rol_is_BKO, rol_is_RKO, rol_is_CWZ, rol_is_beheerder, rol_evalueer_opnieuw
from BasisTypen.models import TeamType, TeamTypeBoog, BoogType, LeeftijdsKlasse, WedstrijdKlasse, \
                              WedstrijdKlasseBoog, WedstrijdKlasseLeeftijd
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from NhbStructuur.models import NhbLid, NhbVereniging
from .models import models_bepaal_startjaar_nieuwe_competitie, competitie_aanmaken, maak_competitieklasse_indiv, \
                    Competitie, ZERO, FavorieteBestuurders, add_favoriete_beheerder, drop_favoriete_beheerder, \
                    DeelCompetitie
from .forms import FavorieteBeheerdersForm, WijzigFavorieteBeheerdersForm, KoppelBeheerdersForm


TEMPLATE_COMPETITIE_OVERZICHT = 'competitie/overzicht.dtl'
TEMPLATE_COMPETITIE_OVERZICHT_CWZ = 'competitie/overzicht-cwz.dtl'
TEMPLATE_COMPETITIE_OVERZICHT_BEHEERDER = 'competitie/overzicht-beheerder.dtl'
TEMPLATE_COMPETITIE_INSTELLINGEN = 'competitie/instellingen-nieuwe-competitie.dtl'
TEMPLATE_COMPETITIE_AANMAKEN = 'competitie/competities-aanmaken.dtl'
TEMPLATE_COMPETITIE_KLASSEGRENZEN = 'competitie/klassegrenzen-vaststellen.dtl'
TEMPLATE_COMPETITIE_BEHEER_FAVORIETEN = 'competitie/beheer-favorieten.dtl'
TEMPLATE_COMPETITIE_KOPPEL_BEHEERDERS_OVERZICHT = 'competitie/koppel-beheerders-overzicht.dtl'
TEMPLATE_COMPETITIE_KOPPEL_BEHEERDERS_WIJZIG = 'competitie/koppel-beheerders-wijzig.dtl'
TEMPLATE_COMPETITIE_LIJST_VERENIGINGEN = 'competitie/lijst-verenigingen.dtl'


JA_NEE = {False: 'Nee', True: 'Ja'}


class CompetitieOverzichtView(View):
    """ Deze view biedt de landingpage vanuit het menu aan """

    # class variables shared by all instances
    # (none)

    def _get_competitie_overzicht_beheerder(self, request):
        context = dict()

        rol_nu, functie_nu = rol_get_huidige_functie(request)
        if functie_nu:
            group = Group.objects.get(pk=functie_nu)
            context['huidige_rol'] = group.name
        else:
            context['huidige_rol'] = rol_get_beschrijving(request)

        context['kan_favorieten_beheren'] = rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO)

        # kies de competities om het tijdschema van de tonen
        objs = list()
        if rol_nu == Rollen.ROL_BB:
            # toon alle competities
            objs = Competitie.objects.filter(is_afgesloten=False).order_by('begin_jaar', 'afstand')
        elif functie_nu:
            # gebaseerd op de functie moeten we de competities filteren
            # de functie wijst naar een deelcompetitie, welke bij een competitie hoort
            competitie = group.deelcompetitie_set.all()[0].competitie
            objs.append(competitie)

        context['object_list'] = objs
        context['have_active_comps'] = (len(objs) > 0)

        # kies de competities waarvoor de beheerder getoond kunnen worden
        for obj in objs:
            obj.zet_fase()
            obj.is_afgesloten_str = JA_NEE[obj.is_afgesloten]
            obj.wijzig_url = reverse('Competitie:toon-competitie-beheerders', kwargs={'comp_pk': obj.id})
        # for

        if rol_nu == Rollen.ROL_BB:
            context['rol_is_bb'] = True
            # als er nog geen competitie is voor het huidige jaar, geeft de BB dan de optie om deze op te starten
            beginjaar = models_bepaal_startjaar_nieuwe_competitie()
            context['nieuwe_seizoen'] = "%s/%s" % (beginjaar, beginjaar+1)
            context['bb_kan_competitie_aanmaken'] = (len(objs.filter(begin_jaar=beginjaar)) == 0)
            context['bb_kan_bko_koppelen'] = True
        elif rol_nu == Rollen.ROL_BKO:
            context['bko_kan_rko_koppelen'] = True
        elif rol_nu == Rollen.ROL_RKO:
            context['rko_kan_rcl_koppelen'] = True
        else:
            context['toon_competitie_beheerders'] = True

        return context, TEMPLATE_COMPETITIE_OVERZICHT_BEHEERDER

    def _get_competitie_overzicht_cwz(self, request):
        context = dict()
        return context, TEMPLATE_COMPETITIE_OVERZICHT_CWZ

    def _get_competitie_overzicht_schutter(self):
        context = dict()
        return context, TEMPLATE_COMPETITIE_OVERZICHT

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """

        if rol_is_beheerder(self.request):
            context, template = self._get_competitie_overzicht_beheerder(request)
        elif rol_is_CWZ(self.request):
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
        res = rol_is_BB(self.request)
        return res

    def _get_queryset_teamtypen(self):
        objs = TeamType.objects.all()
        for teamtype in objs:
            boogtypen = [obj.boogtype.afkorting for obj in TeamTypeBoog.objects.select_related('boogtype').filter(teamtype=teamtype)]
            teamtype.boogtypen = "+".join(boogtypen)
        # for
        return objs

    def _get_queryset_indivklassen(self):
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
        res = rol_is_BB(self.request)
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
        rol_evalueer_opnieuw(request)
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
        res = rol_is_BB(self.request)
        return res

    def _get_targets(self):
        targets = dict()        # [ (min_age, max_age, tuple(bogen)) ] = list(wedstrijdklassen)
        for wedstrklasse in WedstrijdKlasse.objects.filter(is_voor_teams=False, buiten_gebruik=False):
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
        # for

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
        objs2 = sorted(objs, key=lambda k: k['beschrijving'])
        return objs2

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


class WijzigFavorieteBeheerdersView(View):

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """
        raise Resolver404()

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Registreer knop.
        """
        if rol_is_beheerder(request):
            form = WijzigFavorieteBeheerdersForm(request.POST)
            form.full_clean()       # vult cleaned_data
            # form is altijd valid, dus niet nodig om is_valid aan te roepen

            account_pk = form.cleaned_data.get('add_favoriet')
            if account_pk:
                add_favoriete_beheerder(request.user, account_pk)

            account_pk = form.cleaned_data.get('drop_favoriet')
            if account_pk:
                drop_favoriete_beheerder(request.user, account_pk)

        return HttpResponseRedirect(reverse('Competitie:beheerfavorieten'))


class BeheerFavorieteBeheerdersView(UserPassesTestMixin, ListView):

    """ Via deze view kunnen beheerders hun lijst met favoriete NHB leden beheren """

    template_name = TEMPLATE_COMPETITIE_BEHEER_FAVORIETEN

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.form = FavorieteBeheerdersForm()
        self.get_zoekterm = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_is_beheerder(self.request)

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        # retourneer een QuerySet voor de template
        # onthoud zaken in de object instantie

        # haal de GET parameters uit de request
        self.form = FavorieteBeheerdersForm(self.request.GET)
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
        context['favoriete_beheerders'] = FavorieteBestuurders.objects.filter(zelf=self.request.user)
        menu_dynamics(self.request, context, actief='competitie')
        return context


class KoppelBeheerdersOntvangWijzigingView(View):

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """
        raise Resolver404()

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Registreer knop.
        """

        url = reverse('Competitie:overzicht')

        rol_nu, functie_nu = rol_get_huidige_functie(request)

        if rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO):
            # zoek de favoriete beheerders erbij
            # TODO: Wat als twee beheerders niet dezelfde favorieten hebben?
            fav_beheerders = FavorieteBestuurders.objects.filter(zelf=self.request.user)
            form = KoppelBeheerdersForm(request.POST, fav_beheerders=fav_beheerders)
            if form.is_valid():
                # zoek de DeelCompetitie erbij
                try:
                    deelcompetitie = DeelCompetitie.objects.get(pk=form.cleaned_data.get('deelcomp_pk'))
                except DeelCompetitie.DoesNotExist:
                    # foute deelcomp_pk
                    raise Resolver404()

                # controleer dat de beheerders deze wijziging mag maken
                if rol_nu == Rollen.ROL_BB:
                    if deelcompetitie.laag != 'BK':
                        # beheerder heeft hier niets te zoeken
                        raise Resolver404()
                elif rol_nu == Rollen.ROL_BKO:
                    # BKO
                    if deelcompetitie.laag != 'RK':
                        # beheerder heeft hier niets te zoeken
                        raise Resolver404()
                else:
                    # RKO
                    # even het rayon van deze RKO rol erbij zoeken
                    rko_deelcomp = Group(pk=functie_nu).deelcompetitie_set.all()[0]
                    rko_rayon_nr = rko_deelcomp.nhb_rayon.rayon_nr
                    if deelcompetitie.laag != 'Regio' or deelcompetitie.nhb_regio.rayon.rayon_nr != rko_rayon_nr:
                        # beheerder heeft hier niets te zoeken
                        raise Resolver404()

                # haal de functie(=groep) op van deze deelcompetitie
                functie = deelcompetitie.functies.all()[0]

                # gooi alle gekoppelde beheerders weg
                beheerders_old = [pk for pk in functie.user_set.all().values_list('pk', flat=True)]
                functie.user_set.clear()

                # koppel de gekozen beheerders (oud en nieuw)
                for obj in fav_beheerders:
                    is_gekozen = form.cleaned_data.get('beheerder_%s' % obj.favoriet.pk)
                    if is_gekozen:
                        # voeg het account toe aan de functie
                        functie.user_set.add(obj.favoriet)
                # for

                beheerders_new = functie.user_set.all().values_list('pk', flat=True)

                # de wijzigingen in het logboek schrijven
                wijzigingen = list()
                wijzigingen.append("Rol: %s" % deelcompetitie.get_rol_str())
                for pk in beheerders_old:
                    if pk not in beheerders_new:
                        beheerder = Account.objects.get(pk=pk).volledige_naam()
                        wijzigingen.append('Losgekoppeld: %s' % beheerder)
                # for
                for pk in beheerders_new:
                    if pk not in beheerders_old:
                        beheerder = Account.objects.get(pk=pk).volledige_naam()
                        wijzigingen.append('Gekoppeld: %s' % beheerder)
                # for

                if len(wijzigingen) > 1:
                    schrijf_in_logboek(request.user, 'Rollen', "\n".join(wijzigingen))

                url = reverse('Competitie:toon-competitie-beheerders', kwargs={'comp_pk': deelcompetitie.competitie.pk})
            #else:
            #    print("form is not valid: %s" % repr(form.errors))

        return HttpResponseRedirect(url)


def beheerder_context_str(account):
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


class KoppelBeheerderDeelCompetitieView(UserPassesTestMixin, ListView):

    """ Via deze view kan de BKO en RKO beheerder andere beheerders kiezen voor een deelcompetitie.
        Keuze moet komen uit de lijst met favoriete beheerders.
    """

    template_name = TEMPLATE_COMPETITIE_KOPPEL_BEHEERDERS_WIJZIG

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol = rol_get_huidige(self.request)
        return rol in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO)

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        try:
            self.deelcompetitie = DeelCompetitie.objects.get(pk=self.kwargs['deelcomp_pk'])
        except DeelCompetitie.DoesNotExist:
            # foute deelcomp_pk
            raise Resolver404()

        # controleer dat de beheerder dit stukje mag wijzigen
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        if rol_nu == Rollen.ROL_BB:
            if self.deelcompetitie.laag != 'BK':
                # beheerder heeft hier niets te zoeken
                raise Resolver404()
        elif rol_nu == Rollen.ROL_BKO:
            if self.deelcompetitie.laag != 'RK':
                # beheerder heeft hier niets te zoeken
                raise Resolver404()
        elif rol_nu == Rollen.ROL_RKO:
            # even het rayon van de gekozen RKO rol erbij zoeken
            rko_deelcomp = Group(pk=functie_nu).deelcompetitie_set.all()[0]
            rko_rayon_nr = rko_deelcomp.nhb_rayon.rayon_nr
            if self.deelcompetitie.laag != 'Regio' or self.deelcompetitie.nhb_regio.rayon.rayon_nr != rko_rayon_nr:
                # beheerder heeft hier niets te zoeken
                raise Resolver404()
        else:
            # beheerder heeft hier niets te zoeken
            raise Resolver404()

        functie = self.deelcompetitie.functies.all()[0]
        huidige_beheerders = functie.user_set.all()

        # lijst van favoriete beheerders waar uit gekozen kan worden
        # marker de beheerders die nu gekoppeld zijn
        fav_beheerders = FavorieteBestuurders.objects.filter(zelf=self.request.user)
        for obj in fav_beheerders:
            obj.form_index = "beheerder_%s" % obj.favoriet.pk
            obj.is_gekozen_beheerder = len(huidige_beheerders.filter(pk=obj.favoriet.pk)) > 0
            obj.beschrijving = beheerder_context_str(obj.favoriet)
            # for
        # for

        # TODO: rapporteer wie in huidige_beheerders niet in fav_beheerders zit en je dus kwijt kan raken!

        return fav_beheerders

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['deelcompetitie'] = self.deelcompetitie
        context['rol_str'] = self.deelcompetitie.get_rol_str()
        context['formulier_url'] = reverse('Competitie:wijzig-deelcomp-beheerders')
        context['terug_url'] = reverse('Competitie:toon-competitie-beheerders', kwargs={'comp_pk': self.deelcompetitie.competitie.pk})
        menu_dynamics(self.request, context, actief='competitie')
        return context


class KoppelBeheerdersCompetitieView(UserPassesTestMixin, ListView):

    """ Via deze view worden de huidige gekozen beheerders voor een competitie getoond
        en kan de gebruiker, aan de hand van de rol, kiezen om er een te wijzigen.
    """

    template_name = TEMPLATE_COMPETITIE_KOPPEL_BEHEERDERS_OVERZICHT

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_is_beheerder(self.request)

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        competitie_pk = self.kwargs['comp_pk']

        try:
            self.competitie = Competitie.objects.get(pk=competitie_pk)
        except Competitie.DoesNotExist:
            # foute comp_pk
            raise Resolver404()

        # bepaal welke laag door deze beheerder gewijzigd mag worden
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        if rol_nu == Rollen.ROL_BB:
            wijzigbare_laag = 'BK'
        elif rol_nu == Rollen.ROL_BKO:
            wijzigbare_laag = 'RK'
        elif rol_nu == Rollen.ROL_RKO:
            wijzigbare_laag = 'Regio'
            # even het rayon van de gekozen RKO rol erbij zoeken
            deelcomp = Group(pk=functie_nu).deelcompetitie_set.all()[0]
            rko_rayon_nr = deelcomp.nhb_rayon.rayon_nr
        else:
            # beheerder kan niets wijzigen, maar inzien mag wel
            wijzigbare_laag = "niets"

        # maak een lijst van beheerders aan de hand van de deelcompetities in deze competitie
        # per deelcompetitie is er een BKO, RKO of RCL

        # eerst de BKO's zodat deze bovenaan komen te staan
        deelcompetities = list()
        for obj in DeelCompetitie.objects.filter(competitie=self.competitie).filter(laag='BK'):
            obj.rol_str = obj.get_rol_str()
            obj.wijzig_url = None

            if obj.laag == wijzigbare_laag and not obj.is_afgesloten:
                # BB --> BKO
                obj.wijzig_url = reverse('Competitie:kies-deelcomp-beheerders', kwargs={'deelcomp_pk': obj.pk})

            functie = obj.functies.all()[0]
            obj.beheerders = functie.user_set.all()

            deelcompetities.append(obj)
        # for

        # nu de RKO's en RCL's gesorteerd op rayon nummer / regio nummer
        for obj in DeelCompetitie.objects.filter(competitie=self.competitie).exclude(laag='BK').order_by('-laag', 'nhb_rayon__rayon_nr', 'nhb_regio__regio_nr'):
            obj.rol_str = obj.get_rol_str()
            obj.wijzig_url = None

            # bepaal de URL voor het wijzig knopje
            if obj.laag == wijzigbare_laag and not obj.is_afgesloten:
                if obj.laag == 'RK':
                    # BKO --> RKO
                    obj.wijzig_url = reverse('Competitie:kies-deelcomp-beheerders', kwargs={'deelcomp_pk': obj.pk})
                elif obj.laag == 'Regio' and obj.nhb_regio.rayon.rayon_nr == rko_rayon_nr:
                    # RKO --> RCL
                    obj.wijzig_url = reverse('Competitie:kies-deelcomp-beheerders', kwargs={'deelcomp_pk': obj.pk})

            functie = obj.functies.all()[0]
            obj.beheerders = functie.user_set.all()

            deelcompetities.append(obj)
        # for
        return deelcompetities

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['competitie'] = self.competitie

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        if functie_nu:
            context['huidige_rol'] = Group.objects.get(pk=functie_nu).name
        else:
            context['huidige_rol'] = rol_get_beschrijving(self.request)

        if rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO):
            # heeft deze gebruiker al favoriete beheerders?
            if len(FavorieteBestuurders.objects.filter(zelf=self.request.user)) == 0:
                context['kies_favleden_url'] = reverse('Competitie:beheerfavorieten')

        # als er geen wijzig knop in beeld hoeft te komen, dan kan de tabel wat smaller
        context['show_wijzig_kolom'] = False
        for obj in context['object_list']:
            if obj.wijzig_url:
                context['show_wijzig_kolom'] = True
                break   # from the for
        # for
        menu_dynamics(self.request, context, actief='competitie')
        return context


class LijstVerenigingenView(UserPassesTestMixin, ListView):

    """ Via deze view worden kan een BKO, RKO of RCL de lijst van verenigingen zien in zijn werkgebied.
    """

    template_name = TEMPLATE_COMPETITIE_LIJST_VERENIGINGEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_is_beheerder(self.request)

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        if rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO):
            # toon de landelijke lijst
            return NhbVereniging.objects.all().exclude(regio__regio_nr=100).order_by('regio__regio_nr', 'nhb_nr')

        if rol_nu == Rollen.ROL_RKO:
            # toon de lijst van verenigingen in het rayon van de RKO
            # het rayonnummer is verkrijgbaar via de deelcompetitie van de functie
            deelcompetitie = Group(pk=functie_nu).deelcompetitie_set.all()[0]
            return NhbVereniging.objects.filter(regio__rayon=deelcompetitie.nhb_rayon).order_by('regio__regio_nr', 'nhb_nr')

        if rol_nu == Rollen.ROL_RCL:
            # toon de lijst van verenigingen in de regio van de RCL
            # het regionummer is verkrijgbaar via de deelcompetitie van de functie
            deelcompetitie = Group(pk=functie_nu).deelcompetitie_set.all()[0]
            return NhbVereniging.objects.filter(regio=deelcompetitie.nhb_regio)

        # waarom hier?
        raise Resolver404()

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context, actief='competitie')
        return context


# end of file
