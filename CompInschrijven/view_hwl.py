# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import ListView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from BasisTypen.definities import (MAXIMALE_LEEFTIJD_JEUGD, MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT,
                                   BLAZOEN_60CM_4SPOT, BLAZOEN_DT)
from Competitie.definities import DAGDELEN, DAGDEEL_AFKORTINGEN, INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_3
from Competitie.models import (Competitie, CompetitieMatch, get_competitie_indiv_leeftijdsklassen,
                               Regiocompetitie, RegiocompetitieRonde, RegiocompetitieSporterBoog)
from Competitie.operations import KlasseBepaler
from Competitie.operations import get_competitie_bogen
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige_functie
from Score.definities import AG_NUL, AG_DOEL_INDIV, AG_DOEL_TEAM
from Score.models import Aanvangsgemiddelde, AanvangsgemiddeldeHist
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from Sporter.operations import get_sporter_voorkeuren
import copy


TEMPLATE_LEDEN_AANMELDEN = 'compinschrijven/hwl-leden-aanmelden.dtl'
TEMPLATE_LEDEN_INGESCHREVEN = 'compinschrijven/hwl-leden-ingeschreven.dtl'


JA_NEE = {False: 'Nee', True: 'Ja'}


class LedenAanmeldenView(UserPassesTestMixin, ListView):

    """ Deze view laat de HWL leden inschrijven voor een competitie """

    # class variables shared by all instances
    template_name = TEMPLATE_LEDEN_AANMELDEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(*kwargs)
        self.comp = None
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu == Rollen.ROL_HWL

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        try:
            comp_pk = int(self.kwargs['comp_pk'][:10])      # afkappen voor de veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, TypeError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        self.comp = comp
        comp.bepaal_fase()

        # check dat competitie open is voor inschrijvingen
        if not comp.is_open_voor_inschrijven():
            raise Http404('Verkeerde competitie fase')

        objs = list()

        # bepaal de inschrijfmethode voor deze regio
        if self.functie_nu.vereniging.regio.is_administratief:
            # niemand van deze vereniging mag zich inschrijven
            return objs

        hwl_ver = self.functie_nu.vereniging

        # bepaal de boogtypen die voorkomen in de competitie
        boogtype_dict = get_competitie_bogen(comp)
        boogtype_afkortingen = list(boogtype_dict.keys())

        prev_lkl = None
        prev_geslacht = '?'
        prev_wedstrijdleeftijd = 0
        jeugdgrens = comp.begin_jaar - MAXIMALE_LEEFTIJD_JEUGD

        leeftijdsklassen = get_competitie_indiv_leeftijdsklassen(comp)

        # sorteer jeugd op geboortejaar en daarna naam
        for obj in (Sporter
                    .objects
                    .filter(bij_vereniging=hwl_ver,
                            geboorte_datum__year__gte=jeugdgrens)
                    .exclude(is_actief_lid=False)
                    .exclude(is_overleden=True)
                    .order_by('-geboorte_datum__year',
                              'achternaam',
                              'voornaam')):

            # de wedstrijdleeftijd voor dit hele seizoen
            wedstrijdleeftijd = obj.bereken_wedstrijdleeftijd_wa(comp.begin_jaar + 1)
            obj.leeftijd = wedstrijdleeftijd

            # de wedstrijdklasse voor dit hele seizoen
            if prev_lkl and wedstrijdleeftijd == prev_wedstrijdleeftijd and obj.geslacht == prev_geslacht:
                obj.leeftijdsklasse = prev_lkl
            else:
                for lkl in leeftijdsklassen:
                    if lkl.geslacht_is_compatible(obj.geslacht) and lkl.leeftijd_is_compatible(wedstrijdleeftijd):
                        obj.leeftijdsklasse = lkl
                        prev_lkl = obj.leeftijdsklasse
                        prev_geslacht = obj.geslacht
                        prev_wedstrijdleeftijd = wedstrijdleeftijd
                        # stop bij eerste passende klasse
                        break
                # for

            objs.append(obj)
        # for

        # sorteer volwassenen op naam
        for obj in (Sporter
                    .objects
                    .filter(bij_vereniging=hwl_ver,
                            geboorte_datum__year__lt=jeugdgrens)
                    .exclude(is_actief_lid=False)
                    .exclude(is_overleden=True)
                    .order_by('achternaam',
                              'voornaam')):
            obj.leeftijdsklasse = None
            objs.append(obj)
        # for

        # maak een paar tabellen om database toegangen te verminderen
        sporter_dict = dict()    # [lid_nr] = Sporter
        for sporter in objs:
            sporter.wedstrijdbogen = list()
            sporter_dict[sporter.lid_nr] = sporter
        # for

        ag_indiv_dict = dict()        # [sporterboog_pk] = Score
        for ag in (Aanvangsgemiddelde
                   .objects
                   .select_related('sporterboog')
                   .filter(doel=AG_DOEL_INDIV,
                           afstand_meter=comp.afstand)):
            ag_indiv_dict[ag.sporterboog.pk] = ag.waarde
        # for

        ag_teams_dict = dict()        # [sporterboog_pk] = Score
        for ag in (Aanvangsgemiddelde
                   .objects
                   .select_related('sporterboog')
                   .filter(doel=AG_DOEL_TEAM,
                           afstand_meter=comp.afstand)):
            ag_teams_dict[ag.sporterboog.pk] = ag.waarde
        # for

        wil_competitie = dict()     # [lid_nr] = True/False
        for voorkeuren in (SporterVoorkeuren
                           .objects
                           .select_related('sporter')
                           .filter(sporter__bij_vereniging=hwl_ver)):
            wil_competitie[voorkeuren.sporter.lid_nr] = voorkeuren.voorkeur_meedoen_competitie
        # for

        is_aangemeld_dict = dict()   # [sporterboog.pk] = True/False
        for deelnemer in (RegiocompetitieSporterBoog
                          .objects
                          .select_related('sporterboog',
                                          'regiocompetitie')
                          .filter(bij_vereniging=hwl_ver,
                                  regiocompetitie__competitie=comp)):
            is_aangemeld_dict[deelnemer.sporterboog.pk] = True
        # for

        for nr, obj in enumerate(objs):
            obj.volgorde = nr
        # for

        # grootste vereniging heeft een paar honderd leden
        sporter_pks = [sporter.pk for sporter in objs]
        handled_pks = list()

        # zoek de bogen informatie bij elk lid
        # split per sporter-boog
        objs2 = list()
        for sporterboog in (SporterBoog
                            .objects
                            .filter(voor_wedstrijd=True,
                                    sporter__pk__in=sporter_pks,
                                    boogtype__afkorting__in=boogtype_afkortingen)
                            .select_related('sporter',
                                            'boogtype')
                            .order_by('boogtype__volgorde',                # groepeer op boogtype
                                      '-sporter__geboorte_datum__year',    # jongste eerst
                                      'sporter__achternaam',               # binnen de leeftijd op achternaam
                                      'sporter__voornaam')
                            .only('sporter__lid_nr',
                                  'boogtype__afkorting',
                                  'boogtype__beschrijving',
                                  'boogtype__volgorde')):
            try:
                sporter = sporter_dict[sporterboog.sporter.lid_nr]
            except KeyError:
                # sporterboog niet van deze vereniging
                pass
            else:
                if sporter.pk not in handled_pks:
                    handled_pks.append(sporter.pk)

                boogtype = sporterboog.boogtype

                # maak een kopie van de sporter en maak het uniek voor dit boogtype
                obj = copy.copy(sporter)
                obj.afkorting = boogtype.afkorting
                obj.boogtype = boogtype.beschrijving
                obj.check = "lid_%s_boogtype_%s" % (sporter.lid_nr, boogtype.pk)
                obj.mag_teamschieten = True
                if obj.leeftijdsklasse and obj.leeftijdsklasse.is_aspirant_klasse():
                    obj.mag_teamschieten = False

                try:
                    obj.ag = ag_indiv_dict[sporterboog.pk]
                except KeyError:
                    obj.ag = AG_NUL

                try:
                    obj.ag_team = ag_indiv_dict[sporterboog.pk]
                except KeyError:
                    obj.ag_team = obj.ag

                # kijk of de sporter al aangemeld is
                try:
                    obj.is_aangemeld = is_aangemeld_dict[sporterboog.pk]
                except KeyError:
                    obj.is_aangemeld = False

                # kijk of de sporter wel mee wil doen met de competitie
                try:
                    obj.wil_competitie = wil_competitie[sporterboog.sporter.lid_nr]
                except KeyError:
                    # sporter heeft geen voorkeuren
                    # dit is een opt-out, dus standaard True
                    obj.wil_competitie = True

                tup = (sporter.volgorde, boogtype.volgorde, obj)
                objs2.append(tup)
        # for

        for pk in sporter_pks:
            if pk not in handled_pks:
                sporter = sporter_dict[pk]

                # maak een kopie van de sporter en maak het uniek voor dit boogtype
                obj = copy.copy(sporter)
                obj.afkorting = '?'
                obj.boogtype = None
                obj.mag_teamschieten = False

                tup = (sporter.volgorde, 99, sporter)
                objs2.append(tup)
        # for

        # sorteer objs2 zodat deze in dezelfde volgorde staat als objs:
        # - jeugd gesorteerd op leeftijd en daarna gesorteerd op naam
        # - senioren gesorteerd op naam
        objs2.sort()

        objs3 = [obj for v1, v2, obj in objs2]

        return objs3

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['ver'] = hwl_ver = self.functie_nu.vereniging
        # rol is HWL (zie test_func)

        try:
            deelcomp = (Regiocompetitie
                        .objects
                        .get(competitie=self.comp,
                             regio=hwl_ver.regio))
        except Regiocompetitie.DoesNotExist:
            regio_organiseert_teamcomp = False
        else:
            regio_organiseert_teamcomp = deelcomp.regio_organiseert_teamcompetitie

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
        context['url_aanmelden'] = reverse('CompInschrijven:leden-aanmelden', kwargs={'comp_pk': self.comp.pk})
        context['mag_aanmelden'] = True
        context['mag_team_schieten'] = self.comp.fase_indiv == 'C' and regio_organiseert_teamcomp

        # bepaal de inschrijfmethode voor deze regio
        mijn_regio = self.functie_nu.vereniging.regio

        if not mijn_regio.is_administratief:
            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie',
                                        'regio')
                        .get(competitie=self.comp,
                             regio=mijn_regio))

            methode = deelcomp.inschrijf_methode

            if methode == INSCHRIJF_METHODE_1:
                # toon de HWL alle wedstrijden in de regio, dus alle clusters
                pks = list()
                for ronde in (RegiocompetitieRonde
                              .objects
                              .prefetch_related('matches')
                              .filter(regiocompetitie=deelcomp)):
                    pks.extend(ronde.matches.values_list('pk', flat=True))
                # for

                wedstrijden = (CompetitieMatch
                               .objects
                               .filter(pk__in=pks)
                               .exclude(vereniging__isnull=True)      # voorkom wedstrijd niet toegekend aan vereniging
                               .select_related('vereniging')
                               .order_by('datum_wanneer',
                                         'tijd_begin_wedstrijd'))

                # splits de wedstrijden op naar in-cluster en out-of-cluster
                ver_in_hwl_cluster = dict()     # [ver_nr] = True/False
                for cluster in (hwl_ver
                                .clusters
                                .prefetch_related('vereniging_set')
                                .filter(gebruik=self.comp.afstand)
                                .all()):
                    ver_nrs = list(cluster.vereniging_set.values_list('ver_nr', flat=True))
                    for ver_nr in ver_nrs:
                        ver_in_hwl_cluster[ver_nr] = True
                    # for
                # for

                wedstrijden1 = list()
                wedstrijden2 = list()
                for wedstrijd in wedstrijden:
                    try:
                        in_cluster = ver_in_hwl_cluster[wedstrijd.vereniging.ver_nr]
                    except KeyError:
                        in_cluster = False

                    if in_cluster:
                        wedstrijden1.append(wedstrijd)
                    else:
                        wedstrijden2.append(wedstrijd)
                # for

                if len(wedstrijden1):
                    context['wedstrijden_1'] = wedstrijden1
                    context['wedstrijden_2'] = wedstrijden2
                else:
                    context['wedstrijden_1'] = wedstrijden2

            if methode == INSCHRIJF_METHODE_3:
                context['dagdelen'] = DAGDELEN

                if deelcomp.toegestane_dagdelen != '':
                    dagdelen_spl = deelcomp.toegestane_dagdelen.split(',')
                    context['dagdelen'] = list()
                    for dagdeel in DAGDELEN:
                        # dagdeel = tuple(code, beschrijving)
                        # code = GN / AV / ZA / ZO / WE / etc.
                        if dagdeel[0] in dagdelen_spl:
                            context['dagdelen'].append(dagdeel)
                    # for

        url_overzicht = reverse('Vereniging:overzicht')
        anker = '#competitie_%s' % self.comp.pk
        context['kruimels'] = (
            (url_overzicht, 'Beheer vereniging'),
            (url_overzicht + anker, self.comp.beschrijving.replace(' competitie', '')),
            (None, 'Aanmelden')
        )

        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Geselecteerde sporters aanmelden' wordt gebruikt
            het csrf token is al gecontroleerd
        """
        try:
            comp_pk = int(self.kwargs['comp_pk'][:10])      # afkappen voor de veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, TypeError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        # check dat competitie open is voor inschrijvingen
        comp.bepaal_fase()
        if not comp.is_open_voor_inschrijven():
            raise Http404('Verkeerde competitie fase')

        # rol is HWL (zie test_func)

        # bepaal de inschrijfmethode voor deze regio
        hwl_regio = self.functie_nu.vereniging.regio

        if hwl_regio.is_administratief:
            # niemand van deze vereniging mag meedoen aan wedstrijden
            raise Http404('Geen wedstrijden in deze regio')

        # zoek de juiste DeelCompetitie erbij
        deelcomp = Regiocompetitie.objects.get(competitie=comp,
                                               regio=hwl_regio)
        methode = deelcomp.inschrijf_methode

        # zoek eerst de voorkeuren op
        mag_team_schieten = comp.fase_indiv == 'C'
        bulk_team = False
        if request.POST.get('wil_in_team', '') != '':
            if not mag_team_schieten:
                raise Http404('Voorkeur teamschieten niet meer toegestaan')
            bulk_team = True

        bulk_voorkeur_rk_bk = True
        if request.POST.get('geen_rk', '') != '':
            # sporters alvast afmelden voor het RK
            bulk_voorkeur_rk_bk = False

        bulk_wedstrijden = list()
        if methode == INSCHRIJF_METHODE_1:
            pks = list()
            for ronde in (RegiocompetitieRonde
                          .objects
                          .prefetch_related('matches')
                          .filter(regiocompetitie=deelcomp)):
                # sta alle wedstrijden in de regio toe, dus alle clusters
                pks.extend(ronde.matches.values_list('pk', flat=True))
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

        bepaler = KlasseBepaler(comp)

        # all checked boxes are in the post request as keys, typically with value 'on'
        for key, _ in request.POST.items():
            # key = 'lid_NNNNNN_boogtype_MM' (of iets anders)
            spl = key.split('_')
            # spl = ('lid', 'NNNNNN', 'boogtype', 'MM')     # noqa
            if len(spl) == 4 and spl[0] == 'lid' and spl[2] == 'boogtype':
                # dit lijkt ergens op - converteer de getallen (geeft ook input bescherming)
                try:
                    sporter_pk = int(spl[1])
                    boogtype_pk = int(spl[3])
                except (TypeError, ValueError):
                    # iemand loopt te klooien
                    raise Http404('Verkeerde parameters')

                # SporterBoog record met voor_wedstrijd==True moet bestaan
                try:
                    sporterboog = (SporterBoog
                                   .objects
                                   .exclude(sporter__is_overleden=True)
                                   .select_related('sporter',
                                                   'boogtype')
                                   .get(sporter=sporter_pk,
                                        boogtype=boogtype_pk))
                except SporterBoog.DoesNotExist:
                    # iemand loopt te klooien
                    raise Http404('Sporter niet gevonden')

                if not sporterboog.voor_wedstrijd:
                    # iemand loopt te klooien
                    raise Http404('Sporter heeft geen voorkeur voor wedstrijden opgegeven')

                sporter = sporterboog.sporter

                # controleer lid bij vereniging HWL
                if sporter.bij_vereniging != self.functie_nu.vereniging:
                    # iemand loopt te klooien
                    raise PermissionDenied('Geen lid bij jouw vereniging')

                # voorkom dubbele aanmelding
                if (RegiocompetitieSporterBoog
                        .objects
                        .filter(regiocompetitie=deelcomp,
                                sporterboog=sporterboog)
                        .count() > 0):
                    # al aangemeld - zou niet hier moeten zijn gekomen
                    raise Http404('Sporter is al ingeschreven')

                voorkeuren = get_sporter_voorkeuren(sporter, mag_database_wijzigen=True)
                if voorkeuren.wedstrijd_geslacht_gekozen:
                    wedstrijdgeslacht = voorkeuren.wedstrijd_geslacht   # M/V
                else:
                    wedstrijdgeslacht = sporter.geslacht                # M/V/X

                # bepaal in welke wedstrijdklasse de sporter komt
                age = sporterboog.sporter.bereken_wedstrijdleeftijd_wa(deelcomp.competitie.begin_jaar + 1)

                door_account = get_account(request)
                aanmelding = RegiocompetitieSporterBoog(
                                    regiocompetitie=deelcomp,
                                    sporterboog=sporterboog,
                                    bij_vereniging=sporterboog.sporter.bij_vereniging,
                                    ag_voor_indiv=AG_NUL,
                                    ag_voor_team=AG_NUL,
                                    ag_voor_team_mag_aangepast_worden=True,
                                    aangemeld_door=door_account)

                # zoek de aanvangsgemiddelden er bij, indien beschikbaar
                for ag in Aanvangsgemiddelde.objects.filter(sporterboog=sporterboog,
                                                            afstand_meter=comp.afstand,
                                                            doel=AG_DOEL_INDIV):
                    # AG, dus > 0.000
                    aanmelding.ag_voor_indiv = ag.waarde
                    aanmelding.ag_voor_team = ag.waarde
                    aanmelding.ag_voor_team_mag_aangepast_worden = False
                # for

                if aanmelding.ag_voor_team_mag_aangepast_worden:
                    # zoek de aanvangsgemiddelden er bij, indien beschikbaar
                    ag_hist = (AanvangsgemiddeldeHist
                               .objects
                               .filter(ag__sporterboog=sporterboog,
                                       ag__afstand_meter=comp.afstand,
                                       ag__doel=AG_DOEL_TEAM)
                               .order_by('-when')
                               .first())

                    if ag_hist:
                        # iemand heeft een AG ingevoerd voor de teamcompetitie
                        # let op: dit kan van lang geleden zijn
                        ag = ag_hist.ag
                        aanmelding.ag_voor_team = ag.waarde
                        aanmelding.ag_voor_team_mag_aangepast_worden = True
                    # for

                # zoek een toepasselijke klasse aan de hand van de leeftijd
                try:
                    bepaler.bepaal_klasse_deelnemer(aanmelding, wedstrijdgeslacht)
                except LookupError as exc:
                    raise Http404(str(exc))

                # kijk of de sporter met een team mee wil en mag schieten voor deze competitie
                if age > MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT:
                    # is geen aspirant en was op tijd lid
                    aanmelding.inschrijf_voorkeur_team = bulk_team

                aanmelding.inschrijf_voorkeur_rk_bk = bulk_voorkeur_rk_bk

                aanmelding.inschrijf_voorkeur_dagdeel = bulk_dagdeel
                aanmelding.inschrijf_notitie = bulk_opmerking
                aanmelding.save()

                if methode == INSCHRIJF_METHODE_1:
                    aanmelding.inschrijf_gekozen_matches.set(bulk_wedstrijden)

            # else: silently ignore
        # for

        url = reverse('CompInschrijven:leden-ingeschreven', kwargs={'deelcomp_pk': deelcomp.pk})
        return HttpResponseRedirect(url)


class LedenIngeschrevenView(UserPassesTestMixin, ListView):

    """ Deze view laat de HWL/WL zien welke leden ingeschreven zijn voor een competitie """

    # class variables shared by all instances
    template_name = TEMPLATE_LEDEN_INGESCHREVEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

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
            deelcomp_pk = int(self.kwargs['deelcomp_pk'][:6])       # afkappen voor de veiligheid
            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie')
                        .get(pk=deelcomp_pk))
        except (ValueError, TypeError, Regiocompetitie.DoesNotExist):
            raise Http404('Verkeerde parameters')

        self.deelcomp = deelcomp
        comp = deelcomp.competitie
        comp.bepaal_fase()
        mag_toggle = comp.fase_teams <= 'C' and self.functie_nu.rol == 'HWL'

        dagdeel_str = dict()
        for afkorting, beschrijving in DAGDELEN:
            dagdeel_str[afkorting] = beschrijving
        # for
        dagdeel_str[''] = ''

        # maak lijst lid_nrs van sporters met voorkeur voor eigen blazoen
        wens_eigen_blazoen = list(SporterVoorkeuren
                                  .objects
                                  .select_related('sporter')
                                  .filter(voorkeur_eigen_blazoen=True)
                                  .values_list('sporter__lid_nr', flat=True))

        deelnemers = (RegiocompetitieSporterBoog
                      .objects
                      .select_related('sporterboog',
                                      'sporterboog__sporter',
                                      'sporterboog__boogtype',
                                      'bij_vereniging',
                                      'indiv_klasse')
                      .filter(regiocompetitie=deelcomp,
                              bij_vereniging=self.functie_nu.vereniging)
                      .order_by('indiv_klasse__volgorde',
                                'sporterboog__sporter__voornaam',
                                'sporterboog__sporter__achternaam'))

        for deelnemer in deelnemers:
            deelnemer.eigen_blazoen_ja_nee = '-'
            if deelnemer.sporterboog.sporter.lid_nr in wens_eigen_blazoen:
                wkl = deelnemer.indiv_klasse
                if comp.is_indoor():
                    # Indoor
                    if wkl.blazoen1_regio != wkl.blazoen2_regio:
                        # er is keuze
                        if BLAZOEN_DT in (wkl.blazoen1_regio, wkl.blazoen2_regio):
                            deelnemer.eigen_blazoen_ja_nee = 'DT'
                else:
                    # 25m1pijl
                    if wkl.blazoen1_regio != wkl.blazoen2_regio:
                        # er is keuze
                        if BLAZOEN_60CM_4SPOT in (wkl.blazoen1_regio, wkl.blazoen2_regio):
                            deelnemer.eigen_blazoen_ja_nee = '4spot'

            deelnemer.team_ja_nee = JA_NEE[deelnemer.inschrijf_voorkeur_team]
            deelnemer.dagdeel_str = dagdeel_str[deelnemer.inschrijf_voorkeur_dagdeel]
            deelnemer.check = "pk_%s" % deelnemer.pk

            deelnemer.boog_str = deelnemer.sporterboog.boogtype.beschrijving

            sporter = deelnemer.sporterboog.sporter
            deelnemer.lid_nr_en_volledige_naam = sporter.lid_nr_en_volledige_naam()

            if deelnemer.inschrijf_voorkeur_team:
                if mag_toggle:
                    deelnemer.maak_nee = True
            else:
                if mag_toggle:
                    deelnemer.maak_ja = True
        # for

        return deelnemers

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['ver'] = self.functie_nu.vereniging

        context['deelcomp'] = self.deelcomp

        context['mag_afmelden'] = False

        if self.rol_nu == Rollen.ROL_HWL:
            context['afmelden_url'] = reverse('CompInschrijven:leden-ingeschreven',
                                              kwargs={'deelcomp_pk': self.deelcomp.pk})
            comp = self.deelcomp.competitie
            comp.bepaal_fase()
            if comp.fase_indiv <= 'C':
                context['mag_afmelden'] = True

        methode = self.deelcomp.inschrijf_methode
        if methode == INSCHRIJF_METHODE_3:
            context['toon_dagdeel'] = DAGDELEN

        url_overzicht = reverse('Vereniging:overzicht')
        anker = '#competitie_%s' % self.deelcomp.competitie.pk
        context['kruimels'] = (
            (url_overzicht, 'Beheer Vereniging'),
            (url_overzicht + anker, self.deelcomp.competitie.beschrijving.replace(' competitie', '')),
            (None, 'Ingeschreven')
        )

        return context

    def post(self, request, *args, **kwargs):

        if self.rol_nu != Rollen.ROL_HWL:
            raise PermissionDenied('Verkeerde rol')

        deelnemer_pk = request.POST.get('toggle_deelnemer_pk', '')
        if deelnemer_pk:
            try:
                deelnemer_pk = int(deelnemer_pk[:6])        # afkappen voor de veiligheid
                deelnemer = (RegiocompetitieSporterBoog
                             .objects
                             .select_related('bij_vereniging',
                                             'regiocompetitie')
                             .get(pk=deelnemer_pk))
            except (ValueError, RegiocompetitieSporterBoog.DoesNotExist):
                raise Http404('Deelnemer niet gevonden')

            ver = deelnemer.bij_vereniging
            if ver and ver != self.functie_nu.vereniging:
                raise PermissionDenied('Sporter is niet lid bij jouw vereniging')

            deelnemer.inschrijf_voorkeur_team = not deelnemer.inschrijf_voorkeur_team
            deelnemer.save(update_fields=['inschrijf_voorkeur_team'])

            url = reverse('CompInschrijven:leden-ingeschreven',
                          kwargs={'deelcomp_pk': deelnemer.regiocompetitie.pk})
            return HttpResponseRedirect(url)

        # all checked boxes are in the post request as keys, typically with value 'on'
        for key, _ in request.POST.items():
            if key[0:0+3] == 'pk_':
                pk = key[3:3+7]   # afkappen geeft bescherming
                try:
                    inschrijving = RegiocompetitieSporterBoog.objects.get(pk=pk)
                except (ValueError, TypeError, RegiocompetitieSporterBoog.DoesNotExist):
                    # niet normaal
                    raise Http404('Geen valide inschrijving')

                # controleer dat deze inschrijving bij de vereniging hoort
                if inschrijving.bij_vereniging != self.functie_nu.vereniging:
                    raise PermissionDenied('Sporter is niet lid bij jouw vereniging')

                # schrijf de sporter uit
                inschrijving.delete()
        # for

        return HttpResponseRedirect(reverse('Vereniging:overzicht'))


# end of file
