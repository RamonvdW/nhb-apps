# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from BasisTypen.definities import (MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT,
                                   GESLACHT_MAN, GESLACHT_VROUW, GESLACHT_ANDERS, GESLACHT_ALLE)
from Competitie.models import CompetitieIndivKlasse, CompetitieTeamKlasse
from Score.definities import AG_NUL, AG_LAAGSTE_NIET_NUL, AG_DOEL_INDIV
from Score.models import Aanvangsgemiddelde
from Sporter.models import Sporter
from decimal import Decimal
import datetime


def _get_targets_indiv(comp):
    """ Retourneer een data structuur met daarin voor alle individuele wedstrijdklassen
        de toegestane boogtypen en leeftijden

        out: target = dict() met [(min_age, max_age, boogtype, geslacht, heeft_onbekend)] = list(CompetitieIndivKlasse)

        Voorbeeld: { (21,150,'R','A', True ): [obj1, obj2, etc.],
                     (21,150,'C','A', True ): [obj10, obj11],
                     (14, 17,'C','A', False): [obj20,],             # genderneutraal
                     (12, 14,'C','M', False): [obj30,],             # alleen jongens (mannen)
                     (12, 14,'C','V', False): [obj31,] }            # alleen meisjes (vrouwen)
    """
    targets = dict()        # [ (min_age, max_age, boogtype) ] = list(wedstrijdklassen)
    for klasse in (CompetitieIndivKlasse
                   .objects
                   .filter(competitie=comp)
                   .select_related('boogtype')
                   .prefetch_related('leeftijdsklassen')
                   .order_by('volgorde')):
        # zoek de minimale en maximaal toegestane leeftijden voor deze wedstrijdklasse
        geslacht = GESLACHT_ALLE
        age_min = 999
        age_max = 0
        for lkl in klasse.leeftijdsklassen.all():
            age_min = min(lkl.min_wedstrijdleeftijd, age_min)
            age_max = max(lkl.max_wedstrijdleeftijd, age_max)
            geslacht = lkl.wedstrijd_geslacht
        # for

        tup = (age_min, age_max, geslacht, klasse.boogtype)
        if tup not in targets:
            targets[tup] = list()
        targets[tup].append(klasse)
    # for

    targets2 = dict()
    for tup, klassen in targets.items():
        age_min, age_max, geslacht, boogtype = tup
        # print("age=%s..%s, boogtype=%s, wkl=%s, %s" % (
        #          age_min, age_max, boogtype.afkorting, repr(wedstrklassen), wedstrklassen[-1].is_onbekend))
        tup = (age_min, age_max, boogtype, geslacht, klassen[-1].is_onbekend)
        targets2[tup] = klassen
    # for
    return targets2


def _get_targets_teams(comp):
    """ Retourneer een data structuur met daarin voor alle team wedstrijdklassen

        out: target = dict() met [team type afkorting] = list(CompetitieTeamKlasse)

        Voorbeeld: { 'R2': [obj1, obj2, etc.],
                     'C': [obj10, obj11],
                     'BB': [obj20]  }
    """
    targets = dict()
    for obj in (CompetitieTeamKlasse
                .objects
                .filter(competitie=comp,
                        is_voor_teams_rk_bk=False)
                .order_by('volgorde')):        # hoogste klasse (=laagste volgnummer) eerst

        try:
            targets[obj.team_afkorting].append(obj)
        except KeyError:
            targets[obj.team_afkorting] = [obj]
    # for

    return targets


def bepaal_klassengrenzen_indiv(comp):

    """ retourneert een lijst van individuele wedstrijdenklassen, elk bestaande uit een dictionary:
            'beschrijving': tekst
            'count':        aantal sporters ingedeeld in deze klasse
            'ag':           het AG van de laatste sporter in deze klasse
                            of 0.000 voor klasse onbekend
                            of 0.001 voor de laatste klasse voor klasse onbekend
            'klasse':       CompetitieIndivKlasse
            'volgorde':     nummer

        gesorteerd op volgorde (oplopend)
    """

    # bepaal het jaar waarin de wedstrijdleeftijd bepaald moet worden
    # dat is het tweede jaar van de competitie, waarin de BK gehouden wordt
    jaar = comp.begin_jaar + 1

    # haal de AG 1x op per boogtype
    boogtype2ags = dict()        # [boogtype.afkorting] = scores
    for boogtype in comp.boogtypen.all():
        boogtype2ags[boogtype.afkorting] = (Aanvangsgemiddelde
                                            .objects
                                            .select_related('sporterboog',
                                                            'sporterboog__boogtype',        # TODO: niet nodig?
                                                            'sporterboog__sporter')
                                            .filter(doel=AG_DOEL_INDIV,
                                                    afstand_meter=comp.afstand,
                                                    boogtype=boogtype))
    # for
    del boogtype

    lkl_pks = list()
    lkl_unsorted = list()
    klasse2lkl = dict()     # [klasse.pk] = [lkl, lkl, lkl..]
    for klasse in (CompetitieIndivKlasse
                   .objects
                   .filter(competitie=comp)
                   .prefetch_related('leeftijdsklassen')):

        klasse2lkl[klasse.pk] = lkls = list()
        for lkl in klasse.leeftijdsklassen.all():
            lkls.append(lkl)

            if lkl.pk not in lkl_pks:
                lkl_pks.append(lkl.pk)
                tup = (lkl.volgorde, lkl)
                lkl_unsorted.append(tup)
        # for
    # for
    del klasse
    del lkl_pks
    lkl_unsorted.sort()
    lkl_cache = [lkl for _, lkl in lkl_unsorted]
    del lkl_unsorted

    # verdeel de sportersboog (waar we een AG van hebben) over boogtype-leeftijdsklasse groepjes
    done_nrs = list()
    boogtype_lkl2schutters = dict()      # [boogtype.afkorting + '_' + leeftijdsklasse.afkorting] = [lid_nr, lid_nr, ..]
    for boogtype_afkorting in boogtype2ags.keys():
        ags = boogtype2ags[boogtype_afkorting]

        for lkl in lkl_cache:
            index = boogtype_afkorting + '_' + lkl.afkorting
            boogtype_lkl2schutters[index] = nrs = list()

            for ag in ags:
                sporterboog = ag.sporterboog
                nr = sporterboog.pk
                if nr not in done_nrs:
                    sporter = sporterboog.sporter
                    age = sporter.bereken_wedstrijdleeftijd_wa(jaar)
                    # volgorde lkl is jongste naar oudste
                    # pak de eerste de beste klasse die compatible is
                    if lkl.geslacht_is_compatible(sporter.geslacht) and lkl.leeftijd_is_compatible(age):
                        nrs.append(nr)
                        done_nrs.append(nr)
            # for (score)
        # for (lkl)
    # for (boogtype)

    # wedstrijdklassen vs leeftijd + bogen
    targets = _get_targets_indiv(comp)
    # targets[(min_age, max_age, boogtype, geslacht, heeft_onbekend)] = list(CompetitieIndivKlasse)

    # creëer de resultatenlijst
    objs = list()
    for tup, klassen in targets.items():
        _, _, boogtype, geslacht, heeft_klasse_onbekend = tup
        ags = boogtype2ags[boogtype.afkorting]

        # zoek alle sporters-boog die hier in passen (boog, leeftijd, geslacht)
        gemiddelden = list()
        index_gehad = list()
        for klasse in klassen:
            for lkl in klasse2lkl[klasse.pk]:
                index = boogtype.afkorting + '_' + lkl.afkorting
                if index not in index_gehad:
                    index_gehad.append(index)
                    nrs = boogtype_lkl2schutters[index]
                    for ag in ags:
                        if ag.sporterboog.pk in nrs:
                            gemiddelden.append(ag.waarde)
                # for
            # for
        # for

        if len(gemiddelden):
            gemiddelden.sort(reverse=True)  # in-place sort, highest to lowest
            count = len(gemiddelden)        # aantal schutters
            aantal = len(klassen)     # aantal groepen
            if heeft_klasse_onbekend:
                stop = -2
                aantal -= 1
            else:
                stop = -1
            step = int(count / aantal)      # omlaag afgerond = OK voor grote groepen
            pos = 0
            for klasse in klassen[:stop]:
                pos += step
                ag = gemiddelden[pos]
                res = {'beschrijving': klasse.beschrijving,
                       'count': step,
                       'ag': ag,
                       'klasse': klasse,
                       'volgorde': klasse.volgorde}
                objs.append(res)
            # for

            # laatste klasse krijgt speciaal AG
            klasse = klassen[stop]
            ag = AG_LAAGSTE_NIET_NUL if heeft_klasse_onbekend else AG_NUL
            res = {'beschrijving': klasse.beschrijving,
                   'count': count - (aantal - 1) * step,
                   'ag': ag,
                   'klasse': klasse,
                   'volgorde': klasse.volgorde}
            objs.append(res)

            # klasse onbekend met AG=0.000
            if heeft_klasse_onbekend:
                klasse = klassen[-1]
                res = {'beschrijving': klasse.beschrijving,
                       'count': 0,
                       'ag': AG_NUL,
                       'klasse': klasse,
                       'volgorde': klasse.volgorde}
                objs.append(res)
        else:
            # geen historische gemiddelden
            # zet ag op 0,001 als er een klasse onbekend is, anders op 0,000
            ag = AG_LAAGSTE_NIET_NUL if heeft_klasse_onbekend else AG_NUL
            for klasse in klassen:
                if klasse.is_onbekend:  # is de laatste klasse
                    ag = AG_NUL
                res = {'beschrijving': klasse.beschrijving,
                       'count': 0,
                       'ag': ag,
                       'klasse': klasse,
                       'volgorde': klasse.volgorde}
                objs.append(res)
            # for
    # for

    objs2 = sorted(objs, key=lambda k: k['volgorde'])
    return objs2


def bepaal_klassengrenzen_teams(comp):

    """ retourneert een lijst van team wedstrijdenklassen, elk bestaande uit een dictionary:
            'beschrijving': tekst
            'count':        aantal teams ingedeeld in deze klasse
            'ag':           het Team-AG van de laatste team in deze klasse
                            of 0.001 voor de laatste klasse voor klasse onbekend
            'ag_str':       geformatteerd Team-AG als NNN.M
            'klasse':       CompetitieTeamKlasse
            'volgorde':     nummer

        gesorteerd op volgorde (oplopend)
    """

    # per boogtype (dus elke sporterboog in zijn eigen team type):
    #   per vereniging:
    #      - de sporters sorteren op AG
    #      - per groepje van 4 som van beste 3 = team AG

    if comp.is_indoor():
        aantal_pijlen = 30
    else:
        aantal_pijlen = 25

    # eenmalig de wedstrijdleeftijd van elke lid berekenen in het vorige seizoen
    # hiermee kunnen we de aspiranten scores eruit filteren
    jaar = comp.begin_jaar      # gelijk aan tweede jaar vorig seizoen

    # zoek een ongeveer datum zodat we 80% van de leden niet hoeven te analyseren
    jaar_nu = timezone.now().year
    geboren_na = datetime.date(year=jaar_nu - MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT - 1, month=1, day=1)

    was_aspirant = dict()     # [ lid_nr ] = True/False
    for sporter in Sporter.objects.filter(geboorte_datum__gte=geboren_na):
        was_aspirant[sporter.lid_nr] = sporter.bereken_wedstrijdleeftijd_wa(jaar) <= MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT
    # for

    # haal de AG's op per boogtype
    boogtype2ags = dict()        # [boogtype.afkorting] = AG's
    for boogtype in comp.boogtypen.all():
        # TODO: ooit ingevoerde handmatige AG uit filteren
        boogtype2ags[boogtype.afkorting] = (Aanvangsgemiddelde
                                            .objects
                                            .select_related('sporterboog',
                                                            'sporterboog__boogtype',        # TODO: niet nodig?
                                                            'sporterboog__sporter',
                                                            'sporterboog__sporter__bij_vereniging')
                                            .exclude(sporterboog__sporter__bij_vereniging=None)
                                            .filter(doel=AG_DOEL_INDIV,
                                                    afstand_meter=comp.afstand,
                                                    boogtype=boogtype))
    # for

    # wedstrijdklassen vs leeftijd + bogen
    targets = _get_targets_teams(comp)
    # targets[team type afkorting] = list(CompetitieTeamKlasse)

    teamtype2boogtype = {
        'R2': 'R',
        'C': 'C',
        'BB2': 'BB',
        'TR': 'TR',
        'LB': 'LB'
    }

    # bepaal de mogelijk te vormen teams en de team-score
    boog2team_scores = dict()    # [boogtype afkorting] = list(team scores)
    for teamtype_afkorting, klassen in targets.items():

        # vertaal team type naar boog type
        boogtype_afkorting = teamtype2boogtype[teamtype_afkorting]

        boog2team_scores[boogtype_afkorting] = team_scores = list()

        # zoek alle schutters-boog die hier in passen (boog, leeftijd)
        per_ver_gemiddelden = dict()    # [ver_nr] = list(gemiddelde, gemiddelde, ...)
        for ag in boogtype2ags[boogtype_afkorting]:
            try:
                lid_was_aspirant = was_aspirant[ag.sporterboog.sporter.lid_nr]
            except KeyError:
                lid_was_aspirant = False

            if not lid_was_aspirant:
                ver_nr = ag.sporterboog.sporter.bij_vereniging.ver_nr
                try:
                    per_ver_gemiddelden[ver_nr].append(ag.waarde)
                except KeyError:
                    per_ver_gemiddelden[ver_nr] = [ag.waarde]
        # for

        for ver_nr, gemiddelden in per_ver_gemiddelden.items():
            gemiddelden.sort(reverse=True)  # in-place sort, highest to lowest
            aantal = len(gemiddelden)
            teams = int(aantal / 4)
            for team_nr in range(teams):
                index = team_nr * 4
                team_score = sum(gemiddelden[index:index+3])    # totaal van beste 3 scores
                team_score = round(team_score, 3)               # round here, instead of letter database do it
                team_scores.append(team_score)
            # for
        # for
    # for

    objs = list()
    for teamtype_afkorting, klassen in targets.items():
        boogtype_afkorting = teamtype2boogtype[teamtype_afkorting]
        team_scores = boog2team_scores[boogtype_afkorting]
        team_scores.sort(reverse=True)       # hoogste eerst
        count = len(team_scores)
        aantal = len(klassen)
        if aantal > 1:
            if count < aantal:
                step = 0
            else:
                step = int(count / aantal)
            if len(team_scores) == 0:
                team_scores.append(AG_NUL)
            pos = 0
            for klasse in klassen[:-1]:
                pos += step
                ag = team_scores[pos]
                ag_str = "%05.1f" % (ag * aantal_pijlen)
                ag_str = ag_str.replace('.', ',')
                res = {'beschrijving': klasse.beschrijving,
                       'count': step,
                       'ag': ag,
                       'ag_str': ag_str,
                       'klasse': klasse,
                       'volgorde': klasse.volgorde}  # voor sorteren
                objs.append(res)
            # for
            klasse = klassen[-1]
        else:
            step = 0
            klasse = klassen[0]

        ag = AG_NUL
        ag_str = "%05.1f" % (ag * aantal_pijlen)
        ag_str = ag_str.replace('.', ',')
        res = {'beschrijving': klasse.beschrijving,
               'count': count - (aantal - 1) * step,
               'ag': ag,
               'ag_str': ag_str,
               'klasse': klasse,
               'volgorde': klasse.volgorde}     # voor sorteren
        objs.append(res)
    # for

    objs2 = sorted(objs, key=lambda k: k['volgorde'])
    return objs2


class KlasseBepaler(object):
    """ deze klasse helpt met het kiezen van de CompetitieIndivKlasse voor een deelnemer """

    def __init__(self, comp):
        self.competitie = comp
        self.boogtype2klassen = dict()      # [boogtype.afkorting] = [CompetitieIndivKlasse, ...]
        self.rk_mode = False
        self.lkl_cache_mannen = dict()      # [CompetitieIndivKlasse.pk] = [lkl, lkl, ...]
        self.lkl_cache_vrouwen = dict()     # [CompetitieIndivKlasse.pk] = [lkl, lkl, ...]
        self.lkl_cache_neutraal = dict()    # [CompetitieIndivKlasse.pk] = [lkl, lkl, ...]
        self.lkl_cache = {
            GESLACHT_MAN: self.lkl_cache_mannen,
            GESLACHT_ALLE: self.lkl_cache_neutraal,
            GESLACHT_VROUW: self.lkl_cache_vrouwen,
            GESLACHT_ANDERS: self.lkl_cache_neutraal
        }

        # vul de caches met individuele wedstrijdklassen
        for klasse in (CompetitieIndivKlasse
                       .objects
                       .filter(competitie=comp)
                       .prefetch_related('leeftijdsklassen')
                       .select_related('boogtype')
                       .all()):

            boog_afkorting = klasse.boogtype.afkorting
            try:
                self.boogtype2klassen[boog_afkorting].append(klasse)
            except KeyError:
                self.boogtype2klassen[boog_afkorting] = [klasse]

            for lkl in klasse.leeftijdsklassen.all():
                lkl_cache = self.lkl_cache[lkl.wedstrijd_geslacht]
                try:
                    lkl_cache[klasse.pk].append(lkl)
                except KeyError:
                    lkl_cache[klasse.pk] = [lkl]
            # for
        # for

    def begrens_to_rk(self):
        """ begrens de mogelijke klassen tot het RK, zodat regio deelnemers in een RK klasse geplaatst kunnen worden.
            dit is voor aspiranten en late-qualifiers (na score correctie of overschrijving naar andere vereniging)
        """
        for afkorting in self.boogtype2klassen.keys():
            rk_only = [klasse for klasse in self.boogtype2klassen[afkorting] if klasse.is_ook_voor_rk_bk]
            # print(afkorting, repr(rk_only))
            self.boogtype2klassen[afkorting] = rk_only
        # for

        self.rk_mode = True

    def bepaal_klasse_deelnemer(self, deelnemer, wedstrijdgeslacht):
        """ deze functie zet deelnemer klasse aan de hand van de sporterboog

            wedstrijdgeslacht:
                GESLACHT_MAN:    past op leeftijdsklasse GESLACHT_MAN
                GESLACHT_VROUW:  past op leeftijdsklasse GESLACHT_VROUW
                GESLACHT_ANDERS: past op leeftijdsklasse GESLACHT_ALLE
        """

        if self.rk_mode:
            ag = deelnemer.gemiddelde
        else:
            ag = deelnemer.ag_voor_indiv
        sporterboog = deelnemer.sporterboog
        sporter = sporterboog.sporter
        age = sporter.bereken_wedstrijdleeftijd_wa(self.competitie.begin_jaar + 1)

        if not isinstance(ag, Decimal):
            raise LookupError('Verkeerde type')

        # voorkom problemen in de >= vergelijking verderop door afrondingsfouten
        # door conversie naar Decimal, want Decimal(7,42) = 7,4199999999
        ag += Decimal(0.00005)

        mogelijkheden = list()

        try:
            klassen = self.boogtype2klassen[sporterboog.boogtype.afkorting]
        except KeyError:
            raise LookupError('Boogtype %s wordt niet ondersteund' % sporterboog.boogtype.afkorting)
        else:
            for klasse in klassen:
                if ag >= klasse.min_ag or klasse.is_onbekend:
                    for geslacht in (wedstrijdgeslacht, GESLACHT_ALLE):
                        try:
                            lkls = self.lkl_cache[geslacht][klasse.pk]
                        except KeyError:
                            # deze combinatie bestaat niet
                            pass
                        else:
                            for lkl in lkls:
                                if lkl.leeftijd_is_compatible(age):
                                    tup = (lkl.volgorde, klasse.pk, lkl, klasse)
                                    mogelijkheden.append(tup)
                            # for
                    # for
            # for

        mogelijkheden.sort(reverse=True)

        # de sort op lkl.volgorde heeft senioren eerst gezet; aspiranten laatste
        # aspiranten mogen in alle klassen meedoen, maar we kiezen uiteindelijk de Asp klasse
        if len(mogelijkheden):
            _, _, _, klasse = mogelijkheden[-1]
            deelnemer.indiv_klasse = klasse
        else:
            # niet vast kunnen stellen
            raise LookupError("Geen passende wedstrijdklasse")


def competitie_klassengrenzen_vaststellen(comp):
    """ stel voor een specifieke Competitie alle klassengrenzen vast """

    # individueel
    for obj in bepaal_klassengrenzen_indiv(comp):
        klasse = obj['klasse']
        klasse.min_ag = obj['ag']
        klasse.save(update_fields=['min_ag'])
    # for

    # team (regio)
    for obj in bepaal_klassengrenzen_teams(comp):
        klasse = obj['klasse']
        klasse.min_ag = obj['ag']
        klasse.save(update_fields=['min_ag'])
    # for

    comp.klassengrenzen_vastgesteld = True
    comp.save(update_fields=['klassengrenzen_vastgesteld'])


# klassengrenzen vaststellen voor RK/BK teams staat in CompBeheer/views_bko.py


# end of file
