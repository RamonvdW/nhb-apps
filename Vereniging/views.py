# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse, Resolver404
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils import timezone
from Plein.menu import menu_dynamics
from Functie.rol import rol_get_huidige_functie
from BasisTypen.models import LeeftijdsKlasse, MAXIMALE_LEEFTIJD_JEUGD
from NhbStructuur.models import NhbLid
from Schutter.models import SchutterBoog
from Competitie.models import AG_NUL, regiocompetities_schutterboog_aanmelden
from Score.models import Score
import copy

TEMPLATE_OVERZICHT = 'vereniging/overzicht.dtl'
TEMPLATE_LEDENLIJST = 'vereniging/ledenlijst.dtl'
TEMPLATE_LEDEN_VOORKEUREN = 'vereniging/leden-voorkeuren.dtl'
TEMPLATE_LEDEN_AANMELDEN = 'vereniging/leden-aanmelden.dtl'


class OverzichtView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de beheerders van de vereniging """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        _, functie_nu = rol_get_huidige_functie(self.request)
        return functie_nu and functie_nu.rol == "CWZ"

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        _, functie_nu = rol_get_huidige_functie(self.request)
        context['nhb_ver'] = functie_nu.nhb_ver

        menu_dynamics(self.request, context, actief='vereniging')
        return context


class LedenLijstView(UserPassesTestMixin, ListView):

    """ Deze view laat de CWZ zijn ledenlijst zien """

    # class variables shared by all instances
    template_name = TEMPLATE_LEDENLIJST

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        _, functie_nu = rol_get_huidige_functie(self.request)
        return functie_nu and functie_nu.rol == "CWZ"

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

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

        # zoek de schutter-boog informatie en laatste-inlog bij elk lid
        for nhblid in objs:
            nhblid.wijzig_url = reverse('Schutter:voorkeuren-nhblid', kwargs={'nhblid_pk': nhblid.pk})
            nhblid.wedstrijdbogen = [schutterboog.boogtype for schutterboog in nhblid.schutterboog_set.all().order_by('boogtype__volgorde') if schutterboog.voor_wedstrijd]

            if nhblid.account:
                nhblid.laatste_inlog = nhblid.account.last_login
            else:
                nhblid.geen_inlog = 1
        # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        _, functie_nu = rol_get_huidige_functie(self.request)
        context['nhb_ver'] = functie_nu.nhb_ver

        # splits the ledenlijst op in jeugd, senior en inactief
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

        menu_dynamics(self.request, context, actief='vereniging')
        return context


class LedenVoorkeurenView(LedenLijstView):

    """ Deze view laat de CWZ de voorkeuren van de zijn leden aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_LEDEN_VOORKEUREN


class LedenAanmeldenView(UserPassesTestMixin, ListView):

    """ Deze view laat de CWZ zijn ledenlijst zien """

    # class variables shared by all instances
    template_name = TEMPLATE_LEDEN_AANMELDEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        _, functie_nu = rol_get_huidige_functie(self.request)
        return functie_nu and functie_nu.rol == "CWZ"

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    @staticmethod
    def _get_schutterboog_ag(schutterboog, afstand):
        ags = Score.objects.filter(schutterboog=schutterboog, afstand_meter=afstand)
        if len(ags) >= 1:       # zou er maar 1 moeten zijn
            return ags[0].waarde / 1000
        return AG_NUL

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        huidige_jaar = timezone.now().year  # TODO: check for correctness in last hours of the year (due to timezone)
        jeugdgrens = huidige_jaar - MAXIMALE_LEEFTIJD_JEUGD
        self._huidige_jaar = huidige_jaar

        _, functie_nu = rol_get_huidige_functie(self.request)
        qset = NhbLid.objects.filter(bij_vereniging=functie_nu.nhb_ver, is_actief_lid=True)
        objs = list()

        # sorteer jeugd op geboorte jaar en daarna naam
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

        # sorteer volwassenen op naam
        for obj in qset.filter(geboorte_datum__year__lt=jeugdgrens).order_by('achternaam', 'voornaam'):
            objs.append(obj)
            obj.leeftijdsklasse = None
        # for

        # zoek de schutter-boog informatie bij elk lid
        objs2 = list()
        for nhblid in objs:
            heeft_wedstrijdboog = False
            for schutterboog in nhblid.schutterboog_set.all().order_by('boogtype__volgorde'):
                if schutterboog.voor_wedstrijd:
                    # maak een kopie van het nhblid en maak het uniek voor dit boogtype
                    obj = copy.copy(nhblid)
                    obj.boogtype = schutterboog.boogtype
                    obj.check = "lid_%s_boogtype_%s" % (nhblid.nhb_nr, schutterboog.boogtype.pk)
                    heeft_wedstrijdboog = True

                    # zoek de aanvangsgemiddelden er bij
                    obj.ag_18 = self._get_schutterboog_ag(schutterboog, 18)
                    obj.ag_25 = self._get_schutterboog_ag(schutterboog, 25)

                    # kijk of de schutter al aangemeld is
                    obj.is_aangemeld = schutterboog.regiocompetitieschutterboog_set.count() > 0

                    objs2.append(obj)
            # for
            #if not heeft_wedstrijdboog:
            #    nhblid.geen_wedstrijdboog = True
            #    objs2.append(nhblid)
        # for

        return objs2

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        _, functie_nu = rol_get_huidige_functie(self.request)
        context['nhb_ver'] = functie_nu.nhb_ver

        # splits the ledenlijst op in jeugd, senior en inactief
        jeugd = list()
        senior = list()
        for obj in context['object_list']:
            if obj.leeftijdsklasse:
                jeugd.append(obj)
            else:
                senior.append(obj)
        # for

        context['leden_jeugd'] = jeugd
        context['leden_senior'] = senior
        context['wedstrijdklasse_jaar'] = self._huidige_jaar
        context['seizoen'] = '%s/%s' % (self._huidige_jaar, self._huidige_jaar+1)

        menu_dynamics(self.request, context, actief='vereniging')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Geselecteerde schutters aanmelden' wordt gebruikt
            het csrf token is al gecontroleerd
        """
        # all checked boxes are in the post request as keys, typically with value 'on'
        for key, _ in request.POST.items():
            # key = 'lid_NNNNNN_boogtype_MM' (of iets anders)
            spl = key.split('_')
            # spl = ('lid', 'NNNNNN', 'boogtype', 'MM')
            if len(spl) == 4 and spl[0] == 'lid' and spl[2] == 'boogtype':
                # dit lijkt ergens op - converteer de getallen (geeft ook input bescherming)
                try:
                    nhblid_pk = int(spl[1])
                    boogtype_pk = int(spl[3])
                except (TypeError, ValueError):
                    # iemand loopt te klooien
                    raise Resolver404()

                # SchutterBoog record met voor_wedstrijd==True moet bestaan
                try:
                    schutterboog = SchutterBoog.objects.get(nhblid=nhblid_pk, boogtype=boogtype_pk)
                except SchutterBoog.DoesNotExist:
                    # iemand loopt te klooien
                    raise Resolver404()
                else:
                    if not schutterboog.voor_wedstrijd:
                        # iemand loopt te klooien
                        raise Resolver404()

                # zoek de aanvangsgemiddelden er bij
                gem18 = self._get_schutterboog_ag(schutterboog, 18)
                gem25 = self._get_schutterboog_ag(schutterboog, 25)

                regiocompetities_schutterboog_aanmelden(schutterboog, gem18, gem25)

            # else: silently ignore
        # for

        return HttpResponseRedirect(reverse('Vereniging:leden-aanmelden'))

# end of file
