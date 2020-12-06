# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# importeer individuele competitie historie

import argparse
from django.core.management.base import BaseCommand
from Taken.models import Taak
from Account.models import Account


class Command(BaseCommand):
    help = "Maak een taak aan"
    verbose = False

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self._beheerder_accounts = list()

    def add_arguments(self, parser):
        parser.add_argument('toekennen_aan', nargs=1, help="Account inlog naam")
        parser.add_argument('aangemaakt_door', nargs=1, help="Account inlog naam of 'systeem'")
        parser.add_argument('deadline', nargs=1, help='Wanneer moet het af zijn (formaat: YYYY-MM-DD)')
        parser.add_argument('handleiding_pagina', nargs=1, help='Handleiding pagina naam')
        parser.add_argument('beschrijving', nargs=1, help='Beschrijving (gebruik \\n voor nieuwe regel)')

    def handle(self, *args, **options):

        try:
            toekennen_aan = Account.objects.get(username=options['toekennen_aan'][0])
        except Account.DoesNotExist as exc:
            self.stderr.write("%s" % str(exc))
            return

        aangemaakt_door = options['aangemaakt_door'][0]
        if aangemaakt_door.lower() == 'systeem':
            aangemaakt_door = None
        else:
            try:
                aangemaakt_door = Account.objects.get(username=aangemaakt_door)
            except Account.DoesNotExist as exc:
                self.stderr.write("%s" % str(exc))
                return

        deadline = options['deadline'][0]
        pagina = options['handleiding_pagina'][0]
        beschrijving = options['beschrijving'][0].replace('\\n', '\n')

        taak = Taak(aangemaakt_door=aangemaakt_door,
                    toegekend_aan=toekennen_aan,
                    deadline=deadline,
                    beschrijving=beschrijving,
                    handleiding_pagina=pagina)
        taak.save()

# end of file

