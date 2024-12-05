# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Instaptoets vragen inladen uit een CSV file (export van Google Sheets) """

from django.core.management.base import BaseCommand
from Instaptoets.models import Vraag
from difflib import SequenceMatcher
import csv


class Command(BaseCommand):
    help = "Importeer alle vragen van de instaptoets"

    def __init__(self):
        super().__init__()
        self.dryrun = False

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, help="in te lezen bestand")
        parser.add_argument('--dryrun', action='store_true')

    def _vind_of_maak_vraag(self, v, a, b, c, d):
        # kijk of de vraag te vinden is:
        vraag = Vraag.objects.filter(vraag_tekst=v, antwoord_a=a, antwoord_b=b, antwoord_c=c, antwoord_d=d).first()
        if vraag:
            # geen wijziging
            # self.stdout.write('[INFO] Vraag pk=%s: geen wijziging' % vraag.pk)
            return vraag

        vraag = Vraag.objects.filter(vraag_tekst=v, antwoord_b=b, antwoord_c=c, antwoord_d=d).first()
        if vraag:
            # antwoord A is aangepast
            self.stdout.write('[INFO] Vraag pk=%s: antwoord A is aangepast' % vraag.pk)
            return vraag

        vraag = Vraag.objects.filter(vraag_tekst=v, antwoord_a=a, antwoord_c=c, antwoord_d=d).first()
        if vraag:
            # antwoord B is aangepast
            self.stdout.write('[INFO] Vraag pk=%s: antwoord B is aangepast' % vraag.pk)
            return vraag

        vraag = Vraag.objects.filter(vraag_tekst=v, antwoord_a=a, antwoord_b=b, antwoord_d=d).first()
        if vraag:
            # antwoord C is aangepast
            self.stdout.write('[INFO] Vraag pk=%s: antwoord C is aangepast' % vraag.pk)
            return vraag

        vraag = Vraag.objects.filter(vraag_tekst=v, antwoord_a=a, antwoord_b=b, antwoord_c=c).first()
        if vraag:
            # antwoord D is aangepast
            self.stdout.write('[INFO] Vraag pk=%s: antwoord D is aangepast' % vraag.pk)
            return vraag

        vraag = Vraag.objects.filter(vraag_tekst=v).first()
        if vraag:
            # alle antwoorden zijn aangepast
            self.stdout.write('[INFO] Vraag pk=%s: alle antwoorden zijn aangepast' % vraag.pk)
            return vraag

        vraag = Vraag.objects.filter(antwoord_a=a, antwoord_b=b, antwoord_c=c, antwoord_d=d).first()
        if vraag:
            s = SequenceMatcher(a=vraag.vraag_tekst, b=v)
            ratio = s.ratio()
            if ratio >= 0.75:
                # vraag tekst is aanpast, of dit is een vraag met triviale antwoorden (goed/fout/-/-)
                self.stdout.write('[INFO] Vraag pk=%s: vraag is aangepast' % vraag.pk)
                return vraag
            self.stdout.write('[INFO] Matching ratio on pk=%s is %s' % (vraag.pk, ratio))

        return None

    def handle(self, *args, **options):
        self.dryrun = options['dryrun']

        # lees de file in
        fname = options['filename'][0]
        try:
            with open(fname) as csvfile:
                vraag_pks = list(Vraag.objects.values_list('pk', flat=True))
                self.stdout.write('[INFO] Aantal vragen was %s' % len(vraag_pks))

                skip_header = True
                for row in csv.reader(csvfile):
                    if not skip_header:
                        # self.stdout.write('regel: %s' % repr(row))
                        v, a, b, c, d, j = row
                        if d == '-':
                            d = ''
                        if c == '-':
                            c = ''

                        vraag = self._vind_of_maak_vraag(v, a, b, c, d)

                        if not vraag:
                            # maak een nieuwe vraag aan:
                            vraag = Vraag()

                        vraag.vraag_tekst = v
                        vraag.antwoord_a = a
                        vraag.antwoord_b = b
                        vraag.antwoord_c = c
                        vraag.antwoord_d = d
                        vraag.juiste_antwoord = j
                        vraag.save()        # wijzigingen of nieuw

                        if vraag.pk in vraag_pks:
                            vraag_pks.remove(vraag.pk)
                    skip_header = False
                # for

                if vraag_pks:
                    self.stdout.write('[INFO] Verouderde vragen: pks=%s' % repr(vraag_pks))

                self.stdout.write('[INFO] Aantal vragen is nu %s' % Vraag.objects.count())
        except IOError as exc:
            self.stderr.write("[ERROR] Kan bestand %s niet lezen (%s)" % (fname, str(exc)))
            return

        self.stdout.write('Done')

# end of file
