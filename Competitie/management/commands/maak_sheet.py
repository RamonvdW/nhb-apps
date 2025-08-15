# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from GoogleDrive.operations.kamp_programmas_google_drive import Storage


class Command(BaseCommand):
    help = "[devtest] Vind of maak een Google Sheet"

    def __init__(self):
        super().__init__()

    def add_arguments(self, parser):
        parser.add_argument('afstand', nargs=1, type=int, choices=(18, 25, 42))
        parser.add_argument('I_or_T', nargs=1, type=str, choices=('I', 'T'), help="I=Individueel, T=Teams")
        parser.add_argument('RK_or_BK', nargs=1, type=str, choices=('RK', 'BK'))
        parser.add_argument('filename', nargs=1, help="Naam van het bestand")
        parser.add_argument('--create', action='store_true')

    def handle(self, *args, **options):

        afstand = int(options['afstand'][0])
        is_teams = options['I_or_T'][0] == 'T'
        is_bk = options['RK_or_BK'][0] == 'BK'
        fname = options['filename'][0]
        mag_aanmaken = options['create']

        begin_jaar = 2025

        storage = Storage(self.stdout, begin_jaar)
        if not storage.check_access():
            self.stdout.write('[ERROR] Geen toegang tot de drive')
            return

        file_id = storage.vind_sheet(afstand, is_teams, is_bk, fname, mag_aanmaken)
        print('file_id: %s' % repr(file_id))


# end of file
