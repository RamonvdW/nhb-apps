# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Instaptoets vragen inladen uit een Excel bestand """

from django.core.management.base import BaseCommand
from Instaptoets.models import Vraag, Categorie
from openpyxl.utils.exceptions import InvalidFileException
import traceback
import openpyxl
import logging
import sys

my_logger = logging.getLogger('MH.import_instaptoets')


class Command(BaseCommand):
    help = "Importeer alle vragen van de instaptoets"

    def __init__(self):
        super().__init__()
        self.dryrun = False
        self.verbose = False
        self.vraag_pks = list()

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, help="in te lezen bestand")
        parser.add_argument('--dryrun', action='store_true')
        parser.add_argument('--verbose', action='store_true')

    def _lees_regel(self, ws, row_nr):
        regel = list()
        try:
            row = ws[row_nr]
        except IndexError:
            # regel bestaat niet
            regel = [None] * 8
        else:
            for col_nr in range(8):
                cell = row[col_nr]
                regel.append(cell.value)
            # for

        if self.verbose:
            self.stdout.write('[DEBUG] Regel %s: %s' % (row_nr, repr(regel)))
        return regel

    def _vind_of_maak_vraag(self, v, a, b, c, d):
        # kijk of de vraag te vinden is
        qset = (Vraag
                .objects
                .filter(pk__in=self.vraag_pks,
                        vraag_tekst=v,
                        antwoord_a=a,
                        antwoord_b=b,
                        antwoord_c=c,
                        antwoord_d=d))
        vraag = qset.first()

        # aangepaste vraag = nieuwe vraag
        # dat is beter voor de statistiek over het beantwoorden van de vraag

        return vraag

    def _import_categorie(self, ws, row_nr):
        # lees alle vragen in op deze pagina, vanaf row_nr+1
        categorie = ws.title
        self.stdout.write('[INFO] Import categorie %s' % repr(categorie))
        cat, _ = Categorie.objects.get_or_create(beschrijving=categorie)

        while row_nr < 100:     # pragma: no branch
            row_nr += 1
            regel = self._lees_regel(ws, row_nr)

            if regel.count(None) > 7:
                # einde van het sheet gevonden
                break   # from the while

            if len(regel) < 8 or regel.count(None) > 4:
                self.stdout.write('[WARNING] Incomplete vraag wordt overgeslagen: %s' % repr(regel))
                continue

            # v       = vraag
            # a,b,c,d = antwoorden
            # j       = juiste antwoord
            # t,q     = gebruik voor toets, quiz
            v, a, b, c, d, j, t, q = regel[:8]
            if d == '-' or d is None:
                d = ''
            if c == '-' or c is None:
                c = ''

            vraag = self._vind_of_maak_vraag(v, a, b, c, d)

            if vraag:
                self.vraag_pks.remove(vraag.pk)

                # een paar velden mogen aangepast worden
                vraag.juiste_antwoord = j
                vraag.gebruik_voor_toets = t.upper() in ('J', 'JA')
                vraag.gebruik_voor_quiz = q.upper() in ('J', 'JA')
                vraag.save()  # wijzigingen of nieuw

            else:
                # geen vraag gevonden
                # maak een nieuwe vraag aan
                vraag = Vraag.objects.create(
                            categorie=cat,
                            vraag_tekst=v,
                            antwoord_a=a,
                            antwoord_b=b,
                            antwoord_c=c,
                            antwoord_d=d,
                            juiste_antwoord=j,
                            gebruik_voor_toets=t.upper() in ('J', 'JA'),
                            gebruik_voor_quiz=q.upper() in ('J', 'JA'))
                self.stdout.write('[WARNING] Nieuwe vraag met pk %s' % vraag.pk)
        # for

    def _import_data(self, wb: openpyxl.Workbook):
        """ data bestaat sheets in de vorm van een dictionary """
        for ws in wb.worksheets:
            self.stdout.write('[INFO] Found sheet %s' % repr(ws.title))

            # check de headers
            found = False
            row_nr = 0
            while row_nr < 20 and not found:
                row_nr += 1
                regel = self._lees_regel(ws, row_nr)

                if regel[0:8] == ['Vraagtekst', 'Antwoord A', 'Antwoord B', 'Antwoord C', 'Antwoord D', 'Juiste antwoord', 'Toets', 'Quiz']:
                    self._import_categorie(ws, row_nr)
                    found = True
            # for

            if not found:
                self.stderr.write('[ERROR] Kan correcte header niet vinden. Geen vragen ingelezen voor deze categorie.')
        # for

    def handle(self, *args, **options):
        self.dryrun = options['dryrun']
        if options['verbose']:
            self.verbose = True
        fname = options['filename'][0]

        # lees het excel bestand met alle records
        try:
            wb = openpyxl.load_workbook(fname, read_only=True)
        except (IOError,  InvalidFileException) as exc:
            self.stderr.write("[ERROR] Kan bestand %s niet lezen (%s)" % (repr(fname), str(exc)))
            return

        self.vraag_pks = list(Vraag.objects.values_list('pk', flat=True))
        self.stdout.write('[INFO] Aantal vragen was %s' % len(self.vraag_pks))

        try:
            self._import_data(wb)

        except Exception as exc:        # pragma: no cover
            # schrijf in de output
            tups = sys.exc_info()
            lst = traceback.format_tb(tups[2])
            tb = traceback.format_exception(*tups)

            tb_msg_start = 'Onverwachte fout tijdens import_instaptoets\n'
            tb_msg_start += '\n'
            tb_msg = tb_msg_start + '\n'.join(tb)

            # full traceback to syslog
            my_logger.error(tb_msg)

            self.stdout.write('Onverwachte fout (%s): %s' % (type(exc), str(exc)))
            self.stdout.write('Traceback:')
            self.stdout.write(''.join(lst))

        else:
            if self.vraag_pks:
                self.stdout.write('[INFO] Verouderde vragen: pks=%s' % repr(self.vraag_pks))
                self.stdout.write('[WARNING] Deze vragen worden buiten gebruik genomen')
                Vraag.objects.filter(pk__in=self.vraag_pks).update(gebruik_voor_quiz=False, gebruik_voor_toets=False)

            self.stdout.write('[INFO] Aantal vragen is nu %s' % Vraag.objects.count())
            self.stdout.write('[INFO] %s voor de toets' % Vraag.objects.filter(gebruik_voor_toets=True).count())
            self.stdout.write('[INFO] %s voor de quiz' % Vraag.objects.filter(gebruik_voor_quiz=True).count())

        self.stdout.write('Done')


# end of file
