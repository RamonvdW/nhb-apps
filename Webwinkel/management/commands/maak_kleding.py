# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# stel de foto's in voor een product in de webwinkel

from django.core import management
from django.core.management.base import BaseCommand
from Webwinkel.models import WebwinkelProduct
import io


class Command(BaseCommand):

    help = "Maak de webwinkel kleding producten aan de hand van definities uit een bestand"

    def __init__(self):
        super().__init__()

    def add_arguments(self, parser):
        parser.add_argument('bestand', type=str, help='Volledig pad naar het bestand met de definities')

    def _run_command(self, *args):

        args = [arg for arg in args if arg is not None]

        self.stdout.write('[INFO] Running command %s' % repr(args))

        f1 = io.StringIO()
        f2 = io.StringIO()

        bad = False
        try:
            management.call_command(*args, stderr=f1, stdout=f2)
        except SystemExit as exc:
            self.stdout.write('[WARNING] Exception "%s" from command %s' % (str(exc), repr(args)))
            bad = True

        msg = f2.getvalue() + '\n' + f1.getvalue()
        for line in msg.split('\n'):
            if line:
                self.stdout.write('  ' + line)
        # for

        return bad

    def handle(self, *args, **options):
        fname = options['bestand']

        product = WebwinkelProduct()

        self.stdout.write('[INFO] Lees bestand %s' % repr(fname))
        with open(fname, 'r') as f:
            for line in f.readlines():
                line = line.strip()     # remove newline
                if line and line[0] != '#':
                    # self.stdout.write(repr(line))
                    pos = line.find('=')
                    if pos > 0:
                        keyword = line[:pos]
                        line = line[pos+1:]
                    else:
                        keyword = line
                        line = ''

                    if keyword == 'Delete':
                        spl = line.split('-')
                        nr_from = int(spl[0])
                        nr_last = int(spl[1])
                        nrs = [nr for nr in range(nr_from, nr_last+1)]
                        # self.stdout.write('[INFO] Deleting producten met volgorde in %s' % repr(nrs))
                        WebwinkelProduct.objects.filter(volgorde__in=nrs).delete()

                    elif keyword == 'Volgorde':
                        volgorde = int(line)
                        product.volgorde = volgorde

                    elif keyword == 'OmslagTitel':
                        product.omslag_titel = line

                    elif keyword == 'Maat':
                        product.kleding_maat = line

                    elif keyword == 'Voorraad':
                        product.aantal_op_voorraad = int(line)

                    elif keyword == 'Prijs':
                        product.prijs_euro = line

                    elif keyword == 'Sectie':
                        product.sectie = line

                    elif keyword == 'SectieSub':
                        product.sectie_subtitel = line

                    elif keyword == 'Beschrijving':
                        product.beschrijving = line

                    elif keyword == 'Bestelbegrenzing':
                        # voorbeeld: 1-3
                        product.bestel_begrenzing = line

                    elif keyword == 'Save':
                        self.stdout.write('[INFO] Maak product %s: %s (%s)' % (product.volgorde,
                                                                               product.omslag_titel,
                                                                               product.kleding_maat))

                        product.pk = None
                        product.omslag_foto = None
                        product.save()
                        product.fotos.clear()
                        product.volgorde += 1

                    elif keyword == 'KoppelFotos':
                        # gebruik koppel_fotos cli, want die maakt ook de thumbs
                        fnames = line.split(' ')
                        self._run_command('koppel_fotos', product.omslag_titel, *fnames)

                    else:
                        self.stdout.write('[ERROR] Onbekend keyword=%s, line=%s' % (repr(keyword), repr(line)))

            # for
        # with

# end of file

