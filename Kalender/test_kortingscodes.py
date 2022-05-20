# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import BoogType
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter, SporterBoog
from Wedstrijden.models import WedstrijdLocatie
from .models import (KalenderWedstrijd, KalenderWedstrijdSessie, KalenderInschrijving, KalenderWedstrijdKortingscode,
                     KALENDER_KORTING_SPORTER, KALENDER_KORTING_VERENIGING, KALENDER_KORTING_COMBI)
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestKalenderKortingscodes(E2EHelpers, TestCase):

    """ tests voor de Kalender applicatie, module kortingscodes """

    url_kalender_kortingscodes = '/kalender/vereniging/kortingscodes/'
    url_kalender_nieuwe_code = '/kalender/vereniging/kortingscodes/nieuw/'
    url_kalender_wijzig = '/kalender/vereniging/kortingscodes/wijzig/%s/'    # korting_pk

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
        self.nhbver1 = NhbVereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=NhbRegio.objects.get(regio_nr=112))
        self.nhbver1.save()

        self.functie_hwl = maak_functie('HWL Ver 1000', 'HWL')
        self.functie_hwl.nhb_ver = self.nhbver1
        self.functie_hwl.accounts.add(self.account_admin)
        self.functie_hwl.save()

        self.nhbver2 = NhbVereniging(
                            ver_nr=1001,
                            naam="Kleine Club",
                            regio=NhbRegio.objects.get(regio_nr=112))
        self.nhbver2.save()

        # voeg een locatie toe
        self.locatie = WedstrijdLocatie(
                            baan_type='E',      # externe locatie
                            naam='Test locatie')
        self.locatie.save()
        self.locatie.verenigingen.add(self.nhbver1)

        now = timezone.now()
        now_date = now.date()

        self.wedstrijd1 = KalenderWedstrijd(
                                titel='test wedstrijd 1',
                                datum_begin=now_date,
                                datum_einde=now_date,
                                organiserende_vereniging=self.nhbver1,
                                voorwaarden_a_status_when=now,
                                locatie=self.locatie)
        self.wedstrijd2 = KalenderWedstrijd(
                                titel='test wedstrijd 2',
                                datum_begin=now_date,
                                datum_einde=now_date,
                                organiserende_vereniging=self.nhbver1,
                                voorwaarden_a_status_when=now,
                                locatie=self.locatie)
        self.wedstrijd3 = KalenderWedstrijd(
                                titel='test wedstrijd 3',
                                datum_begin=now_date,
                                datum_einde=now_date,
                                organiserende_vereniging=self.nhbver1,
                                voorwaarden_a_status_when=now,
                                locatie=self.locatie)
        self.wedstrijd1.save()
        self.wedstrijd2.save()
        self.wedstrijd3.save()

    def test_anon(self):
        self.client.logout()

        resp = self.client.get(self.url_kalender_kortingscodes)
        self.assert403(resp)

        resp = self.client.get(self.url_kalender_nieuwe_code)
        self.assert403(resp)

        resp = self.client.get(self.url_kalender_wijzig)
        self.assert403(resp)

    def test_codes(self):
        # wissel naar HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # keuze type kortingscode
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_nieuwe_code)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/nieuwe-kortingscode-vereniging.dtl', 'plein/site_layout.dtl'))

        resp = self.client.post(self.url_kalender_nieuwe_code)
        self.assert404(resp, 'Niet ondersteund')

        self.assertEqual(0, KalenderWedstrijdKortingscode.objects.count())

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_kalender_nieuwe_code, {'keuze': 'sporter'})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(1, KalenderWedstrijdKortingscode.objects.count())

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_kalender_nieuwe_code, {'keuze': 'vereniging'})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(2, KalenderWedstrijdKortingscode.objects.count())

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_kalender_nieuwe_code, {'keuze': 'combi'})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(3, KalenderWedstrijdKortingscode.objects.count())

        # haal het overzicht op met de gedeeltelijk ingevulde kortingscodes
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_kortingscodes)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-kortingscodes-vereniging.dtl', 'plein/site_layout.dtl'))

        # vul wat meer details in
        korting_sporter = KalenderWedstrijdKortingscode.objects.get(soort=KALENDER_KORTING_SPORTER)
        self.assertEqual(korting_sporter.uitgegeven_door, self.nhbver1)
        korting_sporter.voor_sporter = self.sporter
        korting_sporter.save(update_fields=['voor_sporter'])
        korting_sporter.voor_wedstrijden.add(self.wedstrijd2)
        self.assertTrue(str(korting_sporter) != '')

        korting_ver = KalenderWedstrijdKortingscode.objects.get(soort=KALENDER_KORTING_VERENIGING)
        self.assertEqual(korting_ver.uitgegeven_door, self.nhbver1)
        korting_ver.voor_vereniging = self.nhbver1
        korting_ver.save(update_fields=['voor_vereniging'])
        korting_ver.voor_wedstrijden.add(self.wedstrijd2)

        korting_combi = KalenderWedstrijdKortingscode.objects.get(soort=KALENDER_KORTING_COMBI)
        self.assertEqual(korting_combi.uitgegeven_door, self.nhbver1)
        korting_combi.combi_basis_wedstrijd = self.wedstrijd1
        korting_combi.save(update_fields=['combi_basis_wedstrijd'])
        korting_combi.voor_wedstrijden.add(self.wedstrijd1)
        korting_combi.voor_wedstrijden.add(self.wedstrijd3)

        # haal het overzicht op met de volledige ingevulde kortingscodes
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_kortingscodes)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-kortingscodes-vereniging.dtl', 'plein/site_layout.dtl'))

        # wijzig scherm ophalen voor elk type korting
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_wijzig % korting_sporter.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/wijzig-kortingscode-sporter.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_wijzig % korting_ver.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/wijzig-kortingscode-vereniging.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_wijzig % korting_combi.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/wijzig-kortingscode-combi.dtl', 'plein/site_layout.dtl'))

        # wijzig korting sporter
        resp = self.client.post(self.url_kalender_wijzig % korting_sporter.pk)
        self.assert404(resp, 'Te korte code')

        resp = self.client.post(self.url_kalender_wijzig % korting_sporter.pk, {'code': 'is kort'})
        self.assert404(resp, 'Te korte code')

        resp = self.client.post(self.url_kalender_wijzig % korting_sporter.pk, {'code': 'is kort !!##%%()'})
        self.assert404(resp, 'Te korte code')

        resp = self.client.post(self.url_kalender_wijzig % korting_sporter.pk, {'code': 'TEST1234',
                                                                                'percentage': 'bla'})
        self.assert404(resp, 'Verkeerde parameter (percentage)')

        resp = self.client.post(self.url_kalender_wijzig % korting_sporter.pk, {'code': 'TEST1234',
                                                                                'percentage': '250'})
        self.assert404(resp, 'Verkeerd percentage')

        resp = self.client.post(self.url_kalender_wijzig % korting_sporter.pk, {'code': 'TEST1234',
                                                                                'percentage': '-10'})
        self.assert404(resp, 'Verkeerd percentage')

        resp = self.client.post(self.url_kalender_wijzig % korting_sporter.pk, {'code': 'TEST1234',
                                                                                'percentage': '0'})
        self.assert_is_redirect_not_plein(resp)

        resp = self.client.post(self.url_kalender_wijzig % korting_sporter.pk, {'code': 'TEST1234',
                                                                                'percentage': '0',
                                                                                'geldig_tm': 'bad'})
        self.assert404(resp, 'Geen valide datum')

        # vandaag is ondergrens
        datum_str = timezone.now().strftime('%Y-%m-%d')
        resp = self.client.post(self.url_kalender_wijzig % korting_sporter.pk, {'code': 'TEST1234',
                                                                                'geldig_tm': datum_str})
        self.assert_is_redirect_not_plein(resp)

        # in het verleden mag niet
        yesterday = timezone.now() - datetime.timedelta(days=1)
        datum_str = yesterday.strftime('%Y-%m-%d')
        resp = self.client.post(self.url_kalender_wijzig % korting_sporter.pk, {'code': 'TEST1234',
                                                                                'geldig_tm': datum_str})
        self.assert404(resp, 'Geen valide datum')

        # maximale datum is 13 december volgend jaar
        datum_str = datetime.date(timezone.now().year + 1, 12, 31).strftime('%Y-%m-%d')
        resp = self.client.post(self.url_kalender_wijzig % korting_sporter.pk, {'code': 'TEST1234',
                                                                                'geldig_tm': datum_str})
        self.assert_is_redirect_not_plein(resp)

        datum_str = datetime.date(timezone.now().year + 2, 1, 1).strftime('%Y-%m-%d')
        resp = self.client.post(self.url_kalender_wijzig % korting_sporter.pk, {'code': 'TEST1234',
                                                                                'geldig_tm': datum_str})
        self.assert404(resp, 'Geen valide datum')

        morgen = timezone.now() + datetime.timedelta(days=1)
        datum_str = morgen.strftime('%Y-%m-%d')

        resp = self.client.post(self.url_kalender_wijzig % korting_sporter.pk, {'code': 'TEST1234',
                                                                                'geldig_tm': datum_str,
                                                                                'voor_lid_nr': '000000'})
        self.assert_is_redirect_not_plein(resp)

        resp = self.client.post(self.url_kalender_wijzig % korting_sporter.pk, {'code': 'TEST1234',
                                                                                'geldig_tm': datum_str,
                                                                                'voor_lid_nr': 999999})
        self.assert404(resp, 'Sporter niet gevonden')

        resp = self.client.post(self.url_kalender_wijzig % korting_sporter.pk, {'code': 'TEST1234',
                                                                                'geldig_tm': datum_str,
                                                                                'voor_lid_nr': self.sporter.lid_nr,
                                                                                'wedstrijd_%s' % self.wedstrijd1.pk: 'ja'})
        self.assert_is_redirect_not_plein(resp)

        # korting voor vereniging
        resp = self.client.post(self.url_kalender_wijzig % korting_ver.pk, {'code': 'TEST5678',
                                                                            'geldig_tm': datum_str,
                                                                            'percentage': 25,
                                                                            'voor_onze_ver': 'ja'})
        self.assert_is_redirect_not_plein(resp)

        # wijzig korting combi
        resp = self.client.post(self.url_kalender_wijzig % korting_combi.pk, {'code': 'COMBI1234',
                                                                              'geldig_tm': datum_str,
                                                                              'percentage': 50,
                                                                              'combi_' + str(self.wedstrijd1.pk): 'ja',
                                                                              'wedstrijd_' + str(self.wedstrijd2.pk): 'ja',
                                                                              'wedstrijd_' + str(self.wedstrijd3.pk): 'ja'})

        # verwijder een kortingscode
        self.assertEqual(3, KalenderWedstrijdKortingscode.objects.count())
        resp = self.client.post(self.url_kalender_wijzig % korting_sporter.pk, {'verwijder': 'yes'})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(2, KalenderWedstrijdKortingscode.objects.count())

        # verwijder korting die al in gebruik is
        sessie = KalenderWedstrijdSessie(
                    datum=self.wedstrijd1.datum_begin,
                    tijd_begin='10:00',
                    tijd_einde='15:00')
        sessie.save()
        inschrijving = KalenderInschrijving(
                            wanneer=timezone.now(),
                            wedstrijd=self.wedstrijd1,
                            sessie=sessie,
                            sporterboog=self.sporterboog,
                            koper=self.account_admin,
                            gebruikte_code=korting_ver)
        inschrijving.save()

        # geen verwijder url, want in gebruik
        resp = self.client.get(self.url_kalender_wijzig % korting_ver.pk)
        self.assertEqual(resp.status_code, 200)

        # verwijderen lukt niet
        self.assertEqual(2, KalenderWedstrijdKortingscode.objects.count())
        resp = self.client.post(self.url_kalender_wijzig % korting_ver.pk, {'verwijder': 'yes'})
        self.assert404(resp, 'Korting is in gebruik')
        self.assertEqual(2, KalenderWedstrijdKortingscode.objects.count())

        # bad
        resp = self.client.get(self.url_kalender_wijzig % "999999")
        self.assert404(resp, 'Niet gevonden')

        resp = self.client.post(self.url_kalender_wijzig % "999999")
        self.assert404(resp, 'Niet gevonden')


# end of file
