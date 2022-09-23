# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.core.management.base import BaseCommand
from Competitie.models import DeelCompetitie, RegioCompetitieSchutterBoog, LAAG_REGIO
from Functie.models import Functie
from Taken.operations import maak_taak
from datetime import timedelta


class Command(BaseCommand):
    help = "Meld inschrijvingen van gisteren via een taak aan de RCL"

    def handle(self, *args, **options):

        now = timezone.now()

        now_date = now.date()
        gisteren_date = now_date - timedelta(days=1)
        self.stdout.write('[INFO] Vandaag is %s; gisteren is %s' % (now_date, gisteren_date))

        afstand_regio2deelcomp = dict()     # [(afstand_str, regio_nr)] = DeelCompetitie
        for deelcomp in (DeelCompetitie
                         .objects
                         .filter(laag=LAAG_REGIO)
                         .select_related('competitie',
                                         'nhb_regio')):

            # alleen nieuwe aanmeldingen rapporteren als de open inschrijving gesloten is
            # en de competitie nog in de actieve wedstrijden periode is waarin mensen zich in kunnen schrijven
            comp = deelcomp.competitie
            comp.bepaal_fase()
            if 'B' < comp.fase <= 'E':
                tup = (deelcomp.competitie.afstand, deelcomp.nhb_regio.regio_nr)
                afstand_regio2deelcomp[tup] = deelcomp
        # for

        # doe 32 queries
        for functie in (Functie
                        .objects
                        .filter(rol='RCL')
                        .select_related('nhb_regio')
                        .order_by('comp_type',
                                  'nhb_regio__regio_nr')):

            tup = (functie.comp_type, functie.nhb_regio.regio_nr)
            try:
                deelcomp = afstand_regio2deelcomp[tup]
            except KeyError:
                # competitie is niet meer in de juiste fase
                pass
            else:
                qset = (RegioCompetitieSchutterBoog
                        .objects
                        .filter(deelcompetitie=deelcomp,
                                wanneer_aangemeld=gisteren_date)
                        .select_related('sporterboog__sporter',
                                        'sporterboog__sporter__bij_vereniging',
                                        'sporterboog__boogtype')
                        .order_by('sporterboog__sporter__bij_vereniging',
                                  'sporterboog__sporter__lid_nr',
                                  'pk'))

                aantal = qset.count()
                if aantal > 0:
                    self.stdout.write('[INFO] %s: %s nieuwe aanmeldingen' % (functie, aantal))

                    regels = list()
                    regels.append('Er zijn nieuwe inschrijvingen')
                    regels.append('')
                    regels.append('Competitie: %s' % deelcomp.competitie.beschrijving)
                    regels.append('Regio: %s' % functie.nhb_regio)
                    regels.append('Datum: %s' % gisteren_date)
                    regels.append('Aantal nieuwe inschrijvingen: %s' % aantal)
                    regels.append('')

                    for deelnemer in qset:
                        regels.append(str(deelnemer))
                        regels.append('    van vereniging %s' % deelnemer.sporterboog.sporter.bij_vereniging)

                        if deelnemer.aangemeld_door != deelnemer.sporterboog.sporter.account:
                            regels.append('    aangemeld door: %s' % deelnemer.aangemeld_door)
                        else:
                            regels.append('    zelfstandig aangemeld')
                    # for

                    beschrijving = '\n'.join(regels)

                    # maak een taak aan met alle details
                    taak_log = "[%s] Taak aangemaakt" % now
                    taak_deadline = now + timedelta(days=7)

                    maak_taak(toegekend_aan_functie=functie,
                              deadline=taak_deadline,
                              aangemaakt_door=None,  # systeem
                              beschrijving=beschrijving,
                              log=taak_log)

        # for

# end of file
