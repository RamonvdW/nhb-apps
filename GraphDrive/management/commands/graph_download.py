# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from GraphDrive.operations import GraphSite, get_file_metadata, download_file
import pprint


class Command(BaseCommand):
    help = "Download een bestand uit Sharepoint/Teams"

    def add_arguments(self, parser):
        parser.add_argument('site_index', nargs=1, type=int, help="Welke id's gebruiken? (index in settings.GRAPH_IDS)")
        parser.add_argument('remote_fpath', nargs=1, help="volledige pad naar het Sharepoint/Teams bestand")
        parser.add_argument('local_fpath', nargs=1, help="pad waaronder het document opgelagen moet worden")

    def handle(self, *args, **options):
        remote_fpath = options['remote_fpath'][0]
        local_fpath = options['local_fpath'][0]

        site = GraphSite(self.stdout)
        if not site.setup(options['site_index'][0]):
            return

        data = get_file_metadata(self.stdout, site, remote_fpath)

        if data:
            try:
                _ = data['@microsoft.graph.downloadUrl']
            except Exception as exc:
                self.stdout.write('[ERROR] ' + repr(exc))

                out = pprint.pformat(data, indent=4)
                self.stdout.write(out)
            else:
                out_fname = download_file(self.stdout, site, remote_fpath, local_fpath)
                if out_fname:
                    self.stdout.write('[INFO] Download gelukt naar %s' % repr(out_fname))

# end of file
