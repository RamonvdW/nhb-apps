# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# zorg dat alle nhblid-boogtype maar 1x voorkomen in de database

from django.core.management.base import BaseCommand
from Schutter.models import SchutterBoog


class Command(BaseCommand):
    help = "Verwijder dubbele schutterboog"

    def handle(self, *args, **options):
        present = list()
        for obj in SchutterBoog.objects.select_related('nhblid', 'boogtype').all():
            tup = (obj.nhblid.nhb_nr, obj.boogtype.afkorting)
            if tup not in present:
                present.append(tup)
            else:
                # this is a dupe
                print("Deleting dupe: %s" % obj)
                obj.delete()
        # for


# end of file

