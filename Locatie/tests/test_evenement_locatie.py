# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from Evenement.models import Evenement
from Functie.models import Functie
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Locatie.models import EvenementLocatie
from Opleiding.models import Opleiding, OpleidingMoment
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging


class TestLocatieEvenementLocatie(E2EHelpers, TestCase):

    """ tests voor de Locatie applicatie, functie Evenement Locatie """

    url_overzicht = '/vereniging/locatie/%s/evenement/'       # ver_nr
    url_wijzig = '/vereniging/locatie/%s/evenement/%s/'       # ver_nr, locatie_pk

    @staticmethod
    def _maak_vereniging(ver_nr, naam, regio):
        # maak een test vereniging
        ver = Vereniging(
                    ver_nr=ver_nr,
                    naam=naam,
                    regio=regio)
        ver.save()

        return ver

    @staticmethod
    def _maak_evenement_locatie(ver):
        # maak een locatie aan
        loc = EvenementLocatie(naam='Grote Hal', adres='Grote baan\n1234XX Pijlstad', vereniging=ver)
        loc.save()
        return loc

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        self.account = self.e2e_create_account_admin()

        regio = Regio.objects.get(regio_nr=101)
        self.ver = self._maak_vereniging(1000, "Noordelijke club", regio)

        sporter = Sporter(
                        lid_nr=100000,
                        voornaam='Manager',
                        achternaam='van de Vereniging',
                        geboorte_datum='1966-06-06',
                        sinds_datum='2020-02-02',
                        postadres_1='Boog weg 1',
                        postadres_2='9999ZZ Boogdorp',
                        account=self.account,
                        bij_vereniging=self.ver)
        sporter.save()

        self.functie_mo = Functie.objects.get(rol='MO')
        self.functie_mo.accounts.add(self.account)

        self.functie_hwl = maak_functie('HWL 1000', 'HWL', vereniging=self.ver)
        self.functie_hwl.accounts.add(self.account)

        self.functie_wl = maak_functie('WL 1000', 'WL', vereniging=self.ver)
        self.functie_wl.accounts.add(self.account)

    def test_anon(self):
        url = self.url_overzicht % 666666
        resp = self.client.get(url)
        self.assert403(resp)
        resp = self.client.post(url)
        self.assert403(resp)

        url = self.url_wijzig % (666666, 666666)
        resp = self.client.get(url)
        self.assert403(resp)
        resp = self.client.post(url)
        self.assert403(resp)

    def test_mo(self):
        self.e2e_login_and_pass_otp(self.account)
        self.e2e_wissel_naar_functie(self.functie_mo)
        self.e2e_check_rol('MO')

        resp = self.client.get(self.url_overzicht % 666666)
        self.assert404(resp, 'Vereniging niet gevonden')

        url = self.url_overzicht % self.ver.ver_nr

        with override_settings(EVENEMENTEN_VERKOPER_VER_NRS=(9999,)):
            resp = self.client.get(url)
            self.assert403(resp)

        with override_settings(EVENEMENTEN_VERKOPER_VER_NRS=(self.ver.ver_nr,)):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)  # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('locatie/evenement-locaties.dtl', 'plein/site_layout.dtl'))

            # maak een nieuwe locatie aan
            self.assertEqual(EvenementLocatie.objects.count(), 0)
            resp = self.client.post(url)
            self.assertEqual(EvenementLocatie.objects.count(), 1)
            loc = EvenementLocatie.objects.first()
            url2 = self.url_wijzig % (self.ver.ver_nr, loc.pk)
            self.assert_is_redirect(resp, url2)

            # resp = self.client.get(url2)
            # self.assertEqual(resp.status_code, 200)  # 200 = OK
            # self.assert_html_ok(resp)
            # self.assert_template_used(resp, ('locatie/evenement-locatie-details.dtl', 'plein/site_layout.dtl'))

            # overzicht met locaties
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)  # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('locatie/evenement-locaties.dtl', 'plein/site_layout.dtl'))

        # helper functions
        loc = self._maak_evenement_locatie(self.ver)
        self.assertEqual(loc.adres_oneliner(), 'Grote baan, 1234XX Pijlstad')

        # corner cases
        resp = self.client.get(self.url_overzicht % 666666)
        self.assert404(resp, 'Vereniging niet gevonden')

        # admin functies
        self.assertTrue(str(loc) != '')
        loc.naam = loc.plaats
        self.assertTrue(str(loc) != '')
        loc.zichtbaar = False
        self.assertTrue(str(loc) != '')

    def test_wl(self):
        # wedstrijdleider krijgt read-only toegang
        self.e2e_login_and_pass_otp(self.account)
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')

        url = self.url_overzicht % self.ver.ver_nr
        with override_settings(EVENEMENTEN_VERKOPER_VER_NRS=(self.ver.ver_nr,)):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)  # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('locatie/evenement-locaties.dtl', 'plein/site_layout.dtl'))

            # probeer toe te voegen (mag niet)
            resp = self.client.post(url)
            self.assert403(resp, 'Geen toegang')

            # probeer te wijzigen (readonly)
            loc = self._maak_evenement_locatie(self.ver)
            url = self.url_wijzig % (self.ver.ver_nr, loc.pk)
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)  # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('locatie/evenement-locatie-details.dtl', 'plein/site_layout.dtl'))

            resp = self.client.post(url)
            self.assert403(resp, 'Wijzigen alleen door HWL en MO')

    def test_hwl(self):
        self.e2e_login_and_pass_otp(self.account)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # juiste vereniging
        url = self.url_overzicht % self.ver.ver_nr
        with override_settings(EVENEMENTEN_VERKOPER_VER_NRS=(self.ver.ver_nr,)):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)  # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('locatie/evenement-locaties.dtl', 'plein/site_layout.dtl'))

            # maak een nieuwe locatie aan
            self.assertEqual(EvenementLocatie.objects.count(), 0)
            resp = self.client.post(url)
            self.assertEqual(EvenementLocatie.objects.count(), 1)
            loc = EvenementLocatie.objects.first()
            url = self.url_wijzig % (self.ver.ver_nr, loc.pk)
            self.assert_is_redirect(resp, url)

            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)  # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('locatie/evenement-locatie-details.dtl', 'plein/site_layout.dtl'))

        # verkeerde vereniging
        ver2 = self._maak_vereniging(1001, 'Andere ver', self.ver.regio)
        loc2 = self._maak_evenement_locatie(ver2)

        with override_settings(EVENEMENTEN_VERKOPER_VER_NRS=(self.ver.ver_nr, ver2.ver_nr)):
            url = self.url_overzicht % ver2.ver_nr
            resp = self.client.get(url)
            self.assert404(resp, 'Niet de beheerder')

        with override_settings(EVENEMENTEN_VERKOPER_VER_NRS=(self.ver.ver_nr, ver2.ver_nr)):
            url = self.url_wijzig % (ver2.ver_nr, loc2.pk)
            resp = self.client.get(url)
            self.assert404(resp, 'Niet de beheerder')

    def test_wijzig(self):
        self.e2e_login_and_pass_otp(self.account)
        self.e2e_wissel_naar_functie(self.functie_mo)
        self.e2e_check_rol('MO')

        loc = self._maak_evenement_locatie(self.ver)
        url = self.url_wijzig % (self.ver.ver_nr, loc.pk)

        with override_settings(EVENEMENTEN_VERKOPER_VER_NRS=(9999,)):
            resp = self.client.get(url)
            self.assert403(resp, 'Geen toegang')

        with override_settings(EVENEMENTEN_VERKOPER_VER_NRS=(self.ver.ver_nr,)):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)  # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('locatie/evenement-locatie-details.dtl', 'plein/site_layout.dtl'))
            urls = self.extract_all_urls(resp, skip_menu=True)
            self.assertEqual(urls, [url, url])      # opslaan en verwijder

            # geen parameters
            resp = self.client.post(url)
            self.assert_is_redirect(resp, self.url_overzicht % self.ver.ver_nr)

            # wijzigingen opslaan
            resp = self.client.post(url, {'naam': 'Nieuwe naam',
                                          'adres': 'Nieuw adres\r\nMeerdere regels\nJaja',
                                          'plaats': 'Nieuwe plaats',
                                          'notities': 'whatever'})
            self.assert_is_redirect(resp, self.url_overzicht % self.ver.ver_nr)
            loc.refresh_from_db()
            self.assertEqual(loc.naam, 'Nieuwe naam')
            self.assertEqual(loc.adres, 'Nieuw adres\nMeerdere regels\nJaja')    # \r\n vervangen door \n
            self.assertEqual(loc.plaats, 'Nieuwe plaats')
            self.assertEqual(loc.notities, 'whatever')

            # opslaan zonder wijzigingen
            resp = self.client.post(url, {'naam': 'Nieuwe naam',
                                          'adres': 'Nieuw adres\r\nMeerdere regels\nJaja',
                                          'plaats': 'Nieuwe plaats',
                                          'notities': 'whatever'})
            self.assert_is_redirect(resp, self.url_overzicht % self.ver.ver_nr)

            # verwijderen
            resp = self.client.post(url, {'verwijder': 'ja'})
            self.assert_is_redirect(resp, self.url_overzicht % self.ver.ver_nr)
            loc.refresh_from_db()
            self.assertFalse(loc.zichtbaar)

        with override_settings(EVENEMENTEN_VERKOPER_VER_NRS=(self.ver.ver_nr,)):
            url2 = self.url_wijzig % (9999, loc.pk)
            resp = self.client.get(url2)
            self.assert404(resp, 'Vereniging niet gevonden')
            resp = self.client.post(url2)
            self.assert404(resp, 'Vereniging niet gevonden')

            url2 = self.url_wijzig % (self.ver.ver_nr, 9999)
            resp = self.client.get(url2)
            self.assert404(resp, 'Locatie bestaat niet')
            resp = self.client.post(url2)
            self.assert404(resp, 'Locatie bestaat niet')

    def test_wijzig_in_gebruik(self):
        self.e2e_login_and_pass_otp(self.account)
        self.e2e_wissel_naar_functie(self.functie_mo)
        self.e2e_check_rol('MO')

        loc = self._maak_evenement_locatie(self.ver)
        url = self.url_wijzig % (self.ver.ver_nr, loc.pk)

        Evenement(
                datum='2000-01-01',
                organiserende_vereniging=self.ver,
                locatie=loc).save()

        moment = OpleidingMoment(locatie=loc)
        moment.save()
        opleiding = Opleiding()
        opleiding.save()
        opleiding.momenten.add(moment)

        with override_settings(EVENEMENTEN_VERKOPER_VER_NRS=(self.ver.ver_nr,)):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)  # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('locatie/evenement-locatie-details.dtl', 'plein/site_layout.dtl'))

            urls = self.extract_all_urls(resp, skip_menu=True)
            self.assertEqual(urls, [url])      # opslaan (niet: verwijder)

            resp = self.client.post(url, {'verwijder': 'ja'})
            self.assert404(resp, 'Nog in gebruik')


# end of file
