# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
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

    def __init__(self):
        super().__init__()

        self.fotos_used = dict()     # [pk] = WebwinkelProduct
        self.aantal_nok = 0
        self.aantal_ok = 0

    def _check_foto_gebruik(self, product, foto, veld='omslag_foto'):
        try:
            product2 = self.fotos_used[foto.pk]
        except KeyError:
            self.fotos_used[foto.pk] = product
        else:
            self.stderr.write('[WARNING] Product pk=%s (%s) %s wordt ook gebruikt door product pk=%s' % (
                product.pk, product, veld, product2.pk))

    def _check_foto_bestand(self, foto, veld):
        locatie = getattr(foto, veld)
        if not locatie:
            self.stderr.write('[ERROR] Foto pk=%s heeft een lege %s' % (foto.pk, veld))
            self.aantal_nok += 1
        else:
            foto_pad = os.path.join(settings.WEBWINKEL_FOTOS_DIR, locatie)
            if os.path.exists(foto_pad):
                self.aantal_ok += 1
            else:
                self.stderr.write('[ERROR] Foto pk=%s %s bestand niet gevonden: %s' % (foto.pk, veld, repr(foto_pad)))
                self.aantal_nok += 1

    def handle(self, *args, **options):
        for product in WebwinkelProduct.objects.select_related('omslag_foto').prefetch_related('fotos').order_by('pk'):

            foto = product.omslag_foto
            if foto:
                self._check_foto_gebruik(product, foto, 'locatie')
                self._check_foto_bestand(foto, 'locatie')
            elif product.kleding_maat == '':
                self.stdout.write('[WARNING] Product pk=%s (%s) heeft geen omslagfoto' % (product.pk,
                                                                                          product.omslag_titel))
                self.aantal_nok += 1

            nr = 0
            for foto in product.fotos.all():
                nr += 1
                veld = 'fotos[%s]' % nr
                self._check_foto_gebruik(product, foto, veld)
                self._check_foto_bestand(foto, 'locatie')
                self._check_foto_bestand(foto, 'locatie_thumb')
        # for

        # rapporteer ongebruikte fotos
        for foto in WebwinkelFoto.objects.all():
            if foto.pk not in self.fotos_used.keys():
                self.stdout.write('[WARNING] Foto pk=%s (%s) wordt niet (meer) gebruikt' % (foto.pk, foto))

                # kan een omslagfoto zijn, dus alleen locatie checken en niet de thumb
                self._check_foto_bestand(foto, 'locatie')
        # for

        if self.aantal_nok:
            self.stdout.write("[INFO] %s foto's OK" % self.aantal_ok)
            self.stderr.write("[ERROR] %s foto's NOK" % self.aantal_nok)
            sys.exit(1)

        # alles goed
        self.stdout.write("[INFO] %s foto's OK; no problems found" % self.aantal_ok)

# end of file

