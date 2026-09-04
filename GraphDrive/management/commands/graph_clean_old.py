# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from GraphDrive.operations import GraphSite, list_folders_and_files, delete_item


class Command(BaseCommand):
    help = "Begrens het aantal bestanden in de backup folder op een Sharepoint/Teams site"

    def add_arguments(self, parser):
        parser.add_argument('site_index', nargs=1, type=int, help="Welke id's gebruiken? (index in settings.GRAPH_IDS)")
        parser.add_argument('remote_folder', nargs=1, help="pad naar de backup folder")
        parser.add_argument('limiet', nargs=1, type=int, help="maximum aantal bestanden in de folder")

    def handle(self, *args, **options):
        remote_folder = options['remote_folder'][0]
        limiet = options['limiet'][0]

        site = GraphSite(self.stdout)
        if not site.setup(options['site_index'][0]):
            return

        _, file_lijst = list_folders_and_files(self.stdout, site, remote_folder)

        if len(file_lijst) < limiet:
            self.stdout.write('[INFO] Niets te verwijderen (er zijn %s bestanden)' % len(file_lijst))
            return

        file_lijst.sort()       # oudste eerst

        # verwijder altijd maximaal 5 van de bestanden
        remove_count = 0
        while len(file_lijst) > limiet and remove_count < 5:
            # verwijder oudste bestand
            _, _, naam, item_id = file_lijst.pop(0)
            self.stdout.write('[INFO] Verwijder oudste bestand: %s' % naam)
            delete_item(self.stdout, site, item_id)
            remove_count += 1
        # while

# end of file
