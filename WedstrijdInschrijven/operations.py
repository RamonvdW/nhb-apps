# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Sporter.models import Sporter, SporterVoorkeuren
from Wedstrijden.definities import (WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD, WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD,
                                    WEDSTRIJD_BEGRENZING_TO_STR,
                                    WEDSTRIJD_BEGRENZING_VERENIGING, WEDSTRIJD_BEGRENZING_REGIO,
                                    WEDSTRIJD_BEGRENZING_RAYON, WEDSTRIJD_BEGRENZING_WERELD)
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving
from typing import Tuple


def get_sessies(wedstrijd: Wedstrijd, sporter: Sporter,
                voorkeuren: SporterVoorkeuren, wedstrijdboog_pk: int) -> Tuple[list, int, list, str, bool]:
    """
        Geef de mogelijke sessies terug waarop de sporter zich in kan schrijven

        In: wedstrijd:         de wedstrijd waar het om gaat (verplicht)
            sporter:           de sporter waar het om gaat (optioneel; mag None zijn)
            voorkeuren:        de voorkeuren van de sporter (optioneel; mag None zijn)
            wedstrijdboog_pk   het boogtype waar het om gaat (optioneel; mag -1 zijn)

        Out: sessies (qset)
             wedstrijdleeftijd      None als deze niet bepaald kon worden
             wedstrijdklassen       lijst van beschrijvingen
             wedstrijd_geslacht     M/V of '?' als deze niet bepaald kon worden
             heeft_beschrijvingen   hebben de sessies beschrijvingen?
    """

    wedstrijdleeftijd = sporter.bereken_wedstrijdleeftijd(wedstrijd.datum_begin, wedstrijd.organisatie)

    wedstrijd_geslacht = '?'
    if voorkeuren and voorkeuren.wedstrijd_geslacht_gekozen:
        wedstrijd_geslacht = voorkeuren.wedstrijd_geslacht

    sessie_pks = list(wedstrijd.sessies.values_list('pk', flat=True))
    sessies = (WedstrijdSessie
               .objects
               .filter(pk__in=sessie_pks)
               .prefetch_related('wedstrijdklassen')
               .order_by('datum',
                         'tijd_begin',
                         'pk'))

    # kijk of de sporter al ingeschreven is
    sessie_pk2inschrijving = dict()       # [sessie.pk] = [inschrijving, ..]
    for inschrijving in (WedstrijdInschrijving
                         .objects
                         .select_related('sessie',
                                         'sporterboog',
                                         'sporterboog__sporter',
                                         'sporterboog__boogtype')
                         .filter(sessie__pk__in=sessie_pks,
                                 sporterboog__sporter=sporter)
                         .exclude(status__in=(WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD,
                                              WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD))):

        sessie_pk = inschrijving.sessie.pk
        try:
            sessie_pk2inschrijving[sessie_pk].append(inschrijving)
        except KeyError:
            sessie_pk2inschrijving[sessie_pk] = [inschrijving]
    # for

    compatible_doelgroep = True

    if sporter.is_gast:
        if wedstrijd.begrenzing != WEDSTRIJD_BEGRENZING_WERELD:
            compatible_doelgroep = False

    if wedstrijd.begrenzing == WEDSTRIJD_BEGRENZING_VERENIGING:
        if sporter.bij_vereniging != wedstrijd.organiserende_vereniging:
            compatible_doelgroep = False

    elif wedstrijd.begrenzing == WEDSTRIJD_BEGRENZING_REGIO:
        if sporter.bij_vereniging.regio != wedstrijd.organiserende_vereniging.regio:
            compatible_doelgroep = False

    elif wedstrijd.begrenzing == WEDSTRIJD_BEGRENZING_RAYON:
        if sporter.bij_vereniging.regio.rayon != wedstrijd.organiserende_vereniging.regio.rayon:
            compatible_doelgroep = False

    if not compatible_doelgroep:
        wedstrijd.begrenzing_str = WEDSTRIJD_BEGRENZING_TO_STR[wedstrijd.begrenzing]

    sessie_beschrijvingen = False
    unsorted_wedstrijdklassen = list()
    for sessie in sessies:
        sessie.aantal_beschikbaar = sessie.max_sporters - sessie.aantal_inschrijvingen
        sessie.klassen = (sessie
                          .wedstrijdklassen
                          .select_related('leeftijdsklasse',
                                          'boogtype')
                          .order_by('volgorde'))        # oudste leeftijdsklasse eerst

        sessie.kan_aanmelden = False
        sessie.al_ingeschreven = False

        compatible_boog = False
        compatible_geslacht = False
        compatible_leeftijd = False

        for klasse in sessie.klassen:
            lkl = klasse.leeftijdsklasse

            klasse_compat_boog = klasse_compat_geslacht = klasse_compat_leeftijd = False

            if klasse.boogtype.pk == wedstrijdboog_pk:
                compatible_boog = klasse_compat_boog = True
                sessie.boogtype_pk = klasse.boogtype.id

            # check geslacht is compatible
            if lkl.geslacht_is_compatible(wedstrijd_geslacht):
                compatible_geslacht = klasse_compat_geslacht = True

            # check leeftijd is compatible
            if lkl.leeftijd_is_compatible(wedstrijdleeftijd):
                compatible_leeftijd = klasse_compat_leeftijd = True

                # verzamel een lijstje van compatibele wedstrijdklassen om te tonen
                lkl_tup = (lkl.volgorde, lkl.beschrijving)
                if lkl_tup not in unsorted_wedstrijdklassen:
                    if lkl.geslacht_is_compatible(wedstrijd_geslacht):
                        unsorted_wedstrijdklassen.append(lkl_tup)

            klasse.is_compat = klasse_compat_boog and klasse_compat_geslacht and klasse_compat_leeftijd
        # for

        if compatible_boog and compatible_leeftijd and compatible_geslacht and compatible_doelgroep:
            try:
                inschrijvingen = sessie_pk2inschrijving[sessie.pk]
            except KeyError:
                # nog niet in geschreven
                sessie.kan_aanmelden = True
            else:
                # al ingeschreven - controleer de boog
                for inschrijving in inschrijvingen:
                    if inschrijving.sporterboog.boogtype.pk == wedstrijdboog_pk:
                        sessie.al_ingeschreven = True
                # for

                if not sessie.al_ingeschreven:
                    sessie.kan_aanmelden = True

        # verzamel waarom een sporter niet op deze sessie in kan schrijven
        sessie.compatible_boog = compatible_boog
        sessie.compatible_leeftijd = compatible_leeftijd
        sessie.compatible_geslacht = compatible_geslacht
        sessie.compatible_doelgroep = compatible_doelgroep

        sessie.prijs_euro_sporter = wedstrijd.bepaal_prijs_voor_sporter(sporter)

        if sessie.aantal_beschikbaar <= 0:
            sessie.kan_aanmelden = False

        if len(sessie.beschrijving):
            sessie_beschrijvingen = True
    # for

    # sorteer de wedstrijdklassen
    unsorted_wedstrijdklassen.sort(reverse=True)        # oudste leeftijdsklasse eerst
    wedstrijdklassen = [lkl for _, lkl in unsorted_wedstrijdklassen]

    return sessies, wedstrijdleeftijd, wedstrijdklassen, wedstrijd_geslacht, sessie_beschrijvingen


# end of file
