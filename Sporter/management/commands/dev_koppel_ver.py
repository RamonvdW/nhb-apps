# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# koppel een Sporter aan een vereniging, vanaf de command-line
# wordt gebruikt voor dev testen, na het opzetten van een lege database

from django.utils import timezone
from django.core.management.base import BaseCommand
from NhbStructuur.models import NhbVereniging
from Sporter.models import Sporter


class Command(BaseCommand):
    help = "Koppel een sporter aan een vereniging"

    def add_arguments(self, parser):
        parser.add_argument('lid_nr', nargs=1,
                            help="Sporter lidnummer")

        parser.add_argument('ver_nr', nargs=1,
                            help="Verenigingsnummer")

    def handle(self, *args, **options):
        lid_nr = options['lid_nr'][0]
        ver_nr = options['ver_nr'][0]

        try:
            ver = NhbVereniging.objects.get(ver_nr=ver_nr)
        except NhbVereniging.DoesNotExist:
            self.stderr.write('Vereniging %s niet gevonden' % repr(ver_nr))
        else:
            try:
                lid = Sporter.objects.get(lid_nr=lid_nr)
            except (Sporter.DoesNotExist, ValueError):
                self.stderr.write('Sporter met lid_nr %s niet gevonden' % repr(lid_nr))
            else:
                lid.bij_vereniging = ver
                lid.is_actief_lid = True
                lid.lid_tot_einde_jaar = timezone.now().year
                lid.save(update_fields=['bij_vereniging', 'is_actief_lid', 'lid_tot_einde_jaar'])

                self.stdout.write('Sporter %s gekoppeld aan vereniging %s' % (lid_nr, ver_nr))

# end of file
