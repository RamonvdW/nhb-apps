# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" vergelijk twee JSON bestanden met data uit het CRM-systeem van de bond """

from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand
from ImportCRM.models import IMPORT_LIMIETEN_PK, ImportLimieten
from Mailer.operations import mailer_notify_internal_error, mailer_queue_email
from Site.core.main_exceptions import SpecificExitCode
import traceback
import logging
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

my_logger = logging.getLogger('MH.ImportCRM.diff_crm_jsons')


class Command(BaseCommand):

    help = "Toon de verschillen tussen twee JSON bestanden met data uit het CRM systeem van de bond"

    def __init__(self):
        super().__init__()
        self._exit_code = 0
        self.club_changes = 0
        self.member_changes = 0
        self._redenen = list()

        # haal de limieten uit de database
        self.limieten = ImportLimieten.objects.filter(pk=IMPORT_LIMIETEN_PK).first()

    def add_arguments(self, parser):
        parser.add_argument('filenames', nargs=2, help="Pad naar twee JSON bestanden")

    def _add_reden(self, msg):
        self._redenen.append(msg)
        if "[ERROR]" in msg:
            self.stderr.write(msg)
            self._exit_code = 3
        else:
            self.stdout.write(msg)

    def _check_keys(self, keys, expected_keys, level):
        has_error = False
        keys = list(keys)
        for key in expected_keys:
            try:
                keys.remove(key)
            except ValueError:
                self._add_reden("[ERROR] [FATAL] Verplichte sleutel %s niet aanwezig in de %s data" % (
                                    repr(key), repr(level)))
                has_error = True
        # for
        if len(keys):
            self._add_reden("[WARNING] Extra sleutel aanwezig in de %s data: %s" % (repr(level), repr(keys)))
        return has_error

    def _load_json(self, fname):
        try:
            with open(fname, encoding='raw_unicode_escape') as f_handle:
                data = json.load(f_handle)
        except IOError as exc:
            self._add_reden("[ERROR] Bestand kan niet gelezen worden (%s)" % str(exc))
            return
        except json.decoder.JSONDecodeError as exc:
            self._add_reden("[ERROR] Probleem met het JSON formaat in bestand %s (%s)" % (repr(fname), str(exc)))
            return
        except UnicodeDecodeError as exc:
            self._add_reden("[ERROR] Bestand heeft unicode problemen (%s)" % str(exc))
            return

        if self._check_keys(data.keys(), EXPECTED_DATA_KEYS, "top-level"):
            return

        for key in EXPECTED_DATA_KEYS:
            if len(data[key]) < 1:
                self._add_reden("[ERROR] Geen data voor top-level sleutel %s" % repr(key))
                return

        data['fname'] = fname
        return data

    def _diff_club_lists(self, sub1, sub2):
        # sub1, sub2 zijn lists of dictionaries
        if sub1 is None:
            sub1 = list()
        if sub2 is None:
            sub2 = list()
        for sub in sub1:
            if sub not in sub2:
                self._add_reden('            -%s' % repr(sub))
                self.club_changes += 1
        # for
        for sub in sub2:
            if sub not in sub1:
                self._add_reden('            +%s' % repr(sub))
                self.club_changes += 1
        # for

    def _diff_club(self, ver_nr, club1, club2):
        first = True
        keys = set(list(club1.keys()) + list(club2.keys()))
        for key in keys:
            try:
                val1 = club1[key]
                val2 = club2[key]
            except KeyError:
                # one of the two does not have this key
                if first:
                    self._add_reden('    club %s' % ver_nr)
                    first = False
                if key in club1:
                    # removed in club2
                    self._add_reden('        -%s' % key)
                else:
                    # added in club2
                    self._add_reden('        +%s' % key)
            else:
                if val1 != val2:
                    if first:
                        self._add_reden('    club %s' % ver_nr)
                        first = False
                    if key in ('member_admins', 'secretaris'):
                        self._add_reden('        %s:' % key)
                        self._diff_club_lists(val1, val2)
                    else:
                        self._add_reden('        -%s: %s' % (key, val1))
                        self._add_reden('        +%s: %s' % (key, val2))
                        self.club_changes += 1
        # for

    def _diff_clubs(self, clubs1, clubs2):
        self._add_reden('clubs:')

        clubs = dict()
        for club in clubs1:
            ver_nr = club['club_number']
            if ver_nr == 'crash':
                raise Exception('crash test')
            clubs[ver_nr] = club
        # for

        for club2 in clubs2:
            ver_nr = club2['club_number']
            try:
                club1 = clubs[ver_nr]
            except KeyError:
                self._add_reden('   +club %s' % ver_nr)
            else:
                self._diff_club(ver_nr, club1, club2)
                del clubs[ver_nr]
        # for

        for ver_nr in clubs.keys():
            self._add_reden('   -club %s' % ver_nr)
            self.club_changes += 1
        # for

    def _diff_member_lists(self, sub1, sub2):
        # sub1, sub2 zijn lists of dictionaries
        if sub1 is None:
            sub1 = list()
        if sub2 is None:
            sub2 = list()
        for sub in sub1:
            if sub not in sub2:
                self._add_reden('            -%s' % repr(sub))
                self.member_changes += 1
        # for
        for sub in sub2:
            if sub not in sub1:
                self._add_reden('            +%s' % repr(sub))
                self.member_changes += 1
        # for

    def _diff_member(self, lid_nr, member1, member2):
        first = True
        keys = set(list(member1.keys()) + list(member2.keys()))
        for key in keys:
            val1 = member1.get(key, None)
            val2 = member2.get(key, None)
            if val1 != val2:
                if first:
                    self._add_reden('    lid %s' % lid_nr)
                    first = False
                if key in ('educations', 'skill_levels'):
                    self._add_reden('        %s:' % key)
                    self._diff_member_lists(val1, val2)
                else:
                    val1 = str(val1).replace('\n', '; ')
                    val2 = str(val2).replace('\n', '; ')
                    self._add_reden('        -%s: %s' % (key, val1))
                    self._add_reden('        +%s: %s' % (key, val2))
                    self.member_changes += 1
        # for

    def _diff_members(self, members1, members2):
        self._add_reden('members:')

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
                self._add_reden('   +lid: %s' % lid_nr)
            else:
                self._diff_member(lid_nr, member1, member2)
                del members[lid_nr]
        # for

        for lid_nr in members.keys():
            self._add_reden('   -lid %s' % lid_nr)
            self.member_changes += 1
        # for

    def _diff_data(self, data1, data2):
        self._diff_clubs(data1['clubs'], data2['clubs'])
        self._diff_members(data1['members'], data2['members'])

    def _diff_jsons(self, fname1, fname2):
        self._add_reden('files:')
        self._add_reden('   %s' % repr(fname1))
        json1 = self._load_json(fname1)
        self._add_reden('   %s' % repr(fname2))
        json2 = self._load_json(fname2)

        if json1 and json2:
            self._diff_data(json1, json2)

            self._add_reden('totals:')
            self._add_reden('    club_changes: %s' % self.club_changes)
            self._add_reden('    member_changes: %s' % self.member_changes)

    def handle(self, *args, **options):
        fname1 = options['filenames'][0]
        fname2 = options['filenames'][1]

        # vang generieke fouten af
        try:
            self._diff_jsons(fname1, fname2)
        except Exception as exc:
            # schrijf in de output
            tups = sys.exc_info()
            lst = traceback.format_tb(tups[2])
            tb = traceback.format_exception(*tups)

            tb_msg_start = 'Unexpected error during diff_crm_json\n'
            tb_msg_start += '\n'
            tb_msg = tb_msg_start + '\n'.join(tb)

            # full traceback to syslog
            my_logger.error(tb_msg)

            self.stderr.write('[ERROR] Onverwachte fout (%s) tijdens diff_crm_json: %s' % (type(exc), str(exc)))
            self.stderr.write('Traceback:')
            self.stderr.write(''.join(lst))

            # stuur een mail naar de ontwikkelaars
            # reduceer tot de nuttige regels
            tb = [line for line in tb if '/site-packages/' not in line]
            tb_msg = tb_msg_start + '\n'.join(tb)

            # deze functie stuurt maximaal 1 mail per dag over hetzelfde probleem
            self.stdout.write('[WARNING] Stuur crash mail naar ontwikkelaar')
            mailer_notify_internal_error(tb_msg)

            self._exit_code = 1
        else:
            if self._exit_code == 0:
                if self.limieten.use_limits:
                    if self.member_changes > self.limieten.max_member_changes:
                        self._add_reden('[ERROR] Too many member changes! (limit: %s)' % self.limieten.max_member_changes)
                        self._exit_code = 1

                    if self.club_changes > self.limieten.max_club_changes:
                        self._add_reden('[ERROR] Too many club changes! (limit: %s)' % self.limieten.max_club_changes)
                        self._exit_code = 2
                else:
                    self.stdout.write('[WARNING] Limieten zijn uitgeschakeld')

            if self._exit_code != 0:
                now = timezone.now()
                now = timezone.localtime(now)
                stamp_str = now.strftime('op %Y-%m-%d om %H:%M')

                self._redenen.insert(0, 'ImportCRM handrem blokkeert import %s' % stamp_str)
                self._redenen.insert(1, '')

                mailer_queue_email(
                    settings.EMAIL_DEVELOPER_TO,
                    'CRM import geblokkeerd %s' % settings.NAAM_SITE,
                    "\n".join(self._redenen),
                    enforce_whitelist=False)

        if self._exit_code > 0:
            raise SpecificExitCode(self._exit_code)

# end of file
