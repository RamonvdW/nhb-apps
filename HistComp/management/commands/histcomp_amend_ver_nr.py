# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from HistComp.models import HistCompSeizoen, HistCompRegioIndiv
from NhbStructuur.models import NhbVereniging
from openpyxl.utils.exceptions import InvalidFileException
import openpyxl
import zipfile
import sys


class Command(BaseCommand):         # pragma: no cover
    help = "Check consistentie van historische uitslag, individueel"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.dryrun = True
        self.verbose = True

    def add_arguments(self, parser):
        parser.add_argument('--dryrun', action='store_true')
        parser.add_argument('--verbose', action='store_true')
        parser.add_argument('seizoen', nargs=1, help="competitie seizoen: 20xx/20yy")
        parser.add_argument('comptype', nargs=1, choices=('18', '25'), help="competitie type: 18 of 25")
        parser.add_argument('bestand', type=str, help='Pad naar het Excel bestand')
        parser.add_argument('tabblad', type=str, help='Naam van het tabblad')
        parser.add_argument('col_lid_nr', type=str, help='Kolomletter waarin het sporter lid nummer staat')
        parser.add_argument('col_ver_nr', type=str, help='Kolomletter waarin het verenigingsnummer staat')
        parser.add_argument('col_naam', type=str, help='Kolomletter waarin de sporter naam staat')

    def handle(self, *args, **options):
        self.dryrun = options['dryrun']
        self.verbose = options['verbose']
        comp_type = options['comptype'][0]
        seizoen = options['seizoen'][0]
        fname = options['bestand']
        ws_name = options['tabblad']
        col_lid_nr = options['col_lid_nr']
        col_ver_nr = options['col_ver_nr']
        col_naam = options['col_naam']

        try:
            hist_seizoen = HistCompSeizoen.objects.get(seizoen=seizoen, comp_type=comp_type)
        except HistCompSeizoen.DoesNotExist:
            self.stderr.write('[ERROR] Historisch seizoen %s - %s niet gevonden' % (repr(seizoen), repr(comp_type)))
            return
        self.stdout.write('[INFO] Seizoen: %s' % hist_seizoen)

        self.stdout.write('[INFO] Lees bestand %s' % repr(fname))
        try:
            prg = openpyxl.load_workbook(fname,
                                         data_only=True)  # do not evaluate formulas; use last calculated values
        except (OSError, zipfile.BadZipFile, KeyError, InvalidFileException) as exc:
            self.stderr.write('[ERROR] Kan het excel bestand niet openen (%s)' % str(exc))
            return

        try:
            ws = prg[ws_name]
        except KeyError:        # pragma: no cover
            self.stderr.write('[ERROR] Kan tabblad %s niet vinden' % repr(ws_name))
            return

        lid_nr2indiv = dict()
        for indiv in HistCompRegioIndiv.objects.filter(seizoen=hist_seizoen):
            try:
                lid_nr2indiv[indiv.sporter_lid_nr].append(indiv)
            except KeyError:
                lid_nr2indiv[indiv.sporter_lid_nr] = [indiv]
        # for

        ver_nr2naam = dict()
        ver_nr2plaats = dict()
        for ver in NhbVereniging.objects.all():
            ver_nr2naam[ver.ver_nr] = ver.naam
            ver_nr2plaats[ver.ver_nr] = ver.plaats
        # for

        row_nr = 2 - 1      # skip header
        while row_nr < 5000:
            row_nr += 1
            row_str = str(row_nr)

            lid_nr = ws[col_lid_nr + row_str].value
            ver_nr = ws[col_ver_nr + row_str].value

            if lid_nr is None and ver_nr is None:
                break   # from the while

            try:
                indiv_list = lid_nr2indiv[lid_nr]
            except KeyError:
                # sporter staat niet in de lijst
                # dat is normaal als er geen uitslag aan hing
                #self.stderr.write('[ERROR] lid_nr %s niet gevonden op regel %s' % (lid_nr, row_nr))
                pass
            else:
                for indiv in indiv_list:
                    if indiv.sporter_naam == '':
                        self.stdout.write('[WARNING] Geen sporter_naam voor pk=%s: %s' % (indiv.pk, indiv))
                        naam = ws[col_naam + row_str].value
                        naam = str(naam).strip()
                        naam = naam.encode('iso-8859-1').decode('utf-8')
                        if naam == naam.lower():
                            naam = naam.title()
                            naam = naam.replace(' De ', ' de ')
                            naam = naam.replace(' Der ', ' der ')
                            naam = naam.replace(' Van ', ' van ')
                            self.stderr.write('[WARNING] Fixing capitalization: %s' % repr(naam))
                        if len(naam) < 5:
                            self.stderr.write('[ERROR] Rejected: %s' % repr(naam))
                        else:
                            self.stdout.write('          Voorstel: %s' % repr(naam))
                            indiv.sporter_naam = naam
                            if not self.dryrun:
                                indiv.save(update_fields=['sporter_naam'])

                    if indiv.vereniging_nr != ver_nr:
                        self.stdout.write('ver_nr %s --> %s for %s' % (indiv.vereniging_nr, ver_nr, indiv))
                        indiv.vereniging_nr = ver_nr
                        indiv.vereniging_naam = ver_nr2naam[ver_nr]
                        indiv.vereniging_plaats = ver_nr2plaats[ver_nr]
                        if not self.dryrun:
                            indiv.save(update_fields=['vereniging_nr', 'vereniging_naam', 'vereniging_plaats'])
                # for


# end of file
