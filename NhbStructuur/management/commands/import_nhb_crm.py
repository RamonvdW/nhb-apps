# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" importeer een JSON file met data uit het CRM systeem van de NHB """

from django.core.management.base import BaseCommand
from django.db.models import ProtectedError
from django.db.utils import DataError
from django.utils import timezone
from django.conf import settings
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from Account.models import Account
from Functie.models import Functie, maak_functie, maak_account_vereniging_secretaris
from Logboek.models import schrijf_in_logboek
from Mailer.models import mailer_email_is_valide
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging
from Overig.helpers import maak_unaccented
from Records.models import IndivRecord
from Sporter.models import Sporter, Secretaris, Speelsterkte
from Wedstrijden.models import WedstrijdLocatie, BAAN_TYPE_EXTERN, BAAN_TYPE_BUITEN
import traceback
import datetime
import json
import sys


def get_secretaris_str(sporter):
    if sporter:
        return "%s %s" % (sporter.lid_nr, sporter.volledige_naam())
    return "geen"


def get_vereniging_str(ver):
    if ver:
        return "%s %s" % (ver.ver_nr, ver.naam)
    return "geen"


# expected keys at each level
EXPECTED_DATA_KEYS = ('rayons', 'regions', 'clubs', 'members')
EXPECTED_RAYON_KEYS = ('rayon_number', 'name')
EXPECTED_REGIO_KEYS = ('rayon_number', 'region_number', 'name')
EXPECTED_CLUB_KEYS = ('region_number', 'club_number', 'name', 'prefix', 'email', 'website',
                      'has_disabled_facilities', 'address', 'postal_code', 'location_name',
                      'phone_business', 'phone_private', 'phone_mobile', 'coc_number',
                      'iso_abbr', 'latitude', 'longitude', 'secretaris', 'iban', 'bic')
EXPECTED_MEMBER_KEYS = ('club_number', 'member_number', 'name', 'prefix', 'first_name',
                        'initials', 'birthday', 'email', 'gender', 'member_from',
                        'para_code', 'address', 'postal_code', 'location_name',
                        'iso_abbr', 'latitude', 'longitude', 'blocked')
OPTIONAL_MEMBER_KEYS = ('skill_levels',)

# administratieve entries (met fouten) die overslagen moeten worden
SKIP_MEMBERS = (101711,)        # CRM developer

GEEN_SECRETARIS_NODIG = (1377,)     # persoonlijk lid

GEEN_WEDSTRIJDEN = (1377,)          # persoonlijk lid, geen wedstrijden

GEEN_WEDSTRIJDLOCATIE = (1368,      # bondsbureau NHB
                         1377,      # persoonlijk lid, geen wedstrijden
                         )


class Command(BaseCommand):

    help = "Importeer een JSON file met data uit het CRM systeem van de NHB"

    def __init__(self):
        super().__init__()
        self._count_errors = 0
        self._count_warnings = 0
        self._count_rayons = 0
        self._count_regios = 0
        self._count_clubs = 0
        self._count_members = 0
        self._count_blocked = 0
        self._count_wijzigingen = 0
        self._count_verwijderingen = 0
        self._count_toevoegingen = 0
        self._count_lid_no_email = 0
        self._count_sec_no_account = 0
        self._count_uitgeschreven = 0

        self._nieuwe_clubs = list()
        self._recordhouder_lid_nrs = list()

        self.lidmaatschap_jaar = 0
        self.zet_lidmaatschap_jaar(timezone.now())

        self.dryrun = False

        self._cache_rayon = dict()      # [rayon_nr] = NhbRayon()
        self._cache_regio = dict()      # [regio_nr] = NhbRegio()
        self._cache_ver = dict()        # [ver_nr] = NhbVereniging()
        self._cache_sec = dict()        # [ver_nr] = Secretaris()
        self._cache_sporter = dict()    # [lid_nr] = Sporter()
        self._cache_functie = dict()    # [(rol, beschrijving)] = Functie()
        self._cache_sterk = dict()      # [lid_nr] = [SpeelSterkte(), ...]

        self._speelsterkte2volgorde = dict()    # [(discipline, beschrijving)] = volgorde

    def _maak_cache(self):
        for rayon in NhbRayon.objects.all():
            self._cache_rayon[rayon.rayon_nr] = rayon
        # for

        for regio in NhbRegio.objects.all():
            self._cache_regio[regio.regio_nr] = regio
        # for

        for ver in (NhbVereniging
                    .objects
                    .select_related('regio')
                    .prefetch_related('wedstrijdlocatie_set')
                    .all()):
            self._cache_ver[ver.ver_nr] = ver
        # for

        for sec in (Secretaris
                    .objects
                    .select_related('vereniging',
                                    'sporter')
                    .all()):
            self._cache_sec[sec.vereniging.ver_nr] = sec
        # for

        for sporter in Sporter.objects.all():
            self._cache_sporter[sporter.lid_nr] = sporter
        # for

        for functie in (Functie
                        .objects
                        .select_related('nhb_ver')
                        .all()):
            tup = (functie.rol, functie.beschrijving)
            self._cache_functie[tup] = functie
        # for

        for sterkte in Speelsterkte.objects.select_related('sporter').all():
            try:
                self._cache_sterk[sterkte.sporter.lid_nr].append(sterkte)
            except KeyError:
                self._cache_sterk[sterkte.sporter.lid_nr] = [sterkte]
        # for

        for disc, beschr, volgorde in settings.SPEELSTERKTE_VOLGORDE:
            # discipline, beschrijving, volgorde
            self._speelsterkte2volgorde[(disc, beschr)] = volgorde
        # for

    def _vind_rayon(self, rayon_nr):
        try:
            rayon_nr = int(rayon_nr)
        except ValueError:
            self.stderr.write('[ERROR] Foutief rayon nummer: %s (geen getal)' % repr(rayon_nr))
        else:
            try:
                return self._cache_rayon[rayon_nr]
            except KeyError:
                pass
        return None

    def _vind_regio(self, regio_nr):
        try:
            regio_nr = int(regio_nr)
        except ValueError:
            self.stderr.write('[ERROR] Foutief regio nummer: %s (geen getal)' % repr(regio_nr))
        else:
            try:
                return self._cache_regio[regio_nr]
            except KeyError:
                pass
        return None

    def _vind_vereniging(self, ver_nr):
        try:
            ver_nr = int(ver_nr)
        except ValueError:
            self.stderr.write('[ERROR] Foutief verenigingsnummer: %s (geen getal)' % repr(ver_nr))
        else:
            try:
                return self._cache_ver[ver_nr]
            except KeyError:
                pass
        return None

    def _vind_sec(self, ver_nr):
        try:
            ver_nr = int(ver_nr)
        except ValueError:          # pragma: no cover
            self.stderr.write('[ERROR] Foutief verenigingsnummer: %s (geen getal)' % repr(ver_nr))
        else:
            try:
                return self._cache_sec[ver_nr]
            except KeyError:
                pass
        return None

    def _vind_sporter(self, lid_nr):
        try:
            lid_nr = int(lid_nr)
        except ValueError:
            self.stderr.write('[ERROR] Foutief bondsnummer: %s (geen getal)' % lid_nr)
            pass
        else:
            try:
                return self._cache_sporter[lid_nr]
            except KeyError:
                pass
        return None

    def _vind_functie(self, rol, beschrijving):
        tup = (rol, beschrijving)
        try:
            return self._cache_functie[tup]
        except KeyError:
            pass
        return None

    def zet_lidmaatschap_jaar(self, now):
        self.lidmaatschap_jaar = now.year               # voorbeeld: 2021
        if now.month == 1 and now.day <= 15:
            # tot en met 15 januari hoort bij het voorgaande jaar
            # leden kunnen dus nog uitgeschreven worden tot 15 jan
            self.lidmaatschap_jaar -= 1                 # voorbeeld: 2020

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, help="pad naar het JSON bestand")
        parser.add_argument('--dryrun', action='store_true')
        parser.add_argument('--sim_now', nargs=1, metavar='YYYY-MM-DD', help="gesimuleerde datum: YYYY-MM-DD")

    def _check_keys(self, keys, expected_keys, optional_keys, level):
        has_error = False
        keys = list(keys)
        for key in expected_keys:
            try:
                keys.remove(key)
            except ValueError:
                self.stderr.write("[ERROR] Verplichte sleutel %s niet aanwezig in de %s data" % (repr(key), repr(level)))
                has_error = True
        # for
        for key in optional_keys:
            try:
                keys.remove(key)
            except ValueError:
                pass
        if len(keys):
            self.stderr.write("[WARNING] Extra sleutel aanwezig in de %s data: %s" % (repr(level), repr(keys)))
        return has_error

    @staticmethod
    def _check_iban(iban):
        """ Voer de mod97 test uit op de IBAN """
        if len(iban) != 18:
            return False

        getal = ''
        for teken in iban[4:] + iban[:4]:
            if teken.isdigit():
                getal += teken
            elif teken.isupper():
                # vertaal in A=10, B=11 .. Z=36
                getal += str(ord(teken) - ord('A') + 10)
            else:
                # niet ondersteund teken
                return False
        # for

        nr = int(getal)
        rest = nr % 97
        return rest == 1

    def _vind_recordhouders(self):
        """ Sporters met een NL record op hun naam worden niet verwijderd.
            Zoek deze op zodat we niet eens een poging gaan doen om ze te verwijderen.
        """
        self._recordhouder_lid_nrs = list(IndivRecord
                                          .objects
                                          .distinct('sporter')
                                          .values_list('sporter__lid_nr', flat=True))
        # self.stdout.write('[DEBUG] Record houders: %s' % repr(self._recordhouder_lid_nrs))

    def _import_rayons(self, data):
        """ Importeert data van alle rayons """

        if self._check_keys(data[0].keys(), EXPECTED_RAYON_KEYS, (), "rayon"):
            return

        # rayons zijn statisch gedefinieerd, met een extra beschrijving
        # controleer alleen of er onverwacht een wijziging is die we over moeten nemen
        for rayon in data:
            self._count_rayons += 1
            rayon_nr = rayon['rayon_number']
            rayon_naam = rayon['name']

            # zoek het rayon op
            obj = self._vind_rayon(rayon_nr)
            if not obj:
                # toevoegen van een rayon ondersteunen we niet
                self.stderr.write('[ERROR] Onbekend rayon %s' % repr(rayon))
                self._count_errors += 1
            else:
                if obj.naam != rayon_naam:
                    self.stdout.write('[INFO] Wijziging naam rayon %s: %s --> %s' % (rayon_nr, repr(obj.naam), repr(rayon_naam)))
                    self._count_wijzigingen += 1
                    obj.naam = rayon_naam
                    if not self.dryrun:
                        obj.save(update_fields=['naam'])
        # for
        # verwijderen van een rayon ondersteunen we niet

    def _import_regions(self, data):
        """ Importeert data van alle regios """

        if self._check_keys(data[0].keys(), EXPECTED_REGIO_KEYS, (), "regio"):
            return

        # regios zijn statisch gedefinieerd
        # naam alleen de naam over
        for regio in data:
            self._count_regios += 1
            # rayon_nr = regio['rayon_number']
            regio_nr = regio['region_number']
            regio_naam = regio['name']

            # zoek de regio op
            obj = self._vind_regio(regio_nr)
            if not obj:
                # toevoegen van een regio ondersteunen we niet
                self.stderr.write('[ERROR] Onbekende regio %s' % repr(regio))
                self._count_errors += 1
            else:
                if obj.naam != regio_naam:
                    self.stdout.write('[INFO] Wijziging naam regio %s: %s --> %s' % (regio_nr, repr(obj.naam), repr(regio_naam)))
                    self._count_wijzigingen += 1
                    obj.naam = regio_naam
                    if not self.dryrun:
                        obj.save(update_fields=['naam'])
        # for
        # verwijderen van een regio ondersteunen we niet

    def _import_clubs(self, data):
        """ Importeert data van alle verenigingen """

        if self._check_keys(data[0].keys(), EXPECTED_CLUB_KEYS, (), "club"):
            return

        # houd bij welke verenigingsnummers in de database zitten
        # als deze niet meer voorkomen, dan zijn ze verwijderd
        ver_nrs = list(self._cache_ver.keys())

        """ JSON velden (string, except):
         'region_number':           int
         'club_number':             int
         'name',
         'prefix': None,            ???
         'phone_business',
         'phone_private',
         'phone_mobile': None,      ???
         'email',                   e-mailadres van de secretaris
         'website',                 vereniging website
         'has_disabled_facilities': boolean
         'address':                 string with newlines
         'postal_code',
         'location_name',
         'coc_number',              KvK nummer
         'iso_abbr': 'NL',          ???
         'latitude', 'longitude',
         'iban', 'bic',
         'secretaris': [{'member_number': int}]
        }
        """

        website_validator = URLValidator(schemes=['http', 'https'])

        for club in data:
            self._count_clubs += 1

            ver_nr = club['club_number']
            try:
                ver_nr = int(ver_nr)
            except ValueError:
                self.stderr.write('[ERROR] Geen valide verenigingsnummer: %s (geen getal)' % repr(ver_nr))
                self._count_errors += 1
                continue

            ver_naam = club['name']
            # maak 1377 wat korter
            pos = ver_naam.find(' (geen deelname wedstrijden)')
            if pos > 0:
                ver_naam = ver_naam[:pos]

            if club['prefix']:
                ver_naam = club['prefix'] + ' ' + ver_naam
            ver_regio = club['region_number']

            ver_plaats = club['location_name']
            if not ver_plaats:
                # een vereniging zonder doel heeft een lege location_name - geen waarschuwing geven
                ver_plaats = ""     # voorkom None
            else:
                ver_plaats = ver_plaats.strip()

            ver_email = club['email']
            if not ver_email:
                self.stdout.write('[WARNING] Vereniging %s (%s) heeft geen contact email' % (ver_nr, ver_naam))
                self._count_warnings += 1
                ver_email = ""      # voorkom None

            ver_geen_wedstrijden = (ver_nr in GEEN_WEDSTRIJDEN)

            ver_kvk = club['coc_number']
            if ver_kvk is None:
                ver_kvk = ''
            ver_kvk = ver_kvk.strip()
            if not ver_kvk:
                self.stdout.write('[WARNING] Vereniging %s heeft geen KvK nummer' % ver_nr)
            elif len(ver_kvk) != 8 or not ver_kvk.isdecimal():
                self.stdout.write('[WARNING] Vereniging %s KvK nummer %s moet 8 cijfers bevatten' % (ver_nr, repr(ver_kvk)))

            ver_website = club['website']
            if ver_website is None:
                ver_website = ''
            ver_website = ver_website.strip()
            if ver_website:
                try:
                    website_validator(ver_website)
                except ValidationError as exc:
                    self.stdout.write('[WARNING] Vereniging %s website url: %s bevat fout (%s)' % (
                                        ver_nr, repr(ver_website), str(exc)))
                    ver_website = ''

            ver_tel_nr = ''
            for field_name in ('phone_business', 'phone_mobile', 'phone_private'):
                phone = club[field_name]
                if phone is None:
                    phone = ''
                phone = phone.strip()
                if phone:
                    ver_tel_nr = phone
                    break
            # for

            ver_adres1 = ''
            ver_adres2 = ''
            # address = "Straat 9\n1234 AB  Plaats\n"
            adres = club['address']
            if not adres:       # handles None and ''
                self.stdout.write('[WARNING] Vereniging %s heeft geen adres' % ver_nr)
            else:
                adres_spl = adres.strip().split('\n')
                if len(adres_spl) != 2:
                    self.stderr.write('[ERROR] Vereniging %s adres bestaat niet uit 2 regels: %s' % (ver_nr, repr(club['address'])))
                if len(adres_spl) >= 2:
                    ver_adres1 = adres_spl[0]
                    ver_adres2 = adres_spl[1]

            ver_iban = club['iban']
            ver_bic = club['bic']
            if ver_bic and ver_iban:
                # correcte situatie
                if len(ver_bic) not in (8, 11):
                    self.stderr.write('[ERROR] Vereniging %s heeft BIC %s met foute length %s (verwacht: 8 of 11) horende bij IBAN %s' % (
                                        ver_nr, repr(ver_bic), len(ver_bic), repr(ver_iban)))
                    ver_bic = None

                if len(ver_iban) != 18:
                    self.stderr.write('[ERROR] Vereniging %s heeft IBAN %s met foute length %s (verwacht: 18)' % (
                                        ver_nr, repr(ver_iban), len(ver_iban)))
                    ver_bic = None
            else:
                # een van de twee is afwezig
                if ver_bic and not ver_iban:
                    self.stdout.write('[WARNING] Vereniging %s heeft een BIC zonder IBAN: %s, %s' % (
                                            ver_nr, repr(ver_bic), repr(ver_iban)))
                elif ver_iban and not ver_bic:
                    self.stdout.write('[WARNING] Vereniging %s heeft een IBAN zonder BIC: %s, %s' % (
                                            ver_nr, repr(ver_bic), repr(ver_iban)))
                ver_bic = None

            if ver_bic:
                if ver_bic not in settings.BEKENDE_BIC_CODES:
                    self.stdout.write('[WARNING] Vereniging %s heeft een onbekende BIC code %s horende bij IBAN %s' % (
                                        ver_nr, repr(ver_bic), repr(ver_iban)))

            if ver_bic:
                # controleer de IBAN
                if not self._check_iban(ver_iban):
                    self.stderr.write('[ERROR] Vereniging %s heeft een foutieve IBAN: %s' % (ver_nr, repr(ver_iban)))
                    ver_bic = None

            # zet None om naar lege string
            if not ver_bic:
                ver_bic = ''
                ver_iban = ''

            # FUTURE: verdere velden: has_disabled_facilities, lat/lon,

            # zoek de vereniging op
            is_nieuw = False
            obj = self._vind_vereniging(ver_nr)
            if not obj:
                # nieuwe vereniging
                is_nieuw = True
            else:
                # bestaande vereniging
                ver_nrs.remove(ver_nr)

                # mutaties verwerken
                updated = list()
                if obj.regio.regio_nr != ver_regio:
                    regio_obj = self._vind_regio(ver_regio)
                    if regio_obj is None:
                        self.stderr.write('[ERROR] Kan vereniging %s niet wijzigen naar onbekende regio %s' % (ver_nr, ver_regio))
                        self._count_errors += 1
                    else:
                        self.stdout.write('[INFO] Wijziging van regio van vereniging %s: %s --> %s' % (ver_nr, obj.regio.regio_nr, ver_regio))
                        self._count_wijzigingen += 1
                        obj.regio = regio_obj
                        updated.append('regio')

                if obj.naam != ver_naam:
                    self.stdout.write('[INFO] Wijziging van naam van vereniging %s: "%s" --> "%s"' % (ver_nr, obj.naam, ver_naam))
                    self._count_wijzigingen += 1
                    obj.naam = ver_naam
                    updated.append('naam')

                if obj.plaats != ver_plaats:
                    self.stdout.write('[INFO] Wijziging van plaats van vereniging %s: "%s" --> "%s"' % (ver_nr, obj.plaats, ver_plaats))
                    self._count_wijzigingen += 1
                    obj.plaats = ver_plaats
                    updated.append('plaats')

                if obj.geen_wedstrijden != ver_geen_wedstrijden:
                    self.stdout.write("[INFO] Wijziging van 'geen wedstrijden' van vereniging %s: %s --> %s" % (ver_nr, obj.geen_wedstrijden, ver_geen_wedstrijden))
                    self._count_wijzigingen += 1
                    obj.geen_wedstrijden = ver_geen_wedstrijden
                    updated.append('geen_wedstrijden')

                if obj.kvk_nummer != ver_kvk:
                    self.stdout.write("[INFO] Wijziging van KvK nummer van vereniging %s: %s --> %s" % (ver_nr, obj.kvk_nummer, ver_kvk))
                    self._count_wijzigingen += 1
                    obj.kvk_nummer = ver_kvk
                    updated.append('kvk_nummer')

                if obj.website != ver_website:
                    self.stdout.write("[INFO] Wijziging van website van vereniging %s: %s --> %s" % (ver_nr, obj.website, ver_website))
                    self._count_wijzigingen += 1
                    obj.website = ver_website
                    updated.append('website')

                if obj.contact_email != ver_email:
                    self.stdout.write("[INFO] Wijziging van contact_email van vereniging %s: %s --> %s" % (ver_nr, obj.contact_email, ver_email))
                    self._count_wijzigingen += 1
                    obj.contact_email = ver_email
                    updated.append('contact_email')

                if obj.telefoonnummer != ver_tel_nr:
                    self.stdout.write("[INFO] Wijziging van telefoonnummer van vereniging %s: %s --> %s" % (ver_nr, obj.telefoonnummer, ver_tel_nr))
                    self._count_wijzigingen += 1
                    obj.telefoonnummer = ver_tel_nr
                    updated.append('telefoonnummer')

                if obj.adres_regel1 != ver_adres1:
                    self.stdout.write("[INFO] Wijziging van adres regel 1 van vereniging %s: %s --> %s" % (ver_nr, obj.adres_regel1, ver_adres1))
                    self._count_wijzigingen += 1
                    obj.adres_regel1 = ver_adres1
                    updated.append('adres_regel1')

                if obj.adres_regel2 != ver_adres2:
                    self.stdout.write("[INFO] Wijziging van adres regel 2 van vereniging %s: %s --> %s" % (ver_nr, obj.adres_regel2, ver_adres2))
                    self._count_wijzigingen += 1
                    obj.adres_regel2 = ver_adres2
                    updated.append('adres_regel2')

                if obj.bank_iban != ver_iban:
                    self.stdout.write("[INFO] Wijziging van IBAN van vereniging %s: %s --> %s" % (ver_nr, obj.bank_iban, ver_iban))
                    self._count_wijzigingen += 1
                    obj.bank_iban = ver_iban
                    updated.append('bank_iban')

                if obj.bank_bic != ver_bic:
                    self.stdout.write("[INFO] Wijziging van BIC van vereniging %s: %s --> %s" % (ver_nr, obj.bank_bic, ver_bic))
                    self._count_wijzigingen += 1
                    obj.bank_bic = ver_bic
                    updated.append('bank_bic')

                if not self.dryrun:
                    obj.save(update_fields=updated)

            if is_nieuw:
                obj = None
                ver = NhbVereniging()
                ver.ver_nr = ver_nr
                ver.naam = ver_naam
                ver.plaats = ver_plaats
                ver.geen_wedstrijden = ver_geen_wedstrijden
                ver.kvk_nummer = ver_kvk
                ver.website = ver_website
                ver.telefoonnummer = ver_tel_nr
                ver.contact_email = ver_email
                ver.adres_regel1 = ver_adres1
                ver.adres_regel2 = ver_adres2
                regio_obj = self._vind_regio(ver_regio)
                if not regio_obj:
                    self._count_errors += 1
                    self.stderr.write('[ERROR] Vereniging %s hoort bij onbekende regio %s' % (ver_nr, ver_regio))
                else:
                    self.stdout.write('[INFO] Vereniging %s aangemaakt: %s' % (ver_nr, repr(ver.naam)))
                    self._count_toevoegingen += 1
                    ver.regio = regio_obj
                    if not self.dryrun:
                        ver.save()
                        self._cache_ver[ver.pk] = ver
                    self._nieuwe_clubs.append(ver_nr)   # voor onderdrukken 'wijziging' secretaris
                    obj = ver

            # maak de functies aan voor deze vereniging
            if obj:
                # let op: in sync houden met migratie m0012_migrate_cwz_hwl
                for rol, beschr in (('WL', 'Wedstrijdleider %s'),
                                    ('HWL', 'Hoofdwedstrijdleider %s'),
                                    ('SEC', 'Secretaris vereniging %s')):

                    beschrijving = beschr % obj.ver_nr
                    functie = self._vind_functie(rol, beschrijving)
                    if not functie:
                        functie = maak_functie(beschrijving, rol)
                        tup = (rol, beschrijving)
                        self._cache_functie[tup] = functie

                    updated = list()

                    if functie.nhb_ver != obj:
                        functie.nhb_ver = obj
                        updated.append('nhb_ver')

                    if rol == 'SEC':
                        # secretaris functie krijgt email uit CRM
                        if functie.bevestigde_email != ver_email and functie.bevestigde_email != "":
                            self.stdout.write('[INFO] Wijziging van secretaris email voor vereniging %s: "%s" --> "%s"' % (
                                                    ver_nr, functie.bevestigde_email, ver_email))
                            self._count_wijzigingen += 1
                        functie.bevestigde_email = ver_email
                        functie.nieuwe_email = ''       # voor de zekerheid opruimen
                        updated.extend(['bevestigde_email', 'nieuwe_email'])

                    if not self.dryrun:
                        functie.save(update_fields=updated)
                # for
        # for

        # kijk of er verenigingen verwijderd moeten worden
        while len(ver_nrs) > 0:
            ver_nr = ver_nrs.pop(0)
            obj = self._vind_vereniging(ver_nr)
            self.stdout.write('[INFO] Vereniging %s wordt nu verwijderd' % str(obj))
            if not self.dryrun:
                # kan alleen als er geen leden maar aan hangen --> de modellen beschermen dit automatisch
                # vang de gerelateerde exceptie af
                try:
                    del self._cache_ver[obj.pk]
                    obj.delete()
                    self._count_verwijderingen += 1
                except ProtectedError as exc:       # pragma: no cover
                    self._count_errors += 1
                    self.stderr.write('[ERROR] Onverwachte fout bij het verwijderen van een vereniging: %s' % str(exc))
        # while

    def _import_clubs_secretaris(self, data):
        """ voor elke club, koppel de secretaris aan een Sporter """

        if self._check_keys(data[0].keys(), EXPECTED_CLUB_KEYS, (), "club"):
            return

        for club in data:
            ver_nr = club['club_number']
            try:
                ver_nr = int(ver_nr)
            except ValueError:
                # is al eerder gerapporteerd
                continue        # met de for

            ver_naam = club['name']

            if len(club['secretaris']) < 1:
                ver_secretaris = None
            else:
                ver_secretaris_nr = club['secretaris'][0]['member_number']
                ver_secretaris = self._vind_sporter(ver_secretaris_nr)
                if ver_secretaris is None:
                    self.stderr.write('[ERROR] Kan secretaris %s van vereniging %s niet vinden' % (
                                            ver_secretaris_nr, ver_nr))
                    self._count_errors += 1

            # zoek de vereniging op
            obj = self._vind_vereniging(ver_nr)
            if not obj:
                # zou niet moeten gebeuren
                self.stderr.write('[ERROR] Kan vereniging %s niet terugvinden' % ver_nr)
                self._count_errors += 1
            else:
                # zoek het secretaris record op
                sec = self._vind_sec(ver_nr)
                if not sec:
                    # maak een nieuw record aan
                    sec = Secretaris(vereniging=obj, sporter=None)
                    sec.save()
                    self._cache_sec[obj.ver_nr] = sec

                if sec.sporter != ver_secretaris:
                    if ver_nr not in self._nieuwe_clubs:
                        old_sec_str = get_secretaris_str(sec.sporter)
                        new_sec_str = get_secretaris_str(ver_secretaris)
                        self.stdout.write('[INFO] Wijziging van secretaris voor vereniging %s: %s --> %s' % (
                                                ver_nr, old_sec_str, new_sec_str))
                        self._count_wijzigingen += 1

                    sec.sporter = ver_secretaris
                    if not self.dryrun:
                        sec.save(update_fields=['sporter'])

                if not ver_secretaris:
                    if ver_nr not in GEEN_SECRETARIS_NODIG:
                        self.stderr.write('[WARNING] Vereniging %s (%s) heeft geen secretaris!' % (ver_nr, ver_naam))
                        self._count_warnings += 1

                # forceer de secretaris in de SEC groep
                if ver_secretaris:
                    try:
                        account = Account.objects.get(sporter=ver_secretaris)
                    except Account.DoesNotExist:
                        # SEC heeft nog geen account
                        self.stdout.write("[INFO] Secretaris %s van vereniging %s heeft nog geen account" % (
                                                ver_secretaris.lid_nr, obj.ver_nr))
                        self._count_sec_no_account += 1
                    else:
                        if maak_account_vereniging_secretaris(obj, account):
                            self.stdout.write("[INFO] Secretaris %s van vereniging %s is gekoppeld aan SEC functie" % (
                                                    ver_secretaris.lid_nr, obj.ver_nr))
        # for

    @staticmethod
    def _corrigeer_tussenvoegsel(lid_nr, tussenvoegsel, achternaam):
        if tussenvoegsel and tussenvoegsel[0].isupper():
            laag = tussenvoegsel.lower()
            if laag in ('de', 'den', 'van', 'van de', 'van der', 'van den', 'ter', 'van t'):
                tussenvoegsel = laag
            # else:
            #     print(lid_nr, tussenvoegsel, achternaam)
        return tussenvoegsel

    def _import_members(self, data):
        """ Importeert data van alle leden """

        if self._check_keys(data[0].keys(), EXPECTED_MEMBER_KEYS, OPTIONAL_MEMBER_KEYS, "member"):
            return

        # houd bij welke leden lid_nrs in de database zitten
        # als deze niet meer voorkomen, dan zijn ze verwijderd
        lid_nrs = list(self._cache_sporter.keys())

        """ JSON velden (string, except):
             'club_number':         int,
             'member_number':       int,
             'name',
             'prefix',              is tussenvoegsel
             'first_name',
             'initials',
             'birthday':            string YYYY-MM-DD
             'email',
             'gender':              'M' or 'V'
             'member_from':         string YYYY-MM-DD
             'para_code': None      ???
             'address':             string with newlines
             'postal_code',
             'location_name',
             'iso_abbr': 'NL',      ???
             'latitude',
             'longitude',
             'blocked'              bool
        """
        for member in data:
            is_valid = True

            lid_nr = member['member_number']

            # silently skip some numbers
            if lid_nr in SKIP_MEMBERS:
                continue

            try:
                lid_nr = int(lid_nr)
            except ValueError:
                self.stderr.write('[ERROR] Foutief bondsnummer: %s (geen getal)' % lid_nr)
                continue

            lid_voornaam = member['first_name']
            if not lid_voornaam:
                lid_voornaam = member['initials']
                if not lid_voornaam:
                    self.stderr.write('[ERROR] Lid %s heeft geen voornaam of initials' % lid_nr)
                    self._count_errors += 1
                    continue

            lid_achternaam = member['name']
            if not lid_achternaam:
                self.stderr.write("[ERROR] Lid %s heeft geen achternaam" % lid_nr)
                self._count_errors += 1
                continue        # data niet compleet voor dit lid

            pos = lid_achternaam.find('(')
            if pos > 0:
                new_achternaam = lid_achternaam[:pos].strip()
                self.stdout.write("[WARNING] Lid %s: verwijder toevoeging achternaam: %s --> %s" % (
                                            lid_nr, repr(lid_achternaam), repr(new_achternaam)))
                self._count_warnings += 1
                lid_achternaam = new_achternaam

            if member['prefix']:
                lid_achternaam = self._corrigeer_tussenvoegsel(lid_nr, member['prefix'], lid_achternaam) + ' ' + lid_achternaam

            naam = lid_voornaam + ' ' + lid_achternaam
            lid_unaccented_naam = maak_unaccented(naam)
            if naam.count('(') != naam.count(')'):
                self.stdout.write('[WARNING] Lid %s: onbalans in haakjes in %s' % (lid_nr, repr(naam)))
                self._count_warnings += 1

            for letter in "!@#$%^&*[]{}=_+\\|\":;,<>/?~`":
                if letter in naam:
                    self.stdout.write("[WARNING] Lid %s: rare tekens in naam %s" % (lid_nr, repr(naam)))
                    self._count_warnings += 1
            # for

            lid_blocked = member['blocked']

            if not member['club_number']:
                # ex-leden hebben geen vereniging, dus niet te veel klagen
                lid_ver = None
            else:
                lid_ver = self._vind_vereniging(member['club_number'])
                if not lid_ver:
                    lid_blocked = True
                    self.stderr.write('[ERROR] Kan vereniging %s voor lid %s niet vinden' % (
                                            repr(member['club_number']), lid_nr))
                    self._count_errors += 1

            if not lid_blocked:
                if member['birthday'] and member['birthday'][0:0+2] not in ("19", "20"):
                    # poging tot repareren
                    if member['birthday'][0:0+2] == "00":
                        old_birthday = member['birthday']
                        year = int(old_birthday[2:2+2])
                        if year < 25:
                            member['birthday'] = '20' + old_birthday[2:]
                        else:
                            member['birthday'] = '19' + old_birthday[2:]
                        self.stderr.write('[WARNING] Lid %s geboortedatum gecorrigeerd van %s naar %s' % (
                                                lid_nr, old_birthday, member['birthday']))
                        self._count_warnings += 1
                    else:
                        is_valid = False
                        self.stderr.write('[ERROR] Lid %s heeft geen valide geboortedatum: %s' % (
                                                lid_nr, member['birthday']))
                        self._count_errors += 1
            try:
                lid_geboorte_datum = datetime.datetime.strptime(member['birthday'], "%Y-%m-%d").date()  # YYYY-MM-DD
            except (ValueError, TypeError):
                lid_geboorte_datum = None
                is_valid = False
                if not lid_blocked:         # pragma: no branch
                    self.stderr.write('[ERROR] Lid %s heeft geen valide geboortedatum' % lid_nr)
                    self._count_errors += 1

            lid_geslacht = member['gender']
            if lid_geslacht not in ('M', 'F', 'X'):
                self.stderr.write('[ERROR] Lid %s heeft onbekend geslacht: %s (moet zijn: M of F)' % (
                                        lid_nr, lid_geslacht))
                self._count_errors += 1
                lid_geslacht = 'M'  # forceer naar iets valide
            if lid_geslacht == 'F':
                lid_geslacht = 'V'

            lid_para = member['para_code']
            if lid_para is None:
                lid_para = ""      # converts None to string

            if member['member_from'] and member['member_from'][0:0+2] not in ("19", "20"):
                self.stderr.write('[ERROR] Lid %s heeft geen valide datum lidmaatschap: %s' % (
                                        lid_nr, member['member_from']))
                self._count_errors += 1
            try:
                lid_sinds = datetime.datetime.strptime(member['member_from'], "%Y-%m-%d").date()  # YYYY-MM-DD
            except (ValueError, TypeError):
                lid_sinds = None
                is_valid = False
                self.stderr.write('[ERROR] Lid %s heeft geen valide lidmaatschapsdatum: %s' % (
                                        lid_nr, repr(member['member_from'])))
                self._count_errors += 1

            lid_email = member['email']
            if not lid_email:
                lid_email = ""  # converts potential None to string

            if not is_valid:
                continue

            lid_adres_code = ''
            postcode = member['postal_code']
            postadres = member['address']
            if postcode is not None and postadres is not None:
                postcode = postcode.upper()     # sommige postcodes zijn kleine letters
                pos = postadres.find(postcode)
                if pos < 0:
                    self.stderr.write('[ERROR] Postcode %s niet gevonden in adres %s' % (repr(postcode), repr(postadres)))
                else:
                    postadres = postadres[:pos].strip()
                    spl = postadres.split(' ')
                    lid_adres_code = postcode.replace(' ', '') + spl[-1]
            # self.stdout.write('[DEBUG] lid_nr=%s, lid_adres_code=%s' % (lid_nr, repr(lid_adres_code)))

            # try:
            #     lid_edu = member['educations']
            #     print('lid: %s, edu: %s' % (lid_nr, repr(lid_edu)))
            #     #"educations": [
            #     #    {"code": "011", "name": "HANDBOOGTRAINER A", "date_start": "1990-01-01", "date_stop": "1990-01-01"},
            #     #    {"code": "031", "name": "WEDSTRIJDLEIDER INDOOR\/OUTDOOR", "date_start": "1990-01-01", "date_stop": "1990-01-01"}]
            # except KeyError:
            #     lid_edu = ''

            try:
                lid_sterk = member['skill_levels']
            except KeyError:
                lid_sterk = list()

            self._count_members += 1

            is_nieuw = False
            obj = self._vind_sporter(lid_nr)
            if not obj:
                # nieuw lid
                is_nieuw = True
            else:
                try:
                    # krimp de lijst zodat verwijderde leden over blijven
                    lid_nrs.remove(lid_nr)
                except ValueError:
                    self.stderr.write("[ERROR] Unexpected: lid_nr %s onverwacht niet in lijst bestaande nhb nrs" % (
                                            repr(lid_nr)))
                    self._count_errors += 1
                else:
                    updated = list()
                    if obj.lid_tot_einde_jaar != self.lidmaatschap_jaar:
                        if lid_ver:
                            # lid bij een vereniging, dus het geldt weer een jaar
                            obj.lid_tot_einde_jaar = self.lidmaatschap_jaar
                            # noteer: geen log regel
                            updated.append('lid_tot_einde_jaar')
                        else:
                            lid_blocked = True

                    if not lid_email:
                        if not lid_blocked:
                            self._count_lid_no_email += 1
                    elif not mailer_email_is_valide(lid_email):     # check alle email adressen
                        self.stderr.write('[ERROR] Lid %s heeft geen valide e-mail (%s)' % (lid_nr, lid_email))
                        self._count_errors += 1
                        self._count_lid_no_email += 1
                        lid_email = ""  # convert invalid email to no email

                    if obj.bij_vereniging != lid_ver:
                        if lid_ver:
                            self.stdout.write('[INFO] Lid %s: vereniging %s --> %s' % (
                                        lid_nr, get_vereniging_str(obj.bij_vereniging), get_vereniging_str(lid_ver)))
                            self._count_wijzigingen += 1
                            obj.bij_vereniging = lid_ver
                            updated.append('bij_vereniging')
                        else:
                            # als het lid uitgeschreven wordt in het CRM houden we de oude vereniging
                            # vast, tot het einde van het lidmaatschap jaar.
                            # dit voorkomt blokkeren en geen toegang tot de diensten tijdens een overschrijving
                            if obj.lid_tot_einde_jaar < self.lidmaatschap_jaar:
                                self.stdout.write('[INFO] Lid %s: vereniging %s --> geen (einde lidmaatschap jaar)' % (
                                            lid_nr, get_vereniging_str(obj.bij_vereniging)))
                                self._count_wijzigingen += 1
                                obj.bij_vereniging = None
                                updated.append('bij_vereniging')
                                lid_blocked = True
                            else:
                                self._count_uitgeschreven += 1

                        # FUTURE: overschrijven tijdens regiocompetitie, bij afsluiten team ronde

                        # let op: tijdens fase G van de competitie wordt de vereniging bevroren en moet de sporter
                        #         uitkomen op het RK van het rayon waarin die vereniging valt

                    if lid_blocked:
                        if obj.is_actief_lid:
                            self.stdout.write('[INFO] Lid %s: is_actief_lid ja --> nee (want blocked)' % lid_nr)
                            self._count_wijzigingen += 1
                            obj.is_actief_lid = False
                            updated.append('is_actief_lid')
                    else:
                        if not obj.is_actief_lid:
                            self.stdout.write('[INFO] Lid %s: is_actief_lid nee --> ja' % lid_nr)
                            self._count_wijzigingen += 1
                            obj.is_actief_lid = True
                            updated.append('is_actief_lid')

                    if obj.voornaam != lid_voornaam or obj.achternaam != lid_achternaam:
                        self.stdout.write('[INFO] Lid %s: naam %s %s --> %s %s' % (
                                                lid_nr, obj.voornaam, obj.achternaam, lid_voornaam, lid_achternaam))
                        obj.voornaam = lid_voornaam
                        obj.achternaam = lid_achternaam
                        updated.extend(['voornaam', 'achternaam'])
                        self._count_wijzigingen += 1

                    if lid_unaccented_naam != obj.unaccented_naam:
                        obj.unaccented_naam = lid_unaccented_naam
                        updated.append('unaccented_naam')
                        # niet nodig om rapporteren want gekoppeld aan naam

                    if obj.email != lid_email:
                        self.stdout.write('[INFO] Lid %s e-mail: %s --> %s' % (
                                                lid_nr, repr(obj.email), repr(lid_email)))
                        obj.email = lid_email
                        updated.append('email')
                        self._count_wijzigingen += 1

                    if obj.geslacht != lid_geslacht:
                        self.stdout.write('[INFO] Lid %s geslacht: %s --> %s' % (
                                                lid_nr, obj.geslacht, lid_geslacht))
                        obj.geslacht = lid_geslacht
                        updated.append('geslacht')
                        self._count_wijzigingen += 1

                    if obj.geboorte_datum != lid_geboorte_datum:
                        self.stdout.write('[INFO] Lid %s geboortedatum: %s --> %s' % (
                                                lid_nr, obj.geboorte_datum, lid_geboorte_datum))
                        obj.geboorte_datum = lid_geboorte_datum
                        updated.append('geboorte_datum')
                        self._count_wijzigingen += 1

                    if obj.sinds_datum != lid_sinds:
                        self.stdout.write('[INFO] Lid %s: sinds_datum: %s --> %s' % (
                                                lid_nr, obj.sinds_datum, lid_sinds))
                        obj.sinds_datum = lid_sinds
                        updated.append('sinds_datum')
                        self._count_wijzigingen += 1

                    if obj.para_classificatie != lid_para:
                        self.stdout.write('[INFO] Lid %s: para_classificatie: %s --> %s' % (
                                                lid_nr, repr(obj.para_classificatie), repr(lid_para)))
                        obj.para_classificatie = lid_para
                        updated.append('para_classificatie')
                        self._count_wijzigingen += 1

                    if obj.adres_code != lid_adres_code:
                        if obj.adres_code != '':        # laat toegevoegd veld: voorkom duizenden regels in de log
                            self.stdout.write('[INFO] Lid %s: adres_code %s --> %s' % (
                                                lid_nr, repr(obj.adres_code), repr(lid_adres_code)))
                        obj.adres_code = lid_adres_code
                        updated.append('adres_code')
                        self._count_wijzigingen += 1

                    if not self.dryrun:
                        obj.save(update_fields=updated)
                        self._cache_sporter[obj.pk] = obj

                        # wijziging van geslacht
                        if 'geslacht' in updated:
                            voorkeuren = obj.sportervoorkeuren_set.all()
                            if len(voorkeuren) > 0:
                                voorkeuren = voorkeuren[0]

                                if lid_geslacht == 'X':
                                    # wijziging naar geslacht X
                                    # geef mogelijkheid om een keuze te maken voor de wedstrijden
                                    voorkeuren.wedstrijd_geslacht_gekozen = False
                                    self.stdout.write(
                                        '[INFO] Lid %s voorkeuren: wedstrijd geslacht instelbaar gemaakt' % lid_nr)
                                else:
                                    # forceer vaste geslacht voor wedstrijden
                                    voorkeuren.wedstrijd_geslacht_gekozen = True
                                    voorkeuren.wedstrijd_geslacht = lid_geslacht
                                    self.stdout.write('[INFO] Lid %s voorkeuren: wedstrijd geslacht vastgezet' % lid_nr)

                                voorkeuren.save(update_fields=['wedstrijd_geslacht_gekozen', 'wedstrijd_geslacht'])
                # else
            # else

            if lid_blocked:
                self._count_blocked += 1

            if is_nieuw:

                if not lid_email:
                    self._count_lid_no_email += 1
                elif not mailer_email_is_valide(lid_email):  # check alle email adressen
                    self.stderr.write('[ERROR] Lid %s heeft geen valide e-mail (%s)' % (lid_nr, lid_email))
                    self._count_errors += 1
                    self._count_lid_no_email += 1
                    lid_email = ""  # convert invalid email to no email

                obj = Sporter()
                obj.lid_nr = lid_nr
                obj.voornaam = lid_voornaam
                obj.achternaam = lid_achternaam
                obj.email = lid_email
                obj.geboorte_datum = lid_geboorte_datum
                obj.geslacht = lid_geslacht
                obj.para_classificatie = lid_para
                obj.sinds_datum = lid_sinds
                obj.bij_vereniging = lid_ver
                obj.lid_tot_einde_jaar = self.lidmaatschap_jaar
                obj.adres_code = lid_adres_code
                if lid_blocked:
                    obj.is_actief_lid = False
                if not self.dryrun:
                    obj.save()
                    self._cache_sporter[obj.pk] = obj
                self._count_toevoegingen += 1

            # speel sterkte verwerken
            nieuwe_lijst = list()
            try:
                huidige_lijst = self._cache_sterk[lid_nr]
            except KeyError:
                huidige_lijst = list()

            for sterk in lid_sterk:
                # sterk = {"date": "1990-01-01", "skill_level_code": "R1000", "skill_level_name": "Recurve 1000", "discipline_code": "REC", "discipline_name": "Recurve", "category_name": "Senior"}
                cat = sterk['category_name']
                disc = sterk['discipline_name']
                datum_raw = sterk['date']
                beschr = sterk['skill_level_name']

                try:
                    datum = datetime.datetime.strptime(datum_raw, "%Y-%m-%d").date()  # YYYY-MM-DD
                except (ValueError, TypeError):
                    self.stderr.write('[ERROR] Lid %s heeft skill level met slechte datum: %s' % (
                                            lid_nr, repr(datum_raw)))
                    self._count_errors += 1
                else:
                    # kijk of deze al bestaat
                    found = None
                    for huidig in huidige_lijst:
                        if huidig.beschrijving == beschr and huidig.discipline == disc and huidig.category == cat:
                            # bestaat al
                            found = huidig
                            break   # from the for
                    # for

                    if found:
                        # verwijderen uit de lijst zodat echt verwijderde speelsterktes kunnen vinden
                        huidige_lijst.remove(found)
                    else:
                        # toevoegen
                        self.stdout.write('[INFO] Lid %s: nieuwe speelsterkte %s, %s, %s' % (lid_nr, datum, disc, beschr))

                        try:
                            volgorde = self._speelsterkte2volgorde[(disc, beschr)]
                        except KeyError:
                            volgorde = 9999
                            self.stderr.write('[WARNING] Kan speelsterkte volgorde niet vaststellen voor: (%s, %s)' % (
                                                    repr(disc), repr(beschr)))
                            self._count_errors += 1

                        sterk = Speelsterkte(
                                     sporter=obj,
                                     beschrijving=beschr,
                                     discipline=disc,
                                     category=cat,
                                     volgorde=volgorde,
                                     datum=datum)
                        nieuwe_lijst.append(sterk)
                        self._count_toevoegingen += 1
            # for

            if len(huidige_lijst):
                # FUTURE: verwijder oude speelsterktes
                self.stderr.write('[WARNING] Kan speelsterktes nog niet verwijderen: lid=%s, te verwijderen: %s' % (lid_nr, repr(huidige_lijst)))
                # self._count_verwijderingen += 1

            if len(nieuwe_lijst):
                Speelsterkte.objects.bulk_create(nieuwe_lijst)
        # for

        # self.stdout.write('[DEBUG] Volgende %s NHB nummers moeten verwijderd worden: %s' % (len(lid_nrs), repr(lid_nrs)))
        while len(lid_nrs) > 0:
            lid_nr = lid_nrs.pop(0)
            obj = self._vind_sporter(lid_nr)
            if obj.is_actief_lid:
                self.stdout.write('[INFO] Lid %s: is_actief_lid: ja --> nee' % repr(lid_nr))
                obj.is_actief_lid = False
                self._count_wijzigingen += 1
                self.stdout.write('               vereniging %s --> geen' % get_vereniging_str(obj.bij_vereniging))
                obj.bij_vereniging = None
                self._count_wijzigingen += 1
                if not self.dryrun:
                    obj.save()
                    self._cache_sporter[obj.pk] = obj
                # FUTURE: afhandelen van het inactiveren/verwijderen van een lid dat in een team zit in een competitie
                # FUTURE: afhandelen van het inactiveren/verwijderen van een lid dat secretaris is
            elif obj.lid_nr in self._recordhouder_lid_nrs:
                # lid heeft een record op zijn/haar naam --> behoud het hele record
                # de CRM applicatie heeft hier nog geen veld voor
                self.stdout.write('[INFO] Lid %s is recordhouder en wordt daarom niet verwijderd' % obj.lid_nr)
            else:
                # lid echt verwijderen
                #
                # echt verwijderen van een lid is een groot risico gezien aangezien het verwijderen
                # van gerelateerde records tot onrepareerbare schade kan lijden.
                #
                # de database structuur is beveiligd tegen het verwijderen van records die nog in gebruik zijn
                # daarnaast hebben we ook altijd nog de backups.
                # daarom is het en acceptabel risico om deze leden echt te verwijderen.

                self.stdout.write('[INFO] Lid %s wordt nu verwijderd' % str(obj))
                if not self.dryrun:
                    try:
                        del self._cache_sporter[obj.pk]
                        obj.delete()
                        self._count_verwijderingen += 1
                    except ProtectedError as exc:
                        self._count_errors += 1
                        self.stderr.write('[ERROR] Onverwachte fout bij het verwijderen van een lid: %s' % str(exc))
        # while

    def _import_wedstrijdlocaties(self, data):
        """ Importeert data van verenigingen als basis voor wedstrijdlocaties """

        if self._check_keys(data[0].keys(), EXPECTED_CLUB_KEYS, (), "club"):
            return

        # voor overige velden, zie _import_clubs
        """ JSON velden (string, except):
         'club_number':             int
         'phone_business',
         'phone_private',
         'phone_mobile': None,      ???
         'email', 'website',
         'has_disabled_facilities': boolean
         'address':                 string with newlines
         'postal_code',
         'location_name',
         'latitude', 'longitude',
        }
        """

        for club in data:
            ver_nr = club['club_number']

            if ver_nr in GEEN_WEDSTRIJDLOCATIE:
                continue

            nhb_ver = self._vind_vereniging(ver_nr)
            if not nhb_ver:
                continue

            # een vereniging zonder doel heeft een lege location_name
            adres = ""
            plaats = ""
            if club['location_name']:
                plaats = club['location_name']
                plaats = plaats.strip()
                adres = club['address']
                if not adres:
                    adres = ""
                plaats = plaats.strip()
                adres = adres.strip()     # remove terminating \n

            if not adres:
                # vereniging heeft geen adres meer
                # verwijder de koppeling met wedstrijdlocatie uit crm
                for obj in nhb_ver.wedstrijdlocatie_set.filter(adres_uit_crm=True):
                    nhb_ver.wedstrijdlocatie_set.remove(obj)
                    self.stdout.write('[INFO] Wedstrijdlocatie %s ontkoppeld voor vereniging %s' % (repr(obj.adres), ver_nr))
                    self._count_wijzigingen += 1
                continue

            # zoek de wedstrijdlocatie bij dit adres
            try:
                wedstrijdlocatie = (WedstrijdLocatie
                                    .objects
                                    .exclude(baan_type__in=(BAAN_TYPE_BUITEN, BAAN_TYPE_EXTERN))
                                    .get(adres=adres))
            except WedstrijdLocatie.MultipleObjectsReturned:            # pragma: no cover
                # er is een ongelukje gebeurt
                self.stderr.write('[ERROR] Onverwacht meer dan 1 wedstrijdlocatie voor vereniging %s' % nhb_ver)
                continue
            except WedstrijdLocatie.DoesNotExist:
                # nieuw aanmaken
                wedstrijdlocatie = WedstrijdLocatie(
                                        adres=adres,
                                        plaats=plaats,
                                        adres_uit_crm=True)
                wedstrijdlocatie.save()
                self.stdout.write('[INFO] Nieuwe wedstrijdlocatie voor adres %s' % repr(adres))
                self._count_toevoegingen += 1
            else:
                # indien nog niet ingevuld, zet de plaats
                if wedstrijdlocatie.plaats != plaats:
                    wedstrijdlocatie.plaats = plaats
                    wedstrijdlocatie.save(update_fields=['plaats'])

            # adres van locatie mag niet wijzigen
            # dus als vereniging een ander adres heeft, ontkoppel dan de oude locatie
            for obj in (nhb_ver
                        .wedstrijdlocatie_set
                        .exclude(adres_uit_crm=False)           # niet extern/buitenbaan
                        .exclude(pk=wedstrijdlocatie.pk)):
                nhb_ver.wedstrijdlocatie_set.remove(obj)
                self.stdout.write('[INFO] Vereniging %s ontkoppeld van wedstrijdlocatie met adres %s' % (nhb_ver, repr(obj.adres)))
                self._count_wijzigingen += 1
            # for

            if wedstrijdlocatie.verenigingen.filter(ver_nr=ver_nr).count() == 0:
                # maak koppeling tussen vereniging en wedstrijdlocatie
                wedstrijdlocatie.verenigingen.add(nhb_ver)
                self.stdout.write('[INFO] Vereniging %s gekoppeld aan wedstrijdlocatie %s' % (nhb_ver, repr(adres)))
                self._count_toevoegingen += 1

            # zoek ook de buitenbaan van de vereniging erbij
            try:
                buiten_locatie = (nhb_ver
                                  .wedstrijdlocatie_set
                                  .get(baan_type=BAAN_TYPE_BUITEN,
                                       zichtbaar=True))
            except WedstrijdLocatie.DoesNotExist:
                # vereniging heeft geen buitenlocatie
                pass
            else:
                updated = list()
                if buiten_locatie.plaats != wedstrijdlocatie.plaats:
                    buiten_locatie.plaats = wedstrijdlocatie.plaats
                    updated.append('plaats')

                if buiten_locatie.adres != wedstrijdlocatie.adres:
                    buiten_locatie.adres = wedstrijdlocatie.adres
                    updated.append('adres')

                if len(updated):
                    buiten_locatie.save(update_fields=updated)
        # for

        # FUTURE: zichtbaar=False zetten voor wedstrijdlocatie zonder vereniging
        # FUTURE: zichtbaar=True zetten voor (revived) wedstrijdlocatie met vereniging

    def handle(self, *args, **options):
        self.dryrun = options['dryrun']
        fname = options['filename'][0]

        if options['sim_now']:
            try:
                sim_now = datetime.datetime.strptime(options['sim_now'][0], '%Y-%m-%d')
            except ValueError as exc:
                self.stderr.write('[ERROR] geen valide sim_now (%s)' % str(exc))
                return
            else:
                self.zet_lidmaatschap_jaar(sim_now)

        self.stdout.write('[INFO] lidmaatschap jaar = %s' % self.lidmaatschap_jaar)

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

        # vang generieke fouten af
        try:
            self._maak_cache()
            self._vind_recordhouders()
            self._import_rayons(data['rayons'])
            self._import_regions(data['regions'])
            # circular dependency: secretaris van vereniging is lid; lid hoort bij vereniging
            # doe clubs eerst, dan members, dan club.secretaris
            self._import_clubs(data['clubs'])
            self._import_members(data['members'])
            self._import_clubs_secretaris(data['clubs'])
            self._import_wedstrijdlocaties(data['clubs'])
        except DataError as exc:        # pragma: no cover
            _, _, tb = sys.exc_info()
            lst = traceback.format_tb(tb)
            self.stderr.write('[ERROR] Onverwachte database fout: %s' % str(exc))
            self.stderr.write('Traceback:')
            self.stderr.write(''.join(lst))

        self.stdout.write('Import van CRM data is klaar')
        # self.stdout.write("Read %s lines; skipped %s dupes; skipped %s errors; added %s records" % (line_nr, dupe_count, error_count, added_count))

        count_sterkte = Speelsterkte.objects.count()

        # rapporteer de samenvatting en schrijf deze ook in het logboek
        samenvatting = "Samenvatting: %s fouten; %s waarschuwingen; %s nieuw; %s wijzigingen; %s verwijderingen; "\
                       "%s leden, %s inactief, %s uitgeschreven; %s verenigingen; %s speelsterktes, %s secretarissen zonder account; %s regios; %s rayons; %s actieve leden zonder e-mail" %\
                       (self._count_errors,
                        self._count_warnings,
                        self._count_toevoegingen,
                        self._count_wijzigingen,
                        self._count_verwijderingen,
                        self._count_members - self._count_blocked,
                        self._count_blocked,
                        self._count_uitgeschreven,
                        self._count_clubs,
                        count_sterkte,
                        self._count_sec_no_account,
                        self._count_regios,
                        self._count_rayons,
                        self._count_lid_no_email)

        if self.dryrun:
            self.stdout.write("\nDRY RUN")
        else:
            schrijf_in_logboek(
                        None, 'NhbStructuur',
                        'Import van CRM data is uitgevoerd\n' +
                        samenvatting)
            self.stdout.write("\n")

        self.stdout.write(samenvatting)

        self.stdout.write('Done')
        return

# end of file
