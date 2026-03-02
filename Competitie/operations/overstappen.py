# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db.models import F
from CompLaagBond.models import DeelnemerBK
from CompLaagRayon.models import DeelnemerRK

""" Functionaliteit om de overstap van een sporter naar een andere vereniging af te handelen voor de bondscompetities
"""


def competitie_hanteer_overstap_sporter(stdout):

    """ wordt 1x per uur aangeroepen vanuit competitie_mutaties"""

    # hanteer overstap RK deelnemer
    for deelnemer in (DeelnemerRK
                     .objects
                     .select_related('kamp__competitie',
                                     'bij_vereniging',
                                     'sporterboog__boogtype',
                                     'sporterboog__sporter__bij_vereniging')
                     .exclude(sporterboog__sporter__bij_vereniging=None)
                     .exclude(sporterboog__sporter__bij_vereniging=F('bij_vereniging'))):

        comp = deelnemer.kamp.competitie
        comp.bepaal_fase()

        oude_vereniging = deelnemer.bij_vereniging
        nieuwe_vereniging = deelnemer.sporterboog.sporter.bij_vereniging

        kamp_str = "%s (%s)" % (deelnemer.sporterboog.sporter.lid_nr_en_volledige_naam(),
                                deelnemer.sporterboog.boogtype.beschrijving)

        accepted = False
        rayon_str = ''
        fase_str = ''

        rayon_oud = oude_vereniging.regio.rayon_nr
        rayon_nieuw = nieuwe_vereniging.regio.rayon_nr
        binnen_zelfde_rayon = rayon_oud == rayon_nieuw

        # tijdens fase K en L van de competitie wordt de vereniging bevroren en moet
        # de sporter uitkomen op het RK van het rayon waarin die vereniging valt

        # tijdens fase J en K mag de sporter overstappen binnen hetzelfde rayon
        if comp.fase_indiv in ('J', 'K') and binnen_zelfde_rayon:
            accepted = True
            rayon_str = ' in rayon %s' % rayon_oud
            fase_str = 'J/K'

        if accepted:
            stdout.write(
                '[INFO] Overstap van [%s] naar [%s]%s tijdens fase %s van %s geaccepteerd voor DeelnemerRK (pk=%s) %s' % (
                    oude_vereniging.ver_nr, nieuwe_vereniging.ver_nr, rayon_str, fase_str,
                    comp.beschrijving, deelnemer.pk, kamp_str))

            deelnemer.bij_vereniging = nieuwe_vereniging
            deelnemer.save(update_fields=['bij_vereniging'])
    # for

    # hanteer overstap BK deelnemer
    for deelnemer in (DeelnemerBK
                     .objects
                     .select_related('kamp__competitie',
                                     'bij_vereniging',
                                     'sporterboog__boogtype',
                                     'sporterboog__sporter__bij_vereniging')
                     .exclude(sporterboog__sporter__bij_vereniging=None)
                     .exclude(sporterboog__sporter__bij_vereniging=F('bij_vereniging'))):

        comp = deelnemer.kamp.competitie
        comp.bepaal_fase()

        oude_vereniging = deelnemer.bij_vereniging
        nieuwe_vereniging = deelnemer.sporterboog.sporter.bij_vereniging

        kamp_str = "%s (%s)" % (deelnemer.sporterboog.sporter.lid_nr_en_volledige_naam(),
                                deelnemer.sporterboog.boogtype.beschrijving)

        accepted = False
        fase_str = ''

        # tijdens fase N en O mag de overstap verwerkt worden
        if comp.fase_indiv in ('N', 'O'):
            accepted = True
            fase_str = 'N/O'

        if accepted:
            stdout.write(
                '[INFO] Overstap van [%s] naar [%s] tijdens fase %s van %s geaccepteerd voor DeelnemerBK (met pk=%s) %s' % (
                    oude_vereniging.ver_nr, nieuwe_vereniging.ver_nr, fase_str,
                    comp.beschrijving, deelnemer.pk, kamp_str))

            deelnemer.bij_vereniging = nieuwe_vereniging
            deelnemer.save(update_fields=['bij_vereniging'])
    # for

    # FUTURE: overschrijven uitstellen tijdens regiocompetitie, tot afsluiten team ronde


# end of file
