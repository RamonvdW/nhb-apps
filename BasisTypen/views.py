# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils import timezone
from Plein.menu import menu_dynamics
from Logboek.models import schrijf_in_logboek
from Account.rol import rol_is_BKO
from .models import TeamType, TeamTypeBoog, BoogType, LeeftijdsKlasse, WedstrijdKlasse, WedstrijdKlasseBoog, WedstrijdKlasseLeeftijd
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from NhbStructuur.models import NhbLid

TEMPLATE_COMPETITIE_DEFAULTS = 'basistypen/competitie-defaults.dtl'
TEMPLATE_COMPETITIE_AANVANGSGEMIDDELDEN = 'basistypen/competitie-aanvangsgemiddelden.dtl'


class InstellingenVolgendeCompetitieView(UserPassesTestMixin, ListView):

    """ deze view laat de defaults voor de volgende competitie zien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_DEFAULTS
    login_url = '/account/login/'       # no reverse call

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
        for klasse in objs:
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
        for klasse in objs:
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
        menu_dynamics(self.request, context)        # TODO: welke menu item actief laten zien?
        return context


class AanvangsgemiddeldenView(UserPassesTestMixin, ListView):

    """ deze view laat de aanvangemiddelden voor de volgende competitie zien,
        aan de hand van de historische competitie data
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_AANVANGSGEMIDDELDEN
    login_url = '/account/login/'       # no reverse call

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        res = rol_is_BKO(self.request)
        return res

    def _get_targets(self, comp_type):
        # TODO: nieuwe competitie verwijst straks naar een set wedstrijdklassen
        # NOTE: voorlopig dezelfde set klassen voor comp_type=18 en 25
        wedstrklassen = WedstrijdKlasse.objects.filter(is_voor_teams=False)

        targets = dict()        # [ (min_age, max_age, tuple(bogen)) ] = list(wedstrijdklassen)
        for wedstrklasse in wedstrklassen:
            age_min = 999
            age_max = 0
            for obj in WedstrijdKlasseLeeftijd.objects.filter(wedstrijdklasse=wedstrklasse):
                lkl = obj.leeftijdsklasse
                age_min = min(lkl.min_wedstrijdleeftijd, age_min)
                age_max = max(lkl.max_wedstrijdleeftijd, age_max)
            # for
            #print("wedstrklasse: %s --> leeftijden: %s .. %s" % (wedstrklasse.beschrijving, age_min, age_max))

            # verzamel alle toegestane boogsoorten voor deze wedstrijdklasse
            bogen = list()
            for obj in WedstrijdKlasseBoog.objects.filter(wedstrijdklasse=wedstrklasse):
                # helaas op beschrijving, want we matchen met
                if obj.boogtype.afkorting not in bogen:
                    bogen.append(obj.boogtype.afkorting)
            # for
            #print("wedstrklasse: %s --> bogen: %s" % (wedstrklasse.beschrijving, repr(bogen)))

            tup = (age_min, age_max, tuple(bogen))
            if tup not in targets:
                targets[tup] = list()
            targets[tup].append(wedstrklasse)
        # for
        return targets

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        # bepaal het jaar waarin de wedstrijdleeftijd bepaald moet worden
        # dit is het huidige jaar + 1
        jaar = timezone.now().year + 1
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
        for comp_type, comptype_str in HistCompetitie.COMP_TYPE:
            #print("comp_type: %s" % repr(comp_type))

            histcomps = HistCompetitie.objects.filter(seizoen=self.seizoen, comp_type=comp_type, is_team=False)
            #print("histcomps: %s" % repr(histcomps))

            targets = self._get_targets(comp_type)
            #print("targets: %s" % repr(targets))

            for tup, wedstrklassen in targets.items():
                min_age, max_age, bogen = tup
                #print("Target: leeftijd %s-%s met bogen %s" % (min_age, max_age, " / ".join(bogen)))
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
                    #print("gemiddelden: [0]=%s [-1]=%s" % (gemiddelden[0], gemiddelden[-1]))
                    count = len(gemiddelden)
                    aantal = len(wedstrklassen)     # aantal groepen
                    step = int(count / aantal)      # omlaag afgerond = OK voor grote groepen
                    pos = 0
                    #print("wedstrklassen: %s" % repr(wedstrklassen))
                    for klasse in wedstrklassen[:-1]:
                        pos += step
                        #print("aantal=%s, count=%s, step=%s, pos=%s" % (aantal, count, step, pos))
                        ag = gemiddelden[pos]
                        res = {'comp_type' : comptype_str, 'klasse': klasse.beschrijving, 'count' : step, 'ag': ag}
                        objs.append(res)
                    # for
                    # laatste klassen heeft geen grens
                    res = {'comp_type' : comptype_str, 'klasse': wedstrklassen[-1].beschrijving, 'count' : count - (aantal - 1) * step, 'ag': '0,000'}
                    objs.append(res)
                else:
                    # geen historische gemiddelden
                    #print("[ERROR] geen gemiddelden voor klassen %s" % repr(wedstrklassen))
                    # zet alles op 0.000 - dit geeft een beetje een rommeltje als er meerdere klassen zijn
                    for klasse in wedstrklassen:
                        res = {'comp_type' : comptype_str, 'klasse': klasse.beschrijving, 'count' : 0, 'ag': '0,000'}
                        objs.append(res)
                    # for
            # for
        # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['seizoen'] = self.seizoen
        context['wedstrijdjaar'] = self.wedstrijdjaar
        menu_dynamics(self.request, context)        # TODO: welke menu item actief laten zien?
        return context

# end of file
