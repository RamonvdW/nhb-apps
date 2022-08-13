# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import CompetitieIndivKlasse, RegioCompetitieSchutterBoog
from Competitie.operations.klassengrenzen import KlasseBepaler


class Command(BaseCommand):
    help = "Controleer AG tegen klasse waarin sporter geplaatst is"

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', help='Voorgestelde wijzigingen opslaan')

    def handle(self, *args, **options):

        do_save = options['commit']
        if not do_save:
            self.stdout.write('Let op: gebruik --commit om voorgestelde wijzigingen op te slaan')

        volgorde2leeftijdsklassen = dict()  # [(competitie.pk, volgorde)] = "<afkorting>/<afkorting>"

        volgorde2klasse = dict()            # [(competitie.pk, volgorde)] = CompetitieIndivKlasse
        volgorde2hogere_klasse = dict()     # [(competitie.pk, volgorde)] = CompetitieIndivKlasse

        for klasse in (CompetitieIndivKlasse
                       .objects
                       .select_related('competitie')
                       .prefetch_related('leeftijdsklassen')
                       .filter(is_onbekend=False)
                       .order_by('volgorde')):

            comp_pk = klasse.competitie.pk
            volgorde = klasse.volgorde

            lkl_lst = list(klasse.leeftijdsklassen.values_list('afkorting', flat=True))
            lkl_lst.sort()
            lkl_str = "/".join(lkl_lst)
            volgorde2leeftijdsklassen[(comp_pk, volgorde)] = lkl_str

            volgorde2klasse[(comp_pk, volgorde)] = klasse

            try:
                hogere_klasse = volgorde2klasse[(comp_pk, volgorde - 1)]
            except KeyError:
                # geen hogere klasse
                pass
            else:
                # some lopen de nummers door, maar is het een andere leeftijdsklasse
                if lkl_str == volgorde2leeftijdsklassen[(comp_pk, hogere_klasse.volgorde)]:
                    if not hogere_klasse.is_onbekend:         # pragma: no branch
                        volgorde2hogere_klasse[(comp_pk, volgorde)] = hogere_klasse
        # for

        # debug dump
        # for volgorde, klasse in volgorde2klasse.items():
        #     try:
        #         hogere_klasse = volgorde2hogere_klasse[volgorde]
        #         print('klasse %s --> hoger: %s' % (klasse, hogere_klasse))
        #     except KeyError:
        #         print('klasse %s --> hoger: geen' % klasse)
        #         pass
        # # for

        for deelnemer in (RegioCompetitieSchutterBoog
                          .objects
                          .select_related('indiv_klasse',
                                          'deelcompetitie__competitie')
                          .all()):                                          # pragma: no cover

            comp_pk = deelnemer.deelcompetitie.competitie.pk
            volgorde = deelnemer.indiv_klasse.volgorde

            try:
                hogere_klasse = volgorde2hogere_klasse[(comp_pk, volgorde)]
            except KeyError:
                pass
            else:
                indiv_ag = deelnemer.ag_voor_indiv
                klasse_min_ag = hogere_klasse.min_ag

                if indiv_ag >= klasse_min_ag:
                    self.stdout.write('[WARNING] %s: klasse %s, indiv_ag %s < hogere klasse min_ag %s (%s)' % (
                                        deelnemer, deelnemer.indiv_klasse, indiv_ag, klasse_min_ag, hogere_klasse))

                    bepaler = KlasseBepaler(deelnemer.deelcompetitie.competitie)
                    bepaler.bepaal_klasse_deelnemer(deelnemer)
                    self.stdout.write('          nieuwe indiv_klasse: %s' % deelnemer.indiv_klasse)

                    if do_save:
                        deelnemer.save(update_fields=['indiv_klasse'])
        # for

# end of file
