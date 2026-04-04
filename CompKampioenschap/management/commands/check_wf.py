# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import CompetitieIndivKlasse
from CompKampioenschap.operations.importeer_uitslag_indiv import ImporteerSheetUitslagIndiv
from CompLaagBond.models import KampBK
from CompLaagRayon.models import KampRK
from GoogleDrive.models import Bestand
import time


class Command(BaseCommand):
    help = "Check wedstrijdformulieren (google sheet)"

    def _check_wf(self, bestand: Bestand):
        print('{check_wf} %s' % bestand.fname)

        if bestand.is_bk:
            qset = KampBK.objects.all()
        else:
            qset = KampRK.objects.filter(rayon__rayon_nr=bestand.rayon_nr)

        kamp = qset.filter(competitie__afstand=bestand.afstand, competitie__begin_jaar=bestand.begin_jaar).first()

        indiv_klasse = CompetitieIndivKlasse.objects.get(pk=bestand.klasse_pk)

        imp = ImporteerSheetUitslagIndiv(kamp, indiv_klasse)
        imp.lees_sheet(bestand)
        if imp.bevat_fout:
            for regels in imp.blokjes_info:
                for regel in regels:
                    self.stdout.write('{check_wf} %s' % regel)
                # for
            # for

    def handle(self, *args, **options):
        for bestand in Bestand.objects.all():
            self._check_wf(bestand)
            time.sleep(1)       # prevent quota overrun
        # for


# end of file
