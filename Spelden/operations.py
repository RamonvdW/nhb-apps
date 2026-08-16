# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Spelden.models import SpeldVoorwaarden
from Sporter.models import Speelsterkte
from Sporter.leeftijdsklassen import bereken_leeftijdsklassen_wa, hogere_en_lagere_lkl_wa
from Wedstrijden.definities import WEDSTRIJD_DISCIPLINE_VELD


def get_hall_of_fame():
    """ Geef de Speelsterkte queries terug van de sporters met pascodes GM, MS, AS,
        elk gesorteerd op datum (oudste eerst) en lidnummer.
        Sporters die niet meer actief lid zijn van een vereniging worden eruit gefilterd.
    """

    qset = (Speelsterkte
            .objects
            .select_related('sporter',
                            'sporter__bij_vereniging')
            .exclude(sporter__bij_vereniging=None)
            .exclude(sporter__bij_vereniging__ver_nr__in=settings.CRM_IMPORT_GEEN_WEDSTRIJDEN)
            .order_by('datum',               # oudste eerst
                      'sporter__lid_nr'))

    leden_gm = qset.filter(pas_code='GM')
    lid_nrs = list(leden_gm.values_list('sporter__lid_nr', flat=True))

    leden_ms = qset.filter(pas_code='MS').exclude(sporter__lid_nr__in=lid_nrs)

    leden_as = qset.filter(pas_code='AS')

    return leden_gm, leden_ms, leden_as


def tel_hall_of_fame():
    """ Geeft het aantal sporters terug dat GM, MS of AS is """

    leden_gm, leden_ms, leden_as = get_hall_of_fame()

    gm_count = leden_gm.count()
    ms_count = leden_ms.count()
    as_count = leden_as.count()

    return gm_count, ms_count, as_count


def get_mogelijke_spelden(discipline: str, boog: str, score: int, wedstrijd_geslacht: str, geboorte_jaar: int):
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
                    # benodigde_score__lte=score,
                    leeftijdsklasse__wedstrijd_geslacht=wedstrijd_geslacht))

    if discipline == WEDSTRIJD_DISCIPLINE_VELD:
        # alleen dames/heren opsplitsing, geen verdere leeftijdsklasse
        pass
    else:
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

        print('{mogelijke_lkl}', mogelijke_lkl)

        alle_lkl = list()
        for lkl in mogelijke_lkl:
            alle_lkl.extend(hogere_en_lagere_lkl_wa(lkl))

        print('{alle_lkl}', alle_lkl)

        qset = qset.filter(leeftijdsklasse__in=alle_lkl)

    return list(qset)


# end of file
