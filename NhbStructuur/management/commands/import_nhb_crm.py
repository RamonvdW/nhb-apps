# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" importeer een JSON file met data uit het CRM systeem van de NHB """

from django.utils.dateparse import parse_date
from django.core.management.base import BaseCommand
from django.db.models import ProtectedError
import django.db.utils
from NhbStructuur.models import NhbRayon, NhbRegio, NhbLid, NhbVereniging
from Account.models import is_email_valide, Account
from Logboek.models import schrijf_in_logboek
from Functie.models import maak_functie, maak_cwz
import argparse
import datetime
import json


def vind_regio(regio_nr):
    try:
        return NhbRegio.objects.get(regio_nr=regio_nr)
    except NhbRegio.DoesNotExist:
        pass
    return None

def vind_lid(nhb_nr):
    try:
        return NhbLid.objects.get(nhb_nr=nhb_nr)
    except NhbLid.DoesNotExist:
        pass
    return None

def vind_vereniging(nhb_nr):
    try:
        return NhbVereniging.objects.get(nhb_nr=nhb_nr)
    except NhbVereniging.DoesNotExist:
        pass
    return None

def get_secretaris_str(lid):
    if lid:
        return "%s %s %s" % (lid.nhb_nr, lid.voornaam, lid.achternaam)
    return "geen"

def get_vereniging_str(ver):
    if ver:
        return "%s %s" % (ver.nhb_nr, ver.naam)
    return "geen"


# expected keys at each level
EXPECTED_DATA_KEYS = ('rayons', 'regions', 'clubs', 'members')
EXPECTED_RAYON_KEYS = ('rayon_number', 'name')
EXPECTED_REGIO_KEYS = ('rayon_number', 'region_number', 'name')
EXPECTED_CLUB_KEYS = ('region_number', 'club_number', 'name', 'prefix', 'email', 'website',
                      'has_disabled_facilities', 'address', 'postal_code', 'location_name',
                      'phone_business', 'phone_private', 'phone_mobile',
                      'iso_abbr', 'latitude', 'longitude', 'secretaris')
EXPECTED_MEMBER_KEYS = ('club_number', 'member_number', 'name', 'prefix', 'first_name',
                        'initials', 'birthday', 'email', 'gender', 'member_from',
                        'para_code', 'address', 'postal_code', 'location_name',
                        'iso_abbr', 'latitude', 'longitude', 'blocked')


# administratieve entries (met fouten) die overslagen moeten worden
SKIP_MEMBERS = (101711,)        # CRM developer

GEEN_SECRETARIS_NODIG = (1377,)

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
        self._count_cwz_no_account = 0

        self._nieuwe_clubs = list()

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, help="pad naar het JSON bestand")
        parser.add_argument('--dryrun', action='store_true')

    def _check_keys(self, keys, expected_keys, level):
        has_error = False
        keys = list(keys)
        for key in expected_keys:
            try:
                keys.remove(key)
            except ValueError:
                self.stderr.write("[ERROR] Verplichte sleutel %s niet aanwezig in de %s data" % (repr(key), repr(level)))
                has_error = True
        # for
        if len(keys):
            self.stderr.write("[WARNING] Extra sleutel aanwezig in de %s data: %s" % (repr(level), repr(keys)))
        return has_error

    def _import_rayons(self, data):
        """ Importeert data van alle rayons """

        if self._check_keys(data[0].keys(), EXPECTED_RAYON_KEYS, "rayon"):
            return

        # rayons zijn statisch gedefinieerd, met een extra beschrijving
        # controleer alleen of er overwacht een wijziging is die we over moeten nemen
        for rayon in data:
            self._count_rayons += 1
            rayon_nr = rayon['rayon_number']
            rayon_naam = rayon['name']

            # zoek het rayon op
            try:
                obj = NhbRayon.objects.get(rayon_nr=rayon_nr)
            except NhbRayon.DoesNotExist:
                # toevoegen van een rayon ondersteunen we niet
                self.stderr.write('[ERROR] Onbekend rayon %s' % repr(rayon))
                self._count_errors += 1
            else:
                if obj.naam != rayon_naam:
                    self.stdout.write('[INFO] Wijziging naam rayon %s: %s --> %s' % (rayon_nr, repr(obj.naam), repr(rayon_naam)))
                    self._count_wijzigingen += 1
                    obj.naam = rayon_naam
                    if not self.dryrun:
                        obj.save()
        # for
        # verwijderen van een rayon ondersteunen we niet

    def _import_regions(self, data):
        """ Importeert data van alle regios """

        if self._check_keys(data[0].keys(), EXPECTED_REGIO_KEYS, "regio"):
            return

        # regios zijn statisch gedefinieerd
        # naam alleen de naam over
        for regio in data:
            self._count_regios += 1
            rayon_nr = regio['rayon_number']
            regio_nr = regio['region_number']
            regio_naam = regio['name']

            # zoek de regio op
            try:
                obj = NhbRegio.objects.get(regio_nr=regio_nr)
            except NhbRegio.DoesNotExist:
                # toevoegen van een regio ondersteunen we niet
                self.stderr.write('[ERROR] Onbekende regio %s' % repr(regio))
                self._count_errors += 1
            else:
                if obj.naam != regio_naam:
                    self.stdout.write('[INFO] Wijziging naam regio %s: %s --> %s' % (regio_nr, repr(obj.naam), repr(regio_naam)))
                    self._count_wijzigingen += 1
                    obj.naam = regio_naam
                    if not self.dryrun:
                        obj.save()
        # for
        # verwijderen van een regio ondersteunen we niet

    def _import_clubs(self, data):
        """ Importeert data van alle verenigingen """

        if self._check_keys(data[0].keys(), EXPECTED_CLUB_KEYS, "club"):
            return

        # houd bij welke vereniging nhb_nrs in de database zitten
        # als deze niet meer voorkomen, dan zijn ze verwijderd
        nhb_nrs = [tup[0] for tup in NhbVereniging.objects.values_list('nhb_nr')]

        """ JSON velden (string, except):
         'region_number':           int
         'club_number':             int
         'name',
         'prefix': None,            ???
         'phone_business',
         'phone_private',
         'phone_mobile': None,      ???
         'email', 'website',
         'has_disabled_facilities': boolean
         'address':                 string with newlines
         'postal_code',
         'location_name',
         'iso_abbr': 'NL',          ???
         'latitude', 'longitude',
         'secretaris': [{'member_number': int}]
        }
        """

        for club in data:
            self._count_clubs += 1
            ver_nhb_nr = club['club_number']
            ver_naam = club['name']
            # maak 1377 wat korter
            pos = ver_naam.find(' (geen deelname wedstrijden)')
            if pos > 0:
                ver_naam = ver_naam[:pos]

            if club['prefix']:
                ver_naam = club['prefix'] + ' ' + ver_naam
            ver_regio = club['region_number']
            # TODO: verdere velden: website, email (secretaris)
            # TODO: wedstrijdlocatie velden verwerken: address, postal_code, location_name, has_disabled_facilities

            # zoek de vereniging op
            is_nieuw = False
            try:
                obj = NhbVereniging.objects.get(nhb_nr=ver_nhb_nr)
            except NhbVereniging.DoesNotExist:
                # nieuwe vereniging
                is_nieuw = True
            else:
                # bestaande vereniging
                nhb_nrs.remove(ver_nhb_nr)

                if obj.regio.regio_nr != ver_regio:
                    regio_obj = vind_regio(ver_regio)
                    if regio_obj is None:
                        self.stderr.write('[ERROR] Kan vereniging %s niet wijzigen naar onbekende regio %s' % (ver_nhb_nr, ver_regio))
                        self._count_errors += 1
                    else:
                        self.stdout.write('[INFO] Wijziging van regio voor vereniging %s: %s --> %s' % (ver_nhb_nr, obj.regio.regio_nr, ver_regio))
                        self._count_wijzigingen += 1
                        obj.regio = regio_obj
                        if not self.dryrun:
                            obj.save()
                if obj.naam != ver_naam:
                    self.stdout.write('[INFO] Wijziging van naam voor vereniging %s: %s --> %s' % (ver_nhb_nr, obj.naam, ver_naam))
                    self._count_wijzigingen += 1
                    obj.naam = ver_naam
                    if not self.dryrun:
                        obj.save()

            if is_nieuw:
                obj = None
                ver = NhbVereniging()
                ver.nhb_nr = ver_nhb_nr
                ver.naam = ver_naam
                regio_obj = vind_regio(ver_regio)
                if not regio_obj:
                    self._count_errors += 1
                    self.stderr.write('[ERROR] Vereniging %s hoort bij onbekende regio %s' % (ver_nhb_nr, ver_regio))
                else:
                    self.stdout.write('[INFO] Vereniging %s aangemaakt: %s' % (ver_nhb_nr, repr(ver.naam)))
                    self._count_toevoegingen += 1
                    ver.regio = regio_obj
                    if not self.dryrun:
                        ver.save()
                    self._nieuwe_clubs.append(ver_nhb_nr)   # voor onderdrukken 'wijziging' secretaris
                    obj = ver

            # maak de cwz functie aan
            if obj:
                functie = maak_functie("CWZ vereniging %s" % obj.nhb_nr, "CWZ")
                functie.nhb_ver = obj
                if not self.dryrun:
                    functie.save()
        # for

        # kijk of er verenigingen verwijderd moeten worden
        while len(nhb_nrs) > 0:
            ver_nhb_nr = nhb_nrs.pop(0)
            obj = NhbVereniging.objects.get(nhb_nr=ver_nhb_nr)
            self.stdout.write('[INFO] Vereniging %s wordt nu verwijderd' % str(obj))
            if not self.dryrun:
                # kan alleen als er geen leden maar aan hangen --> de modellen beschermen dit automatisch
                # vang de gerelateerde exceptie af
                try:
                    obj.delete()
                    self._count_verwijderingen += 1
                except ProtectedError as exc:       # pragma: no coverage
                    self._count_errors += 1
                    self.stderr.write('[ERROR] Onverwachte fout bij het verwijderen van een vereniging: %s' % str(exc))
        # while

    def _import_clubs_secretaris(self, data):
        """ voor elke club, koppel de secretaris aan een NhbLid """

        if self._check_keys(data[0].keys(), EXPECTED_CLUB_KEYS, "club"):
            return

        for club in data:
            ver_nhb_nr = club['club_number']
            ver_naam = club['name']
            if len(club['secretaris']) < 1:
                ver_secretaris_nhblid = None
            else:
                ver_secretaris_nr = club['secretaris'][0]['member_number']
                ver_secretaris_nhblid = vind_lid(ver_secretaris_nr)
                if ver_secretaris_nhblid is None:
                    self.stderr.write('[ERROR] Kan secretaris %s van vereniging %s niet vinden' % (ver_secretaris_nr, ver_nhb_nr))
                    self._count_errors += 1

            # zoek de vereniging op
            try:
                obj = NhbVereniging.objects.get(nhb_nr=ver_nhb_nr)
            except NhbVereniging.DoesNotExist:
                # zou niet moeten gebeuren
                self.stderr.write('[ERROR] Kan vereniging %s niet terugvinden' % ver_nhb_nr)
                self._count_errors += 1
            else:
                if obj.secretaris_lid != ver_secretaris_nhblid:
                    if ver_nhb_nr not in self._nieuwe_clubs:
                        old_secr_str = get_secretaris_str(obj.secretaris_lid)
                        new_secr_str = get_secretaris_str(ver_secretaris_nhblid)
                        self.stdout.write('[INFO] Wijziging van secretaris voor vereniging %s: %s --> %s' % (ver_nhb_nr, old_secr_str, new_secr_str))
                        self._count_wijzigingen += 1

                    obj.secretaris_lid = ver_secretaris_nhblid
                    if not self.dryrun:
                        obj.save()

                if not ver_secretaris_nhblid:
                    if ver_nhb_nr not in GEEN_SECRETARIS_NODIG:
                        self.stderr.write(
                            '[WARNING] Vereniging %s (%s) heeft geen secretaris!' % (ver_nhb_nr, ver_naam))
                        self._count_warnings += 1

                # forceer de secretaris in de CWZ groep
                if ver_secretaris_nhblid:
                    try:
                        account = Account.objects.get(nhblid=ver_secretaris_nhblid)
                    except Account.DoesNotExist:
                        # CWZ heeft nog geen account
                        self.stdout.write("[WARNING] Secretaris %s van vereniging %s heeft nog geen account" % (ver_secretaris_nhblid.nhb_nr, obj.nhb_nr))
                        self._count_cwz_no_account += 1
                    else:
                        if maak_cwz(obj, account):
                            self.stdout.write("[INFO] Secretaris %s van vereniging %s is gekoppeld aan CWZ functie" % (ver_secretaris_nhblid.nhb_nr, obj.nhb_nr))
        # for

    def _import_members(self, data):
        """ Importeert data van alle leden """

        if self._check_keys(data[0].keys(), EXPECTED_MEMBER_KEYS, "member"):
            return

        # houd bij welke leden nhb_nrs in de database zitten
        # als deze niet meer voorkomen, dan zijn ze verwijderd
        nhb_nrs = [tup[0] for tup in NhbLid.objects.values_list('nhb_nr')]

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

            lid_nhb_nr = member['member_number']

            # silently skip some numbers
            if lid_nhb_nr in SKIP_MEMBERS:
                continue

            lid_voornaam = member['first_name']
            if not lid_voornaam:
                lid_voornaam = member['initials']
                if not lid_voornaam:
                    self.stderr.write('[WARNING] Lid %s heeft geen voornaam of initials' % lid_nhb_nr)
                    self._count_warnings += 1

            lid_achternaam = member['name']
            if lid_achternaam.endswith(" (Erelid NHB)"):
                new_achternaam = lid_achternaam[:-13]
                self.stdout.write("[INFO] Lid %s: verwijder toevoeging erelid: %s --> %s" % (lid_nhb_nr, repr(lid_achternaam), repr(new_achternaam)))
                lid_achternaam = new_achternaam

            if member['prefix']:
                lid_achternaam = member['prefix'] + ' ' + lid_achternaam

            lid_blocked = member['blocked']

            if not member['club_number']:
                # ex-leden hebben geen vereniging, dus niet te veel klagen
                lid_blocked = True
                lid_ver = None
            else:
                lid_ver = vind_vereniging(member['club_number'])
                if not lid_ver:
                    lid_blocked = True
                    self.stderr.write('[ERROR] Kan vereniging %s voor lid %s niet vinden' % (repr(member['club_number']), lid_nhb_nr))
                    self._count_errors += 1

            if member['birthday'] and member['birthday'][0:0+2] not in ("19", "20"):
                self.stderr.write('[ERROR] Lid %s heeft geen valide geboortedatum: %s' % (lid_nhb_nr, member['birthday']))
                self._count_errors += 1
                # poging tot repareren
                if member['birthday'][0:0+2] == "00":
                    year = int(member['birthday'][2:2+2])
                    if year < 25:
                        member['birthday'] = '20' + member['birthday'][2:]
                    else:
                        member['birthday'] = '19' + member['birthday'][2:]
                else:
                    is_valid = False
            try:
                lid_geboorte_datum = datetime.datetime.strptime(member['birthday'], "%Y-%m-%d").date() # YYYY-MM-DD
            except (ValueError, TypeError):
                lid_geboorte_datum = None
                is_valid = False
                if not lid_ver:
                    self.stdout.write('[INFO] Lid %s wordt overgeslagen (geen valide geboortedatum, maar toch blocked)' % lid_nhb_nr)
                else:
                    self.stderr.write('[ERROR] Lid %s heeft geen valide geboortedatum' % lid_nhb_nr)
                    self._count_errors += 1

            lid_geslacht = member['gender']
            if lid_geslacht not in ('M', 'F'):
                self.stderr.write('[ERROR] Lid %s heeft onbekend geslacht: %s (moet zijn: M of F)' % (lid_nhb_nr, lid_geslacht))
                self._count_errors += 1
                lid_geslacht = 'M'  # forceer naar iets valides
            if lid_geslacht == 'F':
                lid_geslacht = 'V'

            lid_para = member['para_code']
            if lid_para is None:
                lid_para = ""      # converts None to string

            if member['member_from'] and member['member_from'][0:0+2] not in ("19", "20"):
                self.stderr.write('[ERROR] Lid %s heeft geen valide lidmaatschapdatum: %s' % (lid_nhb_nr, member['member_from']))
                self._count_errors += 1
            try:
                lid_sinds = datetime.datetime.strptime(member['member_from'], "%Y-%m-%d").date() # YYYY-MM-DD
            except (ValueError, TypeError):
                lid_sinds = None
                is_valid = False
                self.stderr.write('[ERROR] Lid %s heeft geen valide lidmaatschapsdatum' % lid_nhb_nr)
                self._count_errors += 1

            lid_email = member['email']
            if not lid_email:
                lid_email = ""      # converts None to string
                if not lid_blocked:
                    self._count_lid_no_email += 1
            elif not is_email_valide(lid_email):
                self.stderr.write('[ERROR] Lid %s heeft geen valide e-mail (%s)' % (lid_nhb_nr, lid_email))
                self._count_errors += 1
                self._count_lid_no_email += 1
                lid_email = ""      # convert invalid email to no email

            if not is_valid:
                continue

            self._count_members += 1

            if lid_blocked:
                self._count_blocked += 1

            is_nieuw = False
            try:
                obj = NhbLid.objects.get(nhb_nr=lid_nhb_nr)
            except NhbLid.DoesNotExist:
                # nieuw lid
                is_nieuw = True
            else:
                nhb_nrs.remove(lid_nhb_nr)

                if lid_blocked:
                    if obj.is_actief_lid:
                        self.stdout.write('[INFO] Lid %s: is_actief_lid ja --> nee (want blocked)' % lid_nhb_nr)
                        self._count_wijzigingen += 1
                        obj.is_actief_lid = False
                        if not self.dryrun:
                            obj.save()
                else:
                    if not obj.is_actief_lid:
                        self.stdout.write('[INFO] Lid %s: is_actief_lid nee --> ja' % lid_nhb_nr)
                        self._count_wijzigingen += 1
                        obj.is_actief_lid = True
                        if not self.dryrun:
                            obj.save()

                if obj.voornaam != lid_voornaam or obj.achternaam != lid_achternaam:
                    self.stdout.write('[INFO] Lid %s: naam %s %s --> %s %s' % (lid_nhb_nr, obj.voornaam, obj.achternaam, lid_voornaam, lid_achternaam))
                    obj.voornaam = lid_voornaam
                    obj.achternaam = lid_achternaam
                    self._count_wijzigingen += 1
                    if not self.dryrun:
                        obj.save()

                if obj.email != lid_email:
                    self.stdout.write('[INFO] Lid %s e-mail: %s --> %s' % (lid_nhb_nr, repr(obj.email), repr(lid_email)))
                    obj.email = lid_email
                    self._count_wijzigingen += 1
                    if not self.dryrun:
                        obj.save()

                if obj.geslacht != lid_geslacht:
                    self.stdout.write('[INFO] Lid %s geslacht: %s --> %s' % (lid_nhb_nr, obj.geslacht, lid_geslacht))
                    obj.geslacht = lid_geslacht
                    self._count_wijzigingen += 1
                    if not self.dryrun:
                        obj.save()

                if obj.geboorte_datum != lid_geboorte_datum:
                    self.stdout.write('[INFO] Lid %s geboortedatum: %s --> %s' % (lid_nhb_nr, obj.geboorte_datum, lid_geboorte_datum))
                    obj.geboorte_datum = lid_geboorte_datum
                    self._count_wijzigingen += 1
                    if not self.dryrun:
                        obj.save()

                if obj.sinds_datum != lid_sinds:
                    self.stdout.write('[INFO] Lid %s: sinds_datum: %s --> %s' % (lid_nhb_nr, obj.sinds_datum, lid_sinds))
                    obj.sinds_datum = lid_sinds
                    self._count_wijzigingen += 1
                    if not self.dryrun:
                        obj.save()

                if obj.para_classificatie != lid_para:
                    self.stdout.write('[INFO] Lid %s: para_classificatie: %s --> %s' % (lid_nhb_nr, repr(obj.para_classificatie), repr(lid_para)))
                    obj.para_classificatie = lid_para
                    self._count_wijzigingen += 1
                    if not self.dryrun:
                        obj.save()

                if obj.bij_vereniging != lid_ver:
                    self.stdout.write('[INFO] Lid %s: vereniging %s --> %s' % (lid_nhb_nr, get_vereniging_str(obj.bij_vereniging), get_vereniging_str(lid_ver)))
                    obj.bij_vereniging = lid_ver
                    self._count_wijzigingen += 1
                    if not self.dryrun:
                        obj.save()

            if is_nieuw:
                lid = NhbLid()
                lid.nhb_nr = lid_nhb_nr
                lid.voornaam = lid_voornaam
                lid.achternaam = lid_achternaam
                lid.email = lid_email
                lid.geboorte_datum = lid_geboorte_datum
                lid.geslacht = lid_geslacht
                lid.para_classificatie = lid_para
                lid.sinds_datum = lid_sinds
                lid.bij_vereniging = lid_ver
                if lid_blocked:
                    lid.is_actief_lid = False
                if not self.dryrun:
                    lid.save()
                self._count_toevoegingen += 1
        # for

        while len(nhb_nrs) > 0:
            lid_nhb_nr = nhb_nrs.pop(0)
            obj = NhbLid.objects.get(nhb_nr=lid_nhb_nr)
            if obj.is_actief_lid:
                self.stdout.write('[INFO] Lid %s: is_actief_lid: ja --> nee' % repr(lid_nhb_nr))
                obj.is_actief_lid = False
                self._count_wijzigingen += 1
                self.stdout.write('               vereniging %s --> geen' % get_vereniging_str(obj.bij_vereniging))
                obj.bij_vereniging = None
                self._count_wijzigingen += 1
                if not self.dryrun:
                    obj.save()
            else:
                # TODO: afhandelen van het verwijderen van een lid dat in een team zit in een competitie
                self.stdout.write('[INFO] Lid %s wordt nu verwijderd' % str(obj))
                if not self.dryrun:
                    # kan alleen als er geen leden maar aan hangen --> de modellen beschermen dit automatisch
                    # vang de gerelateerde exceptie af
                    try:
                        obj.delete()
                        self._count_verwijderingen += 1
                    except ProtectedError as exc:
                        self._count_errors += 1
                        self.stderr.write('[ERROR] Onverwachte fout bij het verwijderen van een lid: %s' % str(exc))
        # while

    def handle(self, *args, **options):
        self.dryrun = options['dryrun']

        try:
            fname = options['filename'][0]
            with open(fname, encoding='raw_unicode_escape') as fhandle:
                data = json.load(fhandle)
        except IOError as exc:
            self.stderr.write("[ERROR] Bestand kan niet gelezen worden (%s)" % str(exc))
            return
        except json.decoder.JSONDecodeError as exc:
            self.stderr.write("[ERROR] Probleem met het JSON formaat in bestand %s (%s)" % (repr(fname), str(exc)))
            return
        except UnicodeDecodeError as exc:
            self.stderr.write("[ERROR] Bestand heeft unicode problemen (%s)" % str(exc))
            return

        if self._check_keys(data.keys(), EXPECTED_DATA_KEYS, "top-level"):
            return

        for key in EXPECTED_DATA_KEYS:
            if len(data[key]) < 1:
                self.stderr.write("[ERROR] Geen data voor top-level sleutel %s" % repr(key))
                return

        # vang generieke fouten af
        try:
            self._import_rayons(data['rayons'])
            self._import_regions(data['regions'])
            # circular dependency: secretaris van vereniging is lid; lid hoort bij vereniging
            # doe clubs eerst, dan members, dan club.secretaris
            self._import_clubs(data['clubs'])
            self._import_members(data['members'])
            self._import_clubs_secretaris(data['clubs'])
        except django.db.utils.DataError as exc:        # pragma: no coverage
            self.stderr.write('[ERROR] Overwachte database fout: %s' % str(exc))

        self.stdout.write('Import van CRM data is klaar')
        #self.stdout.write("Read %s lines; skipped %s dupes; skipped %s errors; added %s records" % (line_nr, dupe_count, error_count, added_count))

        # rapporteer de samenvatting en schrijf deze ook in het logboek
        samenvatting = "Samenvatting: %s fouten; %s waarschuwingen; %s nieuw; %s wijzigingen; %s verwijderingen; "\
                        "%s leden, %s inactief; %s verenigingen; %s cwz's zonder account; %s regios; %s rayons; %s actieve leden zonder e-mail" %\
                          (self._count_errors,
                           self._count_warnings,
                           self._count_toevoegingen,
                           self._count_wijzigingen,
                           self._count_verwijderingen,
                           self._count_members - self._count_blocked,
                           self._count_blocked,
                           self._count_clubs,
                           self._count_cwz_no_account,
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

