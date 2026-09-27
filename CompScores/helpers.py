# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from Competitie.models import CompetitieMatch
from Score.models import Uitslag


def mag_deelcomp_wedstrijd_wijzigen(wedstrijd, functie_nu, deelcomp):
    """ controleer toestemming om scoreverwerking te doen voor deze wedstrijd """
    if (functie_nu.rol == 'RCL'
            and functie_nu.regio == deelcomp.regio
            and functie_nu.comp_type == deelcomp.competitie.afstand):
        # RCL van deze regiocompetitie
        return True

    if functie_nu.rol in ('HWL', 'WL') and functie_nu.vereniging == wedstrijd.vereniging:
        # (H)WL van de organiserende vereniging
        return True

    return False


def bepaal_match_en_deelcomp_of_404(match_pk, mag_database_wijzigen=False):
    try:
        match_pk = int(match_pk[:7])        # afkappen voor de veiligheid
        match = (CompetitieMatch
                 .objects
                 .select_related('uitslag')
                 .prefetch_related('uitslag__scores')
                 .get(pk=match_pk))
    except (ValueError, CompetitieMatch.DoesNotExist):
        raise Http404('Wedstrijd niet gevonden')

    rondes = match.regioronde_set.all()
    if len(rondes) == 0:
        raise Http404('Geen regio wedstrijd')
    ronde = rondes[0]

    deelcomp = ronde.regiocomp

    # maak de uitslag aan indien nog niet gedaan
    if not match.uitslag:
        uitslag = Uitslag()
        if deelcomp.competitie.is_indoor():
            uitslag.max_score = 300
            uitslag.afstand = 18
        else:
            uitslag.max_score = 250
            uitslag.afstand = 25

        if mag_database_wijzigen:
            uitslag.save()
            match.uitslag = uitslag
            match.save(update_fields=['uitslag'])
    else:
        uitslag = match.uitslag

    match.max_score = uitslag.max_score
    match.afstand = uitslag.afstand

    return match, deelcomp, ronde


# end of file
