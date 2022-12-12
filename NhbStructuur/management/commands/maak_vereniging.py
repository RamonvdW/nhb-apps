# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# maak een vereniging aan vanaf de commandline
# dit is bedoeld voor demonstraties en de handleiding

from django.core.management.base import BaseCommand
from NhbStructuur.models import NhbVereniging, NhbRegio


class Command(BaseCommand):
    help = "Maak een vereniging aan"

    def add_arguments(self, parser):
        parser.add_argument('ver_nr', nargs=1,
                            help="Verenigingsnummer")
        parser.add_argument('naam', nargs=1,
                            help="Naam van de vereniging")
        parser.add_argument('plaats', nargs=1,
                            help="Plaats van de vereniging")

    def handle(self, *args, **options):
        ver_nr = options['ver_nr'][0]
        naam = options['naam'][0]
        plaats = options['plaats'][0]

        regio = NhbRegio.objects.get(regio_nr=100)

        # maak een nieuwe vereniging aan
        ver = NhbVereniging(
                    ver_nr=ver_nr,
                    naam=naam,
                    adres_regel1='Doelpakstraat 1',
                    adres_regel2='9999 ZZ  %s' % plaats,
                    plaats=plaats,
                    regio=regio)
        ver.save()

# end of file
