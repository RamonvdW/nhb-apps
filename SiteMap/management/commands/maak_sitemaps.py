# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import apps
from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand
from Mailer.operations import mailer_notify_internal_error
from SiteMap.models import SiteMapLastMod
import traceback
import logging
import hashlib
import sys
import os

my_logger = logging.getLogger('MH.SiteMaps')


class Command(BaseCommand):

    help = "Maak sitemaps"

    # TODO: Opleidingen

    """
        SiteMaps bestaan uit XML files
        Spec: https://www.sitemaps.org/protocol.html
        
        We hebben een sitemap index en aparte sitemaps voor:
            - Plein             (bevat ook login en registreer)
            - Records
            - Webwinkel
            - Kalender
            - Wedstrijden
            - Evenementen
            - Bondscompetities  (bevat ook histcomp)
            
        Elke applicatie kan een plugin_sitemap.py bevatten voor een sitemap generator met een functie generate_urls()
        die een URL's yield in de vorm: change_freq, url waarbij change_freq uit SiteMap.definities komt. 
    """

    def __init__(self):
        super().__init__()
        self.sitemaps_dir = '/tmp/'
        self.all_sitemaps = dict()      # [fname] = last_mod
        self._exit_code = 0

    def add_arguments(self, parser):
        parser.add_argument('sitemaps_dir', nargs=1, help="In deze directory de sitemaps aanmaken")

    @staticmethod
    def calculate_hash(app_name, urls: list) -> str:
        calc = hashlib.md5()
        calc.update(app_name.encode())
        for url in urls:
            calc.update(url.encode())
        # for
        digest = calc.hexdigest()
        return digest

    def write_sitemap_index(self):
        fname = 'sitemaps.xml'
        fpath = os.path.join(self.sitemaps_dir, fname)
        self.stdout.write('[INFO] Generating sitemap index %s' % fpath)

        with open(fpath, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')

            for fname, last_mod in self.all_sitemaps.items():
                loc = settings.SITE_URL + '/sitemaps/%s' % fname

                # last_mod must be W3C Datetime format: 2024-01-30T18:19:20Z (Z means +00:00)
                last_mod_str = last_mod.strftime('%Y-%m-%dT%H:%M:%SZ')
                f.write(' <sitemap>\n')
                f.write('  <loc>%s</loc>\n' % loc)
                f.write('  <lastmod>%s</lastmod>\n' % last_mod_str)
                f.write(' </sitemap>\n')
            # for

            f.write('</sitemapindex>\n')
        # with

    def write_sitemap_file(self, fname, last_mod, tups):
        self.all_sitemaps[fname] = last_mod

        fpath = os.path.join(self.sitemaps_dir, fname)
        self.stdout.write('[INFO] Generating sitemap %s' % fpath)

        with open(fpath, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            for change_frequency, url in tups:
                loc = settings.SITE_URL + url
                f.write(' <url>\n')
                f.write('  <loc>%s</loc>\n' % loc)
                # f.write('  <priority>%s</priority>\n' % priority)
                f.write('  <changefreq>%s</changefreq>\n' % change_frequency)
                f.write(' </url>\n')
            f.write('</urlset>\n')
        # with

    def generate_sitemaps(self):
        # doorloop alle apps en probeer de plugin_sitemap.py module te laden
        now = timezone.now()

        for app in apps.get_app_configs():
            try:
                plugin = __import__(app.name + '.plugin_sitemap').plugin_sitemap
            except ImportError:
                pass
            else:
                # self.stdout.write('[DEBUG] app %s has sitemap plugin' % repr(app.name))

                tups = [tup for tup in plugin.generate_urls()]
                urls = [tup[-1] for tup in tups]
                digest = self.calculate_hash(app.name, urls)
                # print('  digest: %s' % digest)
                fname = 'sitemap-%s.xml' % app.name.lower()

                last_mod = SiteMapLastMod.objects.filter(app_name=app.name).first()
                if not last_mod:
                    # first time
                    last_mod = SiteMapLastMod(app_name=app.name, md5_digest='')

                if last_mod.md5_digest != digest:
                    # update the last modification date
                    last_mod.md5_digest = digest
                    last_mod.last_mod = now
                    last_mod.save()
                    self.stdout.write('[INFO] New last_mod for sitemap %s' % fname)

                self.write_sitemap_file(fname, last_mod.last_mod, tups)

                del plugin
        # for

        self.write_sitemap_index()

    def handle(self, *args, **options):
        self.sitemaps_dir = options['sitemaps_dir'][0]

        try:
            self.generate_sitemaps()
        except Exception as exc:

            # schrijf in de output
            tups = sys.exc_info()
            lst = traceback.format_tb(tups[2])
            tb = traceback.format_exception(*tups)

            tb_msg_start = 'Unexpected error during maak_sitemaps\n'
            tb_msg_start += '\n'
            tb_msg = tb_msg_start + '\n'.join(tb)

            # full traceback to syslog
            my_logger.error(tb_msg)

            self.stderr.write('[ERROR] Onverwachte fout tijdens maak_sitemaps: ' + str(exc))
            self.stderr.write('Traceback:')
            self.stderr.write(''.join(lst))

            # stuur een mail naar de ontwikkelaars
            # reduceer tot de nuttige regels
            tb = [line for line in tb if '/site-packages/' not in line]
            tb_msg = tb_msg_start + '\n'.join(tb)

            # deze functie stuurt maximaal 1 mail per dag over hetzelfde probleem
            self.stdout.write('[WARNING] Stuur crash mail naar ontwikkelaar')
            mailer_notify_internal_error(tb_msg)

            self._exit_code = 1

        if self._exit_code > 0:
            sys.exit(self._exit_code)

# end of file
