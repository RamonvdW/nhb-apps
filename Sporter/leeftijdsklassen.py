# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" ondersteuning voor de leeftijdsklassen binnen de NHB applicaties """

from django.utils import timezone
from BasisTypen.models import (LeeftijdsKlasse, TemplateCompetitieIndivKlasse,
                               GESLACHT_ALLE, GESLACHT_ANDERS, GESLACHT_MAN,
                               ORGANISATIE_IFAA, ORGANISATIE_NHB, ORGANISATIE_WA,
                               BOOGTYPE_AFKORTING_RECURVE)


def alle_wedstrijdleeftijden_groepen_nhb():
    """ Deze functie maakt een volledige tabel met alle wedstrijdleeftijden

        Output: lijst van tuples: (min_leeftijd, max_leeftijd, leeftijdklasse, wedstrijdklasse),

        [ ( 0,  11, 'Onder 12', 'Onder 12 Meisjes'),
          (12,  13, 'Onder 14', 'Onder 14 Meisjes'),
          (14,  17, 'Onder 18', 'Onder 18 Dames'),
          (18,  20, 'Onder 21', 'Onder 21 Dames'),
          (21,  49, '21+',      '21+ Dames'),
          (50,  59, '50+',      '50+ Dames'),
          (60, 150, '60+',      '60+ Dames')
        ]
    """

    # haal alle leeftijdsklassen op en vul de min/max leeftijden aan
    alle_lkl = list()
    prev_lkl = None
    min_wedstrijdleeftijd = 0
    for lkl in (LeeftijdsKlasse
                .objects
                .filter(wedstrijd_geslacht=GESLACHT_ALLE)       # dit geeft alleen NHB klassen
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

    output = list()
    for lkl in alle_lkl:
        tup = (lkl.min_wedstrijdleeftijd, lkl.max_wedstrijdleeftijd, lkl.klasse_kort, lkl.beschrijving)
        # print('lkl: %s' % repr(tup))
        output.append(tup)
    # for

    return output


def bereken_leeftijdsklassen_nhb(geboorte_jaar, wedstrijdgeslacht_nhb):
    """ retourneert de wedstrijdklassen voor een sporter vanaf 1 jaar terug tot 4 jaar vooruit.
        wedstrijdgeslacht_nhb kan zijn GESLACHT_MAN, GESLACHT_VROUW of GESLACHT_ANDERS

        Retourneert:
            Huidige jaar, Leeftijd, False, None, None als het geen jonge schutter betreft
            Huidige jaar, Leeftijd, True, wlst, clst voor jonge schutters
                wlst en clst zijn een lijst van wedstrijdklassen voor
                de jaren -1, 0, +1, +2, +3 ten opzicht van Leeftijd
                Voorbeeld:
                    huidige jaar = 2019
                    leeftijd = 17
                    lkl_lst=(('Onder 18 Uniseks of Onder 18 Heren'),     # -1 = 16
                             ('Onder 18 Uniseks of Onder 18 Heren'),     #  0 = 17
                             ('Onder 21 Uniseks of Onder 21 Heren'),     # +1 = 18
                             ('Onder 21 Uniseks of Onder 21 Heren'),     # +2 = 19
                             ('Onder 21 Uniseks of Onder 21 Heren'))     # +3 = 20
    """

    leeftijd2tekst = dict()     # [leeftijd] = beschrijving

    # begin met de Uniseks klassen
    if True:
        alle_lkl = list()
        prev_lkl = None
        min_wedstrijdleeftijd = 0
        for lkl in (LeeftijdsKlasse
                    .objects
                    .filter(organisatie__in=(ORGANISATIE_WA, ORGANISATIE_NHB),
                            wedstrijd_geslacht=GESLACHT_ALLE)
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

        # maak de look-up tabel
        for lkl in alle_lkl:
            for leeftijd in range(lkl.min_wedstrijdleeftijd, lkl.max_wedstrijdleeftijd+1):
                leeftijd2tekst[leeftijd] = lkl.beschrijving     # 21+ Uniseks
            # for
        # for

    # nu uitbreiden met een specifiek geslacht, indien gekozen
    if wedstrijdgeslacht_nhb != GESLACHT_ANDERS:
        # haal alle leeftijdsklassen op en vul de min/max leeftijden aan
        alle_lkl = list()
        prev_lkl = None
        min_wedstrijdleeftijd = 0
        for lkl in (LeeftijdsKlasse
                    .objects
                    .filter(organisatie__in=(ORGANISATIE_WA, ORGANISATIE_NHB),
                            wedstrijd_geslacht__in=wedstrijdgeslacht_nhb)
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
        # 21+ Uniseks --> 21+ Uniseks of 21+ Heren
        for lkl in alle_lkl:
            for leeftijd in range(lkl.min_wedstrijdleeftijd, lkl.max_wedstrijdleeftijd+1):
                leeftijd2tekst[leeftijd] += ' of ' + lkl.beschrijving
            # for
        # for

    # pak het huidige jaar na conversie naar lokale tijdzone
    # zodat dit ook goed gaat in de laatste paar uren van het jaar
    now = timezone.now()  # is in UTC
    now = timezone.localtime(now)  # convert to active timezone (say Europe/Amsterdam)
    huidige_jaar = now.year
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


def bereken_leeftijdsklassen_bondscompetitie(geboorte_jaar, wedstrijdgeslacht_nhb):
    """ retourneert de wedstrijdklassen voor een sporter vanaf 1 jaar terug tot 4 jaar vooruit
        voor de bondscompetities van de NHB.
        wedstrijdgeslacht_nhb kan zijn GESLACHT_MAN, GESLACHT_VROUW of GESLACHT_ANDERS

        Retourneert:
                huidige_jaar, leeftijd, lkl_dit_jaar, lkl_lst
                lkl_lst is een lijst van wedstrijdklassen voor de jaren -1, 0, +1, +2, +3 ten opzicht van leeftijd
                Voorbeeld:
                    huidige jaar = 2019
                    leeftijd = 14
                    lkl_lst=(('Onder 14 Jongens'),      # -1 = 13
                             ('Onder 14 Jongens'),      #  0 = 14
                             ('Onder 18'),              # +1 = 15
                             ('Onder 18'),              # +2 = 16
                             ('Onder 18'))              # +3 = 27
    """

    # bondscompetitie heeft gender-neutrale klassen, behalve voor Onder 12 en Onder 14
    # de meeste sporters met geslacht 'anders' zullen dus in een gender-neutrale klasse komen
    # een jonge sporter met geslacht 'anders' die nog geen wedstrijdgeslacht gekozen heeft,
    # die moeten we dus forceren in een van de klasse.
    if wedstrijdgeslacht_nhb == GESLACHT_ANDERS:
        wedstrijdgeslacht_nhb = GESLACHT_MAN

    leeftijd2tekst_w = dict()  # [leeftijd] = beschrijving voor wedstrijdgeslacht
    leeftijd2tekst_g = dict()  # [leeftijd] = beschrijving voor gender-neutraal

    lkl_pks = list()
    for ckl in (TemplateCompetitieIndivKlasse
                .objects
                .prefetch_related('leeftijdsklassen')
                .filter(buiten_gebruik=False,
                        boogtype__afkorting=BOOGTYPE_AFKORTING_RECURVE)):
        for lkl in ckl.leeftijdsklassen.all():
            pk = lkl.pk
            if pk not in lkl_pks:
                lkl_pks.append(pk)
        # for
    # for

    alle_lkl = list()
    prev_lkl = None
    min_wedstrijdleeftijd = 0
    for lkl in (LeeftijdsKlasse
                .objects
                .filter(pk__in=lkl_pks,
                        wedstrijd_geslacht__in=(wedstrijdgeslacht_nhb, GESLACHT_ALLE))
                .order_by('volgorde')):        # jongste sporters eerst

        # print(lkl)
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

    # maak de look-up tabel
    for lkl in alle_lkl:
        if lkl.wedstrijd_geslacht == GESLACHT_ALLE:
            target = leeftijd2tekst_g
        else:
            target = leeftijd2tekst_w

        for leeftijd in range(lkl.min_wedstrijdleeftijd, lkl.max_wedstrijdleeftijd + 1):
            target[leeftijd] = lkl.beschrijving.replace(' Uniseks', '')
        # for
    # for

    # pak het huidige jaar na conversie naar lokale tijdzone
    # zodat dit ook goed gaat in de laatste paar uren van het jaar
    now = timezone.now()  # is in UTC
    now = timezone.localtime(now)  # convert to active timezone (say Europe/Amsterdam)
    huidige_jaar = now.year
    wedstrijdleeftijd = huidige_jaar - geboorte_jaar

    # bereken de wedstrijdklassen en competitieklassen
    lkl_lst = list()
    lkl_volgende_competitie = '?'
    for n in (-1, 0, 1, 2, 3):
        try:
            tekst = leeftijd2tekst_w[wedstrijdleeftijd + n]
        except KeyError:
            tekst = leeftijd2tekst_g[wedstrijdleeftijd + n]

        lkl_lst.append(tekst)
        if n == 1:
            lkl_volgende_competitie = tekst
    # for

    # print(lkl_lst)

    return huidige_jaar, wedstrijdleeftijd, lkl_volgende_competitie, lkl_lst


def bereken_leeftijdsklassen_wa(geboorte_jaar, wedstrijdgeslacht):
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

    # haal alle leeftijdsklassen op en vul de min/max leeftijden aan
    alle_lkl = list()
    prev_lkl = None
    min_wedstrijdleeftijd = 0
    for lkl in (LeeftijdsKlasse
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
    prev_lkl.max_wedstrijdleeftijd = 150

    # maak de look-up tabel met alle leeftijden
    leeftijd2tekst = dict()
    for lkl in alle_lkl:
        for leeftijd in range(lkl.min_wedstrijdleeftijd, lkl.max_wedstrijdleeftijd+1):
            leeftijd2tekst[leeftijd] = lkl.beschrijving
        # for
    # for

    # pak het huidige jaar na conversie naar lokale tijdzone
    # zodat dit ook goed gaat in de laatste paar uren van het jaar
    now = timezone.now()  # is in UTC
    now = timezone.localtime(now)  # convert to active timezone (say Europe/Amsterdam)
    huidige_jaar = now.year
    leeftijd = huidige_jaar - geboorte_jaar

    # bereken de wedstrijdklassen en competitieklassen
    lkl_list = list()
    lkl_dit_jaar = ''
    for n in (-1, 0, 1, 2, 3):
        lang = leeftijd2tekst[leeftijd + n]
        lkl_list.append(lang)
        if n == 0:
            lkl_dit_jaar = lang
    # for

    return huidige_jaar, leeftijd, lkl_dit_jaar, lkl_list


def bereken_leeftijdsklassen_ifaa(geboorte_jaar, wedstrijdgeslacht):
    """
        wedstrijdgeslacht moet zijn GESLACHT_MAN of GESLACHT_VROUW

        geeft een lijst terug met het jaartal en twee wedstrijdklassen voor IFAA wedstrijden
        de eerste wedstrijdklasse is geldig tot de verjaardag van de sporter, de tweede erna
        de lijst bevat 5 entries, voor de jaren -1, 0, +1, +2, +3 ten opzicht van het huidige jaartal
    """

    # haal alle leeftijdsklassen op en vul de min/max leeftijden aan
    alle_lkl = (LeeftijdsKlasse
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

    # pak het huidige jaar na conversie naar lokale tijdzone
    # zodat dit ook goed gaat in de laatste paar uren van het jaar
    now = timezone.now()  # is in UTC
    now = timezone.localtime(now)  # convert to active timezone (say Europe/Amsterdam)
    huidige_jaar = now.year
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
    for lkl in (LeeftijdsKlasse
                .objects
                .filter(organisatie=ORGANISATIE_WA,
                        wedstrijd_geslacht=wedstrijdgeslacht)
                .order_by('volgorde')):

        klasse_compat_geslacht = klasse_compat_leeftijd = False

        # check geslacht is compatible
        if lkl.geslacht_is_compatible(wedstrijdgeslacht):
            klasse_compat_geslacht = True

        # check leeftijd is compatible
        if lkl.leeftijd_is_compatible(wedstrijdleeftijd):
            if lkl.min_wedstrijdleeftijd == lkl.max_wedstrijdleeftijd == 0:
                fallback_lkl = lkl
            else:
                klasse_compat_leeftijd = True

        if klasse_compat_geslacht and klasse_compat_leeftijd:
            gevonden_lkl = lkl
            break
    # for

    if not gevonden_lkl:
        gevonden_lkl = fallback_lkl

    return gevonden_lkl.beschrijving


def bereken_leeftijdsklasse_ifaa(wedstrijdleeftijd, wedstrijdgeslacht):
    """
        bepaal de meest exacte IFAA leeftijdsklasse voor een sporter
        afhankelijk van zijn wedstrijdleeftijd en wedstrijdgeslacht.

        Voorbeeld: Senioren vrouwen
    """

    gevonden_lkl = None

    # print('bereken_leeftijdsklasse_ifaa: wedstrijdleeftijd=%s, wedstrijdgeslacht=%s' % (wedstrijdleeftijd, wedstrijdgeslacht))

    # selecteer een geslacht-specifieke wedstrijdklasse
    for lkl in (LeeftijdsKlasse
                .objects
                .filter(organisatie=ORGANISATIE_IFAA,
                        wedstrijd_geslacht=wedstrijdgeslacht)
                .order_by('volgorde')):

        klasse_compat_geslacht = klasse_compat_leeftijd = False

        # check geslacht is compatible
        if lkl.geslacht_is_compatible(wedstrijdgeslacht):
            klasse_compat_geslacht = True

        # check leeftijd is compatible
        if lkl.leeftijd_is_compatible(wedstrijdleeftijd):
            klasse_compat_leeftijd = True

        if klasse_compat_geslacht and klasse_compat_leeftijd:
            gevonden_lkl = lkl
            break
    # for

    return gevonden_lkl.beschrijving


def bereken_leeftijdsklasse_nhb(wedstrijdleeftijd, wedstrijdgeslacht):
    """
        bepaal de meest exacte NHB leeftijdsklasse voor een sporter
        afhankelijk van zijn geboortejaar en wedstrijdgeslacht.

        Voorbeeld: Onder 12 meisjes
                   Onder 18 jongens
    """

    gevonden_lkl = None

    # eerste poging: selecteer een geslacht-specifieke wedstrijdklasse
    for lkl in (LeeftijdsKlasse
                .objects
                .filter(organisatie__in=(ORGANISATIE_WA, ORGANISATIE_NHB),
                        wedstrijd_geslacht=wedstrijdgeslacht)
                .order_by('volgorde')):

        klasse_compat_geslacht = klasse_compat_leeftijd = False

        # check geslacht is compatible
        if lkl.geslacht_is_compatible(wedstrijdgeslacht):
            klasse_compat_geslacht = True

        # check leeftijd is compatible
        if lkl.min_wedstrijdleeftijd != lkl.max_wedstrijdleeftijd:      # skip fall-back klassen
            if lkl.leeftijd_is_compatible(wedstrijdleeftijd):
                klasse_compat_leeftijd = True

        if klasse_compat_geslacht and klasse_compat_leeftijd:
            # print('bereken_leeftijdsklasse_nhb (1): kandidaat = %s' % lkl.beschrijving)
            gevonden_lkl = lkl
            break
    # for

    if not gevonden_lkl:
        fallback_lkl = None

        # tweede poging: selecteer een gender-neutrale wedstrijdklasse
        for lkl in (LeeftijdsKlasse
                    .objects
                    .filter(organisatie__in=(ORGANISATIE_WA, ORGANISATIE_NHB),
                            wedstrijd_geslacht=GESLACHT_ALLE)
                    .order_by('volgorde')):

            klasse_compat_geslacht = klasse_compat_leeftijd = False

            # check geslacht is compatible
            if lkl.geslacht_is_compatible(wedstrijdgeslacht):
                klasse_compat_geslacht = True

            # check leeftijd is compatible
            if lkl.leeftijd_is_compatible(wedstrijdleeftijd):
                if lkl.min_wedstrijdleeftijd == lkl.max_wedstrijdleeftijd == 0:
                    fallback_lkl = lkl
                else:
                    klasse_compat_leeftijd = True

            if klasse_compat_geslacht and klasse_compat_leeftijd:
                gevonden_lkl = lkl
                break
        # for

        if not gevonden_lkl:
            gevonden_lkl = fallback_lkl

    return gevonden_lkl.beschrijving


# end of file
