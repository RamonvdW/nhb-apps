# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Instaptoets vragen inladen uit een JSON file (download van Google Sheets) """

from django.core.management.base import BaseCommand
from Instaptoets.models import Vraag, Categorie
from difflib import SequenceMatcher
import json


class Command(BaseCommand):
    help = "Importeer alle vragen van de instaptoets"

    def __init__(self):
        super().__init__()
        self.dryrun = False
        self.vraag_pks = list()

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
            self.stdout.write('[DEBUG] Vraag: %s' % repr(v))
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

    def _import_categorie(self, categorie, regels):
        """ sheet / categorie bestaat uit regels """
        self.stdout.write('[INFO] Import categorie %s' % repr(categorie))
        cat, _ = Categorie.objects.get_or_create(beschrijving=categorie)

        for regel in regels:
            v, a, b, c, d, j, t, q = regel[:8]
            if d == '-':
                d = ''
            if c == '-':
                c = ''

            vraag = self._vind_of_maak_vraag(v, a, b, c, d)

            if not vraag:
                # maak een nieuwe vraag aan:
                vraag = Vraag()
            else:
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
        # for

    def _import_data(self, data):
        """ data bestaat sheets in de vorm van een dictionary """
        for sheet_name, sheet_data in data.items():
            self.stdout.write('[INFO] Found sheet %s' % repr(sheet_name))
            regels = sheet_data['valueRanges'][0]['values']
            for regel_nr in range(len(regels)):
                regel = regels[regel_nr]
                if regel[0:8] == ['Vraagtekst', 'Antwoord A', 'Antwoord B', 'Antwoord C', 'Antwoord D', 'Juiste antwoord', 'Toets', 'Quiz']:
                    self._import_categorie(sheet_name, regels[regel_nr+1:])
                    break
            # for
        # for
        return
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

    def handle(self, *args, **options):
        self.dryrun = options['dryrun']

        # lees de file in
        fname = options['filename'][0]
        try:
            with open(fname, 'rb') as jsonfile:
                data = json.load(jsonfile)
        except IOError as exc:
            self.stderr.write("[ERROR] Kan bestand %s niet lezen (%s)" % (fname, str(exc)))
            return
        except json.decoder.JSONDecodeError as exc:
            self.stderr.write("[ERROR] Probleem met het JSON formaat in bestand %s (%s)" % (repr(fname), str(exc)))
            return

        self.vraag_pks = list(Vraag.objects.values_list('pk', flat=True))
        self.stdout.write('[INFO] Aantal vragen was %s' % len(self.vraag_pks))

        self._import_data(data)

        if self.vraag_pks:
            self.stdout.write('[INFO] Verouderde vragen: pks=%s' % repr(self.vraag_pks))

        self.stdout.write('[INFO] Aantal vragen is nu %s' % Vraag.objects.count())

        self.stdout.write('Done')


# end of file
