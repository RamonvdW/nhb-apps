# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse, Resolver404
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige_functie
from BasisTypen.models import (LeeftijdsKlasse,
                               MAXIMALE_LEEFTIJD_JEUGD, MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT)
from NhbStructuur.models import NhbLid
from Schutter.models import SchutterBoog, SchutterVoorkeuren
from Competitie.models import (AG_NUL, DAGDEEL, DAGDEEL_AFKORTINGEN, INSCHRIJF_METHODE_3,
                               Competitie, DeelCompetitie, CompetitieKlasse,
                               RegioCompetitieSchutterBoog)
from Score.models import Score
import copy


TEMPLATE_LEDEN_INSCHRIJVEN = 'vereniging/competitie-inschrijven.dtl'
TEMPLATE_LEDEN_INGESCHREVEN = 'vereniging/competitie-ingeschreven.dtl'

JA_NEE = {False: 'Nee', True: 'Ja'}


class LedenInschrijvenView(UserPassesTestMixin, ListView):

    """ Deze view laat de HWL leden inschrijven voor een competitie """

    # class variables shared by all instances
    template_name = TEMPLATE_LEDEN_INSCHRIJVEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        _, functie_nu = rol_get_huidige_functie(self.request)
        return functie_nu and functie_nu.rol == 'HWL'

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        try:
            comp_pk = int(self.kwargs['comp_pk'][:10])
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, TypeError, Competitie.DoesNotExist):
            raise Resolver404()

        self.comp = comp
        comp.zet_fase()

        _, functie_nu = rol_get_huidige_functie(self.request)
        objs = list()

        prev_lkl = None
        prev_wedstrijdleeftijd = 0
        jeugdgrens = comp.begin_jaar - MAXIMALE_LEEFTIJD_JEUGD

        # sorteer jeugd op geboorte jaar en daarna naam
        for obj in (NhbLid
                    .objects
                    .filter(bij_vereniging=functie_nu.nhb_ver)
                    .filter(geboorte_datum__year__gte=jeugdgrens)
                    .order_by('-geboorte_datum__year', 'achternaam', 'voornaam')):

            # de wedstrijdleeftijd voor dit hele seizoen
            wedstrijdleeftijd = obj.bereken_wedstrijdleeftijd(comp.begin_jaar + 1)
            obj.leeftijd = wedstrijdleeftijd

            # de wedstrijdklasse voor dit hele seizoen
            if wedstrijdleeftijd == prev_wedstrijdleeftijd:
                obj.leeftijdsklasse = prev_lkl
            else:
                obj.leeftijdsklasse = (LeeftijdsKlasse
                                       .objects
                                       .filter(max_wedstrijdleeftijd__gte=wedstrijdleeftijd,
                                               geslacht='M')
                                       .order_by('max_wedstrijdleeftijd'))[0]
                prev_lkl = obj.leeftijdsklasse
                prev_wedstrijdleeftijd = wedstrijdleeftijd

            objs.append(obj)
        # for

        # sorteer volwassenen op naam
        for obj in (NhbLid
                    .objects
                    .filter(bij_vereniging=functie_nu.nhb_ver)
                    .filter(geboorte_datum__year__lt=jeugdgrens)
                    .order_by('achternaam', 'voornaam')):
            obj.leeftijdsklasse = None
            objs.append(obj)
        # for

        # maak een paar tabellen om database toegangen te verminderen
        nhblid_dict = dict()    # [nhb_nr] = NhbLid
        for nhblid in objs:
            nhblid.wedstrijdbogen = list()
            nhblid_dict[nhblid.nhb_nr] = nhblid
        # for

        ag_dict = dict()        # [schutterboog_pk] = Score
        for score in (Score
                      .objects
                      .select_related('schutterboog')
                      .filter(is_ag=True, afstand_meter=comp.afstand)):
            ag = score.waarde / 1000
            ag_dict[score.schutterboog.pk] = ag
        # for

        wil_competitie = dict()     # [nhb_nr] = True/False
        for voorkeuren in (SchutterVoorkeuren
                           .objects
                           .select_related('nhblid')
                           .filter(nhblid__bij_vereniging=functie_nu.nhb_ver)):
            wil_competitie[voorkeuren.nhblid.nhb_nr] = voorkeuren.voorkeur_meedoen_competitie
        # for

        is_aangemeld_dict = dict()   # [schutterboog.pk] = True/False
        for deelnemer in (RegioCompetitieSchutterBoog
                          .objects
                          .select_related('schutterboog', 'deelcompetitie')
                          .filter(bij_vereniging=functie_nu.nhb_ver,
                                  deelcompetitie__competitie=comp)):
            is_aangemeld_dict[deelnemer.schutterboog.pk] = True
        # for

        # zoek de bogen informatie bij elk lid
        # split per schutter-boog
        objs2 = list()
        for schutterboog in (SchutterBoog
                             .objects
                             .filter(voor_wedstrijd=True)
                             .select_related('nhblid', 'boogtype')
                             .order_by('boogtype__volgorde')
                             .only('nhblid__nhb_nr', 'boogtype__beschrijving')):
            try:
                nhblid = nhblid_dict[schutterboog.nhblid.nhb_nr]
            except KeyError:
                # schutterboog niet van deze vereniging
                pass
            else:
                # maak een kopie van het nhblid en maak het uniek voor dit boogtype
                obj = copy.copy(nhblid)
                obj.boogtype = schutterboog.boogtype.beschrijving
                obj.check = "lid_%s_boogtype_%s" % (nhblid.nhb_nr, schutterboog.boogtype.pk)

                try:
                    obj.ag = ag_dict[schutterboog.pk]
                except KeyError:
                    obj.ag_18 = AG_NUL

                # kijk of de schutter al aangemeld is
                try:
                    obj.is_aangemeld = is_aangemeld_dict[schutterboog.pk]
                except KeyError:
                    obj.is_aangemeld = False

                # kijk of de schutter wel mee wil doen met de competitie
                try:
                    obj.wil_competitie = wil_competitie[schutterboog.nhblid.nhb_nr]
                except KeyError:
                    # schutter had geen voorkeuren
                    # dit is een opt-out, dus standaard True
                    obj.wil_competitie = True

                objs2.append(obj)
        # for

        return objs2

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        context['nhb_ver'] = functie_nu.nhb_ver
        # rol is HWL (zie test_func)

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
        context['comp'] = self.comp
        context['seizoen'] = '%s/%s' % (self.comp.begin_jaar, self.comp.begin_jaar + 1)
        context['tweede_jaar'] = self.comp.begin_jaar + 1
        context['inschrijven_url'] = reverse('Vereniging:leden-inschrijven', kwargs={'comp_pk': self.comp.pk})
        context['mag_inschrijven'] = True

        # bepaal de inschrijfmethode voor deze regio
        mijn_regio = functie_nu.nhb_ver.regio.regio_nr

        deelcomp = (DeelCompetitie
                    .objects
                    .select_related('competitie', 'nhb_regio')
                    .get(competitie=self.comp, nhb_regio=functie_nu.nhb_ver.regio.regio_nr))

        methode = deelcomp.inschrijf_methode

        if methode == INSCHRIJF_METHODE_3:
            context['dagdelen'] = DAGDEEL

            if deelcomp.toegestane_dagdelen != '':
                context['dagdelen'] = list()
                for dagdeel in DAGDEEL:
                    # dagdeel = tuple(code, beschrijving)
                    # code = GN / AV / ZA / ZO / WE
                    if dagdeel[0] in deelcomp.toegestane_dagdelen:
                        context['dagdelen'].append(dagdeel)
                # for

        menu_dynamics(self.request, context, actief='vereniging')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Geselecteerde schutters aanmelden' wordt gebruikt
            het csrf token is al gecontroleerd
        """
        try:
            comp_pk = int(self.kwargs['comp_pk'][:10])
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, TypeError, Competitie.DoesNotExist):
            raise Resolver404()

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        # rol is HWL (zie test_func)

        # bepaal de inschrijfmethode voor deze regio
        hwl_regio_nr = functie_nu.nhb_ver.regio.regio_nr

        # zoek de juiste DeelCompetitie erbij
        deelcomp = DeelCompetitie.objects.get(competitie=comp,
                                              nhb_regio=hwl_regio_nr)
        methode = deelcomp.inschrijf_methode

        # zoek eerst de voorkeuren op
        bulk_team = False
        if request.POST.get('wil_in_team', '') != '':
            bulk_team = True

        bulk_dagdeel = ''
        if methode == INSCHRIJF_METHODE_3:
            dagdeel = request.POST.get('dagdeel', '')
            if dagdeel in DAGDEEL_AFKORTINGEN:
                if dagdeel in deelcomp.toegestane_dagdelen or deelcomp.toegestane_dagdelen == '':
                    bulk_dagdeel = dagdeel
            if not bulk_dagdeel:
                raise Resolver404()

        bulk_opmerking = request.POST.get('opmerking', '')
        if len(bulk_opmerking) > 500:
            bulk_opmerking = bulk_opmerking[:500]     # moet afkappen, anders database foutmelding

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
                    schutterboog = (SchutterBoog
                                    .objects
                                    .select_related('nhblid')
                                    .get(nhblid=nhblid_pk,
                                         boogtype=boogtype_pk))
                except SchutterBoog.DoesNotExist:
                    # iemand loopt te klooien
                    raise Resolver404()

                if not schutterboog.voor_wedstrijd:
                    # iemand loopt te klooien
                    raise Resolver404()

                # controleer lid bij vereniging HWL
                if schutterboog.nhblid.bij_vereniging != functie_nu.nhb_ver:
                    # iemand loopt te klooien
                    raise Resolver404()

                # voorkom dubbele aanmelding
                if (RegioCompetitieSchutterBoog
                        .objects
                        .filter(deelcompetitie=deelcomp,
                                schutterboog=schutterboog)
                        .count() > 0):
                    # al aangemeld - zie niet hier moeten zijn gekomen
                    raise Resolver404()

                # bepaal in welke wedstrijdklasse de schutter komt
                age = schutterboog.nhblid.bereken_wedstrijdleeftijd(deelcomp.competitie.begin_jaar + 1)

                # zoek de aanvangsgemiddelden er bij, indien beschikbaar
                ag = AG_NUL
                for score in Score.objects.filter(schutterboog=schutterboog,
                                                  afstand_meter=comp.afstand,
                                                  is_ag=True):
                    ag = score.waarde / 1000
                # for

                aanmelding = RegioCompetitieSchutterBoog()
                aanmelding.deelcompetitie = deelcomp
                aanmelding.schutterboog = schutterboog
                aanmelding.bij_vereniging = schutterboog.nhblid.bij_vereniging
                aanmelding.aanvangsgemiddelde = ag

                # zoek alle wedstrijdklassen van deze competitie met het juiste boogtype
                qset = (CompetitieKlasse
                        .objects
                        .filter(competitie=deelcomp.competitie,
                                indiv__boogtype=schutterboog.boogtype)
                        .order_by('indiv__volgorde'))

                # zoek een toepasselijke klasse aan de hand van de leeftijd
                done = False
                for obj in qset:
                    if aanmelding.aanvangsgemiddelde >= obj.min_ag or obj.indiv.is_onbekend:
                        for lkl in obj.indiv.leeftijdsklassen.all():
                            if lkl.geslacht == schutterboog.nhblid.geslacht:
                                if lkl.min_wedstrijdleeftijd <= age <= lkl.max_wedstrijdleeftijd:
                                    aanmelding.klasse = obj
                                    done = True
                                    break
                        # for
                    if done:
                        break
                # for

                # kijk of de schutter met een team mee wil schieten voor deze competitie
                if age > MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT:
                    # is geen aspirant
                    if bulk_team:
                        aanmelding.inschrijf_voorkeur_team = True

                aanmelding.inschrijf_voorkeur_dagdeel = bulk_dagdeel
                aanmelding.inschrijf_notitie = bulk_opmerking
                aanmelding.save()

            # else: silently ignore
        # for

        return HttpResponseRedirect(reverse('Vereniging:leden-ingeschreven', kwargs={'deelcomp_pk': deelcomp.pk}))


class LedenIngeschrevenView(UserPassesTestMixin, ListView):

    """ Deze view laat de HWL/WL zien welke leden ingeschreven zijn voor een competitie """

    # class variables shared by all instances
    template_name = TEMPLATE_LEDEN_INGESCHREVEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        _, functie_nu = rol_get_huidige_functie(self.request)
        return functie_nu and functie_nu.rol in ('HWL', 'WL')

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        try:
            deelcomp_pk = int(self.kwargs['deelcomp_pk'][:6])       # afkappen geeft veiligheid
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(pk=deelcomp_pk))
        except (ValueError, TypeError, DeelCompetitie.DoesNotExist):
            raise Resolver404()

        self.deelcomp = deelcomp

        dagdeel_str = dict()
        for afkorting, beschrijving in DAGDEEL:
            dagdeel_str[afkorting] = beschrijving
        # for
        dagdeel_str[''] = ''

        _, functie_nu = rol_get_huidige_functie(self.request)
        objs = (RegioCompetitieSchutterBoog
                .objects
                .select_related('schutterboog', 'schutterboog__nhblid',
                                'bij_vereniging', 'klasse', 'klasse__indiv')
                .filter(deelcompetitie=deelcomp,
                        bij_vereniging=functie_nu.nhb_ver)
                .order_by('klasse__indiv__volgorde'))

        for obj in objs:
            obj.team_ja_nee = JA_NEE[obj.inschrijf_voorkeur_team]
            obj.dagdeel_str = dagdeel_str[obj.inschrijf_voorkeur_dagdeel]
            obj.check = "pk_%s" % obj.pk
        # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        context['nhb_ver'] = functie_nu.nhb_ver

        context['deelcomp'] = deelcomp = self.deelcomp

        if rol_nu == Rollen.ROL_HWL:
            context['uitschrijven_url'] = reverse('Vereniging:leden-ingeschreven', kwargs={'deelcomp_pk': deelcomp.pk})
            context['mag_uitschrijven'] = True

        methode = deelcomp.inschrijf_methode
        if methode == INSCHRIJF_METHODE_3:
            context['toon_dagdeel'] = DAGDEEL

        menu_dynamics(self.request, context, actief='vereniging')
        return context

    def post(self, request, *args, **kwargs):
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        if rol_nu != Rollen.ROL_HWL:
            raise Resolver404()

        # all checked boxes are in the post request as keys, typically with value 'on'
        for key, _ in request.POST.items():
            if key[0:0+3] == 'pk_':
                pk = key[3:3+7]   # afkappen geeft bescherming
                try:
                    inschrijving = RegioCompetitieSchutterBoog.objects.get(pk=pk)
                except (ValueError, TypeError, RegioCompetitieSchutterBoog.DoesNotExist):
                    # niet normaal
                    raise Resolver404()

                # controleer dat deze inschrijving bij de vereniging hoort
                if inschrijving.schutterboog.nhblid.bij_vereniging != functie_nu.nhb_ver:
                    raise Resolver404()

                # schrijf de schutter uit
                inschrijving.delete()
        # for

        return HttpResponseRedirect(reverse('Vereniging:overzicht'))

# end of file
