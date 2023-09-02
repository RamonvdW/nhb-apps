# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Bondspas.operations import bepaal_jaar_bondspas_en_wedstrijden, maak_bondspas_regels, maak_bondspas_jpeg_en_pdf
from Sporter.models import Sporter


class Command(BaseCommand):     # pragma: no cover

    help = "Maak bondspas pdf"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

    def add_arguments(self, parser):
        parser.add_argument('lid_nr', type=int)

    def handle(self, *args, **options):

        lid_nr = options['lid_nr']
        sporter = Sporter.objects.get(lid_nr=lid_nr)
        if sporter.is_gast:
            self.stderr.write('Geen bondspas voor gast-accounts')
            return

        jaar_pas, jaar_wedstrijden = bepaal_jaar_bondspas_en_wedstrijden()
        regels = maak_bondspas_regels(sporter, jaar_pas, jaar_wedstrijden)
        img_data, pdf_data = maak_bondspas_jpeg_en_pdf(jaar_pas, lid_nr, regels)

        pdf_naam = 'bondspas_%s.pdf' % lid_nr
        with open(pdf_naam, "wb") as f:
            f.write(pdf_data)
            f.close()

        self.stdout.write('[INFO] Gemaakt: %s' % pdf_naam)


# end of file
