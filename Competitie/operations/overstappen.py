# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db.models import F
from Competitie.models import KampioenschapSporterBoog

""" Functionaliteit om de overstap van een sporter naar een andere vereniging af te handelen voor de bondscompetities
"""


def competitie_hanteer_overstap_sporter(stdout):

    """ wordt 1x per uur aangeroepen vanuit regiocomp_mutaties"""

    for kampioen in (KampioenschapSporterBoog
                     .objects
                     .select_related('kampioenschap__competitie',
                                     'bij_vereniging',
                                     'sporterboog__boogtype',
                                     'sporterboog__sporter__bij_vereniging')
                     .exclude(sporterboog__sporter__bij_vereniging=None)
                     .exclude(sporterboog__sporter__bij_vereniging=F('bij_vereniging'))):

        comp = kampioen.kampioenschap.competitie
        comp.bepaal_fase()

        oude_vereniging = kampioen.bij_vereniging
        nieuwe_vereniging = kampioen.sporterboog.sporter.bij_vereniging

        rayon_oud = oude_vereniging.regio.rayon_nr
        rayon_nieuw = nieuwe_vereniging.regio.rayon_nr
        binnen_zelfde_rayon = rayon_oud == rayon_nieuw

        # RK deelname: tijdens fase J mag de sporter overstappen worden binnen hetzelfde rayon
        if comp.fase_indiv == 'J' and binnen_zelfde_rayon:
            kamp_str = "[%s] %s (%s)" % (
                        kampioen.sporterboog.sporter.lid_nr,
                        kampioen.sporterboog.sporter.volledige_naam(),
                        kampioen.sporterboog.boogtype.beschrijving)

            stdout.write(
                '[INFO] Overstap van [%s] naar [%s] in rayon %s tijdens fase J van %s geaccepteerd voor (pk=%s) %s' % (
                            oude_vereniging.ver_nr, nieuwe_vereniging.ver_nr, rayon_oud,
                            comp.beschrijving, kampioen.pk, kamp_str))

            kampioen.bij_vereniging = nieuwe_vereniging
            kampioen.save(update_fields=['bij_vereniging'])
    # for

    # RK deelname: tijdens fase K en L van de competitie wordt de vereniging bevroren en moet
    #              de sporter uitkomen op het RK van het rayon waarin die vereniging valt

    # FUTURE: overschrijven tijdens regiocompetitie, bij afsluiten team ronde



# end of file
