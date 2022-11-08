# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# stel de foto's in voor een product in de webwinkel

from django.conf import settings
from django.core.management.base import BaseCommand
from Webwinkel.models import WebwinkelProduct, WebwinkelFoto
import sys
import os


class Command(BaseCommand):
    help = "Controleer dat alle webwinkel foto's aanwezig zijn"
    verbose = False

    def handle(self, *args, **options):

        aantal_ok = 0
        aantal_nok = 0
        for foto in WebwinkelFoto.objects.all():
            if not foto.locatie:
                self.stderr.write('[ERROR] Foto pk=%s heeft een lege locatie' % foto.pk)
                aantal_nok += 1
            if not foto.locatie_thumb:
                self.stderr.write('[ERROR] Foto pk=%s heeft een lege locatie_thumb' % foto.pk)
                aantal_nok += 1

            for locatie in (foto.locatie, foto.locatie_thumb):
                if locatie:
                    foto_pad = os.path.join(settings.PROJ_DIR, settings.WEBWINKEL_FOTOS_DIR, locatie)
                    if os.path.exists(foto_pad):
                        aantal_ok += 1
                    else:
                        self.stderr.write('[ERROR] Foto pk=%s niet gevonden: %s' % (foto.pk, repr(foto_pad)))
                        aantal_nok += 1
        # for

        self.stdout.write("[INFO] %s foto's OK; %s foto's NOK" % (aantal_ok, aantal_nok))

        if aantal_nok > 0:
            sys.exit(1)

# end of file

