# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from Locatie.definities import BAAN_TYPE_BUITEN, BAAN_TYPE_EXTERN
from Locatie.models import WedstrijdLocatie
from ImportCRM.import_base import ImportCrmBase


EXPECTED_CLUB_KEYS = ('club_number', 'has_disabled_facilities', 'address', 'postal_code', 'location_name',
                      'latitude', 'longitude', )
OPTIONAL_CLUB_KEYS = ('region_number', 'smoke_free_status', 'name', 'prefix', 'email', 'website', 'phone_business',
                      'phone_private', 'phone_mobile', 'coc_number', 'iso_abbr', 'secretaris', 'iban', 'bic',
                      'member_admins')


class ImportCrmLocaties(ImportCrmBase):

    def __init__(self, *args):
        super().__init__(*args)

        self._import_verenigingen = None        # wordt gezet in zet_refs()

    def zet_refs(self, import_verenigingen):
        self._import_verenigingen = import_verenigingen

    def importeer(self, data):
        """ Importeert data van verenigingen als basis voor locaties """

        if self.check_keys(data[0].keys(), EXPECTED_CLUB_KEYS, OPTIONAL_CLUB_KEYS, "club{locatie}"):
            return

        # voor overige velden, zie _import_clubs
        """ JSON velden (string, except):
            [
                {
                    'club_number': int
                    'has_disabled_facilities': boolean
                    'address': string with newlines
                    'postal_code',
                    'location_name',
                    'latitude', 'longitude',
                },
                ...
            ]
        """

        for club in data:
            ver_nr = club['club_number']

            if ver_nr in settings.CRM_IMPORT_GEEN_LOCATIE:
                continue

            ver = self._import_verenigingen.vind_vereniging(ver_nr)
            if not ver:
                continue

            # een vereniging zonder doel heeft een lege location_name
            adres = ""
            plaats = ""
            if club['location_name']:
                plaats = club['location_name']
                adres = club['address']
                if not adres:
                    adres = ""
                plaats = plaats.strip()
                adres = adres.strip()     # remove terminating \n

            if not adres:
                # vereniging heeft geen adres meer
                # verwijder de koppeling met locatie uit crm
                for obj in ver.wedstrijdlocatie_set.filter(adres_uit_crm=True):
                    ver.wedstrijdlocatie_set.remove(obj)
                    self.out_info('Locatie %s ontkoppeld voor vereniging %s' % (repr(obj.adres), ver_nr))
                    self.count_wijzigingen += 1
                continue

            # FUTURE: gebruik: has_disabled_facilities, lat/lon,

            # zoek de locatie bij dit adres
            try:
                locatie = (WedstrijdLocatie
                           .objects
                           .exclude(baan_type__in=(BAAN_TYPE_BUITEN, BAAN_TYPE_EXTERN))
                           .get(adres=adres))
            except WedstrijdLocatie.MultipleObjectsReturned:            # pragma: no cover
                # er is een ongelukje gebeurt
                self.out_error('Onverwacht meer dan 1 locatie voor vereniging %s' % ver)
                continue
            except WedstrijdLocatie.DoesNotExist:
                # nieuw aanmaken
                locatie = WedstrijdLocatie(
                                adres=adres,
                                plaats=plaats,
                                adres_uit_crm=True)
                locatie.save()
                self.out_info('Nieuwe locatie voor adres %s' % repr(adres))
                self.count_toevoegingen += 1
            else:
                # indien nog niet ingevuld, zet de plaats
                if locatie.plaats != plaats:
                    self.out_info('Vereniging %s: Aanpassing locatie plaats %s --> %s' % (
                                        ver_nr, repr(locatie.plaats), repr(plaats)))
                    locatie.plaats = plaats
                    locatie.save(update_fields=['plaats'])

            # adres van locatie mag niet wijzigen
            # dus als vereniging een ander adres heeft, ontkoppel dan de oude locatie
            for obj in (ver
                        .wedstrijdlocatie_set
                        .exclude(adres_uit_crm=False)           # niet extern/buitenbaan
                        .exclude(pk=locatie.pk)):
                ver.wedstrijdlocatie_set.remove(obj)
                self.out_info('Vereniging %s ontkoppeld van locatie met adres %s' % (ver, repr(obj.adres)))
                self.count_wijzigingen += 1
            # for

            if locatie.verenigingen.filter(ver_nr=ver_nr).count() == 0:
                # maak koppeling tussen vereniging en locatie
                locatie.verenigingen.add(ver)
                self.out_info('Vereniging %s gekoppeld aan locatie %s' % (ver, repr(adres)))
                self.count_toevoegingen += 1

            # zoek ook de buitenbaan van de vereniging erbij
            try:
                buiten_locatie = (ver
                                  .wedstrijdlocatie_set
                                  .get(baan_type=BAAN_TYPE_BUITEN,
                                       zichtbaar=True))
            except WedstrijdLocatie.DoesNotExist:
                # vereniging heeft geen buitenlocatie
                pass
            else:
                updated = list()
                if buiten_locatie.plaats != locatie.plaats:
                    buiten_locatie.plaats = locatie.plaats
                    updated.append('plaats')

                if buiten_locatie.adres != locatie.adres:
                    buiten_locatie.adres = locatie.adres
                    updated.append('adres')

                if len(updated):
                    buiten_locatie.save(update_fields=updated)
        # for

        # FUTURE: zichtbaar=False zetten voor locatie zonder vereniging
        # FUTURE: zichtbaar=True zetten voor (revived) locatie met vereniging

# end of file
