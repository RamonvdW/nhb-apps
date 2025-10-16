# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import BoogType
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from Wedstrijden.definities import WEDSTRIJD_KORTING_SPORTER, WEDSTRIJD_KORTING_VERENIGING, WEDSTRIJD_KORTING_COMBI
from Wedstrijden.models import (KalenderWedstrijdklasse, Wedstrijd, WedstrijdSessie,
                                WedstrijdInschrijving, WedstrijdKorting)
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestWedstrijdenKorting(E2EHelpers, TestCase):

    """ tests voor de Wedstrijden applicatie, module Kortingen """

    url_kortingen_overzicht = '/wedstrijden/vereniging/kortingen/'
    url_korting_nieuw = '/wedstrijden/vereniging/kortingen/nieuw/'
    url_korting_wijzig = '/wedstrijden/vereniging/kortingen/wijzig/%s/'    # korting_pk

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        sporter = Sporter(
                    lid_nr=100000,
                    voornaam='Ad',
                    achternaam='de Admin',
                    geboorte_datum='1966-06-06',
                    sinds_datum='2020-02-02',
                    account=self.account_admin)
        sporter.save()
        self.sporter = sporter

        boog_c = BoogType.objects.get(afkorting='C')
        sporterboog = SporterBoog(
                            sporter=sporter,
                            boogtype=boog_c,
                            voor_wedstrijd=True)
        sporterboog.save()
        self.sporterboog = sporterboog

        # maak een test vereniging
        self.ver1 = Vereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=Regio.objects.get(regio_nr=112))
        self.ver1.save()

        self.functie_hwl = maak_functie('HWL Ver 1000', 'HWL')
        self.functie_hwl.vereniging = self.ver1
        self.functie_hwl.accounts.add(self.account_admin)
        self.functie_hwl.save()

        self.ver2 = Vereniging(
                            ver_nr=1001,
                            naam="Kleine Club",
                            regio=Regio.objects.get(regio_nr=112))
        self.ver2.save()

        # voeg een locatie toe
        self.locatie = WedstrijdLocatie(
                            baan_type='E',      # externe locatie
                            naam='Test locatie')
        self.locatie.save()
        self.locatie.verenigingen.add(self.ver1)

        now = timezone.now()
        now_date = now.date()

        self.wedstrijd1 = Wedstrijd(
                                titel='test wedstrijd 1',
                                datum_begin=now_date,
                                datum_einde=now_date,
                                organiserende_vereniging=self.ver1,
                                voorwaarden_a_status_when=now,
                                locatie=self.locatie)
        self.wedstrijd2 = Wedstrijd(
                                titel='test wedstrijd 2',
                                datum_begin=now_date,
                                datum_einde=now_date,
                                organiserende_vereniging=self.ver1,
                                voorwaarden_a_status_when=now,
                                locatie=self.locatie)
        self.wedstrijd3 = Wedstrijd(
                                titel='test wedstrijd 3',
                                datum_begin=now_date,
                                datum_einde=now_date,
                                organiserende_vereniging=self.ver1,
                                voorwaarden_a_status_when=now,
                                locatie=self.locatie)
        self.wedstrijd1.save()
        self.wedstrijd2.save()
        self.wedstrijd3.save()

        wkls = KalenderWedstrijdklasse.objects.filter(organisatie=self.wedstrijd1.organisatie,
                                                      buiten_gebruik=False,
                                                      boogtype=boog_c,
                                                      leeftijdsklasse__volgorde__gte=20)    # Onder18 en ouder
        self.wedstrijd1.wedstrijdklassen.set(wkls)
        self.wkls = wkls

    def test_anon(self):
        self.client.logout()

        resp = self.client.get(self.url_kortingen_overzicht)
        self.assert403(resp)

        resp = self.client.get(self.url_korting_nieuw)
        self.assert403(resp)

        resp = self.client.get(self.url_korting_wijzig)
        self.assert403(resp)

    def test_alles(self):
        # wissel naar HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # keuze type korting
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_korting_nieuw)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/korting-nieuw-kies.dtl', 'design/site_layout.dtl'))

        resp = self.client.post(self.url_korting_nieuw)
        self.assert404(resp, 'Niet ondersteund')

        self.assertEqual(0, WedstrijdKorting.objects.count())

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_korting_nieuw, {'keuze': 'sporter'})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(1, WedstrijdKorting.objects.count())

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_korting_nieuw, {'keuze': 'vereniging'})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(2, WedstrijdKorting.objects.count())

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_korting_nieuw, {'keuze': 'combi'})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(3, WedstrijdKorting.objects.count())

        # haal het overzicht op met de gedeeltelijk ingevulde kortingen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kortingen_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/kortingen-overzicht.dtl', 'design/site_layout.dtl'))

        korting_sporter = WedstrijdKorting.objects.get(soort=WEDSTRIJD_KORTING_SPORTER)
        korting_ver = WedstrijdKorting.objects.get(soort=WEDSTRIJD_KORTING_VERENIGING)
        korting_combi = WedstrijdKorting.objects.get(soort=WEDSTRIJD_KORTING_COMBI)

        # haal de edit schermen op met onvolledige kortingen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_korting_wijzig % korting_sporter.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-korting-sporter.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_korting_wijzig % korting_ver.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-korting-vereniging.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_korting_wijzig % korting_combi.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-korting-combi.dtl', 'design/site_layout.dtl'))

        # vul wat meer details in
        self.assertEqual(korting_sporter.uitgegeven_door, self.ver1)
        korting_sporter.voor_sporter = self.sporter
        korting_sporter.save(update_fields=['voor_sporter'])
        korting_sporter.voor_wedstrijden.add(self.wedstrijd2)
        self.assertTrue(str(korting_sporter) != '')

        self.assertEqual(korting_ver.uitgegeven_door, self.ver1)
        korting_ver.voor_wedstrijden.add(self.wedstrijd2)

        self.assertEqual(korting_combi.uitgegeven_door, self.ver1)
        korting_combi.voor_wedstrijden.add(self.wedstrijd1)
        korting_combi.voor_wedstrijden.add(self.wedstrijd3)

        # haal het overzicht op met de volledige ingevulde kortingen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kortingen_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/kortingen-overzicht.dtl', 'design/site_layout.dtl'))

        # wijzig scherm ophalen voor elk type korting
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_korting_wijzig % korting_sporter.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-korting-sporter.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_korting_wijzig % korting_ver.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-korting-vereniging.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_korting_wijzig % korting_combi.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-korting-combi.dtl', 'design/site_layout.dtl'))

        # wijzig korting sporter
        resp = self.client.post(self.url_korting_wijzig % korting_sporter.pk, {'percentage': 'bla'})
        self.assert404(resp, 'Verkeerde parameter (percentage)')

        resp = self.client.post(self.url_korting_wijzig % korting_sporter.pk, {'percentage': '250'})
        self.assert404(resp, 'Verkeerd percentage')

        resp = self.client.post(self.url_korting_wijzig % korting_sporter.pk, {'percentage': '-10'})
        self.assert404(resp, 'Verkeerd percentage')

        resp = self.client.post(self.url_korting_wijzig % korting_sporter.pk, {'percentage': '0'})
        self.assert_is_redirect_not_plein(resp)

        resp = self.client.post(self.url_korting_wijzig % korting_sporter.pk, {'percentage': '0',
                                                                               'geldig_tm': 'bad'})
        self.assert404(resp, 'Geen valide datum')

        # vandaag is ondergrens
        datum_str = timezone.now().strftime('%Y-%m-%d')
        resp = self.client.post(self.url_korting_wijzig % korting_sporter.pk, {'geldig_tm': datum_str})
        self.assert_is_redirect_not_plein(resp)

        # in het verleden mag niet
        yesterday = timezone.now() - datetime.timedelta(days=1)
        datum_str = yesterday.strftime('%Y-%m-%d')
        resp = self.client.post(self.url_korting_wijzig % korting_sporter.pk, {'geldig_tm': datum_str})
        self.assert404(resp, 'Geen valide datum')

        # maximale datum is 13 december volgend jaar
        datum_str = datetime.date(timezone.now().year + 1, 12, 31).strftime('%Y-%m-%d')
        resp = self.client.post(self.url_korting_wijzig % korting_sporter.pk, {'geldig_tm': datum_str})
        self.assert_is_redirect_not_plein(resp)

        datum_str = datetime.date(timezone.now().year + 3, 1, 1).strftime('%Y-%m-%d')
        resp = self.client.post(self.url_korting_wijzig % korting_sporter.pk, {'geldig_tm': datum_str})
        self.assert404(resp, 'Geen valide datum')

        morgen = timezone.now() + datetime.timedelta(days=1)
        datum_str = morgen.strftime('%Y-%m-%d')

        resp = self.client.post(self.url_korting_wijzig % korting_sporter.pk, {'geldig_tm': datum_str,
                                                                               'voor_lid_nr': '000000'})
        self.assert_is_redirect_not_plein(resp)

        resp = self.client.post(self.url_korting_wijzig % korting_sporter.pk, {'geldig_tm': datum_str,
                                                                               'voor_lid_nr': 999999})
        self.assert404(resp, 'Sporter niet gevonden')

        resp = self.client.post(self.url_korting_wijzig % korting_sporter.pk, {'geldig_tm': datum_str,
                                                                               'voor_lid_nr': self.sporter.lid_nr,
                                                                               'wedstrijd_%s' % self.wedstrijd1.pk: 'ja'
                                                                               })
        self.assert_is_redirect_not_plein(resp)

        # korting voor vereniging
        resp = self.client.post(self.url_korting_wijzig % korting_ver.pk,
                                {
                                    'geldig_tm': datum_str,
                                    'percentage': 25,
                                    'voor_onze_ver': 'ja'
                                })
        self.assert_is_redirect_not_plein(resp)

        # wijzig korting combi
        resp = self.client.post(self.url_korting_wijzig % korting_combi.pk,
                                {
                                    'geldig_tm': datum_str,
                                    'percentage': 50,
                                    'wedstrijd_' + str(self.wedstrijd2.pk): 'ja',
                                    'wedstrijd_' + str(self.wedstrijd3.pk): 'ja'
                                })
        self.assert_is_redirect_not_plein(resp)

        # verwijder een korting
        self.assertEqual(3, WedstrijdKorting.objects.count())
        resp = self.client.post(self.url_korting_wijzig % korting_sporter.pk, {'verwijder': 'yes'})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(2, WedstrijdKorting.objects.count())

        # verwijder korting die al in gebruik is
        sessie = WedstrijdSessie(
                    datum=self.wedstrijd1.datum_begin,
                    tijd_begin='10:00',
                    tijd_einde='15:00')
        sessie.save()
        sessie.wedstrijdklassen.set(self.wkls)

        inschrijving = WedstrijdInschrijving(
                            wanneer=timezone.now(),
                            wedstrijd=self.wedstrijd1,
                            sessie=sessie,
                            wedstrijdklasse=self.wkls[0],
                            sporterboog=self.sporterboog,
                            koper=self.account_admin,
                            korting=korting_ver)
        inschrijving.save()

        # geen verwijder url, want in gebruik
        resp = self.client.get(self.url_korting_wijzig % korting_ver.pk)
        self.assertEqual(resp.status_code, 200)

        # verwijderen lukt niet
        self.assertEqual(2, WedstrijdKorting.objects.count())
        resp = self.client.post(self.url_korting_wijzig % korting_ver.pk, {'verwijder': 'yes'})
        self.assert404(resp, 'Korting is in gebruik')
        self.assertEqual(2, WedstrijdKorting.objects.count())

        # bad
        resp = self.client.get(self.url_korting_wijzig % "999999")
        self.assert404(resp, 'Niet gevonden')

        resp = self.client.post(self.url_korting_wijzig % "999999")
        self.assert404(resp, 'Niet gevonden')


# end of file
