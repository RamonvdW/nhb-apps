# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from django.db.models import ProtectedError
from Account.models import AccountSessions
from ImportCRM.import_base import ImportCrmBase
from Mailer.operations import mailer_email_is_valide
from Overig.helpers import maak_unaccented
from Records.models import IndivRecord
from Sporter.models import Sporter
from Vereniging.models import Vereniging
import datetime


EXPECTED_MEMBER_KEYS = ('club_number', 'member_number', 'name', 'prefix', 'first_name',
                        'initials', 'birthday', 'birthplace', 'email', 'gender', 'member_from', 'member_until',
                        'para_code', 'address', 'postal_code', 'location_name',
                        'phone_business', 'phone_mobile', 'phone_private',
                        'iso_abbr', 'latitude', 'longitude', 'blocked', 'wa_id', 'date_of_death')
OPTIONAL_MEMBER_KEYS = ('skill_levels', 'educations')


class ImportCrmSporters(ImportCrmBase):

    def __init__(self, *args):
        super().__init__(*args)

        self._import_verenigingen = None      # wordt gezet in zet_ref()

        self.count_sporters = 0
        self.count_lang_ex_lid = 0
        self.count_uitgeschreven = 0
        self.count_admin = 0           # administratief aanwezig
        self.count_blocked = 0
        self.count_recordhouders = 0
        self.count_lid_no_email = 0

        self.lidmaatschap_jaar = 0
        self.zet_lidmaatschap_jaar(timezone.now().date())

        self._recordhouder_lid_nrs = list()
        self._cache_sporter = dict()    # [lid_nr] = Sporter()
        self._vul_cache()

    def zet_refs(self, import_verenigingen):
        self._import_verenigingen = import_verenigingen

    def zet_lidmaatschap_jaar(self, now: datetime.date):
        self.lidmaatschap_jaar = now.year               # voorbeeld: 2021
        if now.month == 1 and now.day <= 15:
            # tot en met 15 januari hoort bij het voorgaande jaar
            # leden kunnen dus nog uitgeschreven worden tot 15 jan
            self.lidmaatschap_jaar -= 1                 # voorbeeld: 2020

    def _vul_cache(self):
        for sporter in Sporter.objects.select_related('bij_vereniging').all():
            self._cache_sporter[sporter.lid_nr] = sporter
        # for

        # Sporters met een NL record op hun naam worden niet verwijderd.
        # Zoek deze op zodat we niet eens een poging gaan doen om ze te verwijderen.

        self._recordhouder_lid_nrs = list(IndivRecord
                                          .objects
                                          .distinct('sporter')
                                          .values_list('sporter__lid_nr', flat=True))
        # self.stdout.write('[DEBUG] Record houders: %s' % repr(self._recordhouder_lid_nrs))

    def vind_sporter(self, lid_nr: int | str) -> Sporter | None:
        try:
            lid_nr = int(lid_nr)
        except ValueError:
            self.out_error('Foutief bondsnummer: %s (geen getal)' % lid_nr)
            return None

        return self._cache_sporter.get(lid_nr, None)

    def _corrigeer_achternaam(self, lid_nr, achternaam):
        """ corrigeer de achternaam van een lid, indien nodig """
        if achternaam.upper().startswith('IJ'):
            if achternaam[:2] != 'IJ':
                # dit kan fout gaan bij niet-NL namen, daarom alleen melden
                new_achternaam = 'IJ' + achternaam[2:]
                self.out_warning("[WARNING] Lid %s: achternaam correctie nodig: %s --> %s" % (
                                    lid_nr, repr(achternaam), repr(new_achternaam)))

        return achternaam

    @staticmethod
    def _corrigeer_geboorteplaats(plaats):
        if plaats:
            upper_plaats = plaats.upper()
            if plaats[:2] != upper_plaats[:2] and not "'" in plaats[:2]:
                if upper_plaats[:2] == 'IJ':
                    new_plaats = 'IJ' + plaats[2:]
                else:
                    new_plaats = upper_plaats[0] + plaats[1:]

                # afgesproken dat we dit automatisch aanpassen
                # if plaats != new_plaats:
                #     self.stdout.write("[WARNING] Lid %s: corrigeer geboorteplaats: %s --> %s" % (
                #         lid_nr, repr(plaats), repr(new_plaats)))
                #     self._count_warnings += 1

                return new_plaats

        return plaats

    @staticmethod
    def _corrigeer_tussenvoegsel(tussenvoegsel: str, _achternaam: str):
        if tussenvoegsel and tussenvoegsel[0].isupper():
            laag = tussenvoegsel.lower()
            if laag in ('de', 'den', 'van', 'van de', 'van der', 'van den', 'ter', 'van t', 'op de', 'ten'):
                tussenvoegsel = laag
            # else:
            #     print(lid_nr, tussenvoegsel, _achternaam)
        return tussenvoegsel

    @staticmethod
    def _get_vereniging_str(ver: Vereniging):
        if ver:
            return "%s %s" % (ver.ver_nr, ver.naam)
        return "geen"

    def importeer(self, data: list):
        """ Importeert data van alle leden """

        # check alleen het eerste record
        if self.check_keys(data[0].keys(), EXPECTED_MEMBER_KEYS, OPTIONAL_MEMBER_KEYS, "member{sporters}"):
            return

        date_now = timezone.now().date()

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
             'gender':              'M' or 'V'/'F'
             'member_from':         string YYYY-MM-DD
             'member_until':        string YYYY-MM-DD
             'date_of_death':       string YYYY-MM-DD or null
             'para_code': None of string
             'address':             string with newlines
             'postal_code',
             'location_name',
             'phone_business',
             'phone_private',
             'phone_mobile': None of string "+31123456789"
             'iso_abbr': 'NL',      ???
             'latitude',
             'longitude',
             'blocked':             bool
             'wa':                  string
             'educations':          lijst van opleidingen
             'skill_level':         lijst van speelsterktes
        """
        for member in data:
            is_valid = True
            is_administratief_aanwezig = False

            lid_nr = member['member_number']

            # silently skip some numbers
            if lid_nr in settings.CRM_IMPORT_SKIP_MEMBERS:
                continue

            try:
                lid_nr = int(lid_nr)
            except ValueError:
                self.out_error('Foutief bondsnummer: %s (geen getal)' % lid_nr)
                continue

            lid_voornaam = member['first_name']
            if not lid_voornaam:
                lid_voornaam = member['initials']
                if not lid_voornaam:
                    self.out_error('Lid %s heeft geen voornaam of initials' % lid_nr)
                    continue

            lid_achternaam = member['name']
            if not lid_achternaam:
                self.stdout.write("[ERROR] Lid %s heeft geen achternaam" % lid_nr)
                continue        # data niet compleet voor dit lid

            lid_is_erelid = False
            pos = lid_achternaam.find('(')
            if pos > 0:
                toevoeging = lid_achternaam[pos:]
                new_achternaam = lid_achternaam[:pos].strip()

                if toevoeging in ('(Erelid KHSN)', '(Erevoorzitter KHSN)'):
                    lid_is_erelid = True
                else:
                    self.out_warning("Lid %s: verwijder toevoeging achternaam: %s --> %s" % (
                                                lid_nr, repr(lid_achternaam), repr(new_achternaam)))

                lid_achternaam = new_achternaam

            lid_achternaam = self._corrigeer_achternaam(lid_nr, lid_achternaam)

            if member['prefix']:
                lid_achternaam = self._corrigeer_tussenvoegsel(member['prefix'], lid_achternaam) + ' ' + lid_achternaam

            naam = lid_voornaam + ' ' + lid_achternaam
            lid_unaccented_naam = maak_unaccented(naam)
            if naam.count('(') != naam.count(')'):
                self.out_warning('Lid %s: onbalans in haakjes in %s' % (lid_nr, repr(naam)))

            for letter in "!@#$%^&*[]{}=_+\\|\":;,<>/?~`":
                if letter in naam:
                    self.out_warning("Lid %s: rare tekens in naam %s" % (lid_nr, repr(naam)))
            # for

            lid_blocked = member['blocked']

            if not member['club_number']:
                # ex-leden hebben geen vereniging
                # tijdens overstap kunnen leden ook (tijdelijk) geen club hebben
                # dus niet te veel klagen
                lid_ver = None
            else:
                lid_ver = self._import_verenigingen.vind_vereniging(member['club_number'])
                if not lid_ver:
                    lid_blocked = True
                    self.out_error('Kan vereniging %s voor lid %s niet vinden' % (repr(member['club_number']), lid_nr))

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
                        self.out_warning("Lid %s geboortedatum gecorrigeerd van %s naar %s" % (
                                                lid_nr, old_birthday, member['birthday']))
                    else:
                        is_valid = False
                        self.out_error('Lid %s heeft geen valide geboortedatum: %s' % (
                                                lid_nr, member['birthday']))
            try:
                lid_geboorte_datum = datetime.datetime.strptime(member['birthday'],
                                                                "%Y-%m-%d").date()          # YYYY-MM-DD
            except (ValueError, TypeError):
                lid_geboorte_datum = None
                is_valid = False
                if not lid_blocked:         # pragma: no branch
                    self.out_error('Lid %s heeft geen valide geboortedatum' % lid_nr)

            # datum overlijden
            lid_is_overleden = False
            lid_overleden_datum = '?'
            if member['date_of_death']:
                try:
                    lid_overleden_datum = datetime.datetime.strptime(member['date_of_death'],
                                                                     "%Y-%m-%d").date()      # YYYY-MM-DD
                except (ValueError, TypeError):
                    is_valid = False
                    if not lid_blocked:         # pragma: no branch
                        self.out_error('Lid %s heeft geen valide datum van overlijden: %s' % (
                                            lid_nr, repr(member['date_of_death'])))
                else:
                    lid_is_overleden = True

            lid_geslacht = member['gender']
            if lid_geslacht not in ('M', 'F', 'V', 'X'):
                self.out_error('Lid %s heeft onbekend geslacht: %s (moet zijn: M, F, V of X)' % (
                                        lid_nr, lid_geslacht))
                lid_geslacht = 'M'  # forceer naar iets valide
            if lid_geslacht == 'F':
                lid_geslacht = 'V'

            lid_para = member['para_code']
            if lid_para is None:
                lid_para = ""      # converts None to string

            if member['member_from'] and member['member_from'][0:0+2] not in ("19", "20"):
                self.out_error('Lid %s heeft geen valide datum lidmaatschap: %s' % (lid_nr, member['member_from']))
            try:
                lid_sinds = datetime.datetime.strptime(member['member_from'], "%Y-%m-%d").date()  # YYYY-MM-DD
            except (ValueError, TypeError):
                lid_sinds = None
                is_valid = False
                self.out_error('Lid %s heeft geen valide lidmaatschapsdatum: %s' % (lid_nr,
                                                                                    repr(member['member_from'])))
            else:
                if lid_sinds > date_now:
                    lid_blocked = True
                    self.out_info('Lidmaatschap voor %s gaat pas in op datum: %s' % (
                                            lid_nr, repr(member['member_from'])))

            if member['member_until']:
                tot_str = str(member['member_until'])
                if not tot_str.startswith('9999-'):
                    try:
                        lid_tot = datetime.datetime.strptime(tot_str, "%Y-%m-%d").date()  # YYYY-MM-DD
                    except (ValueError, TypeError):
                        self.out_error('Lid %s heeft geen valide datum einde lidmaatschap: %s' % (
                                                lid_nr, repr(member['member_until'])))
                    else:
                        # bereken hoe lang deze persoon al lid-af is
                        dagen_geen_lid = (date_now - lid_tot).days

                        # indien 2 jaar geen lid meer, dan verwijderen uit de administratie
                        if dagen_geen_lid > 2 * 365:
                            self.count_lang_ex_lid += 1
                            if lid_ver:
                                self.out_error('Lid %s is al %s dagen geen lid meer, maar heeft vereniging %s' % (
                                                lid_nr, dagen_geen_lid, lid_ver))
                            else:
                                is_valid = False        # niet importeren

            lid_email = member['email']
            if not lid_email:
                lid_email = ""  # converts potential None to string

            if not is_valid:
                # silently skip due to missing mandatory fields
                continue

            # postcode + huisnummer maken
            lid_adres_code = ''
            postcode = member['postal_code']
            postadres = member['address']
            # lat_lon = (member['latitude'], member['longitude'])  --> is van dorp ipv adres?
            if postcode is not None and postadres is not None:
                postcode = postcode.upper()     # sommige postcodes zijn kleine letters
                pos = postadres.find(postcode)
                if pos < 0:
                    self.out_error('Postcode %s niet gevonden in adres %s' % (repr(postcode), repr(postadres)))
                else:
                    # typisch: "Straatnaam 123\n1234 ZZ  Plaats\n"
                    sub_postadres = postadres[:pos]             # postcode en verder eraf kappen
                    sub_postadres = sub_postadres.strip()       # verwijder newlines
                    spl = sub_postadres.split(' ')              # scheid straatnaam en huisnummer
                    huis_nr = spl[-1]
                    lid_adres_code = postcode.replace(' ', '') + huis_nr

                # try:
                #     check_lat_lon = self._postcode2latlon[postcode]
                # except KeyError:
                #     self._postcode2latlon[postcode] = lat_lon
                # else:
                #     if check_lat_lon != lat_lon:
                #         self.stdout.write('[DEBUG] Multiple lat_lon for postal_code %s: %s, %s' % (
                #                           repr(postcode), repr(check_lat_lon), repr(lat_lon)))

            lid_postadres = list()
            if postadres is not None:
                for regel in postadres.split('\n'):
                    regel = regel.strip()
                    if regel != '':
                        lid_postadres.append(regel)
            while len(lid_postadres) < 3:
                lid_postadres.append('')
            # while

            lid_tel_nr = ''
            for field_name in ('phone_mobile', 'phone_private', 'phone_business'):      # hoogste voorkeur eerst
                phone = member[field_name]
                if phone is None:
                    phone = ''
                phone = phone.strip()
                if phone:
                    # geen fouten kunnen vinden in de telefoonnummers, dus geen waarschuwingen nodig
                    lid_tel_nr = phone
                    break       # gebruik eerste gevonden nummer
            # for

            lid_geboorteplaats = member['birthplace']
            if not lid_geboorteplaats:
                lid_geboorteplaats = ''     # vervang None to lege string
            else:
                lid_geboorteplaats = self._corrigeer_geboorteplaats(lid_geboorteplaats)

            lid_wa_id = member['wa_id']
            if not lid_wa_id:
                # verander None in leeg
                lid_wa_id = ''
            else:
                lid_wa_id = str(lid_wa_id)
            # print('lid %s wa_id: %s' % (lid_nr, lid_wa_id))

            self.count_sporters += 1

            is_nieuw = False
            obj = self.vind_sporter(lid_nr)
            if not obj:
                # nieuw lid
                is_nieuw = True
            else:
                try:
                    # krimp de lijst zodat verwijderde leden over blijven
                    lid_nrs.remove(lid_nr)
                except ValueError:          # pragma: no cover
                    self.out_error('Unexpected: lid_nr %s onverwacht niet in lijst bestaande nummers' % (repr(lid_nr)))
                else:
                    updated = list()

                    if lid_is_overleden:
                        if not obj.is_overleden:
                            self.out_info('Lid %s is overleden op %s en wordt op inactief gezet' % (
                                            repr(lid_nr), lid_overleden_datum))
                            obj.is_overleden = True
                            updated.append('is_overleden')
                            self.count_wijzigingen += 1
                        lid_blocked = True

                    if not lid_blocked:
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
                            self.count_lid_no_email += 1
                    elif not mailer_email_is_valide(lid_email):     # check alle email adressen
                        self.out_error('Lid %s heeft geen valide e-mail (%s)' % (lid_nr, lid_email))
                        self.count_lid_no_email += 1
                        lid_email = ""  # convert invalid email to no email

                    if obj.bij_vereniging != lid_ver:
                        if lid_ver:
                            self.out_info('Lid %s: vereniging %s --> %s' % (
                                            lid_nr,
                                            self._get_vereniging_str(obj.bij_vereniging),
                                            self._get_vereniging_str(lid_ver)))
                            self.count_wijzigingen += 1
                            obj.bij_vereniging = lid_ver
                            updated.append('bij_vereniging')
                        else:
                            # als het lid uitgeschreven wordt in het CRM houden we de oude vereniging
                            # vast, tot het einde van het lidmaatschap jaar.
                            # dit voorkomt blokkeren en geen toegang tot de diensten tijdens een overschrijving
                            if obj.lid_tot_einde_jaar < self.lidmaatschap_jaar:
                                self.out_info('Lid %s: vereniging %s --> geen (einde lidmaatschap jaar)' % (
                                                    lid_nr, self._get_vereniging_str(obj.bij_vereniging)))
                                self.count_wijzigingen += 1
                                obj.bij_vereniging = None
                                updated.append('bij_vereniging')
                                lid_blocked = True
                            else:
                                self.count_uitgeschreven += 1

                    if lid_blocked:
                        if obj.is_actief_lid:
                            self.out_info('Lid %s: is_actief_lid ja --> nee (want blocked)' % lid_nr)
                            self.count_wijzigingen += 1
                            obj.is_actief_lid = False
                            updated.append('is_actief_lid')
                    else:
                        if not obj.is_actief_lid:
                            self.out_info('Lid %s: is_actief_lid nee --> ja' % lid_nr)
                            self.count_wijzigingen += 1
                            obj.is_actief_lid = True
                            updated.append('is_actief_lid')

                    if obj.voornaam != lid_voornaam or obj.achternaam != lid_achternaam:
                        self.out_info('Lid %s: naam %s %s --> %s %s' % (
                                        lid_nr, obj.voornaam, obj.achternaam, lid_voornaam, lid_achternaam))
                        obj.voornaam = lid_voornaam
                        obj.achternaam = lid_achternaam
                        updated.extend(['voornaam', 'achternaam'])
                        self.count_wijzigingen += 1

                    if lid_unaccented_naam != obj.unaccented_naam:
                        obj.unaccented_naam = lid_unaccented_naam
                        updated.append('unaccented_naam')
                        # niet nodig om rapporteren want gekoppeld aan naam

                    if obj.email != lid_email:
                        self.out_info('Lid %s e-mail: %s --> %s' % (
                                                lid_nr, repr(obj.email), repr(lid_email)))
                        obj.email = lid_email
                        updated.append('email')
                        self.count_wijzigingen += 1

                    if obj.geslacht != lid_geslacht:
                        self.out_info('Lid %s geslacht: %s --> %s' % (
                                                lid_nr, obj.geslacht, lid_geslacht))
                        obj.geslacht = lid_geslacht
                        updated.append('geslacht')
                        self.count_wijzigingen += 1

                    if obj.geboorte_datum != lid_geboorte_datum:
                        self.out_info('Lid %s geboortedatum: %s --> %s' % (
                                                lid_nr, obj.geboorte_datum, lid_geboorte_datum))
                        obj.geboorte_datum = lid_geboorte_datum
                        updated.append('geboorte_datum')
                        self.count_wijzigingen += 1

                    if obj.sinds_datum != lid_sinds:
                        self.out_info('Lid %s: sinds_datum: %s --> %s' % (
                                                lid_nr, obj.sinds_datum, lid_sinds))
                        obj.sinds_datum = lid_sinds
                        updated.append('sinds_datum')
                        self.count_wijzigingen += 1

                    if obj.para_classificatie != lid_para:
                        self.out_info('Lid %s: para_classificatie: %s --> %s' % (
                                                lid_nr, repr(obj.para_classificatie), repr(lid_para)))
                        obj.para_classificatie = lid_para
                        updated.append('para_classificatie')
                        self.count_wijzigingen += 1

                    if obj.adres_code != lid_adres_code:
                        if obj.adres_code != '':        # laat toegevoegd veld: voorkom duizenden regels in de log
                            self.out_info('Lid %s: adres_code %s --> %s' % (
                                                lid_nr, repr(obj.adres_code), repr(lid_adres_code)))
                        obj.adres_code = lid_adres_code
                        updated.append('adres_code')
                        self.count_wijzigingen += 1

                    if obj.telefoon != lid_tel_nr:
                        # geen telefoonnummer controle hier
                        if obj.telefoon != '':
                            self.out_info('Lid %s: telefoonnummer %s --> %s' % (
                                lid_nr, repr(obj.telefoon), repr(lid_tel_nr)))
                        obj.telefoon = lid_tel_nr
                        updated.append('telefoon')
                        self.count_wijzigingen += 1

                    if obj.geboorteplaats != lid_geboorteplaats:
                        self.out_info('Lid %s: geboorteplaats %s --> %s' % (
                            lid_nr, repr(obj.geboorteplaats), repr(lid_geboorteplaats)))
                        obj.geboorteplaats = lid_geboorteplaats
                        updated.append('geboorteplaats')
                        self.count_wijzigingen += 1

                    if obj.wa_id != lid_wa_id:
                        self.out_info('Lid %s: wa_id %s --> %s' % (lid_nr, repr(obj.wa_id), repr(lid_wa_id)))
                        obj.wa_id = lid_wa_id
                        updated.append('wa_id')
                        self.count_wijzigingen += 1

                    if obj.postadres_1 != lid_postadres[0] or obj.postadres_2 != lid_postadres[1] or obj.postadres_3 != lid_postadres[2]:
                        self.out_info('Lid %s: postadres_1 %s --> %s' % (
                                            lid_nr, repr(obj.postadres_1), repr(lid_postadres[0])))
                        self.out_info('Lid %s: postadres_2 %s --> %s' % (
                                            lid_nr, repr(obj.postadres_2), repr(lid_postadres[1])))
                        if obj.postadres_3 != lid_postadres[2]:     # voorkomt vele '' --> ''
                            self.out_info('Lid %s: postadres_3 %s --> %s' % (
                                            lid_nr, repr(obj.postadres_3), repr(lid_postadres[2])))
                        obj.postadres_1 = lid_postadres[0]
                        obj.postadres_2 = lid_postadres[1]
                        obj.postadres_3 = lid_postadres[2]
                        obj.adres_lat = ''
                        obj.adres_lon = ''
                        updated.extend(['postadres_1', 'postadres_2', 'postadres_3', 'adres_lat', 'adres_lon'])
                        self.count_wijzigingen += 3

                    if obj.is_erelid != lid_is_erelid:
                        self.out_info('Lid %s: is_erelid %s --> %s' % (lid_nr, obj.is_erelid, lid_is_erelid))
                        obj.is_erelid = lid_is_erelid
                        updated.append('is_erelid')
                        self.count_wijzigingen += 1


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
                                    self.out_info('Lid %s voorkeuren: wedstrijd geslacht vastgezet' % lid_nr)

                                voorkeuren.save(update_fields=['wedstrijd_geslacht_gekozen', 'wedstrijd_geslacht'])
                # else
            # else

            if lid_blocked:
                if is_administratief_aanwezig:
                    self.count_admin += 1
                else:
                    self.count_blocked += 1

            if is_nieuw:

                if not lid_email:
                    self.count_lid_no_email += 1
                elif not mailer_email_is_valide(lid_email):  # check alle email adressen
                    self.out_error('Lid %s heeft geen valide e-mail (%s)' % (lid_nr, lid_email))
                    self.count_lid_no_email += 1
                    lid_email = ""  # convert invalid email to no email

                obj = Sporter(
                            lid_nr=lid_nr,
                            wa_id=lid_wa_id,
                            voornaam=lid_voornaam,
                            achternaam=lid_achternaam,
                            email=lid_email,
                            telefoon=lid_tel_nr,
                            geboorte_datum=lid_geboorte_datum,
                            geboorteplaats=lid_geboorteplaats,
                            geslacht=lid_geslacht,
                            para_classificatie=lid_para,
                            sinds_datum=lid_sinds,
                            bij_vereniging=lid_ver,
                            lid_tot_einde_jaar=self.lidmaatschap_jaar,
                            adres_code=lid_adres_code,
                            is_overleden=lid_is_overleden,
                            postadres_1=lid_postadres[0],
                            postadres_2=lid_postadres[1],
                            postadres_3=lid_postadres[2])

                if not lid_ver:
                    obj.lid_tot_einde_jaar -= 1
                    obj.is_actief_lid = False

                if lid_blocked:
                    obj.is_actief_lid = False

                if not self.dryrun:
                    obj.save()
                    self._cache_sporter[obj.pk] = obj

                self.count_toevoegingen += 1
        # for member

        self._verwijder_sporters(lid_nrs)

    def _verwijder_sporters(self, lid_nrs: list):
        # self.stdout.write('[DEBUG] Volgende %s bondsnummers moeten verwijderd worden: %s' % (len(lid_nrs),
        #                                                                                      repr(lid_nrs)))
        while len(lid_nrs) > 0:
            lid_nr = lid_nrs.pop(0)
            obj = self.vind_sporter(lid_nr)

            # behoud fictieve leden en externe leden
            if obj.bij_vereniging and obj.bij_vereniging.ver_nr in settings.CRM_IMPORT_BEHOUD_CLUB:
                continue

            if obj.is_actief_lid:
                self.out_info('Lid %s: is_actief_lid: ja --> nee' % repr(lid_nr))
                self.stdout.write('               vereniging %s --> geen' % self._get_vereniging_str(obj.bij_vereniging))
                obj.is_actief_lid = False
                obj.bij_vereniging = None
                self.count_wijzigingen += 2
                if not self.dryrun:
                    obj.save()
                    self._cache_sporter[obj.pk] = obj
                # FUTURE: afhandelen van het inactiveren/verwijderen van een lid dat in een team zit in een competitie
                # FUTURE: afhandelen van het inactiveren/verwijderen van een lid dat secretaris is

            elif obj.lid_nr in self._recordhouder_lid_nrs:
                # lid heeft een record op zijn naam --> behoud het hele record
                # de CRM applicatie heeft hier nog geen veld voor
                # self.out_info('Lid %s is recordhouder en wordt daarom niet verwijderd' % obj.lid_nr)
                self.count_recordhouders += 1

            else:
                # lid echt verwijderen
                #
                # echt verwijderen van een lid is een groot risico gezien aangezien het verwijderen
                # van gerelateerde records tot niet herstelbare schade kan lijden.
                #
                # de database structuur is beveiligd tegen het verwijderen van records die nog in gebruik zijn
                # daarnaast hebben we ook altijd nog de backups.
                # daarom is het en acceptabel risico om deze leden echt te verwijderen.

                self.out_info('Lid %s wordt nu verwijderd' % str(obj))
                if not self.dryrun:
                    if obj.account:
                        # blokkeer inlog
                        obj.account.is_active = False
                        obj.account.save(update_fields=['is_active'])

                        # verwijder sessies zodat het account niet meer ingelogd is
                        AccountSessions.objects.filter(account=obj.account).delete()

                        # probeer het account te verwijderen
                        # note: dit resulteert in heel veel queries voor om verwijzingen af te handelen (cascade, etc.)
                        try:
                            obj.account.delete()
                        except ProtectedError:
                            # dit kan gebeuren als er nog referenties aan het account zijn
                            # bijvoorbeeld vanuit een bestelling
                            pass

                    try:
                        del self._cache_sporter[obj.pk]
                        obj.delete()
                        self.count_verwijderingen += 1
                    except ProtectedError as exc:
                        self.out_error('Onverwachte fout bij het verwijderen van een lid: %s' % str(exc))
        # while

# end of file
