# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import CompetitieKlasse, RegioCompetitieSchutterBoog
from Competitie.operations.klassengrenzen import KlasseBepaler


class Command(BaseCommand):
    help = "Controleer AG tegen klasse waarin sporter geplaatst is"

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', help='Voorgestelde wijzigingen opslaan')

    def handle(self, *args, **options):

        do_save = options['commit']
        if not do_save:
            self.stdout.write('Let op: gebruik --commit om voorgestelde wijzigingen op te slaan')

        volgorde2klasse = dict()             # [(competitie.pk, volgorde)] = CompetitieKlasse
        volgorde2hogere_klasse = dict()      # [(competitie.pk, volgorde)] = CompetitieKlasse

        for klasse in (CompetitieKlasse
                       .objects
                       .select_related('competitie',
                                       'indiv')
                       .exclude(indiv=None)
                       .filter(indiv__is_onbekend=False)
                       .order_by('indiv__volgorde')):

            comp_pk = klasse.competitie.pk
            volgorde = klasse.indiv.volgorde

            volgorde2klasse[(comp_pk, volgorde)] = klasse

            try:
                hogere_klasse = volgorde2klasse[(comp_pk, volgorde - 1)]
            except KeyError:
                # geen hogere klasse
                pass
            else:
                if not hogere_klasse.indiv.is_onbekend:         # pragma: no branch
                    volgorde2hogere_klasse[(comp_pk, volgorde)] = hogere_klasse
        # for

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
                          .select_related('klasse__indiv',
                                          'deelcompetitie__competitie')
                          .all()):                                          # pragma: no cover

            comp_pk = deelnemer.deelcompetitie.competitie.pk
            volgorde = deelnemer.klasse.indiv.volgorde

            try:
                hogere_klasse = volgorde2hogere_klasse[(comp_pk, volgorde)]
            except KeyError:
                pass
            else:
                indiv_ag = deelnemer.ag_voor_indiv
                klasse_min_ag = hogere_klasse.min_ag

                if indiv_ag >= klasse_min_ag:
                    self.stdout.write('[WARNING] %s: klasse %s, indiv_ag %s < hogere klasse min_ag %s (%s)' % (deelnemer, deelnemer.klasse, indiv_ag, klasse_min_ag, hogere_klasse))

                    bepaler = KlasseBepaler(deelnemer.deelcompetitie.competitie)
                    bepaler.bepaal_klasse_deelnemer(deelnemer)
                    self.stdout.write('          nieuwe klasse: %s' % deelnemer.klasse)

                    if do_save:
                        deelnemer.save(update_fields=['klasse'])
        # for

# end of file
