# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" vergelijk twee JSON bestanden met data uit het CRM-systeem van de bond """

from django.core.management.base import BaseCommand
from Site.core.main_exceptions import SpecificExitCode
import json
import sys

# expected keys at each level
EXPECTED_DATA_KEYS = ('rayons', 'regions', 'clubs', 'members')

EXPECTED_CLUB_KEYS = ('region_number', 'club_number', 'name', 'prefix', 'email', 'website',
                      'has_disabled_facilities', 'address', 'postal_code', 'location_name',
                      'phone_business', 'phone_private', 'phone_mobile', 'coc_number',
                      'iso_abbr', 'latitude', 'longitude', 'secretaris', 'iban', 'bic')

EXPECTED_MEMBER_KEYS = ('club_number', 'member_number', 'name', 'prefix', 'first_name',
                        'initials', 'birthday', 'birthplace', 'email', 'gender', 'member_from', 'member_until',
                        'para_code', 'address', 'postal_code', 'location_name',
                        'phone_business', 'phone_mobile', 'phone_private',
                        'iso_abbr', 'latitude', 'longitude', 'blocked', 'wa_id', 'date_of_death')


class Command(BaseCommand):

    help = "Toon de verschillen tussen twee JSON bestanden met data uit het CRM systeem van de bond"

    def __init__(self):
        super().__init__()
        self.club_changes = 0
        self.member_changes = 0

    def add_arguments(self, parser):
        parser.add_argument('filenames', nargs=2, help="Pad naar twee JSON bestanden")
        parser.add_argument('max_club_changes', type=int, help="Maximum aantal wijzigingen in sectie 'clubs'")
        parser.add_argument('max_member_changes', type=int, help="Maximum aantal wijzigingen in sectie 'members'")

    def _check_keys(self, keys, expected_keys, optional_keys, level):
        has_error = False
        keys = list(keys)
        for key in expected_keys:
            try:
                keys.remove(key)
            except ValueError:
                self.stderr.write("[ERROR] [FATAL] Verplichte sleutel %s niet aanwezig in de %s data" % (
                                    repr(key), repr(level)))
                has_error = True
        # for
        for key in optional_keys:
            try:
                keys.remove(key)
            except ValueError:
                pass
        if len(keys):
            self.stdout.write("[WARNING] Extra sleutel aanwezig in de %s data: %s" % (repr(level), repr(keys)))
        return has_error

    def _load_json(self, fname):
        try:
            with open(fname, encoding='raw_unicode_escape') as f_handle:
                data = json.load(f_handle)
        except IOError as exc:
            self.stderr.write("[ERROR] Bestand kan niet gelezen worden (%s)" % str(exc))
            return
        except json.decoder.JSONDecodeError as exc:
            self.stderr.write("[ERROR] Probleem met het JSON formaat in bestand %s (%s)" % (repr(fname), str(exc)))
            return
        except UnicodeDecodeError as exc:
            self.stderr.write("[ERROR] Bestand heeft unicode problemen (%s)" % str(exc))
            return

        if self._check_keys(data.keys(), EXPECTED_DATA_KEYS, (), "top-level"):
            return

        for key in EXPECTED_DATA_KEYS:
            if len(data[key]) < 1:
                self.stderr.write("[ERROR] Geen data voor top-level sleutel %s" % repr(key))
                return

        data['fname'] = fname
        return data

    def _diff_club(self, ver_nr, club1, club2):
        first = True
        keys = set(list(club1.keys()) + list(club2.keys()))
        for key in keys:
            val1 = club1[key]
            val2 = club2[key]
            if val1 != val2:
                if first:
                    self.stdout.write('    club %s' % ver_nr)
                    first = False
                self.stdout.write('        -%s: %s' % (key, val1))
                self.stdout.write('        +%s: %s' % (key, val2))
                self.club_changes += 1
        # for

    def _diff_clubs(self, clubs1, clubs2):
        self.stdout.write('clubs:')

        clubs = dict()
        for club in clubs1:
            ver_nr = club['club_number']
            clubs[ver_nr] = club
        # for

        for club2 in clubs2:
            ver_nr = club2['club_number']
            try:
                club1 = clubs[ver_nr]
            except KeyError:
                self.stdout.write('   +club %s' % ver_nr)
            else:
                self._diff_club(ver_nr, club1, club2)
        # for

    def _diff_member(self, lid_nr, member1, member2):
        first = True
        keys = set(list(member1.keys()) + list(member2.keys()))
        for key in keys:
            val1 = member1[key]
            val2 = member2[key]
            if val1 != val2:
                if first:
                    self.stdout.write('    lid %s' % lid_nr)
                    first = False
                self.stdout.write('        -%s: %s' % (key, val1))
                self.stdout.write('        +%s: %s' % (key, val2))
                self.member_changes += 1
        # for

    def _diff_members(self, members1, members2):
        self.stdout.write('members:')

        members = dict()
        for member1 in members1:
            lid_nr = member1['member_number']
            members[lid_nr] = member1
        # for

        for member2 in members2:
            lid_nr = member2['member_number']
            try:
                member1 = members[lid_nr]
            except KeyError:
                self.stdout.write('   +lid: %s' % lid_nr)
            else:
                self._diff_member(lid_nr, member1, member2)
        # for

    def _diff(self, data1, data2):
        self._diff_clubs(data1['clubs'], data2['clubs'])
        self._diff_members(data1['members'], data2['members'])

    def handle(self, *args, **options):

        fname1 = options['filenames'][0]
        fname2 = options['filenames'][1]

        self.stdout.write('files:')
        self.stdout.write('   %s' % repr(fname1))
        json1 = self._load_json(fname1)
        self.stdout.write('   %s' % repr(fname2))
        json2 = self._load_json(fname2)

        self._diff(json1, json2)

        self.stdout.write('totals:')
        self.stdout.write('    club_changes: %s' % self.club_changes)
        self.stdout.write('    member_changes: %s' % self.member_changes)

        # sys.exit raises SystemExit, which is caught in manage.py, which changes the exit status to 3
        # but that is fine

        if self.member_changes > options['max_member_changes']:
            self.stdout.write('[ERROR] Too many member changes! (limit: %s)' % options['max_member_changes'])
            raise SpecificExitCode(1)

        if self.club_changes > options['max_club_changes']:
            self.stdout.write('[ERROR] Too many club changes! (limit: %s)' % options['max_club_changes'])
            raise SpecificExitCode(2)


# end of file
