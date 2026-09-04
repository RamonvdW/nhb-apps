# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from GraphDrive.operations import GraphSite, upload_file
import os


class Command(BaseCommand):
    help = "Upload een backup naar a Sharepoint/Teams site en begrens aantal bestanden in de backup"

    def add_arguments(self, parser):
        parser.add_argument('site_index', nargs=1, type=int, help="Welke id's gebruiken? (index in settings.GRAPH_IDS)")
        parser.add_argument('local_fpath', nargs=1, help="backup bestand dat geupload moet worden")
        parser.add_argument('remote_folder', nargs=1, help="pad naar de backup folder")

    def handle(self, *args, **options):
        local_fpath = options['local_fpath'][0]
        remote_folder = options['remote_folder'][0]

        if remote_folder[-1] != '/':
            remote_folder += '/'

        _, local_fname = os.path.split(local_fpath)
        remote_fpath = remote_folder + local_fname

        site = GraphSite(self.stdout)
        if not site.setup(options['site_index'][0]):
            return

        if not os.path.isfile(local_fpath):
            self.stdout.write('[ERROR] Kan lokaal bestand niet vinden: %s' % local_fpath)
            return

        upload_file(self.stdout, site, local_fpath, remote_fpath)

        self.stdout.write('[INFO] Done')

# end of file
