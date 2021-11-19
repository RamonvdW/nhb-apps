# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from BasisTypen.models import BoogType, LeeftijdsKlasse
from BasisTypen.models import IndivWedstrijdklasse, TeamWedstrijdklasse, MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT
from Competitie.models import AG_NUL, AG_LAAGSTE_NIET_NUL, CompetitieKlasse
from Score.models import Score, SCORE_TYPE_INDIV_AG
from Sporter.models import Sporter
from decimal import Decimal
import datetime


def _get_targets_indiv():
    """ Retourneer een data structuur met daarin voor alle individuele wedstrijdklassen
        de toegestane boogtypen en leeftijden

        out: target = dict() met [ (min_age, max_age, boogtype, heeft_onbekend) ] = list(IndivWedstrijdklasse)

        Voorbeeld: { (21,150,'R',True ): [obj1, obj2, etc.],
                     (21,150,'C',True ): [obj10, obj11],
                     (14, 17,'C',False): [obj20,]  }
    """
    targets = dict()        # [ (min_age, max_age, boogtype) ] = list(wedstrijdklassen)
    for wedstrklasse in (IndivWedstrijdklasse
                         .objects
                         .select_related('boogtype')
                         .prefetch_related('leeftijdsklassen')
                         .filter(buiten_gebruik=False)
                         .order_by('volgorde')):
        # zoek de minimale en maximaal toegestane leeftijden voor deze wedstrijdklasse
        age_min = 999
        age_max = 0
        for lkl in wedstrklasse.leeftijdsklassen.all():
            age_min = min(lkl.min_wedstrijdleeftijd, age_min)
            age_max = max(lkl.max_wedstrijdleeftijd, age_max)
        # for

        tup = (age_min, age_max, wedstrklasse.boogtype)
        if tup not in targets:
            targets[tup] = list()
        targets[tup].append(wedstrklasse)
    # for

    targets2 = dict()
    for tup, wedstrklassen in targets.items():
        age_min, age_max, boogtype = tup
        # print("age=%s..%s, boogtype=%s, wkl=%s, %s" % (age_min, age_max, boogtype.afkorting, repr(wedstrklassen), wedstrklassen[-1].is_onbekend))
        tup = (age_min, age_max, boogtype, wedstrklassen[-1].is_onbekend)
        targets2[tup] = wedstrklassen
    # for
    return targets2


def _get_targets_teams():
    """ Retourneer een data structuur met daarin voor alle team wedstrijdklassen

        out: target = dict() met [ boogtype afkorting ] = list(TeamWedstrijdklasse)

        Voorbeeld: { 'R': [obj1, obj2, etc.],
                     'C': [obj10, obj11],
                     'BB': [obj20]  }
    """
    targets = dict()
    for obj in (TeamWedstrijdklasse
                .objects
                .filter(buiten_gebruik=False)
                .select_related('team_type')
                .order_by('volgorde')):        # hoogste klasse (=laagste volgnummer) eerst

        afkorting = obj.team_type.afkorting

        try:
            targets[afkorting].append(obj)
        except KeyError:
            targets[afkorting] = [obj]
    # for
    return targets


def bepaal_klassegrenzen_indiv(comp, trans_indiv):

    """ retourneert een lijst van individuele wedstrijdenklassen, elk bestaande uit een dictionary:
            'beschrijving': tekst
            'count':        aantal sporters ingedeeld in deze klasse
            'ag':           het AG van de laatste sporter in deze klasse
                            of 0.000 voor klasse onbekend
                            of 0.001 voor de laatste klasse voor klasse onbekend
            'wedstrkl_obj': indiv klasse
            'klasse':       competitieklasse
            'volgorde':     nummer

        gesorteerd op volgorde (oplopend)
    """

    # bepaal het jaar waarin de wedstrijdleeftijd bepaald moet worden
    # dat is het tweede jaar van de competitie, waarin de BK gehouden wordt
    jaar = comp.begin_jaar + 1

    # haal de scores 1x op per boogtype
    boogtype2ags = dict()        # [boogtype.afkorting] = scores
    for boogtype in BoogType.objects.all():
        boogtype2ags[boogtype.afkorting] = (Score
                                            .objects
                                            .select_related('sporterboog',
                                                            'sporterboog__boogtype',
                                                            'sporterboog__sporter')
                                            .filter(type=SCORE_TYPE_INDIV_AG,
                                                    afstand_meter=comp.afstand,
                                                    sporterboog__boogtype=boogtype))
    # for
    del boogtype

    lkl_cache = list()
    klasse2lkl_mannen = dict()     # [klasse.pk] = [lkl, lkl, lkl..]
    for lkl in (LeeftijdsKlasse
                .objects
                .filter(geslacht='M')
                .order_by('volgorde')):         # Aspiranten eerst, Senioren laatst

        klasse_pks = list(lkl.indivwedstrijdklasse_set.values_list('pk', flat=True))
        if len(klasse_pks) > 0:
            # wordt gebruikt in de bondscompetities
            lkl_cache.append(lkl)
            for pk in klasse_pks:
                try:
                    klasse2lkl_mannen[pk].append(lkl)
                except KeyError:
                    klasse2lkl_mannen[pk] = [lkl]
            # for
    # for
    del lkl

    # verdeel de schuttersboog (waar we een AG van hebben) over boogtype-leeftijdsklasse groepjes
    done_nrs = list()
    boogtype_lkl2schutters = dict()      # [boogtype.afkorting + '_' + leeftijdsklasse.afkorting] = [lid_nr, lid_nr, ..]
    for boogtype_afkorting in boogtype2ags.keys():
        scores = boogtype2ags[boogtype_afkorting]

        for lkl in lkl_cache:
            index = boogtype_afkorting + '_' + lkl.afkorting
            boogtype_lkl2schutters[index] = nrs = list()

            for score in scores:
                sporterboog = score.sporterboog
                nr = sporterboog.pk
                if nr not in done_nrs:
                    sporter = sporterboog.sporter
                    age = sporter.bereken_wedstrijdleeftijd(jaar)
                    # volgorde lkl is Aspirant .. Senior
                    # pak de eerste de beste klasse die compatible is
                    if lkl.leeftijd_is_compatible(age):
                        nrs.append(nr)
                        done_nrs.append(nr)
            # for (score)
        # for (lkl)
    # for (boogtype)

    # wedstrijdklassen vs leeftijd + bogen
    targets = _get_targets_indiv()     # TODO: pass the caches

    # creëer de resultatenlijst
    objs = list()
    for tup, wedstrklassen in targets.items():
        _, _, boogtype, heeft_klasse_onbekend = tup
        scores = boogtype2ags[boogtype.afkorting]

        # zoek alle schutters-boog die hier in passen (boog, leeftijd)
        gemiddelden = list()
        index_gehad = list()
        for klasse in wedstrklassen:
            for lkl in klasse2lkl_mannen[klasse.pk]:
                index = boogtype.afkorting + '_' + lkl.afkorting
                if index not in index_gehad:
                    index_gehad.append(index)
                    nrs = boogtype_lkl2schutters[index]
                    for score in scores:
                        if score.sporterboog.pk in nrs:
                            gemiddelden.append(score.waarde)        # is AG*1000
                # for
            # for
        # for

        if len(gemiddelden):
            gemiddelden.sort(reverse=True)  # in-place sort, highest to lowest
            count = len(gemiddelden)        # aantal schutters
            aantal = len(wedstrklassen)     # aantal groepen
            if heeft_klasse_onbekend:
                stop = -2
                aantal -= 1
            else:
                stop = -1
            step = int(count / aantal)      # omlaag afgerond = OK voor grote groepen
            pos = 0
            for klasse in wedstrklassen[:stop]:
                pos += step
                ag = gemiddelden[pos] / 1000        # conversie Score naar AG met 3 decimalen
                res = {'beschrijving': klasse.beschrijving,
                       'count': step,
                       'ag': ag,
                       'wedstrkl_obj': klasse,
                       'volgorde': klasse.volgorde}
                objs.append(res)
            # for

            # laatste klasse krijgt speciaal AG
            klasse = wedstrklassen[stop]
            ag = AG_LAAGSTE_NIET_NUL if heeft_klasse_onbekend else AG_NUL
            res = {'beschrijving': klasse.beschrijving,
                   'count': count - (aantal - 1) * step,
                   'ag': ag,
                   'wedstrkl_obj': klasse,
                   'volgorde': klasse.volgorde}
            objs.append(res)

            # klasse onbekend met AG=0.000
            if heeft_klasse_onbekend:
                klasse = wedstrklassen[-1]
                res = {'beschrijving': klasse.beschrijving,
                       'count': 0,
                       'ag': AG_NUL,
                       'wedstrkl_obj': klasse,
                       'volgorde': klasse.volgorde}
                objs.append(res)
        else:
            # geen historische gemiddelden
            # zet ag op 0,001 als er een klasse onbekend is, anders op 0,000
            ag = AG_LAAGSTE_NIET_NUL if heeft_klasse_onbekend else AG_NUL
            for klasse in wedstrklassen:
                if klasse.is_onbekend:  # is de laatste klasse
                    ag = AG_NUL
                res = {'beschrijving': klasse.beschrijving,
                       'count': 0,
                       'ag': ag,
                       'wedstrkl_obj': klasse,
                       'volgorde': klasse.volgorde}
                objs.append(res)
            # for
    # for

    for obj in objs:
        obj['klasse'] = trans_indiv[obj['wedstrkl_obj'].pk]
    # for

    objs2 = sorted(objs, key=lambda k: k['volgorde'])
    return objs2


def bepaal_klassegrenzen_teams(comp, trans_team):

    """ retourneert een lijst van team wedstrijdenklassen, elk bestaande uit een dictionary:
            'beschrijving': tekst
            'count':        aantal teams ingedeeld in deze klasse
            'ag':           het Team-AG van de laatste team in deze klasse
                            of 0.001 voor de laatste klasse voor klasse onbekend
            'ag_str':       geformatteerd Team-AG als NNN.M
            'wedstrkl_obj': team klasse
            'klasse':       competitieklasse
            'volgorde':     nummer

        gesorteerd op volgorde (oplopend)
    """

    # per boogtype (dus elke schutter-boog in zijn eigen team type):
    #   per vereniging:
    #      - de schutters sorteren op AG
    #      - per groepje van 4 som van beste 3 = team AG

    if comp.afstand == '18':
        aantal_pijlen = 30
    else:
        aantal_pijlen = 25

    # eenmalig de wedstrijdleeftijd van elke nhblid berekenen in het vorige seizoen
    # hiermee kunnen we de aspiranten scores eruit filteren
    jaar = comp.begin_jaar      # gelijk aan tweede jaar vorig seizoen

    # zoek een ongeveer datum zodat we 80% van de leden niet hoeven te analyseren
    jaar_nu = timezone.now().year
    geboren_na = datetime.date(year=jaar_nu - MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT - 1, month=1, day=1)

    was_aspirant = dict()     # [ lid_nr ] = True/False
    for sporter in Sporter.objects.filter(geboorte_datum__gte=geboren_na):
        was_aspirant[sporter.lid_nr] = sporter.bereken_wedstrijdleeftijd(jaar) <= MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT
    # for

    # haal de AG's op per boogtype
    boogtype2ags = dict()        # [boogtype.afkorting] = AG's
    for boogtype in BoogType.objects.all():
        boogtype2ags[boogtype.afkorting] = (Score
                                            .objects
                                            .select_related('sporterboog',
                                                            'sporterboog__boogtype',
                                                            'sporterboog__sporter',
                                                            'sporterboog__sporter__bij_vereniging')
                                            .exclude(sporterboog__sporter__bij_vereniging=None)
                                            .filter(type=SCORE_TYPE_INDIV_AG,
                                                    afstand_meter=comp.afstand,
                                                    sporterboog__boogtype=boogtype))
    # for

    # wedstrijdklassen vs leeftijd + bogen
    targets = _get_targets_teams()

    # bepaal de mogelijk te vormen teams en de team score
    boog2team_scores = dict()    # [boogtype afkorting] = list(team scores)
    for boogtype_afkorting, klassen in targets.items():
        boog2team_scores[boogtype_afkorting] = team_scores = list()

        # zoek alle schutters-boog die hier in passen (boog, leeftijd)
        per_ver_gemiddelden = dict()    # [ver_nr] = list(gemiddelde, gemiddelde, ...)
        for score in boogtype2ags[boogtype_afkorting]:
            try:
                lid_was_aspirant = was_aspirant[score.sporterboog.sporter.lid_nr]
            except KeyError:
                lid_was_aspirant = False

            if not lid_was_aspirant:
                ver_nr = score.sporterboog.sporter.bij_vereniging.ver_nr
                try:
                    per_ver_gemiddelden[ver_nr].append(score.waarde)        # is AG*1000
                except KeyError:
                    per_ver_gemiddelden[ver_nr] = [score.waarde]
        # for

        for ver_nr, gemiddelden in per_ver_gemiddelden.items():
            gemiddelden.sort(reverse=True)  # in-place sort, highest to lowest
            aantal = len(gemiddelden)
            teams = int(aantal / 4)
            for team_nr in range(teams):
                index = team_nr * 4
                team_score = sum(gemiddelden[index:index+3])    # totaal van beste 3 scores
                team_score = team_score / 1000          # converteer terug van score.waarde = AG*1000
                team_score = round(team_score, 3)       # round here, instead of letter database do it
                team_scores.append(team_score)
            # for
        # for
    # for

    objs = list()
    for boogtype_afkorting, klassen in targets.items():
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
                       'wedstrkl_obj': klasse,
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
               'wedstrkl_obj': klasse,
               'volgorde': klasse.volgorde}     # voor sorteren
        objs.append(res)
    # for

    for obj in objs:
        obj['klasse'] = trans_team[obj['wedstrkl_obj'].pk]
    # for

    objs2 = sorted(objs, key=lambda k: k['volgorde'])
    return objs2


def get_mappings_wedstrijdklasse_to_competitieklasse(comp):
    """ geeft een look-up tabel terug van IndivWedstrijdklasse / TeamWedstrijdklasse naar CompetitieKlasse """
    trans_indiv = dict()
    trans_team = dict()

    for klasse in (CompetitieKlasse
                   .objects
                   .filter(competitie=comp)
                   .prefetch_related('indiv', 'team')):
        if klasse.indiv:
            trans_indiv[klasse.indiv.pk] = klasse
        else:
            trans_team[klasse.team.pk] = klasse
    # for

    return trans_indiv, trans_team


class KlasseBepaler(object):
    """ deze klasse helpt met het bepalen van de CompetitieKlasse voor een deelnemer """

    def __init__(self, competitie):
        self.competitie = competitie
        self.boogtype2klassen = dict()      # [boogtype.afkorting] = [CompetitieKlasse, CompetitieKlasse, ..]
        self.lkl_cache_mannen = dict()      # [CompetitieKlasse.pk] = [lkl, lkl, ...]
        self.lkl_cache_vrouwen = dict()     # [CompetitieKlasse.pk] = [lkl, lkl, ...]
        self.lkl_cache = {'M': self.lkl_cache_mannen,
                          'V': self.lkl_cache_vrouwen}

        # vul de caches
        for klasse in (CompetitieKlasse
                       .objects
                       .filter(competitie=competitie)
                       .exclude(indiv=None)
                       .prefetch_related('indiv__leeftijdsklassen')
                       .select_related('indiv',
                                       'indiv__boogtype')
                       .all()):

            indiv = klasse.indiv
            boog_afkorting = indiv.boogtype.afkorting
            try:
                self.boogtype2klassen[boog_afkorting].append(klasse)
            except KeyError:
                self.boogtype2klassen[boog_afkorting] = [klasse]

            for lkl in indiv.leeftijdsklassen.all():
                lkl_cache = self.lkl_cache[lkl.geslacht]
                try:
                    lkl_cache[klasse.pk].append(lkl)
                except KeyError:
                    lkl_cache[klasse.pk] = [lkl]
            # for
        # for

    def bepaal_klasse_deelnemer(self, deelnemer):
        """ deze functie zet deelnemer.klasse aan de hand van de sporterboog """

        ag = deelnemer.ag_voor_indiv
        sporterboog = deelnemer.sporterboog
        sporter = sporterboog.sporter
        age = sporter.bereken_wedstrijdleeftijd(self.competitie.begin_jaar + 1)

        if not isinstance(ag, Decimal):
            raise LookupError('Verkeerde type')

        # voorkom problemen in de >= vergelijking verderop door afrondingsfouten
        # door conversie naar Decimal, want Decimal(7,42) = 7,4199999999
        ag += Decimal(0.00005)

        mogelijkheden = list()
        for klasse in self.boogtype2klassen[sporterboog.boogtype.afkorting]:
            if ag >= klasse.min_ag or klasse.indiv.is_onbekend:
                for lkl in self.lkl_cache[sporter.geslacht][klasse.pk]:
                    if lkl.leeftijd_is_compatible(age):
                        tup = (lkl.volgorde, klasse.pk, lkl, klasse)
                        mogelijkheden.append(tup)
                # for
        # for

        mogelijkheden.sort(reverse=True)

        # de sort op lkl.volgorde heeft senioren eerst gezet; aspiranten laatste
        # aspiranten mogen in alle klassen meedoen, maar we kiezen uiteindelijk de Asp klasse
        if len(mogelijkheden):
            _, _, _, klasse = mogelijkheden[-1]
            deelnemer.klasse = klasse
        else:
            # niet vast kunnen stellen
            # deelnemer.klasse = None       # werkt niet, want ForeignKey kan je niet testen op None (geen DoesNotExist exceptie)
            raise LookupError("Geen passende wedstrijdklasse")


def competitie_klassegrenzen_vaststellen(comp):
    """ stel voor een specifieke Competitie alle klassegrenzen vast """

    trans_indiv, trans_team = get_mappings_wedstrijdklasse_to_competitieklasse(comp)

    # individueel
    for obj in bepaal_klassegrenzen_indiv(comp, trans_indiv):
        klasse = obj['klasse']
        klasse.min_ag = obj['ag']
        klasse.save(update_fields=['min_ag'])
    # for

    # team
    for obj in bepaal_klassegrenzen_teams(comp, trans_team):
        klasse = obj['klasse']
        klasse.min_ag = obj['ag']
        klasse.save(update_fields=['min_ag'])
    # for

    comp.klassegrenzen_vastgesteld = True
    comp.save(update_fields=['klassegrenzen_vastgesteld'])


# end of file
