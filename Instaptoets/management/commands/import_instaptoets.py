# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Instaptoets vragen inladen uit een Excel bestand """

from django.core.management.base import BaseCommand
from Instaptoets.models import Vraag, Categorie
from difflib import SequenceMatcher
from openpyxl.utils.exceptions import InvalidFileException
import openpyxl


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

    @staticmethod
    def _remove_newlines(v):
        return v.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')

    def _lees_regel(self, ws, row_nr):
        row = ws[row_nr]
        regel = list()
        for col_nr in range(8):
            cell = row[col_nr]
            regel.append(cell.value)
        # for
        if self.verbose:
            self.stdout.write('[DEBUG] Regel %s: %s' % (row_nr, repr(regel)))
        return regel

    def _vind_of_maak_vraag(self, v, a, b, c, d):
        # kijk of de vraag te vinden is:
        qset = Vraag.objects.filter(pk__in=self.vraag_pks)

        vraag = qset.filter(vraag_tekst=v, antwoord_a=a, antwoord_b=b, antwoord_c=c, antwoord_d=d).first()
        if vraag:
            # geen wijziging
            # self.stdout.write('[WARNING] Vraag pk=%s: geen wijziging' % vraag.pk)
            return vraag

        vraag = qset.filter(vraag_tekst=v,               antwoord_b=b, antwoord_c=c, antwoord_d=d).first()
        if vraag:
            # antwoord A is aangepast
            self.stdout.write('[WARNING] Vraag pk=%s: antwoord A is aangepast' % vraag.pk)
            return vraag

        vraag = qset.filter(vraag_tekst=v, antwoord_a=a,               antwoord_c=c, antwoord_d=d).first()
        if vraag:
            # antwoord B is aangepast
            self.stdout.write('[WARNING] Vraag pk=%s: antwoord B is aangepast' % vraag.pk)
            return vraag

        vraag = qset.filter(vraag_tekst=v, antwoord_a=a, antwoord_b=b,               antwoord_d=d).first()
        if vraag:
            # antwoord C is aangepast
            self.stdout.write('[WARNING] Vraag pk=%s: antwoord C is aangepast' % vraag.pk)
            return vraag

        vraag = qset.filter(vraag_tekst=v, antwoord_a=a, antwoord_b=b, antwoord_c=c              ).first()
        if vraag:
            # antwoord D is aangepast
            self.stdout.write('[WARNING] Vraag pk=%s: antwoord D is aangepast' % vraag.pk)
            return vraag

        vraag = qset.filter(vraag_tekst=v).first()
        if vraag:
            # alle antwoorden zijn aangepast
            self.stdout.write('[WARNING] Vraag pk=%s: alle antwoorden zijn aangepast' % vraag.pk)
            self.stdout.write('[DEBUG] Vraag: %s' % repr(v))
            return vraag

        options = list()
        for vraag in qset.filter(antwoord_a=a, antwoord_b=b, antwoord_c=c, antwoord_d=d):
            print('option:', vraag)
            s = SequenceMatcher(a=vraag.vraag_tekst, b=v)
            ratio = s.ratio()
            if ratio >= 0.75:
                tup = (ratio, vraag)
                options.append(tup)
        # for

        if len(options) > 1:
            options.sort()
            for option in options:
                print(option)
            krak        # is sorting in the correct order?

        if len(options) == 1:
            # vraag tekst is aanpast, of dit is een vraag met triviale antwoorden (goed/fout/-/-)
            ratio, vraag = options[0]
            self.stdout.write('[WARNING] Vraag pk=%s (ratio=%.2f): vraag is aangepast' % (vraag.pk, ratio))
            return vraag

        return None

    def _import_categorie(self, ws, row_nr):
        # lees alle vragen in op deze pagina, vanaf row_nr+1
        categorie = ws.title
        self.stdout.write('[INFO] Import categorie %s' % repr(categorie))
        cat, _ = Categorie.objects.get_or_create(beschrijving=categorie)

        while row_nr < 100:
            row_nr += 1
            regel = self._lees_regel(ws, row_nr)

            if regel.count(None) > 7:
                # einde van het sheet gevonden
                break   # from the while

            if regel.count(None) > 4:
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

            #v = self._remove_newlines(v)

            vraag = self._vind_of_maak_vraag(v, a, b, c, d)

            if vraag:
                if vraag.pk in self.vraag_pks:
                    self.vraag_pks.remove(vraag.pk)
                else:
                    self.stdout.write('[WARNING] Vraag pk %s is al eerder gebruikt' % vraag.pk)
                    self.stdout.write('[DEBUG] Regel: %s' % repr(regel))

                vraag.categorie = cat
                vraag.vraag_tekst = v
                vraag.antwoord_a = a
                vraag.antwoord_b = b
                vraag.antwoord_c = c
                vraag.antwoord_d = d
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
        except (IOError, InvalidFileException) as exc:
            self.stdout.write("[ERROR] Kan bestand %s niet lezen (%s)" % (fname, str(exc)))
            return

        self.vraag_pks = list(Vraag.objects.values_list('pk', flat=True))
        self.stdout.write('[INFO] Aantal vragen was %s' % len(self.vraag_pks))

        self._import_data(wb)

        if self.vraag_pks:
            self.stdout.write('[INFO] Verouderde vragen: pks=%s' % repr(self.vraag_pks))
            self.stdout.write('[WARNING] Deze vragen worden buiten gebruik genomen')
            Vraag.objects.filter(pk__in=self.vraag_pks).update(gebruik_voor_quiz=False, gebruik_voor_toets=False)

        self.stdout.write('[INFO] Aantal vragen is nu %s' % Vraag.objects.count())
        self.stdout.write('[INFO] %s voor de toets' % Vraag.objects.filter(gebruik_voor_toets=True).count())
        self.stdout.write('[INFO] %s voor de quiz' % Vraag.objects.filter(gebruik_voor_quiz=True).count())

        self.stdout.write('Done')


# end of file
