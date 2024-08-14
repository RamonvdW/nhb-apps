# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# stel de foto's in voor een product in de webwinkel

from django.conf import settings
from django.core.management.base import BaseCommand
from Webwinkel.definities import THUMB_SIZE
from Webwinkel.models import WebwinkelProduct, WebwinkelFoto
from PIL import Image, UnidentifiedImageError
import sys
import os


class Command(BaseCommand):
    help = "Koppel de foto's aan een webwinkel product"
    verbose = False

    def add_arguments(self, parser):
        parser.add_argument('omslag_titel', nargs=1, help="Omslag titel van het (bestaande) product")
        parser.add_argument('foto_locatie', type=str, nargs="+", action='store',
                            help="Locatie van het foto bestanden (1e = omslag)")

    def handle(self, *args, **options):
        # controleer dat de foto's bestaan
        bad = False
        foto_locaties = list()
        for locatie in options['foto_locatie']:
            spl = os.path.splitext(locatie)     # ('/pad/fname', '.ext')
            locatie_thumb = spl[0] + '_thumb' + spl[1]

            foto_pad = os.path.join(settings.WEBWINKEL_FOTOS_DIR, locatie)
            if os.path.exists(foto_pad):
                thumb_pad = os.path.join(settings.WEBWINKEL_FOTOS_DIR, locatie_thumb)
                tup = (locatie, foto_pad, locatie_thumb, thumb_pad)
                foto_locaties.append(tup)
            else:
                self.stderr.write('[ERROR] Kan foto niet vinden: %s' % repr(foto_pad))
                bad = True
        # for
        if bad:
            sys.exit(1)

        # zoek het product
        omslag_titel = options['omslag_titel'][0]
        self.stdout.write('[INFO] Zoek product met omslag_titel %s' % repr(omslag_titel))

        product = (WebwinkelProduct
                   .objects
                   .select_related('omslag_foto')
                   .prefetch_related('fotos')
                   .filter(omslag_titel__icontains=omslag_titel)
                   .order_by('volgorde')
                   .first())

        if not product:
            self.stderr.write('[ERROR] Product met titel %s niet gevonden' % repr(omslag_titel))
            sys.exit(2)

        self.stdout.write('[INFO] Gevonden product: %s' % str(product))

        # zoek voor elk van de foto's het bestaande WebwinkelFoto objects op
        volgorde = 0
        foto_pks = list(product.fotos.values_list('pk', flat=True))
        for locatie, foto_pad, locatie_thumb, thumb_pad in foto_locaties:
            foto, is_created = WebwinkelFoto.objects.get_or_create(locatie=locatie)

            if volgorde != foto.volgorde:
                foto.volgorde = volgorde
                foto.save(update_fields=['volgorde'])

            # de eerste foto is de omslagfoto
            if volgorde == 0:
                if product.omslag_foto != foto:
                    self.stdout.write('[INFO] Foto %s gekoppeld als omslagfoto' % repr(locatie))
                    product.omslag_foto = foto
                    product.save(update_fields=['omslag_foto'])
                else:
                    self.stdout.write('[INFO] Foto %s was al gekoppeld als omslagfoto' % repr(locatie))
            else:
                # maak een thumbnail
                self.stdout.write('[INFO] Maak thumbnail %s' % repr(locatie_thumb))
                try:
                    im = Image.open(foto_pad)
                    im.thumbnail(THUMB_SIZE)
                    im.save(thumb_pad)
                except UnidentifiedImageError as exc:
                    self.stderr.write('[ERROR] Kan thumbnail niet maken: %s' % str(exc))
                else:
                    if locatie_thumb != foto.locatie_thumb:
                        foto.locatie_thumb = locatie_thumb
                        foto.save(update_fields=['locatie_thumb'])

                    if foto.pk in foto_pks:
                        foto_pks.remove(foto.pk)
                        self.stdout.write('[INFO] Foto %s was al gekoppeld aan product' % repr(locatie))
                    else:
                        product.fotos.add(foto)
                        self.stdout.write('[INFO] Foto %s + thumb gekoppeld aan product' % repr(locatie))

            volgorde += 1
        # for

        # overgebleven foto pk's moeten verwijderd worden
        if len(foto_pks):
            self.stdout.write("[INFO] De volgende foto's worden losgekoppeld: %s" % repr(foto_pks))
            qset = WebwinkelFoto.objects.filter(pk__in=foto_pks)
            product.fotos.remove(*qset)

# end of file

