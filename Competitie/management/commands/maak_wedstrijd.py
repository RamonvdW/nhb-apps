# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# maak een account HWL van specifieke vereniging, vanaf de commandline

from django.core.management.base import BaseCommand
from Competitie.models import Competitie, DeelcompetitieRonde, LAAG_REGIO
from NhbStructuur.models import NhbRegio, NhbCluster, NhbVereniging
from Wedstrijden.models import Wedstrijd
import datetime


class Command(BaseCommand):
    help = "Maak en competitiewedstrijd aan"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

    def add_arguments(self, parser):
        parser.add_argument('afstand', nargs=1, help="Competitie afstand: 18 of 25")
        parser.add_argument('geo', nargs=1, help="Regio (101) of cluster (101N)")
        parser.add_argument('ver_nr', nargs=1, help="Verenigingsnummer")
        parser.add_argument('datum', nargs=1, help="Datum in formaat YYYY-MM-DD")
        parser.add_argument('tijd', nargs=1, help="Tijdstip in formaat HHMM")

    def _maak_regio_wedstrijd(self, comp, geo, ver_nr, datum, tijd):
        pass

    @staticmethod
    def _maak_wedstrijd(plan, ver, datum, tijd):

        loc = ver.wedstrijdlocatie_set.all()[0]

        wedstrijd = Wedstrijd(beschrijving='automatisch aangemaakt',
                              vereniging=ver,
                              locatie=loc,
                              datum_wanneer=datum,
                              tijd_begin_wedstrijd=tijd,
                              tijd_begin_aanmelden='00:00',
                              tijd_einde_wedstrijd='00:00')
        wedstrijd.save()
        plan.wedstrijden.add(wedstrijd)

    def handle(self, *args, **options):
        afstand = options['afstand'][0]
        geo = options['geo'][0]
        ver_nr = options['ver_nr'][0]
        datum = options['datum'][0]
        tijd = options['tijd'][0]

        if afstand not in ('18', '25'):
            self.stderr.write('afstand moet 18 of 25 zijn')
            return

        cluster = None
        try:
            if len(geo) == 4:
                cluster = NhbCluster.objects.get(regio__regio_nr=geo[:3],
                                                 letter=geo[-1])
                regio = cluster.regio
            else:
                regio = NhbRegio.objects.get(regio_nr=geo)
        except (NhbRegio.DoesNotExist, NhbCluster.DoesNotExist):
            self.stderr.write('Geen regio of cluster kunnen matchen met %s' % repr(geo))
            return

        try:
            ver = NhbVereniging.objects.get(nhb_nr=ver_nr)
        except NhbVereniging.DoesNotExist:
            self.stderr.write('Kan vereniging %s niet vinden' % repr(ver_nr))
            return

        # controleer dat de vereniging in het cluster zit
        if cluster:
            if not cluster.nhbvereniging_set.filter(nhb_nr=ver_nr).exists():
                self.stderr.write('Vereniging %s zit niet in cluster %s' % (repr(ver_nr), repr(geo)))
                return

        done = False
        for comp in Competitie.objects.filter(is_afgesloten=False,
                                              afstand=afstand):
            for ronde in (DeelcompetitieRonde
                          .objects
                          .filter(deelcompetitie__competitie=comp,
                                  deelcompetitie__laag=LAAG_REGIO,
                                  deelcompetitie__nhb_regio=regio,
                                  cluster=cluster)):
                if not ronde.is_voor_import_oude_programma():
                    self._maak_wedstrijd(ronde.plan, ver, datum, tijd)
                    done = True
        # for

        if not done:
            self.stderr.write('Geen competitie kunnen vinden in fase < F')

# end of file
