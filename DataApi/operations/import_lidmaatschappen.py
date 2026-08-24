# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from django.db.models import ProtectedError
from DataApi.import_base import ImportCrmBase
from DataApi.models import DataApiLidmaatschap, DataApiVereniging
import datetime


EXPECTED_MEMBER_KEYS = ('club_number', 'member_number', 'birthday', 'gender', 'member_from',
                        'postal_code', 'iso_abbr')
OPTIONAL_MEMBER_KEYS = ('skill_levels', 'educations', 'latitude', 'longitude', 'location_name',
                        'phone_business', 'phone_mobile', 'phone_private', 'para_code', 'address',
                        'initials', 'name', 'prefix', 'first_name', 'birthplace', 'email', 'wa_id',
                        'member_until', 'blocked', 'date_of_death')     # was vroeger niet aanwezig


class ImportCrmLidmaatschappen(ImportCrmBase):

    def __init__(self, *args):
        super().__init__(*args)

        self.count_actief = 0
        self.count_gestopt = 0

        self._ver_nrs = list()      # alle bestaande verenigingen

        self._cache_actieve_lidmaatschappen = dict()    # [lid_nr] = DataApiLidmaatschap
        self._vul_cache()

    def zet_ver_nrs(self, ver_nrs):
        self._ver_nrs = ver_nrs[:]

    def _vul_cache(self):
        for lms in DataApiLidmaatschap.objects.order_by('pk'):      # oudste eerst
            try:
                self._cache_actieve_lidmaatschappen[lms.lid_nr].append(lms)
            except KeyError:
                self._cache_actieve_lidmaatschappen[lms.lid_nr] = [lms]

            if lms.afmeld_datum == '':
                self.count_actief += 1
            else:
                self.count_gestopt += 1
        # for

    def _vind_lidmaatschap(self, lid_nr: int, aanmeld_datum: str) -> DataApiLidmaatschap | None:
        laatste_lms = None
        for lms in self._cache_actieve_lidmaatschappen.get(lid_nr, []):
            if lms.aanmeld_datum == aanmeld_datum:
                laatste_lms = lms
        # for
        return laatste_lms

    def _store_lid(self,
                   lid_nr: int, ver_nr: int, geslacht: str,
                   geboorte_datum: datetime.date, lid_sinds: datetime.date, lid_tot: datetime.date | None,
                   land_iso: str, postcode: str):

        geboorte_datum = geboorte_datum.strftime('%Y-%m-%d')
        aanmeld_datum = lid_sinds.strftime('%Y-%m-%d')
        afmeld_datum = lid_tot.strftime('%Y-%m-%d') if lid_tot else ''

        lms = self._vind_lidmaatschap(lid_nr, aanmeld_datum)

        if not lms:
            # nieuw record nodig
            lms = DataApiLidmaatschap.objects.create(
                        lid_nr=lid_nr,
                        ver_nr=ver_nr,
                        geslacht=geslacht,
                        geboorte_datum=geboorte_datum,
                        aanmeld_datum=aanmeld_datum,
                        land_iso=land_iso,
                        postcode=postcode)
            try:
                self._cache_actieve_lidmaatschappen[lid_nr].append(lms)
            except KeyError:
                self._cache_actieve_lidmaatschappen[lid_nr] = [lms]
            self.count_actief += 1
            if lms.lid_nr == 144498:
                self.out_debug('Lid %s is aangemaakt: lms %s' % (lid_nr, lms.pk))
        else:
            if lid_nr == 144498:
                self.out_debug('Lid %s heeft lms %s' % (lid_nr, lms.pk))

        if afmeld_datum and lms.afmeld_datum == '':
            lms.afmeld_datum = afmeld_datum
            lms.ver_nr = 0
            lms.save(update_fields=['afmeld_datum', 'ver_nr'])
            self.count_actief -= 1
            self.count_gestopt += 1
            if lms.lid_nr == 144498:
                self.out_debug('Lid %s, lms %s krijg afmeld_datum %s' % (lid_nr, lms.pk, afmeld_datum))

    def importeer(self, data: list):
        """ Importeert data van alle leden """

        # check alleen het eerste record
        if self.check_keys(data[0].keys(), EXPECTED_MEMBER_KEYS, OPTIONAL_MEMBER_KEYS, "member{sporters}"):
            return

        date_now = timezone.now().date()

        # houd bij welke leden lid_nrs in de database zitten
        # als deze niet meer voorkomen, dan zijn ze verwijderd
        lid_nrs = list(self._cache_actieve_lidmaatschappen.keys())

        """ JSON velden (string, except):
             'member_number':       int,
             'club_number':         int,
             'birthday':            string YYYY-MM-DD
             'gender':              'M' of 'V'/'F' of 'X'
             'member_from':         string YYYY-MM-DD
             'member_until':        string YYYY-MM-DD
             'date_of_death':       string YYYY-MM-DD or null
             'postal_code',
             'iso_abbr': 'NL',      land code
        """
        for member in data:

            lid_nr = member['member_number']
            if lid_nr in settings.CRM_IMPORT_SKIP_MEMBERS:
                # silently skip some numbers
                continue
            try:
                lid_nr = int(lid_nr)
            except ValueError:
                self.out_error('Foutief bondsnummer: %s (geen getal)' % lid_nr)
                continue

            lid_ver_nr = 0
            ver_nr = member['club_number']
            if ver_nr:
                try:
                    lid_ver_nr = int(ver_nr)
                except ValueError:
                    pass

                if lid_ver_nr not in self._ver_nrs:
                    self.out_error('Lid %s heeft onbekende vereniging %s' % (lid_nr, lid_ver_nr))

            if member['birthday'] and member['birthday'][0:0+2] not in ("19", "20"):
                # poging tot repareren
                if member['birthday'][0:0+2] == "00":
                    old_birthday = member['birthday']
                    year = int(old_birthday[2:2+2])
                    if year < 25:
                        member['birthday'] = '20' + old_birthday[2:]
                    else:
                        member['birthday'] = '19' + old_birthday[2:]
                    self.out_warning("Lid %s geboortedatum gecorrigeerd van %s naar %s" % (
                                            lid_nr, old_birthday, member['birthday']))
                else:
                    self.out_error('Lid %s heeft geen valide geboortedatum: %s' % (lid_nr, member['birthday']))
                    continue
            try:
                lid_geboorte_datum = datetime.datetime.strptime(member['birthday'], "%Y-%m-%d").date()   # YYYY-MM-DD
            except (ValueError, TypeError):
                self.out_error('Lid %s heeft geen valide geboortedatum: %s' % (lid_nr, repr(member['birthday'])))
                continue

            lid_geslacht = member['gender']
            if lid_geslacht not in ('M', 'F', 'V', 'X'):
                self.out_error('Lid %s heeft onbekend geslacht: %s' % (lid_nr, lid_geslacht))
                continue
            if lid_geslacht == 'F':
                lid_geslacht = 'V'

            # postcode + huisnummer maken
            lid_postcode = ''
            postcode = member['postal_code']
            if postcode:
                postcode = postcode.upper()     # sommige postcodes zijn kleine letters
                lid_postcode = postcode.replace(' ', '')

            land_iso = member['iso_abbr']
            if not land_iso:
                land_iso = 'NL'

            # lid sinds
            if member['member_from'] and member['member_from'][0:0+2] not in ("19", "20"):
                self.out_error('Lid %s heeft geen valide datum lidmaatschap: %s' % (lid_nr, member['member_from']))
                continue
            try:
                lid_sinds = datetime.datetime.strptime(member['member_from'], "%Y-%m-%d").date()  # YYYY-MM-DD
            except (ValueError, TypeError):
                self.out_error('Lid %s heeft geen valide lidmaatschapsdatum: %s' % (lid_nr,
                                                                                    repr(member['member_from'])))
                continue

            if lid_sinds > date_now:
                self.out_info('Lidmaatschap voor %s gaat pas in op datum: %s' % (
                                        lid_nr, repr(member['member_from'])))
                # wacht met importeren
                continue

            # lid_tot
            lid_tot = None
            tot_str = member.get('member_until', None)
            if tot_str:
                if not tot_str.startswith('9999-'):
                    try:
                        lid_tot = datetime.datetime.strptime(tot_str, "%Y-%m-%d").date()  # YYYY-MM-DD
                    except (ValueError, TypeError):
                        self.out_error('Lid %s heeft geen valide datum einde lidmaatschap: %s' % (
                                                lid_nr, repr(member['member_until'])))
                        continue

            # datum overlijden
            overleden_datum = member.get('date_of_death', None)
            if overleden_datum:
                try:
                    lid_tot = datetime.datetime.strptime(member['date_of_death'], "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    self.out_error('Lid %s heeft geen valide datum van overlijden: %s' %
                                        (lid_nr, repr(member['date_of_death'])))
                    continue

            self._store_lid(lid_nr, lid_ver_nr, lid_geslacht, lid_geboorte_datum,
                            lid_sinds, lid_tot, land_iso, lid_postcode)

            if lid_nr in lid_nrs:
                lid_nrs.remove(lid_nr)
        # for member

        self._verwijder_sporters(lid_nrs)

    def _verwijder_sporters(self, lid_nrs: list):
        # self.stdout.write('[DEBUG] Volgende %s bondsnummers moeten verwijderd worden: %s' % (len(lid_nrs),
        #                                                                                      repr(lid_nrs)))
        afmeld_datum = timezone.now().date().strftime('%Y-%m-%d')

        while len(lid_nrs) > 0:
            lid_nr = lid_nrs.pop(0)

            for lms in self._cache_actieve_lidmaatschappen.get(lid_nr, []):
                if lms.afmeld_datum == '':
                    if lms.lid_nr == 144498:
                        self.out_debug('Lid %s is verwijderd; lms %s wordt afgemeld=%s' % (lid_nr, lms.pk, afmeld_datum))
                    lms.afmeld_datum = afmeld_datum
                    lms.ver_nr = 0
                    lms.save(update_fields=['afmeld_datum', 'ver_nr'])
                    self.count_gestopt += 1
            # for
        # while

# end of file
