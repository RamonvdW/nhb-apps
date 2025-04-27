# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Locatie.operations import ReistijdBepaler
from Mailer.operations import mailer_notify_internal_error
import traceback
import logging
import sys

my_logger = logging.getLogger('MH.ReistijdBepaler')


class Command(BaseCommand):

    help = "Reistijden tabel bijwerken"

    # limiteer het aantal verzoeken per run, om hoge kosten bij ontsporing te voorkomen
    VERZOEKEN_GRENS = 150

    def __init__(self):
        super().__init__()

        self._exit_code = 0

    def handle(self, *args, **options):

        bepaler = ReistijdBepaler(self.stdout, self.stderr, self.VERZOEKEN_GRENS)

        # vang generieke fouten af
        try:
            bepaler.run()
        except Exception as exc:
            # schrijf in de output
            tups = sys.exc_info()
            lst = traceback.format_tb(tups[2])
            tb = traceback.format_exception(*tups)

            tb_msg_start = 'Unexpected error during reistijd_bijwerken\n'
            tb_msg_start += '\n'
            tb_msg = tb_msg_start + '\n'.join(tb)

            # full traceback to syslog
            my_logger.error(tb_msg)

            self.stderr.write('[ERROR] Onverwachte fout (%s) tijdens reistijd_bijwerken: %s' % (type(exc), str(exc)))
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
