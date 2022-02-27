# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" ondersteuning voor de leeftijdsklassen binnen de NHB applicaties """

from django.utils import timezone
from BasisTypen.models import LeeftijdsKlasse, GESLACHT_ALLE


def alle_wedstrijdleeftijden_groepen():
    """ Deze functie maakt een volledige tabel met alle wedstrijdleeftijden

        Output: lijst van tuples: (min_leeftijd, max_leeftijd, leeftijdklasse, wedstrijdklasse),

        [ ( 0,  11, 'Onder 12', 'Onder 12 (aspiranten)'),
          (12,  13, 'Onder 14', 'Onder 14 (aspiranten)'),
          (14,  17, 'Onder 18', 'Onder 18 (cadetten)'),
          (18,  20, 'Onder 21', 'Onder 21 (junioren)'),
          (21,  49, '21+',      '21+ (senioren)'),
          (50,  59, '50+',      '50+ (masters)'),
          (60, 150, '60+',      '60+ (veteranen)')
        ]
    """

    # haal alle leeftijdsklassen op en vul de min/max leeftijden aan
    alle_lkl = list()
    prev_lkl = None
    min_wedstrijdleeftijd = 0
    for lkl in (LeeftijdsKlasse
                .objects
                .filter(wedstrijd_geslacht=GESLACHT_ALLE)
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


def bereken_leeftijdsklassen(geboorte_jaar):
    """ retourneert de eerder bepaalde informatie over de wedstrijdklasse
        voor jonge schutters (onder de 30 jaar).
        Retourneert:
            Huidige jaar, Leeftijd, False, None, None als het geen jonge schutter betreft
            Huidige jaar, Leeftijd, True, wlst, clst voor jonge schutters
                wlst en clst zijn een lijst van wedstrijdklassen voor
                de jaren -1, 0, +1, +2, +3 ten opzicht van Leeftijd
                Voorbeeld:
                    huidige jaar = 2019
                    leeftijd = 17
                    is_jong = True
                    wlst=(Cadet, Junior, Junior, Junior, Senior)
    """

    # haal alle groepjes van wedstrijdleeftijden op
    # en zet om in look-up tabel
    leeftijd2tekst = dict()
    for min_leeftijd, max_leeftijd, lkl, wkl in alle_wedstrijdleeftijden_groepen():
        for leeftijd in range(min_leeftijd, max_leeftijd+1):
            leeftijd2tekst[leeftijd] = (lkl, wkl)
        # for
    # for

    # pak het huidige jaar na conversie naar lokale tijdzone
    # zodat dit ook goed gaat in de laatste paar uren van het jaar
    now = timezone.now()  # is in UTC
    now = timezone.localtime(now)  # convert to active timezone (say Europe/Amsterdam)
    huidige_jaar = now.year
    leeftijd = huidige_jaar - geboorte_jaar

    # bereken de wedstrijdklassen en competitieklassen
    lkl_volgende_competitie = None
    wlst = list()
    clst = list()
    for n in (-1, 0, 1, 2, 3):
        wleeftijd = leeftijd + n            # voor wedstrijden
        lkl, _ = leeftijd2tekst[wleeftijd]
        wlst.append(lkl)

        cleeftijd = wleeftijd + 1           # voor de competitie
        cleeftijd = min(49, cleeftijd)      # begrens op Senior voor de competitie
        lkl, wkl = leeftijd2tekst[cleeftijd]
        clst.append(wkl)
        if n == 1:
            lkl_volgende_competitie = lkl
    # for

    return huidige_jaar, leeftijd, wlst, clst, lkl_volgende_competitie


# end of file
