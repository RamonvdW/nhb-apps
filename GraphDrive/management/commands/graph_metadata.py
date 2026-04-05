# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from GraphDrive.operations import get_file_metadata
import pprint


class Command(BaseCommand):
    help = "Toon de meta-data van een gedeeld bestand vanuit Sharepoint/Teams"

    def add_arguments(self, parser):
        parser.add_argument('fpath', nargs=1, help="pad naar het bestand")

    def handle(self, *args, **options):
        fpath = options['fpath'][0]

        data = get_file_metadata(self.stdout, fpath)

        pprint.pp(data, indent=4)

# end of file
