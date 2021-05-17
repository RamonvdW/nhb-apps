# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import ListView, TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige_functie
from BasisTypen.models import (LeeftijdsKlasse, TeamType,
                               MAXIMALE_LEEFTIJD_JEUGD,
                               MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT)
from NhbStructuur.models import NhbLid
from Schutter.models import SchutterBoog, SchutterVoorkeuren
from Competitie.models import (AG_NUL, DAGDELEN, DAGDEEL_AFKORTINGEN,
                               INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_3,
                               Competitie, CompetitieKlasse,
                               DeelCompetitie, DeelcompetitieRonde,
                               RegioCompetitieSchutterBoog, KlasseBepaler)
from Score.models import Score, SCORE_TYPE_INDIV_AG
from Wedstrijden.models import CompetitieWedstrijd
import copy


TEMPLATE_LEDEN_AANMELDEN = 'vereniging/competitie-aanmelden.dtl'
TEMPLATE_LEDEN_INGESCHREVEN = 'vereniging/competitie-ingeschreven.dtl'
TEMPLATE_TOGGLE_VOORKEUR_TEAMCOMPETITIE = 'vereniging/competitie-toggle-voorkeur-teamcompetitie.dtl'


JA_NEE = {False: 'Nee', True: 'Ja'}


class LedenAanmeldenView(UserPassesTestMixin, ListView):

    """ Deze view laat de HWL leden inschrijven voor een competitie """

    # class variables shared by all instances
    template_name = TEMPLATE_LEDEN_AANMELDEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(*kwargs)
        self.comp = None
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.functie_nu.rol == 'HWL'

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        try:
            comp_pk = int(self.kwargs['comp_pk'][:10])
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, TypeError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        self.comp = comp
        comp.bepaal_fase()

        # check dat competitie open is voor inschrijvingen
        if not ('B' <= comp.fase <= 'E'):
            raise Http404('Verkeerde competitie fase')

        _, functie_nu = rol_get_huidige_functie(self.request)
        objs = list()

        # bepaal de inschrijfmethode voor deze regio
        if functie_nu.nhb_ver.regio.is_administratief:
            # niemand van deze vereniging mag zich inschrijven
            return objs

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
                for lkl in LeeftijdsKlasse.objects.filter(geslacht='M'):
                    if lkl.leeftijd_is_compatible(wedstrijdleeftijd):
                        obj.leeftijdsklasse = lkl
                        # geen master/veteraan, dus stop bij eerste passende klasse
                        break
                # for

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
                      .filter(type=SCORE_TYPE_INDIV_AG,
                              afstand_meter=comp.afstand)):
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
                             .only('nhblid__nhb_nr', 'boogtype__afkorting', 'boogtype__beschrijving')):
            try:
                nhblid = nhblid_dict[schutterboog.nhblid.nhb_nr]
            except KeyError:
                # schutterboog niet van deze vereniging
                pass
            else:
                # maak een kopie van het nhblid en maak het uniek voor dit boogtype
                obj = copy.copy(nhblid)
                obj.afkorting = schutterboog.boogtype.afkorting
                obj.boogtype = schutterboog.boogtype.beschrijving
                obj.check = "lid_%s_boogtype_%s" % (nhblid.nhb_nr, schutterboog.boogtype.pk)
                obj.mag_teamschieten = True
                if obj.leeftijdsklasse and obj.leeftijdsklasse.is_aspirant_klasse():
                    obj.mag_teamschieten = False

                try:
                    obj.ag = ag_dict[schutterboog.pk]
                except KeyError:
                    obj.ag = AG_NUL

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

        context['nhb_ver'] = self.functie_nu.nhb_ver
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
        context['aanmelden_url'] = reverse('Vereniging:leden-aanmelden', kwargs={'comp_pk': self.comp.pk})
        context['mag_aanmelden'] = True

        # bepaal de inschrijfmethode voor deze regio
        mijn_regio = self.functie_nu.nhb_ver.regio

        if not mijn_regio.is_administratief:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie',
                                        'nhb_regio')
                        .get(competitie=self.comp,
                             nhb_regio=mijn_regio))

            methode = deelcomp.inschrijf_methode

            if methode == INSCHRIJF_METHODE_1:
                pks = list()
                for ronde in (DeelcompetitieRonde
                              .objects
                              .select_related('plan')
                              .filter(deelcompetitie=deelcomp)):
                    if not ronde.is_voor_import_oude_programma():
                        # toon de HWL alle wedstrijden in de regio, dus alle clusters
                        pks.extend(ronde.plan.wedstrijden.values_list('pk', flat=True))
                # for

                wedstrijden = (CompetitieWedstrijd
                               .objects
                               .filter(pk__in=pks)
                               .select_related('vereniging')
                               .order_by('datum_wanneer',
                                         'tijd_begin_wedstrijd'))
                context['wedstrijden'] = wedstrijden

            if methode == INSCHRIJF_METHODE_3:
                context['dagdelen'] = DAGDELEN

                if deelcomp.toegestane_dagdelen != '':
                    context['dagdelen'] = list()
                    for dagdeel in DAGDELEN:
                        # dagdeel = tuple(code, beschrijving)
                        # code = GN / AV / ZA / ZO / WE / etc.
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
            raise Http404('Competitie niet gevonden')

        # check dat competitie open is voor inschrijvingen
        comp.bepaal_fase()
        if not ('B' <= comp.fase <= 'E'):
            raise Http404('Verkeerde competitie fase')

        # rol is HWL (zie test_func)

        # bepaal de inschrijfmethode voor deze regio
        hwl_regio = self.functie_nu.nhb_ver.regio

        if hwl_regio.is_administratief:
            # niemand van deze vereniging mag meedoen aan wedstrijden
            raise Http404('Geen wedstrijden in deze regio')

        # zoek de juiste DeelCompetitie erbij
        deelcomp = DeelCompetitie.objects.get(competitie=comp,
                                              nhb_regio=hwl_regio)
        methode = deelcomp.inschrijf_methode

        boog2teamtype = dict()
        for obj in TeamType.objects.all():
            boog2teamtype[obj.afkorting] = obj
        # for

        # zoek eerst de voorkeuren op
        bulk_team = False
        if request.POST.get('wil_in_team', '') != '':
            bulk_team = True

        bulk_wedstrijden = list()
        if methode == INSCHRIJF_METHODE_1:
            pks = list()
            for ronde in (DeelcompetitieRonde
                          .objects
                          .select_related('plan')
                          .filter(deelcompetitie=deelcomp)):
                if not ronde.is_voor_import_oude_programma():
                    # sta alle wedstrijden in de regio toe, dus alle clusters
                    pks.extend(ronde.plan.wedstrijden.values_list('pk', flat=True))
            # for
            for pk in pks:
                key = 'wedstrijd_%s' % pk
                if request.POST.get(key, '') != '':
                    bulk_wedstrijden.append(pk)
            # for

        bulk_dagdeel = ''
        if methode == INSCHRIJF_METHODE_3:
            dagdeel = request.POST.get('dagdeel', '')
            if dagdeel in DAGDEEL_AFKORTINGEN:
                if dagdeel in deelcomp.toegestane_dagdelen or deelcomp.toegestane_dagdelen == '':
                    bulk_dagdeel = dagdeel
            if not bulk_dagdeel:
                raise Http404('Incompleet verzoek')

        bulk_opmerking = request.POST.get('opmerking', '')
        if len(bulk_opmerking) > 500:
            bulk_opmerking = bulk_opmerking[:500]     # moet afkappen, anders database foutmelding

        udvl = comp.uiterste_datum_lid

        bepaler = KlasseBepaler(comp)

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
                    raise Http404('Verkeerde parameters')

                # SchutterBoog record met voor_wedstrijd==True moet bestaan
                try:
                    schutterboog = (SchutterBoog
                                    .objects
                                    .select_related('nhblid',
                                                    'boogtype')
                                    .get(nhblid=nhblid_pk,
                                         boogtype=boogtype_pk))
                except SchutterBoog.DoesNotExist:
                    # iemand loopt te klooien
                    raise Http404('Sporter niet gevonden')

                if not schutterboog.voor_wedstrijd:
                    # iemand loopt te klooien
                    raise Http404('Sporter heeft geen voorkeur voor wedstrijden opgegeven')

                # controleer lid bij vereniging HWL
                if schutterboog.nhblid.bij_vereniging != self.functie_nu.nhb_ver:
                    # iemand loopt te klooien
                    raise PermissionDenied('Geen lid bij jouw vereniging')

                # voorkom dubbele aanmelding
                if (RegioCompetitieSchutterBoog
                        .objects
                        .filter(deelcompetitie=deelcomp,
                                schutterboog=schutterboog)
                        .count() > 0):
                    # al aangemeld - zou niet hier moeten zijn gekomen
                    raise Http404('Sporter is al ingeschreven')

                # bepaal in welke wedstrijdklasse de schutter komt
                age = schutterboog.nhblid.bereken_wedstrijdleeftijd(deelcomp.competitie.begin_jaar + 1)
                dvl = schutterboog.nhblid.sinds_datum

                aanmelding = RegioCompetitieSchutterBoog()
                aanmelding.deelcompetitie = deelcomp
                aanmelding.schutterboog = schutterboog
                aanmelding.bij_vereniging = schutterboog.nhblid.bij_vereniging
                aanmelding.ag_voor_indiv = AG_NUL
                aanmelding.ag_voor_team = AG_NUL
                aanmelding.ag_voor_team_mag_aangepast_worden = True

                # zoek de aanvangsgemiddelden er bij, indien beschikbaar
                for score in Score.objects.filter(schutterboog=schutterboog,
                                                  afstand_meter=comp.afstand,
                                                  type=SCORE_TYPE_INDIV_AG):
                    ag = score.waarde / 1000
                    aanmelding.ag_voor_indiv = ag
                    aanmelding.ag_voor_team = ag
                    if ag > AG_NUL:
                        aanmelding.ag_voor_team_mag_aangepast_worden = False
                # for

                # zoek een toepasselijke klasse aan de hand van de leeftijd
                bepaler.bepaal_klasse(aanmelding)
                if not aanmelding.klasse:
                    raise Http404('Geen passende wedstrijdklasse kunnen kiezen')

                # kijk of de schutter met een team mee wil en mag schieten voor deze competitie
                if age > MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT and dvl < udvl:
                    # is geen aspirant en was op tijd lid
                    if bulk_team:
                        aanmelding.inschrijf_voorkeur_team = True

                aanmelding.inschrijf_voorkeur_dagdeel = bulk_dagdeel
                aanmelding.inschrijf_notitie = bulk_opmerking
                aanmelding.save()

                if methode == INSCHRIJF_METHODE_1:
                    aanmelding.inschrijf_gekozen_wedstrijden.set(bulk_wedstrijden)

            # else: silently ignore
        # for

        return HttpResponseRedirect(reverse('Vereniging:leden-ingeschreven', kwargs={'deelcomp_pk': deelcomp.pk}))


class LedenIngeschrevenView(UserPassesTestMixin, ListView):

    """ Deze view laat de HWL/WL zien welke leden ingeschreven zijn voor een competitie """

    # class variables shared by all instances
    template_name = TEMPLATE_LEDEN_INGESCHREVEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deelcomp = None
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.functie_nu.rol in ('HWL', 'WL')

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        try:
            deelcomp_pk = int(self.kwargs['deelcomp_pk'][:6])       # afkappen geeft veiligheid
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(pk=deelcomp_pk))
        except (ValueError, TypeError, DeelCompetitie.DoesNotExist):
            raise Http404('Verkeerde parameters')

        self.deelcomp = deelcomp
        comp = deelcomp.competitie
        comp.bepaal_fase()
        mag_toggle = comp.fase <= 'B' and self.functie_nu.rol == 'HWL'
        mag_uit_team = comp.fase <= 'F' and self.functie_nu.rol == 'HWL'

        dagdeel_str = dict()
        for afkorting, beschrijving in DAGDELEN:
            dagdeel_str[afkorting] = beschrijving
        # for
        dagdeel_str[''] = ''

        objs = (RegioCompetitieSchutterBoog
                .objects
                .select_related('schutterboog', 'schutterboog__nhblid',
                                'bij_vereniging', 'klasse', 'klasse__indiv')
                .filter(deelcompetitie=deelcomp,
                        bij_vereniging=self.functie_nu.nhb_ver)
                .order_by('klasse__indiv__volgorde',
                          'schutterboog__nhblid__voornaam',
                          'schutterboog__nhblid__achternaam'))

        for obj in objs:
            obj.team_ja_nee = JA_NEE[obj.inschrijf_voorkeur_team]
            obj.dagdeel_str = dagdeel_str[obj.inschrijf_voorkeur_dagdeel]
            obj.check = "pk_%s" % obj.pk
            lid = obj.schutterboog.nhblid
            obj.nhb_nr = lid.nhb_nr
            obj.naam_str = lid.volledige_naam()

            if obj.inschrijf_voorkeur_team:
                if mag_toggle:
                    obj.maak_nee = True
                elif mag_uit_team:
                    obj.url_maak_nee_rood = reverse('Vereniging:toggle-voorkeur-teamcompetitie',
                                                    kwargs={'deelnemer_pk': obj.pk})
            else:
                if mag_toggle:
                    obj.maak_ja = True
        # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['nhb_ver'] = self.functie_nu.nhb_ver

        context['deelcomp'] = self.deelcomp

        context['mag_afmelden'] = False

        if self.rol_nu == Rollen.ROL_HWL:
            context['afmelden_url'] = reverse('Vereniging:leden-ingeschreven',
                                              kwargs={'deelcomp_pk': self.deelcomp.pk})
            comp = self.deelcomp.competitie
            comp.bepaal_fase()
            if comp.fase <= 'B':
                context['mag_afmelden'] = True

        methode = self.deelcomp.inschrijf_methode
        if methode == INSCHRIJF_METHODE_3:
            context['toon_dagdeel'] = DAGDELEN

        menu_dynamics(self.request, context, actief='vereniging')
        return context

    def post(self, request, *args, **kwargs):

        if self.rol_nu != Rollen.ROL_HWL:
            raise PermissionDenied('Verkeerde rol')

        deelnemer_pk = request.POST.get('toggle_deelnemer_pk', '')
        if deelnemer_pk:
            try:
                deelnemer_pk = int(deelnemer_pk[:6])        # afkappen voor de veiligheid
                deelnemer = (RegioCompetitieSchutterBoog
                             .objects
                             .select_related('bij_vereniging',
                                             'deelcompetitie')
                             .get(pk=deelnemer_pk))
            except (ValueError, RegioCompetitieSchutterBoog.DoesNotExist):
                raise Http404('Deelnemer niet gevonden')

            ver = deelnemer.bij_vereniging
            if ver and ver != self.functie_nu.nhb_ver:
                raise PermissionDenied('Sporter is niet lid bij jouw vereniging')

            deelnemer.inschrijf_voorkeur_team = not deelnemer.inschrijf_voorkeur_team
            deelnemer.save(update_fields=['inschrijf_voorkeur_team'])

            url = reverse('Vereniging:leden-ingeschreven',
                          kwargs={'deelcomp_pk': deelnemer.deelcompetitie.pk})
            return HttpResponseRedirect(url)

        # all checked boxes are in the post request as keys, typically with value 'on'
        for key, _ in request.POST.items():
            if key[0:0+3] == 'pk_':
                pk = key[3:3+7]   # afkappen geeft bescherming
                try:
                    inschrijving = RegioCompetitieSchutterBoog.objects.get(pk=pk)
                except (ValueError, TypeError, RegioCompetitieSchutterBoog.DoesNotExist):
                    # niet normaal
                    raise Http404('Geen valide inschrijving')

                # controleer dat deze inschrijving bij de vereniging hoort
                if inschrijving.bij_vereniging != self.functie_nu.nhb_ver:
                    raise PermissionDenied('Sporter is niet lid bij jouw vereniging')

                # schrijf de schutter uit
                inschrijving.delete()
        # for

        return HttpResponseRedirect(reverse('Vereniging:overzicht'))


class ToggleVoorkeurTeamcompetitieView(UserPassesTestMixin, TemplateView):

    template_name = TEMPLATE_TOGGLE_VOORKEUR_TEAMCOMPETITIE

    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deelcomp = None
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_HWL, Rollen.ROL_RCL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])      # afkappen voor de veiligheid
            deelnemer = (RegioCompetitieSchutterBoog
                         .objects
                         .select_related('deelcompetitie',
                                         'deelcompetitie__competitie',
                                         'schutterboog',
                                         'schutterboog__nhblid',
                                         'bij_vereniging',
                                         'bij_vereniging__regio')
                         .get(pk=deelnemer_pk))
        except (ValueError, RegioCompetitieSchutterBoog.DoesNotExist):
            raise Http404('Deelnemer niet gevonden')

        context['deelnemer'] = deelnemer

        ver = deelnemer.bij_vereniging
        deelcomp = deelnemer.deelcompetitie

        if self.rol_nu == Rollen.ROL_RCL:
            # RCL: moet van zijn deelcompetitie zijn
            if deelcomp.nhb_regio != self.functie_nu.nhb_regio:
                raise PermissionDenied('Sporter uit andere regio')
            context['is_rcl'] = True
        else:
            # HWL: moet deelnemer van eigen vereniging zijn
            if ver and ver != self.functie_nu.nhb_ver:
                raise PermissionDenied('Sporter is niet lid bij jouw vereniging')
            context['is_hwl'] = True

        url = reverse('Vereniging:toggle-voorkeur-teamcompetitie',
                      kwargs={'deelnemer_pk': deelnemer.pk})

        if deelnemer.inschrijf_voorkeur_team:
            # zowel HWL als RCL mogen de sporter afmelden
            context['url_afmelden'] = url
        else:
            # alleen RCL mag weer aanmelden
            if self.rol_nu == Rollen.ROL_RCL:
                context['url_aanmelden'] = url

        if not ('url_aanmelden' in context or 'url_afmelden' in context):
            context['geen_actie_mogelijk'] = True

        menu_dynamics(self.request, context, actief='vereniging')
        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als de beheerder op de knop Aanmelden of Afmelden drukt
        """
        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])        # afkappen voor de veiligheid
            deelnemer = (RegioCompetitieSchutterBoog
                         .objects
                         .select_related('bij_vereniging',
                                         'deelcompetitie')
                         .get(pk=deelnemer_pk))
        except (ValueError, RegioCompetitieSchutterBoog.DoesNotExist):
            raise Http404('Deelnemer niet gevonden')

        deelcomp = deelnemer.deelcompetitie
        ver = deelnemer.bij_vereniging

        if self.rol_nu == Rollen.ROL_RCL:
            # RCL: moet van zijn deelcompetitie zijn
            if deelcomp.nhb_regio != self.functie_nu.nhb_regio:
                raise PermissionDenied('Sporter uit andere regio')

            # RCL mag beide kanten op wijzigen
            deelnemer.inschrijf_voorkeur_team = not deelnemer.inschrijf_voorkeur_team
            deelnemer.save(update_fields=['inschrijf_voorkeur_team'])

            url = reverse('Competitie:overzicht',
                          kwargs={'comp_pk': deelcomp.competitie.pk})
        else:
            # HWL: moet deelnemer van eigen vereniging zijn
            if ver and ver != self.functie_nu.nhb_ver:
                raise PermissionDenied('Sporter is niet lid bij jouw vereniging')

            # HWL mag alleen afmelden
            if deelnemer.inschrijf_voorkeur_team:
                deelnemer.inschrijf_voorkeur_team = False
                deelnemer.save(update_fields=['inschrijf_voorkeur_team'])

            url = reverse('Vereniging:leden-ingeschreven',
                          kwargs={'deelcomp_pk': deelnemer.deelcompetitie.pk})

        return HttpResponseRedirect(url)


# end of file
