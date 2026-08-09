# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db.models import ProtectedError
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from Account.models import Account
from Functie.operations import koppel_account_aan_functie_sec
from ImportCRM.import_base import ImportCrmBase
from Vereniging.models import Vereniging, Secretaris


EXPECTED_CLUB_KEYS = ('region_number', 'club_number', 'name', 'prefix', 'email', 'website', 'address', 'location_name',
                      'coc_number', 'iban', 'bic')
OPTIONAL_CLUB_KEYS = ('smoke_free_status', 'has_disabled_facilities', 'postal_code', 'phone_business', 'phone_private',
                      'phone_mobile', 'iso_abbr', 'latitude', 'longitude', 'secretaris', 'member_admins')


class ImportCrmVerenigingen(ImportCrmBase):

    def __init__(self, *args):
        super().__init__(*args)

        self.count_clubs = 0
        self.count_sec_no_account = 0

        self._import_geo = None
        self._import_functies = None
        self._import_sporters = None

        self._cache_ver = dict()        # [ver_nr] = Vereniging()
        self._cache_sec = dict()        # [ver_nr] = Secretaris()
        self._cache_account = dict()    # [username] = Account()
        self._vul_cache()

        self._website_validator = URLValidator(schemes=['http', 'https'])

    def zet_refs(self, import_geo, import_functies, import_sporters):
        self._import_geo = import_geo
        self._import_functies = import_functies
        self._import_sporters = import_sporters

    def vind_vereniging(self, ver_nr) -> Vereniging | None:
        try:
            ver_nr = int(ver_nr)
        except ValueError:
            self.out_error('Foutief verenigingsnummer: %s (geen getal)' % repr(ver_nr))
            return None

        return self._cache_ver.get(ver_nr, None)

    def _vind_sec(self, ver_nr) -> Secretaris | None:
        try:
            ver_nr = int(ver_nr)
        except ValueError:          # pragma: no cover
            self.out_error('Foutief verenigingsnummer: %s (geen getal)' % repr(ver_nr))
            return None

        return self._cache_sec.get(ver_nr, None)

    def _vind_account(self, username):
        try:
            account = self._cache_account[str(username)]
        except KeyError:
            account = None
        return account

    def _vul_cache(self):
        # vereniging 8000 komt niet voor in de CRM data
        skip_ver_nrs = (settings.EXTERN_VER_NR,)

        for ver in (Vereniging
                    .objects
                    .exclude(ver_nr__in=skip_ver_nrs)
                    .select_related('regio')
                    .prefetch_related('wedstrijdlocatie_set')
                    .all()):
            self._cache_ver[ver.ver_nr] = ver
        # for

        for sec in (Secretaris
                    .objects
                    .select_related('vereniging')
                    .prefetch_related('sporters')
                    .all()):
            self._cache_sec[sec.vereniging.ver_nr] = sec
        # for

        for account in Account.objects.all():
            self._cache_account[account.username] = account
        # for

    @staticmethod
    def _check_iban(iban):
        """ Voer de mod97 test uit op de IBAN """
        if len(iban) < 18:      # pragma: no cover
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

    def importeer(self, data: list):
        """ Importeert data van alle verenigingen """

        if self.check_keys(data[0].keys(), EXPECTED_CLUB_KEYS, OPTIONAL_CLUB_KEYS, "club{vereniging}"):
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
                'member_admins': [{'member_number': int, 'read_only': true/false}, ...]
        }
        """

        for club in data:
            self.count_clubs += 1

            ver_nr = club['club_number']
            try:
                ver_nr = int(ver_nr)
            except ValueError:
                if self.dryrun and ver_nr == 'crash':
                    raise Exception('crash test')

                self.out_error('Geen valide verenigingsnummer: %s (geen getal)' % repr(ver_nr))
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
                ver_plaats = ""  # voorkom None
            else:
                ver_plaats = ver_plaats.strip()

            ver_email = club['email']
            if not ver_email:
                self.out_warning('Vereniging %s (%s) heeft geen contact email' % (ver_nr, ver_naam))
                ver_email = ""  # voorkom None

            ver_geen_wedstrijden = (ver_nr in settings.CRM_IMPORT_GEEN_WEDSTRIJDEN)

            ver_kvk = club['coc_number']
            if ver_kvk is None:
                ver_kvk = ''
            ver_kvk = ver_kvk.strip()
            if not ver_kvk:
                self.out_warning('Vereniging %s heeft geen KvK nummer' % ver_nr)
            elif len(ver_kvk) != 8 or not ver_kvk.isdecimal():
                self.out_warning('Vereniging %s KvK nummer %s moet 8 cijfers bevatten' % (ver_nr, repr(ver_kvk)))

            ver_website = club['website']
            if ver_website is None:
                ver_website = ''
            ver_website = ver_website.strip()
            if ver_website:
                try:
                    self._website_validator(ver_website)
                except ValidationError as exc:
                    self.out_warning('Vereniging %s website url: %s bevat fout (%s)' % (ver_nr, repr(ver_website),
                                                                                        str(exc)))
                    ver_website = ''

            ver_tel_nr = ''
            for field_name in ('phone_business', 'phone_mobile', 'phone_private'):  # hoogste voorkeur eerst
                phone = club[field_name]
                if phone is None:
                    phone = ''
                phone = phone.strip()
                if phone:
                    # geen fouten kunnen vinden in de telefoonnummers, dus geen waarschuwingen nodig
                    ver_tel_nr = phone
                    break  # gebruik eerste gevonden nummer
            # for

            ver_adres1 = ''
            ver_adres2 = ''
            # address = "Straat 9\n1234 AB  Plaats\n"
            adres = club['address']
            if not adres:  # handles None and ''
                self.out_warning('Vereniging %s heeft geen adres' % ver_nr)
            else:
                adres_spl = adres.strip().split('\n')
                if len(adres_spl) != 2:
                    self.out_error('Vereniging %s adres bestaat niet uit 2 regels: %s' % (ver_nr,
                                                                                          repr(club['address'])))
                if len(adres_spl) >= 2:
                    ver_adres1 = adres_spl[0]
                    ver_adres2 = adres_spl[1]

            ver_iban = club['iban']
            ver_bic = club['bic']
            if ver_bic and ver_iban:
                ver_bic = str(ver_bic)
                ver_iban = str(ver_iban)
                # correcte situatie
                if len(ver_bic) not in (8, 11):
                    self.out_error(
                        'Vereniging %s heeft BIC %s met foute lengte %s (niet 8 of 11) horende bij IBAN %s' % (
                            ver_nr, repr(ver_bic), len(ver_bic), repr(ver_iban)))
                    ver_bic = None

                if len(ver_iban) != 18:
                    self.out_error('Vereniging %s heeft IBAN %s met foute lengte %s (niet 18)' % (
                        ver_nr, repr(ver_iban), len(ver_iban)))
                    ver_bic = None
            else:
                # een van de twee is afwezig
                if ver_bic and not ver_iban:
                    self.out_warning('Vereniging %s heeft een BIC zonder IBAN: %s, %s' % (
                                        ver_nr, repr(ver_bic), repr(ver_iban)))
                elif ver_iban and not ver_bic:
                    self.out_warning('Vereniging %s heeft een IBAN zonder BIC: %s, %s' % (
                                        ver_nr, repr(ver_bic), repr(ver_iban)))
                ver_bic = None

            if ver_bic:
                if ver_bic not in settings.BEKENDE_BIC_CODES:
                    self.out_warning('Vereniging %s heeft een onbekende BIC code %s horende bij IBAN %s' % (
                                        ver_nr, repr(ver_bic), repr(ver_iban)))

            if ver_bic:
                # controleer de IBAN
                if not self._check_iban(ver_iban):
                    self.out_error('Vereniging %s heeft een foutieve IBAN: %s' % (ver_nr, repr(ver_iban)))
                    ver_bic = None

            # zet None om naar lege string
            if not ver_bic:
                ver_bic = ''
                ver_iban = ''

            # zoek de vereniging op
            is_nieuw = False
            obj = self.vind_vereniging(ver_nr)
            if not obj:
                # nieuwe vereniging
                is_nieuw = True
            else:
                # bestaande vereniging
                ver_nrs.remove(ver_nr)

                # mutaties verwerken
                updated = list()
                if obj.regio.regio_nr != ver_regio:
                    regio_obj = self._import_geo.vind_regio(ver_regio)
                    if regio_obj is None:
                        self.out_error('Kan vereniging %s niet wijzigen naar onbekende regio %s' % (
                                        ver_nr, ver_regio))
                    else:
                        self.out_info('Wijziging van regio van vereniging %s: %s --> %s' % (
                                        ver_nr, obj.regio.regio_nr, ver_regio))
                        self.count_wijzigingen += 1
                        obj.regio = regio_obj
                        updated.append('regio')

                if obj.naam != ver_naam:
                    self.out_info('Wijziging van naam van vereniging %s: "%s" --> "%s"' % (
                                    ver_nr, obj.naam, ver_naam))
                    self.count_wijzigingen += 1
                    obj.naam = ver_naam
                    updated.append('naam')

                if obj.plaats != ver_plaats:
                    self.out_info('Wijziging van plaats van vereniging %s: "%s" --> "%s"' % (
                                    ver_nr, obj.plaats, ver_plaats))
                    self.count_wijzigingen += 1
                    obj.plaats = ver_plaats
                    updated.append('plaats')

                if obj.geen_wedstrijden != ver_geen_wedstrijden:
                    self.out_info("Wijziging van 'geen wedstrijden' van vereniging %s: %s --> %s" % (
                                    ver_nr, obj.geen_wedstrijden, ver_geen_wedstrijden))
                    self.count_wijzigingen += 1
                    obj.geen_wedstrijden = ver_geen_wedstrijden
                    updated.append('geen_wedstrijden')

                if obj.kvk_nummer != ver_kvk:
                    self.out_info("Wijziging van KvK nummer van vereniging %s: %s --> %s" % (
                                    ver_nr, obj.kvk_nummer, ver_kvk))
                    self.count_wijzigingen += 1
                    obj.kvk_nummer = ver_kvk
                    updated.append('kvk_nummer')

                if obj.website != ver_website:
                    self.out_info("Wijziging van website van vereniging %s: %s --> %s" % (
                                    ver_nr, obj.website, ver_website))
                    self.count_wijzigingen += 1
                    obj.website = ver_website
                    updated.append('website')

                if obj.contact_email != ver_email:
                    self.out_info("Wijziging van contact_email van vereniging %s: %s --> %s" % (
                                    ver_nr, obj.contact_email, ver_email))
                    self.count_wijzigingen += 1
                    obj.contact_email = ver_email
                    updated.append('contact_email')

                if obj.telefoonnummer != ver_tel_nr:
                    self.out_info("Wijziging van telefoonnummer van vereniging %s: %s --> %s" % (
                                    ver_nr, obj.telefoonnummer, ver_tel_nr))
                    self.count_wijzigingen += 1
                    obj.telefoonnummer = ver_tel_nr
                    updated.append('telefoonnummer')

                if obj.adres_regel1 != ver_adres1:
                    self.out_info("Wijziging van adres regel 1 van vereniging %s: %s --> %s" % (
                                    ver_nr, obj.adres_regel1, ver_adres1))
                    self.count_wijzigingen += 1
                    obj.adres_regel1 = ver_adres1
                    updated.append('adres_regel1')

                if obj.adres_regel2 != ver_adres2:
                    self.out_info("Wijziging van adres regel 2 van vereniging %s: %s --> %s" % (
                                    ver_nr, obj.adres_regel2, ver_adres2))
                    self.count_wijzigingen += 1
                    obj.adres_regel2 = ver_adres2
                    updated.append('adres_regel2')

                if obj.bank_iban != ver_iban:
                    self.out_info("Wijziging van IBAN van vereniging %s: %s --> %s" % (
                                    ver_nr, obj.bank_iban, ver_iban))
                    self.count_wijzigingen += 1
                    obj.bank_iban = ver_iban
                    updated.append('bank_iban')

                if obj.bank_bic != ver_bic:
                    self.out_info("Wijziging van BIC van vereniging %s: %s --> %s" % (
                                    ver_nr, obj.bank_bic, ver_bic))
                    self.count_wijzigingen += 1
                    obj.bank_bic = ver_bic
                    updated.append('bank_bic')

                if not self.dryrun:
                    obj.save(update_fields=updated)

            if is_nieuw:
                obj = None
                ver = Vereniging(
                            ver_nr=ver_nr,
                            naam=ver_naam,
                            plaats=ver_plaats,
                            geen_wedstrijden=ver_geen_wedstrijden,
                            kvk_nummer=ver_kvk,
                            website=ver_website,
                            telefoonnummer=ver_tel_nr,
                            contact_email=ver_email,
                            adres_regel1=ver_adres1,
                            adres_regel2=ver_adres2)
                regio_obj = self._import_geo.vind_regio(ver_regio)
                if not regio_obj:
                    self.out_error('Vereniging %s hoort bij onbekende regio %s' % (ver_nr, ver_regio))
                else:
                    self.out_info('Vereniging %s aangemaakt: %s' % (ver_nr, repr(ver.naam)))
                    self.count_toevoegingen += 1
                    ver.regio = regio_obj
                    if not self.dryrun:
                        ver.save()
                        self._cache_ver[ver.pk] = ver
                    obj = ver

            # maak de functies aan voor deze vereniging
            if obj:
                self._import_functies.maak_functies_voor_vereniging(obj, ver_email)
        # for

        # kijk of er verenigingen verwijderd moeten worden
        self._verwijder_verenigingen(ver_nrs)

    def _verwijder_verenigingen(self, ver_nrs):
        while len(ver_nrs) > 0:
            ver_nr = ver_nrs.pop(0)
            if ver_nr in settings.CRM_IMPORT_BEHOUD_CLUB:
                continue
            obj = self.vind_vereniging(ver_nr)
            if obj:
                leden_count = obj.sporter_set.count()
                if leden_count > 0:
                    self.out_error('Kan vereniging %s met %s leden niet verwijderen' % (str(obj), leden_count))
                    continue

                if not self.dryrun:
                    # kan alleen als er geen leden meer aan hangen --> de modellen beschermen dit automatisch
                    # vang de gerelateerde exceptie af
                    msg = str(obj)
                    try:
                        del self._cache_ver[obj.pk]
                        obj.delete()
                        self.count_verwijderingen += 1
                        self.out_info('Vereniging %s is verwijderd' % msg)
                    except ProtectedError as exc:  # pragma: no cover
                        self.out_warning('Vereniging %s is nog in gebruik en kan daarom niet verwijderen' % msg)
                        self.out_debug('Reden: %s' % str(exc))
        # while

    def importeer_secretaris(self, data: list):
        """ voor elke club, koppel de secretaris aan een Sporter """

        for club in data:
            ver_nr = club['club_number']

            obj = self.vind_vereniging(ver_nr)
            if not obj:
                continue

            ver_secretarissen = list()
            for sec in club['secretaris']:
                sec_lid_nr = sec['member_number']
                sporter = self._import_sporters.vind_sporter(sec_lid_nr)
                if not sporter:
                    self.out_error('Kan secretaris %s van vereniging %s niet vinden' % (sec_lid_nr, ver_nr))
                else:
                    if sporter.bij_vereniging is None or sporter.bij_vereniging != obj:
                        self.out_warning('Secretaris %s is geen lid bij vereniging %s' % (sporter.lid_nr, ver_nr))

                    ver_secretarissen.append(sporter)
            # for

            # zoek het Secretaris-record op
            sec = self._vind_sec(ver_nr)
            if not sec:
                # maak een nieuw record aan
                sec = Secretaris(vereniging=obj)
                sec.save()
                self._cache_sec[obj.ver_nr] = sec

            lid_nrs_oud = [sporter.lid_nr for sporter in sec.sporters.all()]
            lid_nrs_new = [sporter.lid_nr for sporter in ver_secretarissen]

            if set(lid_nrs_oud) != set(lid_nrs_new):

                str_oud = "+".join([str(lid_nr) for lid_nr in lid_nrs_oud])
                if str_oud == '':
                    str_oud = 'geen'
                str_new = "+".join([str(lid_nr) for lid_nr in lid_nrs_new])
                if str_new == '':
                    str_new = 'geen'

                self.out_info('Vereniging %s secretarissen: %s --> %s' % (ver_nr, str_oud, str_new))

                self.count_wijzigingen += 1

                if not self.dryrun:
                    sec.sporters.set(ver_secretarissen)

            # forceer de juiste secretarissen in de SEC functie
            functie_sec = self._import_functies.vind_functie('SEC', 'Secretaris vereniging %s' % ver_nr)
            if functie_sec:
                functie_account_pks = list(functie_sec.accounts.values_list('pk', flat=True))
                sec_account_pks = list()
                for sporter in ver_secretarissen:
                    account = self._vind_account(sporter.lid_nr)
                    if not account:
                        # SEC heeft nog geen account
                        # self.stdout.write("[INFO] Secretaris %s van vereniging %s heeft nog geen account" % (
                        #                         sporter.lid_nr, obj.ver_nr))
                        self.count_sec_no_account += 1
                    else:
                        if account.pk in functie_account_pks:
                            sec_account_pks.append(account.pk)
                        else:
                            # nog niet gekoppeld
                            if koppel_account_aan_functie_sec(obj, account):
                                self.out_info(
                                    "Secretaris %s van vereniging %s is gekoppeld aan SEC functie en krijgt een e-mail" % (
                                            sporter.lid_nr, obj.ver_nr))
                                sec_account_pks.append(account.pk)
                            else:
                                self.out_warning("Secretaris %s van vereniging %s heeft nog geen bevestigd e-mailadres" % (
                                        sporter.lid_nr, obj.ver_nr))
                # for

                for account in functie_sec.accounts.all():
                    if account.pk not in sec_account_pks:
                        self.out_info("Account %s wordt losgekoppeld van de rol %s" % (
                                            account.username, functie_sec.beschrijving))
                        functie_sec.accounts.remove(account)
                # for
        # for

# end of file
