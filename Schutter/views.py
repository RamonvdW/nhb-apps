# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from BasisTypen.models import BoogType
from Records.models import IndivRecord
from .leeftijdsklassen import get_sessionvars_leeftijdsklassen
from .models import SchutterBoog

TEMPLATE_PROFIEL = 'schutter/profiel.dtl'
TEMPLATE_VOORKEUREN = 'schutter/voorkeuren.dtl'
TEMPLATE_VOORKEUREN_OPGESLAGEN = 'schutter/voorkeuren-opgeslagen.dtl'
TEMPLATE_LEEFTIJDSKLASSEN = 'schutter/leeftijdsklassen.dtl'


class ProfielView(UserPassesTestMixin, TemplateView):

    """ Dit is de profiel pagina van een schutter """

    template_name = TEMPLATE_PROFIEL

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en schutter rol gekozen hebben
        return rol_get_huidige(self.request) == Rollen.ROL_SCHUTTER

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    @staticmethod
    def _find_scores(account):
        """ Zoek alle scores van deze schutter """
        objs = list()
        if account.nhblid:
            boogtype2str = dict()
            for boog in BoogType.objects.all():
                boogtype2str[boog.afkorting] = boog.beschrijving
            # for

            for obj in HistCompetitieIndividueel.objects.filter(schutter_nr=account.nhblid.nhb_nr):
                wedstrijd = HistCompetitie.comptype2str[obj.histcompetitie.comp_type]
                datum_str = 'Seizoen ' + obj.histcompetitie.seizoen
                try:
                    boog_str = boogtype2str[obj.boogtype]
                except KeyError:
                    boog_str = "?"
                for score in (obj.score1, obj.score2, obj.score3, obj.score4, obj.score5, obj.score6, obj.score7):
                    if score:
                        entry = dict()
                        entry['score'] = score
                        entry['datum'] = datum_str
                        entry['wedstrijd'] = wedstrijd
                        entry['boog'] = boog_str
                        objs.append(entry)
                # for
            # for

            # records niet toevoegen, want dan wordt het dubbel getoond
        return objs

    @staticmethod
    def _find_records(account):
        objs = list()
        if account.nhblid:
            for rec in IndivRecord.objects.filter(nhb_lid=account.nhblid).order_by('-datum'):
                rec.url = reverse('Records:specifiek', kwargs={'discipline': rec.discipline, 'nummer': rec.volg_nr})
                objs.append(rec)
            # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        account = self.request.user

        context['nhb_nummer'] = account.nhblid.nhb_nr

        _, _, is_jong, _, _ = get_sessionvars_leeftijdsklassen(self.request)
        context['toon_leeftijdsklassen'] = is_jong

        context['records'] = self._find_records(account)
        context['scores'] = self._find_scores(account)

        menu_dynamics(self.request, context, actief='schutter')
        return context


class VoorkeurenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen schutters hun voorkeuren inzien en aanpassen """

    template_name = TEMPLATE_VOORKEUREN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en schutter rol gekozen hebben
        return rol_get_huidige(self.request) == Rollen.ROL_SCHUTTER

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als een POST request ontvangen is."""

        # sla de nieuwe voorkeuren op
        for obj in SchutterBoog.objects.filter(account=self.request.user):
            check_info = 'info_' + obj.boogtype.afkorting

            old_voor_wedstrijd = obj.voor_wedstrijd
            obj.voor_wedstrijd = False
            if request.POST.get('schiet_' + obj.boogtype.afkorting, None):
                obj.voor_wedstrijd = True

            old_heeft_interesse = obj.heeft_interesse
            obj.heeft_interesse = False
            if request.POST.get('info_' + obj.boogtype.afkorting, None):
                obj.heeft_interesse = True

            old_voorkeur_dutchtarget_18m = obj.voorkeur_dutchtarget_18m
            obj.voorkeur_dutchtarget_18m = False
            if obj.boogtype.afkorting == "R":
                if request.POST.get('voorkeur_DT_18m', None):
                    obj.voorkeur_dutchtarget_18m = True

            if (old_voor_wedstrijd != obj.voor_wedstrijd or
                    old_heeft_interesse != obj.heeft_interesse or
                    old_voorkeur_dutchtarget_18m != obj.voorkeur_dutchtarget_18m):
                # wijzigingen opslaan
                obj.save()
        # for

        context = dict()
        menu_dynamics(request, context, actief='schutter')
        return render(request, TEMPLATE_VOORKEUREN_OPGESLAGEN, context)

    def _get_bogen(self):
        # TODO: control order?

        # om het simpel te houden maken we voor elk account en boogtype
        # een SchutterBoog record aan waarin de instellingen opgeslagen worden

        # kijk welke schutter-boog er al bekend zijn voor deze gebruiker
        # we maken alleen een record aan als een voorkeur opgegeven wordt
        objs = SchutterBoog.objects.filter(account=self.request.user)

        boogtypen = BoogType.objects.all()
        if len(objs) < len(boogtypen):
            # kijk welke er ontbreken en maak deze aan
            aanwezig = objs.values_list('boogtype__pk', flat=True)
            for boogtype in boogtypen.exclude(pk__in=aanwezig):
                schutterboog = SchutterBoog()
                schutterboog.account = self.request.user
                schutterboog.boogtype = boogtype
                schutterboog.save()
            # for
            objs = SchutterBoog.objects.filter(account=self.request.user)

        voorkeur_dt = False
        for obj in objs:
            obj.check_schiet = 'schiet_' + obj.boogtype.afkorting
            obj.check_info = 'info_' + obj.boogtype.afkorting
            if obj.voorkeur_dutchtarget_18m:
                voorkeur_dt = True
        # for
        return objs, voorkeur_dt

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        bogen, voorkeur_dt = self._get_bogen()
        context['bogen'] = bogen
        context['voorkeur_dt'] = voorkeur_dt
        context['opslaan_url'] = reverse('Schutter:voorkeuren')
        menu_dynamics(self.request, context, actief='schutter')
        return context


class LeeftijdsklassenView(UserPassesTestMixin, TemplateView):
    """ Django class-based view voor de leeftijdsklassen """

    # class variables shared by all instances
    template_name = TEMPLATE_LEEFTIJDSKLASSEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol = rol_get_huidige(self.request)
        return rol == Rollen.ROL_SCHUTTER

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        huidige_jaar, leeftijd, is_jong, wlst, clst = get_sessionvars_leeftijdsklassen(self.request)
        context['plein_is_jonge_schutter'] = is_jong
        context['plein_huidige_jaar'] = huidige_jaar
        context['plein_leeftijd'] = leeftijd
        context['plein_wlst'] = wlst
        context['plein_clst'] = clst

        menu_dynamics(self.request, context)
        return context


# end of file
