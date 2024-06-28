# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from BasisTypen.definities import GESLACHT_MAN, GESLACHT_VROUW, GESLACHT_ANDERS
from Competitie.models import CompetitieIndivKlasse, RegiocompetitieSporterBoog
from Competitie.operations.klassengrenzen import KlasseBepaler
from Sporter.models import SporterVoorkeuren


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

            lkl_lst: list[str] = list(klasse.leeftijdsklassen.values_list('afkorting', flat=True))
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
        # comp_pk2afstand = dict()
        # for comp in Competitie.objects.all():
        #     comp_pk2afstand[comp.pk] = comp.afstand
        # # for
        # for volgorde, klasse in volgorde2klasse.items():
        #     comp_pk = volgorde[0]
        #     afstand = comp_pk2afstand[comp_pk]
        #     try:
        #         hogere_klasse = volgorde2hogere_klasse[volgorde]
        #         print('klasse %s %sm --> hoger: %s' % (klasse, afstand, hogere_klasse))
        #     except KeyError:
        #         print('klasse %s %sm --> hoger: geen' % (klasse, afstand))
        #         pass
        # # for

        sporter_pk2wedstrijdgeslacht = dict()
        for voorkeuren in SporterVoorkeuren.objects.select_related('sporter').all():
            if voorkeuren.wedstrijd_geslacht_gekozen:
                wedstrijdgeslacht = voorkeuren.wedstrijd_geslacht   # M/V
            else:
                wedstrijdgeslacht = voorkeuren.sporter.geslacht     # M/V/X
            sporter_pk2wedstrijdgeslacht[voorkeuren.sporter.pk] = wedstrijdgeslacht
        # for

        prev_comp_pk = jaartal = -1
        for deelnemer in (RegiocompetitieSporterBoog
                          .objects
                          .select_related('indiv_klasse',
                                          'sporterboog',
                                          'sporterboog__sporter',
                                          'regiocompetitie__competitie')
                          .order_by('regiocompetitie__competitie__pk')):     # pragma: no cover

            comp_pk = deelnemer.regiocompetitie.competitie.pk
            volgorde = deelnemer.indiv_klasse.volgorde

            if comp_pk != prev_comp_pk:
                bepaler = KlasseBepaler(deelnemer.regiocompetitie.competitie)
                prev_comp_pk = comp_pk
                jaartal = deelnemer.regiocompetitie.competitie.begin_jaar + 1

            try:
                wedstrijdgeslacht = sporter_pk2wedstrijdgeslacht[deelnemer.sporterboog.sporter.pk]
            except KeyError:
                wedstrijdgeslacht = deelnemer.sporterboog.sporter.geslacht

            try:
                hogere_klasse = volgorde2hogere_klasse[(comp_pk, volgorde)]
            except KeyError:
                # controleer dat aspiranten met geslacht anders niet in Onder 18 terecht gekomen zijn
                wedstrijdleeftijd = deelnemer.sporterboog.sporter.bereken_wedstrijdleeftijd_wa(jaartal)

                if wedstrijdgeslacht == GESLACHT_ANDERS and wedstrijdleeftijd < 18:
                    self.stdout.write('Aspirant met geslacht anders mogelijk in te hogen gender-neutrale klasse ingedeeld')
                    # omdat wedstrijdgeslacht niet ingesteld is
                    oude_klasse = deelnemer.indiv_klasse
                    oude_max_leeftijd = max([lkl.max_wedstrijdleeftijd
                                             for lkl in deelnemer.indiv_klasse.leeftijdsklassen.all()])
                    self.stdout.write(deelnemer, wedstrijdleeftijd, '\n          ', oude_klasse, '<=', oude_max_leeftijd, 'jaar')
                    bepaler.bepaal_klasse_deelnemer(deelnemer, GESLACHT_MAN)
                    alt_h = deelnemer.indiv_klasse
                    alt_h_leeftijd = max([lkl.max_wedstrijdleeftijd
                                          for lkl in deelnemer.indiv_klasse.leeftijdsklassen.all()])
                    bepaler.bepaal_klasse_deelnemer(deelnemer, GESLACHT_VROUW)
                    alt_d = deelnemer.indiv_klasse
                    alt_d_leeftijd = max([lkl.max_wedstrijdleeftijd
                                          for lkl in deelnemer.indiv_klasse.leeftijdsklassen.all()])

                    if alt_d_leeftijd != oude_max_leeftijd or alt_d_leeftijd != oude_max_leeftijd:
                        self.stdout.write('    alt_h: %s <= %s jaar' % (alt_h, alt_h_leeftijd))
                        self.stdout.write('    alt_d: %s <= %s jaar' % (alt_d, alt_d_leeftijd))

            else:
                indiv_ag = deelnemer.ag_voor_indiv
                klasse_min_ag = hogere_klasse.min_ag

                if indiv_ag >= klasse_min_ag:
                    self.stdout.write('[WARNING] %s: klasse %s, indiv_ag %s < hogere klasse min_ag %s (%s)' % (
                                        deelnemer, deelnemer.indiv_klasse, indiv_ag, klasse_min_ag, hogere_klasse))

                    bepaler.bepaal_klasse_deelnemer(deelnemer, wedstrijdgeslacht)
                    self.stdout.write('          nieuwe indiv_klasse: %s' % deelnemer.indiv_klasse)

                    if do_save:
                        deelnemer.save(update_fields=['indiv_klasse'])
        # for

# end of file
