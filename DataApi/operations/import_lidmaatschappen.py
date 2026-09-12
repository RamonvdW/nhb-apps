# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from DataApi.import_base import ImportCrmBase
from DataApi.models import DataApiLidmaatschap
import datetime


EXPECTED_MEMBER_KEYS = ('club_number', 'member_number', 'birthday', 'gender', 'member_from',
                        'postal_code', 'iso_abbr')
OPTIONAL_MEMBER_KEYS = ('skill_levels', 'educations', 'latitude', 'longitude', 'location_name',
                        'phone_business', 'phone_mobile', 'phone_private', 'para_code', 'address',
                        'initials', 'name', 'prefix', 'first_name', 'birthplace', 'email', 'wa_id',
                        'member_until', 'blocked', 'date_of_death')     # was vroeger niet aanwezig


class ImportHistCrmLidmaatschappen(ImportCrmBase):

    def __init__(self, *args):
        super().__init__(*args)

        self.count_actief = 0
        self.count_gestopt = 0
        self.count_ver_null = 0

        self._cache_actieve_lidmaatschappen = dict()    # [lid_nr] = [DataApiLidmaatschap, ...]
        self._vul_cache()
        self._changed_and_new_lms_pks = list()

    def _vul_cache(self):
        for lms in DataApiLidmaatschap.objects.order_by('pk'):      # oudste eerst
            try:
                self._cache_actieve_lidmaatschappen[lms.lid_nr].append(lms)
            except KeyError:
                self._cache_actieve_lidmaatschappen[lms.lid_nr] = [lms]

            if lms.afmeld_datum != '':
                self.count_gestopt += 1
            elif lms.ver_nr == 0:
                self.count_ver_null += 1
            else:
                self.count_actief += 1
        # for

    def _vind_lidmaatschap(self, lid_nr: int, aanmeld_datum: str) -> DataApiLidmaatschap | None:
        lms_lijst = self._cache_actieve_lidmaatschappen.get(lid_nr, [])
        if len(lms_lijst) == 0:
            # helemaal niets gevonden voor dit lid
            return None

        # fallback = meest recente
        laatste_lms = lms_lijst[-1]

        # probeer een exacte match te vinden op de aanmelddatum
        for lms in lms_lijst:
            if lms.afmeld_datum == '' and lms.aanmeld_datum == aanmeld_datum:
                laatste_lms = lms
        # for

        return laatste_lms

    def _afmelden(self, lms: DataApiLidmaatschap, afmeld_datum: str):
        # let op: ver_nr behouden
        lms.afmeld_datum = afmeld_datum
        self.out_info('Einde lms: %s' % lms)

        if not self.dryrun:
            lms.save(update_fields=['afmeld_datum'])
            self._changed_and_new_lms_pks.append(lms.pk)

        self.count_afmeldingen += 1
        self.count_actief -= 1
        self.count_gestopt += 1

    def _maak_lms(self,
                  lid_nr: int, ver_nr: int, geslacht: str,
                  geboorte_datum: str, aanmeld_datum: str,
                  land_iso: str, postcode: str):

        lms = DataApiLidmaatschap(
                    lid_nr=lid_nr,
                    ver_nr=ver_nr,
                    aanmeld_datum=aanmeld_datum,
                    geboorte_datum=geboorte_datum,
                    geslacht=geslacht,
                    land_iso=land_iso,
                    postcode=postcode)
        if not self.dryrun:
            lms.save()

        self.count_toevoegingen += 1

        try:
            self._cache_actieve_lidmaatschappen[lid_nr].append(lms)
        except KeyError:
            self._cache_actieve_lidmaatschappen[lid_nr] = [lms]

        return lms

    def _store_lid(self,
                   lid_nr: int, ver_nr: int, geslacht: str,
                   geboorte_datum: datetime.date, lid_sinds: datetime.date, lid_tot: datetime.date | None,
                   land_iso: str, postcode: str):

        geboorte_datum = geboorte_datum.strftime('%Y-%m-%d')
        aanmeld_datum = lid_sinds.strftime('%Y-%m-%d')          # dit is de historische aanmelddatum
        afmeld_datum = lid_tot.strftime('%Y-%m-%d') if lid_tot else ''

        lms_lijst = self._cache_actieve_lidmaatschappen.get(lid_nr, [])
        if len(lms_lijst) == 0:
            if not ver_nr:
                # al afgemeld, maar geen lms bekend
                if afmeld_datum < "2021-01-01":
                    # erg lang geleden --> niet meer melden
                    return

                self.out_warning('Onbekend lid: %s [%s %s %s] van %s tot %s' % (lid_nr, geboorte_datum, geslacht, postcode, aanmeld_datum, afmeld_datum))
                return

            # nieuw lid
            lms = self._maak_lms(lid_nr, ver_nr, geslacht, geboorte_datum, aanmeld_datum, land_iso, postcode)
            self.out_info('Nieuw lms: %s' % lms)
            return

        lms = lms_lijst[-1]

        if not ver_nr:
            if lms.afmeld_datum != '':
                # al geregistreerd
                return

            # huidige record afsluiten
            self._afmelden(lms, afmeld_datum or self.afmelddatum)
            return

        if lms.ver_nr != ver_nr:
            self.out_info('Overstap lid %s naar ver %s' % (lid_nr, ver_nr))
            for lms in lms_lijst:
                self.out_debug(str(lms))

            lms = lms_lijst[-1]
            if lms.afmeld_datum == '':
                # huidige record afsluiten en nieuwe beginnen
                self._afmelden(lms, afmeld_datum or self.afmelddatum)

                if lms.afmeld_datum < aanmeld_datum:
                    self.out_error('Aanmelddatum vóór vorige afmelddatum: %s < %s' % (aanmeld_datum, lms.afmeld_datum))
                    return

            lms = self._maak_lms(lid_nr, ver_nr, geslacht, geboorte_datum, aanmeld_datum, land_iso, postcode)
            self.out_info('Nieuw lms: %s' % lms)
            return

        # wijzigingen doorvoeren
        updated = list()

        if lms.geboorte_datum != geboorte_datum:
            self.out_warning('Geboortedatum aangepast naar %s (was %s)' % (geboorte_datum, lms))
            lms.geboorte_datum = geboorte_datum
            updated.append('geboorte_datum')

        if lms.geslacht != geslacht:
            self.out_info('Geslacht aangepast naar %s (was %s)' % (geslacht, lms))
            lms.geslacht = geslacht
            updated.append('geslacht')

        if lms.postcode != postcode:
            self.out_info('Postcode aangepast naar %s (was %s)' % (postcode, lms))
            lms.postcode = postcode
            updated.append('postcode')

        if len(updated) > 0:
            self.count_wijzigingen += len(updated)
            if not self.dryrun:
                lms.save(update_fields=updated)

        return

        print('store_lid %s, ver %s, postcode %s, geslacht %s, geboren %s, sinds %s, tot %s' % (lid_nr, ver_nr, postcode, geslacht, geboorte_datum, lid_sinds, lid_tot))
        for lms in lms_lijst:
            print(lms)

        return

        # zoek het meest recente record van dit lid
        lms = self._vind_lidmaatschap(lid_nr, aanmeld_datum)

        if lms and lms.ver_nr != ver_nr:
            # overgestapt naar een andere vereniging
            if lms.afmeld_datum == '':
                zeker_afmeld_datum = afmeld_datum or self.afmelddatum
                self._afmelden(lms, zeker_afmeld_datum)
            lms = None

        if lms and lms.aanmeld_datum != aanmeld_datum:
            # aanpassing van de aanmelddatum
            self.stdout.write('[INFO] Lid %s wijziging aanmelddatum %s --> %s' % (lid_nr, lms.aanmeld_datum, aanmeld_datum))
            if not self.dryrun:
                lms.aanmeld_datum = aanmeld_datum
                lms.save(update_fields=['aanmeld_datum'])
            return

        if not lms and ver_nr == 0:
            if not self.include_ver_null:
                return

        if not lms:
            # nieuw record nodig
            if self.dryrun:
                return

            lms = DataApiLidmaatschap.objects.create(
                        lid_nr=lid_nr,
                        ver_nr=ver_nr,
                        geslacht=geslacht,
                        geboorte_datum=geboorte_datum,
                        aanmeld_datum=aanmeld_datum,
                        land_iso=land_iso,
                        postcode=postcode)

            self._changed_and_new_lms_pks.append(lms.pk)

            try:
                self._cache_actieve_lidmaatschappen[lid_nr].append(lms)
            except KeyError:
                self._cache_actieve_lidmaatschappen[lid_nr] = [lms]

            self.count_actief += 1
            self.count_toevoegingen += 1

        if afmeld_datum != '' and lms.afmeld_datum == '':
            self._afmelden(lms, afmeld_datum)
            return

        if lms.geboorte_datum != geboorte_datum:
            # self.out_warning('Wijziging lid %s geboortedatum %s --> %s' % (lid_nr, repr(lms.geboorte_datum),
            #                                                                        repr(geboorte_datum)))
            if not self.dryrun:
                lms.geboorte_datum = geboorte_datum
                lms.save(update_fields=['geboorte_datum'])
                self._changed_and_new_lms_pks.append(lms.pk)

        if lms.geslacht != geslacht:
            # self.out_warning('Wijziging lid %s geslacht %s --> %s' % (lid_nr, repr(lms.geslacht),
            #                                                                    repr(geslacht)))
            if not self.dryrun:
                lms.geslacht = geslacht
                lms.save(update_fields=['geslacht'])
                self._changed_and_new_lms_pks.append(lms.pk)

        if lms.postcode != postcode or lms.land_iso != land_iso:
            # verhuisd
            if not self.dryrun:
                lms.postcode = postcode
                lms.land_iso = land_iso
                lms.save(update_fields=['postcode', 'land_iso'])
                self._changed_and_new_lms_pks.append(lms.pk)

    def _importeer_data(self, data: list):
        """ Importeert data van alle leden """

        # check alleen het eerste record
        if self.check_keys(data[0].keys(), EXPECTED_MEMBER_KEYS, OPTIONAL_MEMBER_KEYS, "member{sporters}"):
            return

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

            self._store_lid(lid_nr, lid_ver_nr,
                            lid_geslacht, lid_geboorte_datum,
                            lid_sinds, lid_tot,
                            land_iso, lid_postcode)

            if lid_nr in lid_nrs:
                lid_nrs.remove(lid_nr)
        # for member

        self._lidmaatschappen_stoppen(lid_nrs)

    def _lidmaatschappen_stoppen(self, lid_nrs: list):
        while len(lid_nrs) > 0:
            lid_nr = lid_nrs.pop(0)

            for lms in self._cache_actieve_lidmaatschappen.get(lid_nr, []):
                if lms.afmeld_datum == '':
                    self._afmelden(lms, self.afmelddatum)
            # for
        # while

    def importeer(self, data: list):
        """ Importeert data van alle leden """
        self._importeer_data(data)

# end of file
