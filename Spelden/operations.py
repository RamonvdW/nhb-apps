# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Spelden.definities import (SPELD_DISCIPLINE_OUTDOOR, SPELD_DISCIPLINE_INDOOR, SPELD_DISCIPLINE_VELD,
                                SPELD_DISCIPLINE_NVT,
                                SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR, SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR,
                                SPELD_CATEGORIE_NL_GRAADSPELD_VELD, SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC,
                                SPELD_CATEGORIE_NL_GRAADSPELD_ALGEMEEN)
from Spelden.models import Speld, SpeldVoorwaarden, SpeldToegekend
from Sporter.leeftijdsklassen import bereken_leeftijdsklassen_wa, hogere_en_lagere_lkl_wa
from Wedstrijden.definities import (WEDSTRIJD_DISCIPLINE_OUTDOOR, WEDSTRIJD_DISCIPLINE_INDOOR,
                                    WEDSTRIJD_DISCIPLINE_25M1P, WEDSTRIJD_DISCIPLINE_VELD)


def get_hall_of_fame():
    """ Geef de SpeldToegekend queries terug van de sporters met pascodes GM, MS, AS,
        elk gesorteerd op datum (oudste eerst) en lidnummer.
        Sporters die niet meer actief lid zijn van een vereniging worden eruit gefilterd.
    """

    qset = (SpeldToegekend
            .objects
            .select_related('sporter',
                            'sporter__bij_vereniging')
            .exclude(sporter__bij_vereniging=None)
            .exclude(sporter__bij_vereniging__ver_nr__in=settings.CRM_IMPORT_GEEN_WEDSTRIJDEN)
            .order_by('datum',               # oudste eerst
                      'sporter__lid_nr'))

    leden_gm = qset.filter(speld__pas_code='GM')
    lid_nrs = list(leden_gm.values_list('sporter__lid_nr', flat=True))

    leden_ms = qset.filter(speld__pas_code='MS').exclude(sporter__lid_nr__in=lid_nrs)

    leden_as = qset.filter(speld__pas_code='AS')

    return leden_gm, leden_ms, leden_as


def tel_hall_of_fame():
    """ Geeft het aantal sporters terug dat GM, MS of AS is """

    leden_gm, leden_ms, leden_as = get_hall_of_fame()

    gm_count = leden_gm.count()
    ms_count = leden_ms.count()
    as_count = leden_as.count()

    return gm_count, ms_count, as_count


def speld_discipline2wedstrijd_discplines(speld_discipline: str):
    """ maak een Wedstrijden discpline filter aan de hand van de gekozen discipline voor de spelden """

    if speld_discipline == SPELD_DISCIPLINE_OUTDOOR:
        wed_disciplines = (WEDSTRIJD_DISCIPLINE_OUTDOOR,)

    elif speld_discipline == SPELD_DISCIPLINE_INDOOR:
        wed_disciplines = (WEDSTRIJD_DISCIPLINE_INDOOR, WEDSTRIJD_DISCIPLINE_25M1P)

    elif speld_discipline == SPELD_DISCIPLINE_VELD:
        wed_disciplines = (WEDSTRIJD_DISCIPLINE_VELD,)

    else:
        wed_disciplines = ()

    return wed_disciplines


def get_mogelijke_spelden_wa(discipline: str, boog: str, score: int,
                             wedstrijd_geslacht: str, geboorte_jaar: int) -> list[SpeldVoorwaarden]:

    """ Bepaalt de mogelijke spelden aan de hand van ingevoerde informatie

        discipline:         uit SPELD_DISCIPLINE_CHOICES: 'OD', 'IN', '25', 'VE'
        boog:               uit SPELD_BOOGTYPE_CHOICES:   'R', 'C', 'BB'
        score:              de behaalde score
        wedstrijd_geslacht: uit GESLACHT_MV: 'M' of 'V'
        geboorte_jaar:      geboortejaar van de sporter (1980, etc.)

        returns:    list of SpeldVoorwaarden
    """

    # print('{get_mogelijke_spelden} discpline=%s, boog=%s, score=%s, wedstrijd_geslacht=%s' % (
    #               repr(discipline), repr(boog), score, repr(wedstrijd_geslacht)))

    qset = (SpeldVoorwaarden
            .objects
            .filter(discipline=discipline,
                    boog_type__afkorting=boog,
                    leeftijdsklasse__wedstrijd_geslacht=wedstrijd_geslacht)
            .select_related('speld',
                            'boog_type',
                            'leeftijdsklasse'))

    if discipline == WEDSTRIJD_DISCIPLINE_VELD:
        # alleen dames/heren opsplitsing, geen verdere leeftijdsklasse
        pass
    else:
        # bereken het minimale aantal pijlen dat geschoten moet zijn om deze score te halen
        # verwijder afstanden waarop minder pijlen geschoten worden
        aantal_pijlen_geschoten = int(score / 10)
        if score > aantal_pijlen_geschoten * 10:
            aantal_pijlen_geschoten += 1
        # print('{get_mogelijke_spelden} score=%s --> aantal_pijlen=%s' % (score, aantal_pijlen_geschoten))
        qset = qset.exclude(aantal_pijlen__lt=aantal_pijlen_geschoten)
        qset = qset.exclude(aantal_pijlen__gt=(aantal_pijlen_geschoten-1) * 2)   # filtert 1440 bij lage score

        now = timezone.now()
        _, _, _, lkl_lst = bereken_leeftijdsklassen_wa(geboorte_jaar, wedstrijd_geslacht, now.year, lst_als_str=False)
        mogelijke_lkl = lkl_lst[0:0+2]      # vorige jaar en dit jaar

        if mogelijke_lkl[0] != mogelijke_lkl[1] and now.month <= 6:
            # tijdens de eerste 6 maanden na overgang naar een andere wedstrijdklasse, ook de vorige klasse laten gebruiken
            # beide behouden, in die specifieke volgorde
            pass
        else:
            # alleen de nieuwste behouden
            mogelijke_lkl = mogelijke_lkl[-1:]

        # print('{mogelijke_lkl}', mogelijke_lkl)
        alle_lkl = list()
        for lkl in mogelijke_lkl:
            alle_lkl.extend(hogere_en_lagere_lkl_wa(lkl))
        # for

        # print('{alle_lkl}', alle_lkl)
        qset = qset.filter(leeftijdsklasse__in=alle_lkl)

    return list(qset)


def get_mogelijke_graadspelden_khsn(discipline: str, afstanden: str, aantal_doelen: int, aantal_pijlen: int, wedstrijdgeslacht: str, score: int, score_sm: int) -> list[SpeldVoorwaarden]:
    # print('{get_mogelijke_graadspelden_khsn} discipline=%s, afstanden=%s, aantal doelen=%s, aantal_pijlen=%s, m/v=%s, score=%s' % (
    #           discipline, afstanden, aantal_doelen, aantal_pijlen, wedstrijdgeslacht, score))

    lkl = 'SH'
    if wedstrijdgeslacht != 'M':
        lkl = 'SV'

    opties = list()

    if discipline == SPELD_DISCIPLINE_OUTDOOR:
        qset = (SpeldVoorwaarden
                .objects
                .filter(discipline=SPELD_DISCIPLINE_NVT,
                        wedstrijd_soort='Outdoor',
                        leeftijdsklasse__afkorting=lkl,
                        speld__categorie=SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR)
                .select_related('speld')
                .order_by('speld__volgorde'))
        opties.extend(list(qset))

        # short metric
        if score_sm > 0:
            qset = (SpeldVoorwaarden
                    .objects
                    .filter(discipline=SPELD_DISCIPLINE_NVT,
                            wedstrijd_soort='Short Metric',
                            leeftijdsklasse__afkorting=lkl,
                            speld__categorie=SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC)
                    .select_related('speld')
                    .order_by('speld__volgorde'))
            opties.extend(list(qset))

    if discipline == SPELD_DISCIPLINE_VELD and aantal_doelen == 24:
        qset = (SpeldVoorwaarden
                .objects
                .filter(discipline=SPELD_DISCIPLINE_NVT,
                        wedstrijd_soort='Veld',
                        leeftijdsklasse__afkorting=lkl,
                        speld__categorie=SPELD_CATEGORIE_NL_GRAADSPELD_VELD)
                .select_related('speld')
                .order_by('speld__volgorde'))
        opties.extend(list(qset))

    if discipline == SPELD_DISCIPLINE_INDOOR and afstanden == '18' and aantal_pijlen == 60:
        qset = (SpeldVoorwaarden
                .objects
                .filter(discipline=SPELD_DISCIPLINE_NVT,
                        wedstrijd_soort='Indoor',
                        leeftijdsklasse__afkorting=lkl,
                        speld__categorie=SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR)
                .select_related('speld')
                .order_by('speld__volgorde'))
        opties.extend(list(qset))

    return opties


def get_mogelijke_meesterspelden_khsn(heeft_spelden: list[Speld], nieuw_behaald: list[Speld]) -> list[SpeldVoorwaarden]:
    # print('{get_mogelijke_meesterspelden_khsn} heeft_spelden=%s, nieuw_behaald=%s' % (heeft_spelden, nieuw_behaald))

    nr2speld = dict()
    for speld in Speld.objects.filter(volgorde__in=(5401, 5402, 5403)):
        nr2speld[speld.volgorde] = speld
    # for

    nrs = [speld.volgorde
           for speld in heeft_spelden + nieuw_behaald]

    # nrs:
    # 5001, 5002, 5003 = 1e/2e/3e graad Indoor
    # 5103, 5102, 5101 = 1e/2e/3e graad Outdoor
    # 5203, 5202, 5201 = 1e/2e/3e graad Veld
    # 5303, 5302, 5301 = 1e/2e/3e graad Short Metric

    opties = list()

    # 5401 = Allround schutter:    3e graad in 4 disciplines
    allround = 0
    for nr in (5003, 5101, 5201, 5301):
        if nr in nrs:
            allround += 1
    # for

    optie = SpeldVoorwaarden(
                speld=nr2speld[5401],
                wedstrijd_soort='',
                benodigde_score='4x 3e graad')
    optie.mag_besteld_worden = (allround == 4)
    optie.heeft_aantal = allround
    optie.heeft_nodig = 4
    optie.graadspeld_soort = '3e graad'
    opties.append(optie)

    # 5402 = Meesterschutter:      2e graad in 3 disciplines
    meester = 0
    for nr in (5002, 5102, 5202, 5302):
        if nr in nrs:
            meester += 1
    # for

    optie = SpeldVoorwaarden(
                speld=nr2speld[5402],
                wedstrijd_soort='',
                benodigde_score='3x 2e graad')
    optie.mag_besteld_worden = (meester >= 3)
    optie.heeft_aantal = meester
    optie.heeft_nodig = 3
    optie.graadspeld_soort = '2e graad'
    opties.append(optie)

    # 5403 = Grootmeesterschutter: 1e graad in 3 disciplines
    groot = 0
    for nr in (5001, 5103, 5203, 5303):
        if nr in nrs:
            groot += 1
    # for

    optie = SpeldVoorwaarden(
                speld=nr2speld[5403],
                wedstrijd_soort='',
                benodigde_score='3x 1e graad')
    optie.mag_besteld_worden = (groot >= 3)
    optie.heeft_aantal = groot
    optie.heeft_nodig = 3
    optie.graadspeld_soort = '1e graad'
    opties.append(optie)

    return opties


# end of file
