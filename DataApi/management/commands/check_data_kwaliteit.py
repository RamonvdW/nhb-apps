# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" controleert de kwaliteit van de opgeslagen data """

from django.core.management.base import BaseCommand
from DataApi.models import DataApiVereniging, DataApiLidmaatschap


class Command(BaseCommand):

    help = "Controleert de kwaliteit van de opgelsagen data"

    def __init__(self):
        super().__init__()
        self.count_errors = 0
        self.count_warnings = 0
        self.count_postcode_issue = 0

    def add_arguments(self, parser):
        # parser.add_argument('--dryrun', action='store_true')
        pass

    def _check_no_lms_on_ver(self, ver: DataApiVereniging):
        lms_actief = list()
        lms_later_afgemeld = list()
        for lms in DataApiLidmaatschap.objects.filter(ver_nr=ver.ver_nr):
            if lms.afmeld_datum == '':
                lms_actief.append(lms)
            elif lms.afmeld_datum > ver.afmeld_datum:
                lms_later_afgemeld.append(lms)
        # for

        if len(lms_actief):
            self.stdout.write('[ERROR] Vereniging %s is afgemeld per %s maar heeft nog %s lidmaatschappen:' % (ver.ver_nr, ver.afmeld_datum, len(lms_actief)))
            self.count_errors += 1
            for lms in lms_actief:
                self.stdout.write('        %s' % lms)
            # for

        if len(lms_later_afgemeld):
            self.stdout.write('[WARNING] Vereniging %s is afgemeld per %s maar %s lidmaatschappen lopen langer door:' % (ver.ver_nr, ver.afmeld_datum, len(lms_later_afgemeld)))
            self.count_warnings += 1
            for lms in lms_later_afgemeld:
                self.stdout.write('        %s' % lms)
            # for

    def _check_ver(self):
        self.stdout.write('[INFO] Controleer alle verenigingen')
        for ver in DataApiVereniging.objects.all():
            if ver.afmeld_datum != '':
                # vereniging is niet meer actief
                # alle lidmaatschappen moeten voor deze datum geeindigd zijn
                self._check_no_lms_on_ver(ver)
        # for

    def _check_lms(self):
        self.stdout.write('[INFO] Controleer alle lidmaatschappen')
        ver_nr2ver = dict()
        for ver in DataApiVereniging.objects.all():
            ver_nr2ver[ver.ver_nr] = ver
        # for

        lid_nr2lms = dict()
        for lms in DataApiLidmaatschap.objects.all():
            if lms.afmeld_datum == '':
                # dit is een actief lidmaatschap
                other_lms = lid_nr2lms.get(lms.lid_nr, None)
                if other_lms:
                    self.stdout.write('[ERROR] Lid %s heeft meerdere actieve lms:\n%s\n%s' % (lms.lid_nr, other_lms, lms))
                    self.count_errors += 1
                else:
                    lid_nr2lms[lms.lid_nr] = lms

            ver = ver_nr2ver.get(lms.ver_nr, None)
            if not ver:
                self.stdout.write('[ERROR] Onbekende vereniging %s voor lms %s' % (lms.ver_nr, lms))
                self.count_errors += 1

            if lms.land_iso not in ('NL', 'BE', 'DE', 'LU', 'AE', 'AT', 'CH', 'HU', 'GB', 'SE', 'NO'):
                self.stdout.write('[WARNING] Onverwachte land code: %s in %s' % (repr(lms.land_iso), lms))
                self.count_postcode_issue += 1

            if lms.land_iso == 'NL':
                if len(lms.postcode) != 6:
                    self.stdout.write('[WARNING] Niet standaard postcode %s (land %s) voor %s' % (repr(lms.postcode), lms.land_iso, lms))
                    self.count_postcode_issue += 1
        # for

    def handle(self, *args, **options):
        # self.dryrun = options['dryrun']

        # don't turn these signal into exceptions (just exit process)
        import signal
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

        self._check_ver()
        self._check_lms()

        self.stdout.write('%s errors, %s warnings, %s postcode issues' % (self.count_errors,
                                                                          self.count_warnings,
                                                                          self.count_postcode_issue))

        self.stdout.write('Done')

# end of file
