# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from GraphDrive.operations import get_file_metadata, download
import pprint


class Command(BaseCommand):
    help = "Toon de meta-data van een gedeeld bestand vanuit Sharepoint/Teams"

    def add_arguments(self, parser):
        parser.add_argument('fpath', nargs=1, help="pad naar het bestand")

    def handle(self, *args, **options):
        fpath = options['fpath'][0]

        if '/' in fpath:
            download_fpath = fpath[fpath.rfind('/')+1:]
        else:
            download_fpath = fpath
        download_fpath = '/tmp/' + download_fpath

        data = get_file_metadata(self.stdout, fpath)

        if data:
            try:
                download_url = data['@microsoft.graph.downloadUrl']
            except Exception as exc:
                self.stdout.write('[ERROR] ' + repr(exc))

                out = pprint.pformat(data, indent=4)
                self.stdout.write(out)
            else:
                out_fname = download(self.stdout, fpath, download_fpath)
                if out_fname:
                    self.stdout.write('[INFO] Download gelukt naar %s' % repr(out_fname))

# end of file
