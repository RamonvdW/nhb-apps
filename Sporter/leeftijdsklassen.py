# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" ondersteuning voor de leeftijdsklassen binnen de applicatie """

from BasisTypen.definities import (GESLACHT_ALLE, GESLACHT_ANDERS, GESLACHT_MAN,
                                   ORGANISATIE_IFAA, ORGANISATIE_KHSN, ORGANISATIE_WA,
                                   BOOGTYPE_AFKORTING_RECURVE)
from BasisTypen.models import Leeftijdsklasse, TemplateCompetitieIndivKlasse


def bereken_leeftijdsklassen_khsn(geboorte_jaar, wedstrijdgeslacht_khsn, huidige_jaar):
    """ retourneert de wedstrijdklassen voor een sporter vanaf 1 jaar terug tot 4 jaar vooruit.
        wedstrijdgeslacht_khsn kan zijn GESLACHT_MAN, GESLACHT_VROUW of GESLACHT_ANDERS

        Retourneert:
            Huidige jaar, Leeftijd, False, None, None als het geen jonge schutter betreft
            Huidige jaar, Leeftijd, True, wlst, clst voor jonge schutters
                wlst en clst zijn een lijst van wedstrijdklassen voor
                de jaren -1, 0, +1, +2, +3 ten opzicht van Leeftijd
                Voorbeeld:
                    huidige jaar = 2019
                    leeftijd = 17
                    lkl_lst=(('Onder 18 Gemengd of Onder 18 Heren'),     # -1 = 16
                             ('Onder 18 Gemengd of Onder 18 Heren'),     #  0 = 17
                             ('Onder 21 Gemengd of Onder 21 Heren'),     # +1 = 18
                             ('Onder 21 Gemengd of Onder 21 Heren'),     # +2 = 19
                             ('Onder 21 Gemengd of Onder 21 Heren'))     # +3 = 20
    """

    leeftijd2tekst = dict()     # [leeftijd] = beschrijving

    # begin met de Gemengd klassen
    if True:
        alle_lkl = list()
        prev_lkl = None
        min_wedstrijdleeftijd = 0
        for lkl in (Leeftijdsklasse
                    .objects
                    .filter(organisatie__in=(ORGANISATIE_WA, ORGANISATIE_KHSN),
                            wedstrijd_geslacht=GESLACHT_ALLE)
                    .order_by('volgorde')):

            if lkl.min_wedstrijdleeftijd == 0:
                # sluit aan op vorige (jongere) klasse
                lkl.min_wedstrijdleeftijd = min_wedstrijdleeftijd

            if prev_lkl and prev_lkl.max_wedstrijdleeftijd == 0:
                # sluit vorige (jongere) klasse aan op deze
                prev_lkl.max_wedstrijdleeftijd = lkl.min_wedstrijdleeftijd - 1

            # volgende leeftijdsklasse gaat verder waar deze ophoudt
            min_wedstrijdleeftijd = lkl.max_wedstrijdleeftijd + 1
            alle_lkl.append(lkl)
            prev_lkl = lkl
        # for
        prev_lkl.max_wedstrijdleeftijd = 150

        # maak de look-up tabel
        for lkl in alle_lkl:
            for leeftijd in range(lkl.min_wedstrijdleeftijd, lkl.max_wedstrijdleeftijd+1):
                leeftijd2tekst[leeftijd] = lkl.beschrijving     # 21+ Gemengd
            # for
        # for

    # nu uitbreiden met een specifiek geslacht, indien gekozen
    if wedstrijdgeslacht_khsn != GESLACHT_ANDERS:
        # haal alle leeftijdsklassen op en vul de min/max leeftijden aan
        alle_lkl = list()
        prev_lkl = None
        min_wedstrijdleeftijd = 0
        for lkl in (Leeftijdsklasse
                    .objects
                    .filter(organisatie__in=(ORGANISATIE_WA, ORGANISATIE_KHSN),
                            wedstrijd_geslacht__in=wedstrijdgeslacht_khsn)
                    .order_by('volgorde')):

            if lkl.min_wedstrijdleeftijd == 0:
                lkl.min_wedstrijdleeftijd = min_wedstrijdleeftijd

            if prev_lkl and prev_lkl.max_wedstrijdleeftijd == 0:
                prev_lkl.max_wedstrijdleeftijd = lkl.min_wedstrijdleeftijd - 1

            # volgende leeftijdsklasse gaat verder waar deze ophoudt
            min_wedstrijdleeftijd = lkl.max_wedstrijdleeftijd + 1
            alle_lkl.append(lkl)
            prev_lkl = lkl
        # for
        prev_lkl.max_wedstrijdleeftijd = 150

        # de look-up tabel uitbreiden met een tweede beschrijving
        # 21+ Gemengd --> 21+ Gemengd of 21+ Heren
        for lkl in alle_lkl:
            for leeftijd in range(lkl.min_wedstrijdleeftijd, lkl.max_wedstrijdleeftijd+1):
                leeftijd2tekst[leeftijd] += ' of ' + lkl.beschrijving
            # for
        # for

    wedstrijdleeftijd = huidige_jaar - geboorte_jaar

    # bereken de wedstrijdklassen en competitieklassen
    lkl_lst = list()
    lkl_dit_jaar = '?'
    for n in (-1, 0, 1, 2, 3):
        tekst = leeftijd2tekst[wedstrijdleeftijd + n]
        lkl_lst.append(tekst)
        if n == 0:
            lkl_dit_jaar = tekst
    # for

    return huidige_jaar, wedstrijdleeftijd, lkl_dit_jaar, lkl_lst


def bereken_leeftijdsklassen_bondscompetitie(geboorte_jaar, wedstrijdgeslacht_khsn, huidige_jaar, huidige_maand):
    """ retourneert de wedstrijdklassen voor een sporter vanaf 1 jaar terug tot 4 jaar vooruit
        voor de bondscompetities van de KHSN.
        wedstrijdgeslacht_khsn kan zijn GESLACHT_MAN, GESLACHT_VROUW of GESLACHT_ANDERS

        Retourneert:
                wedstrijdleeftijd, lkl_lst
                lkl_lst is een lijst van wedstrijdklassen voor de seizoenen -1, 0, +1, +2, +3
                    ten opzicht van huidige seizoen
                Voorbeeld:
                    leeftijd = 14
                    lkl_lst=({seizoen:'2018/2019', tekst:'Onder 14 Jongens'},      # 0 = 13
                             {seizoen:'2019/2020', tekst:'Onder 14 Jongens'),      # 1 = 14  huidige seizoen
                             {seizoen:'2020/2021', tekst:'Onder 18'),              # 2 = 15
                             {seizoen:'2021/2022', tekst:'Onder 18'),              # 3 = 16
                             {seizoen:'2022/2023', tekst:'Onder 18'))              # 4 = 27
    """

    # bondscompetitie heeft gender-neutrale klassen, behalve voor Onder 12 en Onder 14
    # de meeste sporters met geslacht 'anders' zullen dus in een gender-neutrale klasse komen
    # een jonge sporter met geslacht 'anders' die nog geen wedstrijdgeslacht gekozen heeft,
    # die moeten we dus forceren in een van de klasse.
    if wedstrijdgeslacht_khsn == GESLACHT_ANDERS:
        wedstrijdgeslacht_khsn = GESLACHT_MAN

    leeftijd2tekst_w = dict()  # [leeftijd] = beschrijving voor wedstrijdgeslacht
    leeftijd2tekst_g = dict()  # [leeftijd] = beschrijving voor gender-neutraal

    lkl_pks = list()
    for ckl in (TemplateCompetitieIndivKlasse
                .objects
                .prefetch_related('leeftijdsklassen')
                .filter(gebruik_18m=True,
                        boogtype__afkorting=BOOGTYPE_AFKORTING_RECURVE)):
        for lkl in ckl.leeftijdsklassen.all():
            pk = lkl.pk
            if pk not in lkl_pks:
                lkl_pks.append(pk)
        # for
    # for

    alle_lkl = list()
    min_wedstrijdleeftijd = 0
    for lkl in (Leeftijdsklasse
                .objects
                .filter(pk__in=lkl_pks,
                        wedstrijd_geslacht__in=(wedstrijdgeslacht_khsn, GESLACHT_ALLE))
                .order_by('volgorde')):        # jongste sporters eerst

        lkl.min_wedstrijdleeftijd = min_wedstrijdleeftijd

        # volgende leeftijdsklasse gaat verder waar deze ophoudt
        min_wedstrijdleeftijd = lkl.max_wedstrijdleeftijd + 1
        alle_lkl.append(lkl)
    # for
    alle_lkl[-1].max_wedstrijdleeftijd = 150

    # maak de look-up tabel
    for lkl in alle_lkl:
        if lkl.wedstrijd_geslacht == GESLACHT_ALLE:
            target = leeftijd2tekst_g
        else:
            target = leeftijd2tekst_w

        for leeftijd in range(lkl.min_wedstrijdleeftijd, lkl.max_wedstrijdleeftijd + 1):
            target[leeftijd] = lkl.beschrijving.replace(' Gemengd', '')
        # for
    # for

    eerste_jaar = huidige_jaar
    if huidige_maand <= 6:
        # toon voor seizoen vorig-jaar/dit-jaar
        eerste_jaar -= 1
    else:
        # toon voor seizoen dit-jaar/volgend-jaar
        pass

    wedstrijdleeftijd = eerste_jaar - geboorte_jaar
    wedstrijdleeftijd += 1      # neem 2e jaar van de competitie

    # bereken de wedstrijdklassen en competitieklassen
    lkl_lst = list()
    for n in (-1, 0, 1, 2, 3):
        seizoen = '%s/%s' % (eerste_jaar+n, eerste_jaar+n+1)

        try:
            tekst = leeftijd2tekst_w[wedstrijdleeftijd + n]
        except KeyError:
            tekst = leeftijd2tekst_g[wedstrijdleeftijd + n]

        lkl = {'seizoen': seizoen, 'tekst': tekst}
        lkl_lst.append(lkl)
    # for

    # print(lkl_lst)

    return wedstrijdleeftijd, lkl_lst


def bereken_leeftijdsklassen_wa(geboorte_jaar, wedstrijdgeslacht, huidige_jaar):
    """ retourneert de wedstrijdklassen voor een sporter vanaf 1 jaar terug tot 4 jaar vooruit.
        wedstrijdgeslacht moet zijn GESLACHT_MAN of GESLACHT_VROUW

        Retourneert: huidige jaar, leeftijd, lkl_dit_jaar, lkl_lst
                lkl_lst is een lijst van wedstrijdklassen voor
                de jaren -1, 0, +1, +2, +3 ten opzicht van Leeftijd
                Voorbeeld:
                    huidige jaar = 2019
                    leeftijd = 20
                    lkl_dit_jaar = '21+ Mannen'
                    lkl_lst=('Onder 21 Mannen', '21+ Mannen', '21+ Mannen', '21+ Mannen', '21+ Mannen')
    """

    sporter_leeftijd = huidige_jaar - geboorte_jaar

    # haal alle leeftijdsklassen op en vul de min/max leeftijden aan
    alle_lkl = list()
    prev_lkl = None
    min_wedstrijdleeftijd = 0
    for lkl in (Leeftijdsklasse
                .objects
                .filter(organisatie=ORGANISATIE_WA,
                        wedstrijd_geslacht=wedstrijdgeslacht)
                .order_by('volgorde')):

        if lkl.min_wedstrijdleeftijd == 0:
            lkl.min_wedstrijdleeftijd = min_wedstrijdleeftijd

        if prev_lkl and prev_lkl.max_wedstrijdleeftijd == 0:
            prev_lkl.max_wedstrijdleeftijd = lkl.min_wedstrijdleeftijd - 1

        # volgende leeftijdsklasse gaat verder waar deze ophoudt
        min_wedstrijdleeftijd = lkl.max_wedstrijdleeftijd + 1
        alle_lkl.append(lkl)
        prev_lkl = lkl
    # for

    if not prev_lkl:
        # geen klassen gevonden
        return huidige_jaar, sporter_leeftijd, None, list()

    prev_lkl.max_wedstrijdleeftijd = 150

    # maak de look-up tabel met alle leeftijden
    leeftijd2tekst = dict()
    for lkl in alle_lkl:
        for leeftijd in range(lkl.min_wedstrijdleeftijd, lkl.max_wedstrijdleeftijd+1):
            leeftijd2tekst[leeftijd] = lkl.beschrijving
        # for
    # for

    # bereken de wedstrijdklassen en competitieklassen
    lkl_list = list()
    lkl_dit_jaar = ''
    for n in (-1, 0, 1, 2, 3):
        lang = leeftijd2tekst[sporter_leeftijd + n]
        lkl_list.append(lang)
        if n == 0:
            lkl_dit_jaar = lang
    # for

    return huidige_jaar, sporter_leeftijd, lkl_dit_jaar, lkl_list


def bereken_leeftijdsklassen_ifaa(geboorte_jaar, wedstrijdgeslacht, huidige_jaar):
    """
        wedstrijdgeslacht moet zijn GESLACHT_MAN of GESLACHT_VROUW

        geeft een lijst terug met het jaartal en twee wedstrijdklassen voor IFAA wedstrijden
        de eerste wedstrijdklasse is geldig tot de verjaardag van de sporter, de tweede erna
        de lijst bevat 5 entries, voor de jaren -1, 0, +1, +2, +3 ten opzicht van het huidige jaartal
    """

    # haal alle leeftijdsklassen op en vul de min/max leeftijden aan
    alle_lkl = (Leeftijdsklasse
                .objects
                .filter(organisatie=ORGANISATIE_IFAA,
                        wedstrijd_geslacht=wedstrijdgeslacht)
                .order_by('volgorde'))
    prev_lkl = None
    min_wedstrijdleeftijd = 0
    for lkl in alle_lkl:
        if lkl.min_wedstrijdleeftijd == 0:
            lkl.min_wedstrijdleeftijd = min_wedstrijdleeftijd

        if prev_lkl and prev_lkl.max_wedstrijdleeftijd == 0:
            prev_lkl.max_wedstrijdleeftijd = lkl.min_wedstrijdleeftijd - 1

        # volgende leeftijdsklasse gaat verder waar deze ophoudt
        min_wedstrijdleeftijd = lkl.max_wedstrijdleeftijd + 1
        prev_lkl = lkl
    # for
    prev_lkl.max_wedstrijdleeftijd = 150

    # zet om in look-up tabel
    leeftijd2tekst = dict()
    for lkl in alle_lkl:
        for leeftijd in range(lkl.min_wedstrijdleeftijd, lkl.max_wedstrijdleeftijd+1):
            leeftijd2tekst[leeftijd] = lkl.beschrijving
        # for
    # for

    leeftijd = huidige_jaar - geboorte_jaar

    lst = list()
    for n in (-1, 0, 1, 2, 3):
        wleeftijd2 = leeftijd + n
        wleeftijd1 = wleeftijd2 - 1

        tup = (huidige_jaar + n, leeftijd2tekst[wleeftijd1], leeftijd2tekst[wleeftijd2])
        lst.append(tup)
    # for

    return lst


def bereken_leeftijdsklasse_wa(wedstrijdleeftijd, wedstrijdgeslacht):
    """
        bepaal de meest exacte WA leeftijdsklasse voor een sporter
        afhankelijk van zijn geboortejaar en wedstrijdgeslacht.

        Voorbeeld: Onder 12 meisjes
                   Onder 18 jongens
    """

    fallback_lkl = None
    gevonden_lkl = None

    # selecteer een geslacht-specifieke wedstrijdklasse
    for lkl in (Leeftijdsklasse
                .objects
                .filter(organisatie=ORGANISATIE_WA,
                        wedstrijd_geslacht=wedstrijdgeslacht)
                .order_by('volgorde')):                              # pragma: no branch

        # check leeftijd is compatible
        if lkl.leeftijd_is_compatible(wedstrijdleeftijd):
            if lkl.min_wedstrijdleeftijd == lkl.max_wedstrijdleeftijd == 0:
                fallback_lkl = lkl
            else:
                gevonden_lkl = lkl
                break
    # for

    if not gevonden_lkl:
        gevonden_lkl = fallback_lkl

    if not gevonden_lkl:
        return "?"

    return gevonden_lkl.beschrijving


def bereken_leeftijdsklasse_ifaa(wedstrijdleeftijd, wedstrijdgeslacht):
    """
        bepaal de meest exacte IFAA leeftijdsklasse voor een sporter
        afhankelijk van zijn wedstrijdleeftijd en wedstrijdgeslacht.

        Voorbeeld: Senioren vrouwen
    """

    gevonden_lkl = None

    # print('bereken_leeftijdsklasse_ifaa: wedstrijdleeftijd=%s, wedstrijdgeslacht=%s' % (
    #           wedstrijdleeftijd, wedstrijdgeslacht))

    # selecteer een geslacht-specifieke wedstrijdklasse
    prev_lkl = None
    for lkl in (Leeftijdsklasse
                .objects
                .filter(organisatie=ORGANISATIE_IFAA,
                        wedstrijd_geslacht=wedstrijdgeslacht)
                .order_by('volgorde')):

        # voorkom dat de jongste sporters ook in een hogere klasse passen
        if prev_lkl and lkl.min_wedstrijdleeftijd == 0:
            lkl.min_wedstrijdleeftijd = prev_lkl.max_wedstrijdleeftijd + 1

        # check leeftijd is compatible
        if lkl.leeftijd_is_compatible(wedstrijdleeftijd):
            gevonden_lkl = lkl
            # blijf doorzoeken voor de oudere sporters

        prev_lkl = lkl
    # for

    if not gevonden_lkl:
        return "?"

    return gevonden_lkl.beschrijving


def bereken_leeftijdsklasse_khsn(wedstrijdleeftijd, wedstrijdgeslacht):
    """
        bepaal de meest exacte KHSN leeftijdsklasse voor een sporter
        afhankelijk van zijn geboortejaar en wedstrijdgeslacht.

        Voorbeeld: Onder 12 Meisjes
                   Onder 18 Heren
    """

    gevonden_lkl = None

    # eerste poging: selecteer een geslacht-specifieke wedstrijdklasse
    prev_lkl = None
    for lkl in (Leeftijdsklasse
                .objects
                .filter(organisatie__in=(ORGANISATIE_WA, ORGANISATIE_KHSN),
                        wedstrijd_geslacht=wedstrijdgeslacht)
                .order_by('volgorde')):

        # voorkom dat de jongste sporters ook in een hogere klasse passen
        if prev_lkl and lkl.min_wedstrijdleeftijd == 0:
            lkl.min_wedstrijdleeftijd = prev_lkl.max_wedstrijdleeftijd + 1

        # check leeftijd is compatible
        if lkl.leeftijd_is_compatible(wedstrijdleeftijd):
            gevonden_lkl = lkl

        prev_lkl = lkl
    # for

    if not gevonden_lkl:
        # tweede poging: selecteer een gender-neutrale wedstrijdklasse
        prev_lkl = None
        for lkl in (Leeftijdsklasse
                    .objects
                    .filter(organisatie__in=(ORGANISATIE_WA, ORGANISATIE_KHSN),
                            wedstrijd_geslacht=GESLACHT_ALLE)
                    .order_by('volgorde')):

            # voorkom dat de jongste sporters ook in een hogere klasse passen
            if prev_lkl and lkl.min_wedstrijdleeftijd == 0:
                lkl.min_wedstrijdleeftijd = prev_lkl.max_wedstrijdleeftijd + 1

            # check leeftijd is compatible
            if lkl.leeftijd_is_compatible(wedstrijdleeftijd):
                gevonden_lkl = lkl

            prev_lkl = lkl
        # for

    if not gevonden_lkl:
        return "?"

    return gevonden_lkl.beschrijving


# end of file
