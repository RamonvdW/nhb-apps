# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Functie.models import Functie
from Functie.tests.helpers import maak_functie
from ImportCRM.import_base import ImportCrmBase
from Vereniging.models import Vereniging


EXPECTED_CLUB_KEYS = ('region_number', 'club_number', 'name', 'prefix', 'email', 'website',
                      'has_disabled_facilities', 'address', 'postal_code', 'location_name',
                      'phone_business', 'phone_private', 'phone_mobile', 'coc_number',
                      'iso_abbr', 'latitude', 'longitude', 'secretaris', 'iban', 'bic', 'member_admins')
OPTIONAL_CLUB_KEYS = ('smoke_free_status',)


class ImportCrmFuncties(ImportCrmBase):

    def __init__(self, *args):
        super().__init__(*args)

        self._importeer_verenigingen = None     # wordt gezet in zet_refs
        self._importeer_sporters = None

        self._cache_functie = dict()    # [(rol, beschrijving)] = Functie()
        self._vul_cache()

    def zet_refs(self, import_verenigingen, import_sporters):
        self._importeer_verenigingen = import_verenigingen
        self._importeer_sporters = import_sporters

    def _vul_cache(self):
        for functie in (Functie
                        .objects
                        .select_related('vereniging')
                        .prefetch_related('accounts')
                        .all()):
            tup = (functie.rol, functie.beschrijving)
            self._cache_functie[tup] = functie
        # for

    def vind_functie(self, rol, beschrijving):
        tup = (rol, beschrijving)
        return self._cache_functie.get(tup, None)

    def maak_functies_voor_vereniging(self, ver: Vereniging, sec_email: str):
        """ zorg dat de functies bestaan voor een vereniging """

        for rol, beschr in (('WL', 'Wedstrijdleider %s'),
                            ('HWL', 'Hoofdwedstrijdleider %s'),
                            ('SEC', 'Secretaris vereniging %s'),
                            ('LA', 'Ledenadministratie %s')):

            beschrijving = beschr % ver.ver_nr
            functie = self.vind_functie(rol, beschrijving)
            if not functie:
                functie = maak_functie(beschrijving, rol)
                tup = (rol, beschrijving)
                self._cache_functie[tup] = functie

            updated = list()

            if functie.vereniging != ver:
                functie.vereniging = ver
                updated.append('vereniging')

            if rol == 'SEC':
                # secretaris functie krijgt email uit CRM
                if functie.bevestigde_email != sec_email and functie.bevestigde_email != "":
                    self.out_info('Wijziging van secretaris email voor vereniging %s: "%s" --> "%s"' % (
                                    ver.ver_nr, functie.bevestigde_email, sec_email))
                    self.count_wijzigingen += 1
                functie.bevestigde_email = sec_email
                functie.nieuwe_email = ''  # voor de zekerheid opruimen
                updated.extend(['bevestigde_email', 'nieuwe_email'])

            if not self.dryrun:
                functie.save(update_fields=updated)
        # for

    def importeer_leden_admins(self, data: list):
        """ voor elke club, koppel de ledenadministrateurs aan de LA-functie """

        for club in data:
            ver_nr = club['club_number']

            obj = self._importeer_verenigingen.vind_vereniging(ver_nr)
            if not obj:
                # zou niet moeten gebeuren
                self.out_error('Kan vereniging %s niet terugvinden' % ver_nr)
                continue

            # zoek de LA functie op
            functie_la = self.vind_functie('LA', 'Ledenadministratie %s' % ver_nr)
            if not functie_la:
                self.out_error('Kan functie LA niet vinden voor vereniging %s' % ver_nr)
                continue

            # zoek de secretaris op
            secretaris = self._importeer_verenigingen._vind_sec(ver_nr)

            admin_sporters = list()
            for admin in club['member_admins']:
                la_lid_nr = admin['member_number']
                sporter = self._importeer_sporters.vind_sporter(la_lid_nr)
                if not sporter:
                    self.out_error('Kan member admin lid %s van vereniging %s niet vinden' % (la_lid_nr, ver_nr))
                else:
                    if sporter.bij_vereniging is None or sporter.bij_vereniging.ver_nr != ver_nr:
                        self.out_warning('Member admin lid %s is geen lid bij vereniging %s' % (
                                            sporter.lid_nr, ver_nr))
                    else:
                        if secretaris and sporter in secretaris.sporters.all():
                            # self.stdout.write('[WARNING] Member admin lid %s is also SEC %s; skipping' % (
                            #                     la_lid_nr, ver_nr))
                            pass        # silently ignore
                        else:
                            if sporter.account:
                                admin_sporters.append(sporter)
            # for

            # rapporteer de wijzigingen
            lid_nrs_oud = [account.username for account in functie_la.accounts.all()]
            lid_nrs_new = [str(sporter.lid_nr) for sporter in admin_sporters]

            if set(lid_nrs_oud) != set(lid_nrs_new):

                str_oud = "+".join([str(lid_nr) for lid_nr in lid_nrs_oud])
                if str_oud == '':
                    str_oud = 'geen'
                str_new = "+".join([str(lid_nr) for lid_nr in lid_nrs_new])
                if str_new == '':
                    str_new = 'geen'

                self.out_info('Vereniging %s member admins: %s --> %s' % (ver_nr, str_oud, str_new))

                self.count_wijzigingen += 1

                # wijzigingen doorvoeren
                if not self.dryrun:
                    accounts = [sporter.account for sporter in admin_sporters]
                    functie_la.accounts.set(accounts)
        # for club

# end of file
