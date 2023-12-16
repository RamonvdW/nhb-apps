# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Locatie.operations import ReistijdBepalen


class Command(BaseCommand):

    help = "Reistijd tabel bijwerken"

    def handle(self, *args, **options):

        bepaler = ReistijdBepalen(self.stdout, self.stderr)
        bepaler.run()


# end of file
