# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.core.management.base import BaseCommand
from Competitie.models import Regiocompetitie, RegiocompetitieSporterBoog
from Functie.models import Functie
from Taken.operations import check_taak_bestaat, maak_taak
from datetime import timedelta


class Command(BaseCommand):

    help = "Meld inschrijvingen van gisteren via een taak aan de RCL"

    def handle(self, *args, **options):

        now = timezone.now()
        now = timezone.localtime(now)
        stamp_str = now.strftime('%Y-%m-%d om %H:%M')

        # dit commando wordt elk uur uitgevoerd
        # we willen pas vanaf 08:00 een taak / mailtje
        # voor het geval het commando een keer niet kan draaien herhalen we dit tot 12:00
        if now.hour < 8 or now.hour > 12:
            self.stdout.write('[INFO] meld_rcl_nieuwe_inschrijvingen: skipping want uur=%s' % now.hour)
            return

        now_date = now.date()
        gisteren_date = now_date - timedelta(days=1)
        self.stdout.write('[INFO] Vandaag is %s; gisteren is %s' % (now_date, gisteren_date))

        afstand_regio2deelcomp = dict()     # [(afstand_str, regio_nr)] = DeelCompetitie
        for deelcomp in (Regiocompetitie
                         .objects
                         .select_related('competitie',
                                         'regio')):

            # alleen nieuwe aanmeldingen rapporteren als de open inschrijving gesloten is
            # en de competitie nog in de actieve wedstrijden periode is waarin mensen zich in kunnen schrijven
            comp = deelcomp.competitie
            comp.bepaal_fase()
            if 'D' <= comp.fase_indiv <= 'F':
                # D = late inschrijvingen voordat wedstrijden beginnen
                # F = late inschrijvingen tijdens wedstrijden
                # tijdens deze periode willen we de RCL informeren over late inschrijvingen
                tup = (deelcomp.competitie.afstand, deelcomp.regio.regio_nr)
                afstand_regio2deelcomp[tup] = deelcomp
        # for

        aantal_nieuwe_taken = 0

        # doe 32 queries
        for functie in (Functie
                        .objects
                        .filter(rol='RCL')
                        .select_related('regio')
                        .order_by('comp_type',
                                  'regio__regio_nr')):

            tup = (functie.comp_type, functie.regio.regio_nr)
            try:
                deelcomp = afstand_regio2deelcomp[tup]
            except KeyError:
                # competitie is niet (meer) in de juiste fase
                pass
            else:
                qset = (RegiocompetitieSporterBoog
                        .objects
                        .filter(regiocompetitie=deelcomp,
                                wanneer_aangemeld=gisteren_date)
                        .select_related('sporterboog__sporter',
                                        'sporterboog__sporter__bij_vereniging',
                                        'sporterboog__boogtype')
                        .order_by('sporterboog__sporter__bij_vereniging',
                                  'sporterboog__sporter__lid_nr',
                                  'pk'))

                aantal = qset.count()
                if aantal > 0:
                    regels = list()
                    regels.append('Er zijn nieuwe inschrijvingen')
                    regels.append('')
                    regels.append('Competitie: %s' % deelcomp.competitie.beschrijving)
                    regels.append('Regio: %s' % functie.regio)
                    regels.append('Datum: %s' % gisteren_date)
                    regels.append('Aantal nieuwe inschrijvingen: %s' % aantal)

                    for deelnemer in qset:
                        regels.append('')
                        regels.append(str(deelnemer))
                        regels.append('    van vereniging %s' % deelnemer.sporterboog.sporter.bij_vereniging)

                        if deelnemer.aangemeld_door != deelnemer.sporterboog.sporter.account:
                            regels.append('    aangemeld door: %s' % deelnemer.aangemeld_door)
                        else:
                            regels.append('    zelfstandig aangemeld')
                    # for

                    beschrijving = '\n'.join(regels)

                    taak_onderwerp = "Nieuwe inschrijvingen %s" % deelcomp.competitie.beschrijving

                    # maak een taak aan met alle details
                    taak_log = "[%s] Taak aangemaakt" % stamp_str
                    taak_deadline = now + timedelta(days=7)

                    # voorkom dubbele meldingen (ook als deze al afgehandeld is)
                    if not check_taak_bestaat(skip_afgerond=False,
                                              toegekend_aan_functie=functie,
                                              beschrijving=beschrijving):

                        self.stdout.write('[INFO] %s: %s nieuwe aanmeldingen' % (functie, aantal))

                        maak_taak(toegekend_aan_functie=functie,
                                  deadline=taak_deadline,
                                  aangemaakt_door=None,  # systeem
                                  onderwerp=taak_onderwerp,
                                  beschrijving=beschrijving,
                                  log=taak_log)
                        aantal_nieuwe_taken += 1
        # for

        self.stdout.write("[INFO] Aantal nieuwe taken aangemaakt voor de RCL's: %s" % aantal_nieuwe_taken)

# end of file
