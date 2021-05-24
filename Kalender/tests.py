# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
from Wedstrijden.models import WedstrijdLocatie
from .models import KalenderWedstrijd, KalenderWedstrijdSessie, WEDSTRIJD_STATUS_GEANNULEERD
import datetime


class TestKalender(E2EHelpers, TestCase):
    """ unit tests voor de Kalender applicatie """

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        lid = NhbLid(
                    nhb_nr=100000,
                    voornaam='Ad',
                    achternaam='de Admin',
                    geboorte_datum='1966-06-06',
                    sinds_datum='2020-02-02',
                    account=self.account_admin)
        lid.save()

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

        self.url_kalender = '/kalender/'
        self.url_kalender_maand = '/kalender/pagina-%s-%s/'                  # jaar, maand
        self.url_kalender_manager = '/kalender/manager/'
        self.url_kalender_vereniging = '/kalender/vereniging/'
        self.url_kalender_wijzig_wedstrijd = '/kalender/%s/wijzig/'          # wedstrijd_pk
        self.url_kalender_zet_status = '/kalender/%s/zet-status/'            # wedstrijd_pk
        self.url_kalender_sessies = '/kalender/%s/sessies/'                  # wedstrijd_pk
        self.url_kalender_wijzig_sessie = '/kalender/%s/sessies/%s/wijzig/'  # wedstrijd_pk, sessie_pk

    @staticmethod
    def _maak_externe_locatie(ver):
        # voeg een locatie toe
        locatie = WedstrijdLocatie(
                        baan_type='E',      # externe locatie
                        naam='Test locatie')
        locatie.save()
        locatie.verenigingen.add(ver)

        return locatie

    @staticmethod
    def _maak_accommodatie_binnen(ver):
        # voeg een locatie toe
        binnen_locatie = WedstrijdLocatie(
                                baan_type='X',      # onbekend
                                adres='Verweg 1, Om de hoek',
                                adres_uit_crm=True)
        binnen_locatie.save()
        binnen_locatie.verenigingen.add(ver)
        return binnen_locatie

    @staticmethod
    def _maak_accommodatie_buiten(ver):
        # voeg een locatie toe
        buiten_locatie = WedstrijdLocatie(
                                baan_type='B',      # buiten
                                adres_uit_crm=False,
                                discipline_outdoor=True,
                                buiten_banen=4)
        buiten_locatie.save()
        buiten_locatie.verenigingen.add(ver)
        return buiten_locatie

    def test_anon(self):
        self.client.logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender)
        self.assert_is_redirect_not_plein(resp)

        resp = self.client.get(self.url_kalender_manager)
        self.assert403(resp)

        resp = self.client.get(self.url_kalender_vereniging)
        self.assert403(resp)

        resp = self.client.get(self.url_kalender_wijzig_wedstrijd % 0)
        self.assert403(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_kalender)

    def test_gebruiker(self):
        self.client.logout()

        # haal de url op van de eerste pagina
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender)
        url = resp.url

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(url)

    def test_bb(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        resp = self.client.get(self.url_kalender)
        self.assert_is_redirect(resp, self.url_kalender_manager)

        resp = self.client.get(self.url_kalender_vereniging)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_manager)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-manager.dtl', 'plein/site_layout.dtl'))

        # wissel naar HWL en maak een wedstrijd aan
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self._maak_externe_locatie(self.nhbver1)
        resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        # wissel terug naar BB
        self.e2e_wisselnaarrol_bb()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_manager)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-manager.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_kalender_manager, post=False)

    def test_hwl(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        resp = self.client.get(self.url_kalender)
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        resp = self.client.get(self.url_kalender_manager)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_vereniging)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_kalender_vereniging, post=False)

        # gebruik de post interface zonder verzoek
        self.assertEqual(0, KalenderWedstrijd.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_kalender_vereniging)
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        self.assertEqual(0, KalenderWedstrijd.objects.count())

        # wedstrijd aanmaken zonder dat de vereniging een externe locatie heeft
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        self.assertEqual(0, KalenderWedstrijd.objects.count())

        # maak een wedstrijd aan
        self._maak_externe_locatie(self.nhbver1)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        self.assertEqual(1, KalenderWedstrijd.objects.count())

        # haal de wedstrijd op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_vereniging)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

    def test_maand(self):
        # maand als getal
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (2020, 1))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))

        # illegale maand getallen
        resp = self.client.get(self.url_kalender_maand % (2020, 0))
        self.assert404(resp)
        resp = self.client.get(self.url_kalender_maand % (2020, 0))
        self.assert404(resp)

        # maand als tekst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (2020, 'mrt'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # maand als tekst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (2020, 'maart'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # illegale maand tekst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (2020, 'xxx'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # illegaal jaar
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (2020, 'maart'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # wrap-around in december voor 'next'
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (2020, 12))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # wrap-around in januari voor 'prev'
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (2020, 1))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

    def test_wijzig_wedstrijd(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # wissel naar HWL en maak een wedstrijd aan
        self._maak_externe_locatie(self.nhbver1)            # locatie is noodzakelijk
        self.e2e_wissel_naar_functie(self.functie_hwl)
        resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        self.assertEqual(1, KalenderWedstrijd.objects.count())
        wedstrijd = KalenderWedstrijd.objects.all()[0]
        self.assertTrue(str(wedstrijd) != '')
        url = self.url_kalender_wijzig_wedstrijd % wedstrijd.pk

        # haal de wedstrijd op met status 'ontwerp'
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # buiten locatie zonder binnen locatie
        locatie_buiten = self._maak_accommodatie_buiten(self.nhbver1)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # buiten locatie met binnen locatie
        self._maak_accommodatie_binnen(self.nhbver1)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # wijzig velden via de 'post' interface
        loc_sel = 'loc_%s' % locatie_buiten.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'titel': 'Test Titel',
                                          'wedstrijd_duur': 'duur_1',
                                          'contact_naam': 'Test Naam',
                                          'contact_email': 'Test Email',
                                          'contact_website': 'http://test.website.nl',
                                          'contact_telefoon': 'Test Telefoon',
                                          'aantal_banen': '42',
                                          'discipline': 'disc_OD',
                                          'wa_status': 'wa_B',
                                          'locatie': loc_sel,
                                          'aanwezig': 'aanwezig_35',
                                          'scheidsrechters': 'Scheid1\nScheid2',
                                          'begrenzing': 'begrenzing_L',
                                          'extern': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.titel, 'Test Titel')
        self.assertEqual(wedstrijd.datum_begin, wedstrijd.datum_einde)
        self.assertEqual(wedstrijd.contact_naam, 'Test Naam')
        self.assertEqual(wedstrijd.contact_email, 'Test Email')
        self.assertEqual(wedstrijd.contact_website, 'http://test.website.nl')
        self.assertEqual(wedstrijd.contact_telefoon, 'Test Telefoon')
        self.assertEqual(wedstrijd.aantal_banen, 42)
        self.assertEqual(wedstrijd.discipline, 'OD')
        self.assertEqual(wedstrijd.scheidsrechters, 'Scheid1\nScheid2')
        self.assertEqual(wedstrijd.minuten_voor_begin_sessie_aanwezig_zijn, 35)
        self.assertEqual(wedstrijd.locatie, locatie_buiten)
        self.assertEqual(wedstrijd.begrenzing, 'L')
        self.assertTrue(wedstrijd.extern_beheerd)

        datum = '%s-1-1' % (wedstrijd.datum_begin.year + 1)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum_begin': datum,
                                          'wedstrijd_duur': 'duur_5',
                                          'wa_status': 'wa_A',
                                          'aantal_banen': '0'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.wa_status, 'B')
        self.assertFalse(wedstrijd.extern_beheerd)

        return

        # akkoord WA status
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wa_status': 'wa_A',
                                          'akkoord_a_status': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.wa_status, 'A')

        # zet de wedstrijd door 'Wacht op goedkeuring' en haal de pagina opnieuw op
        wedstrijd.status = 'W'
        wedstrijd.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # probeer wijzigingen te doen aan een wedstrijd die voorbij Ontwerp fase is
        datum = '%s-3-3' % wedstrijd.datum_begin.year
        oude_datum_begin = wedstrijd.datum_begin
        oude_datum_einde = wedstrijd.datum_einde
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'titel': 'Test Titel 3',              # mag wel
                                          'datum_begin': datum,
                                          'wedstrijd_duur': 'duur_1',
                                          'contact_naam': 'Test Naam 3',        # mag wel
                                          'contact_email': 'Test Email 3',
                                          'contact_website': 'http://test3.website.nl',
                                          'contact_telefoon': 'Test Telefoon 3',
                                          'aantal_banen': '41',                 # mag wel
                                          'discipline': 'disc_3D',
                                          'wa_status': 'wa_B',
                                          'scheidsrechters': 'Scheid4',         # mag wel
                                          'begrenzing': 'begrenzing_V'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.titel, 'Test Titel 3')
        self.assertEqual(wedstrijd.datum_begin, oude_datum_begin)
        self.assertEqual(wedstrijd.datum_einde, oude_datum_einde)
        self.assertEqual(wedstrijd.contact_naam, 'Test Naam 3')
        self.assertEqual(wedstrijd.contact_email, 'Test Email 3')
        self.assertEqual(wedstrijd.contact_website, 'http://test3.website.nl')
        self.assertEqual(wedstrijd.contact_telefoon, 'Test Telefoon 3')
        self.assertEqual(wedstrijd.aantal_banen, 41)
        self.assertEqual(wedstrijd.discipline, 'OD')
        self.assertEqual(wedstrijd.scheidsrechters, 'Scheid4')
        self.assertEqual(wedstrijd.begrenzing, 'L')

        # zet de wedstrijd door 'Geaccepteerd' en haal de pagina opnieuw op
        wedstrijd.status = 'A'
        wedstrijd.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # zet de wedstrijd door 'Geannuleerd' en haal de pagina opnieuw op
        wedstrijd.status = WEDSTRIJD_STATUS_GEANNULEERD
        wedstrijd.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # probeer wijzigingen te doen aan een geannuleerde wedstrijd
        datum = '%s-2-2' % wedstrijd.datum_begin.year
        oude_datum_begin = wedstrijd.datum_begin
        oude_datum_einde = wedstrijd.datum_einde
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'titel': 'Test Titel 2',              # mag wel
                                          'datum_begin': datum,
                                          'wedstrijd_duur': 'duur_1',
                                          'contact_naam': 'Test Naam 2',
                                          'contact_email': 'Test Email 2',
                                          'contact_website': 'Test Website 2',
                                          'contact_telefoon': 'Test Telefoon 2',
                                          'aantal_banen': '40',
                                          'discipline': 'disc_3D',
                                          'wa_status': 'wa_B',
                                          'scheidsrechters': 'Scheid3',
                                          'begrenzing': 'begrenzing_Y'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.titel, 'Test Titel 2')
        self.assertEqual(wedstrijd.datum_begin, oude_datum_begin)
        self.assertEqual(wedstrijd.datum_einde, oude_datum_einde)
        self.assertEqual(wedstrijd.contact_naam, 'Test Naam 3')
        self.assertEqual(wedstrijd.contact_email, 'Test Email 3')
        self.assertEqual(wedstrijd.contact_website, 'http://test3.website.nl')
        self.assertEqual(wedstrijd.contact_telefoon, 'Test Telefoon 3')
        self.assertEqual(wedstrijd.aantal_banen, 41)
        self.assertEqual(wedstrijd.discipline, 'OD')
        self.assertEqual(wedstrijd.scheidsrechters, 'Scheid4')
        self.assertEqual(wedstrijd.begrenzing, 'L')

        # niet bestaande wedstrijd
        resp = self.client.get(self.url_kalender_wijzig_wedstrijd % 999999)
        self.assert404(resp)
        resp = self.client.post(self.url_kalender_wijzig_wedstrijd % 999999)
        self.assert404(resp)

        # nu als BB
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

        wedstrijd.status = 'W'
        wedstrijd.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        wedstrijd.status = 'A'
        wedstrijd.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'titel': 'Aangepast door BB'})
        self.assert_is_redirect(resp, self.url_kalender_manager)

        # echt verwijderen van de wedstrijd
        wedstrijd.status = 'O'
        wedstrijd.save()
        self.assertEqual(1, KalenderWedstrijd.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verwijder_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_manager)
        self.assertEqual(0, KalenderWedstrijd.objects.count())

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

    def test_wijzig_bad(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # wissel naar HWL en maak een wedstrijd aan
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self._maak_externe_locatie(self.nhbver1)
        resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        self.assertEqual(1, KalenderWedstrijd.objects.count())
        wedstrijd = KalenderWedstrijd.objects.all()[0]
        url = self.url_kalender_wijzig_wedstrijd % wedstrijd.pk

        # wijzig velden via de 'post' interface
        with self.assert_max_queries(20):
            resp = self.client.post(url, {})        # geen parameters
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        # geen valide datum (parsing exception)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum_begin': 'not-a-date'})
        self.assert404(resp)

        # te ver in het verleden
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum_begin': '2000-01-02'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wedstrijd_duur': 'duur_'})
        self.assert404(resp)

        # illegaal aantal banen
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_banen': 'x'})
        self.assert404(resp)

        # niet bestaande locatie
        # en niet bekende aanwezigheid
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'locatie': 'loc_99999',
                                          'aanwezig': 'aanwezig_99'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        # verwijderen in verkeerde fase
        for status in "WAX":
            wedstrijd.status = status
            wedstrijd.save()
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'verwijder_wedstrijd': 'ja'})
            self.assert_is_redirect(resp, self.url_kalender_vereniging)
            wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)      # nog steeds aanwezig?
        # for

        # verkeerder vereniging
        wedstrijd.organiserende_vereniging = self.nhbver2
        wedstrijd.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {})
        self.assert403(resp)

    def test_zet_status(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # wissel naar HWL en maak een wedstrijd aan
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self._maak_externe_locatie(self.nhbver1)
        resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        self.assertEqual(1, KalenderWedstrijd.objects.count())
        wedstrijd = KalenderWedstrijd.objects.all()[0]
        url = self.url_kalender_zet_status % wedstrijd.pk

        with self.assert_max_queries(20):
            resp = self.client.post(url, {})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        # doorzetten naar 'Wacht op goedkeuring'
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verder': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.status, 'W')

        # verkeerde vereniging
        wedstrijd.organiserende_vereniging = self.nhbver2
        wedstrijd.save()
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verder': 'ja'})
        self.assert403(resp)

        wedstrijd.organiserende_vereniging = self.nhbver1
        wedstrijd.save()

        # nu als BB
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.post(url, {})
        self.assert_is_redirect(resp, self.url_kalender_manager)

        # van Wacht-op-goedkeuring terug naar Ontwerp
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'terug': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_manager)
        wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.status, 'O')

        # vanuit ontwerp blijf je in Ontwerp
        with self.assert_max_queries(20):
            resp = self.client.post(url, {})
        self.assert_is_redirect(resp, self.url_kalender_manager)

        # van Ontwerp weer naar Wacht-op-goedkeuring
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verder': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_manager)
        wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.status, 'W')

        # van Wacht-op-goedkeuring door naar Geaccepteerd
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verder': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_manager)
        wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.status, 'A')

        # van Geaccepteerd kan je niet verder of terug
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verder': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_manager)
        wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.status, 'A')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'terug': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_manager)
        wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.status, 'A')

        # Annuleer
        for status in "OWAX":
            wedstrijd.status = status
            wedstrijd.save()
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'annuleer': 'ja'})
            self.assert_is_redirect(resp, self.url_kalender_manager)
            wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
            self.assertEqual(wedstrijd.status, 'X')
        # for

        # slechte wedstrijd_pk
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_kalender_zet_status % 999999, {})
        self.assert404(resp)

    def test_sessies(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # wissel naar HWL en maak een wedstrijd aan
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self._maak_externe_locatie(self.nhbver1)
        resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        self.assertEqual(1, KalenderWedstrijd.objects.count())
        wedstrijd = KalenderWedstrijd.objects.all()[0]
        url = self.url_kalender_sessies % wedstrijd.pk

        # haal de sessie op
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/wijzig-sessies.dtl', 'plein/site_layout.dtl'))

        # post zonder actie
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, url)

        # nieuwe sessie
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'nieuwe_sessie': 'graag'})
        self.assert_is_redirect(resp, url)

        # schakel naar BB rol
        self.e2e_wisselnaarrol_bb()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/wijzig-sessies.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

    def test_sessies_bad(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # niet bestaande sessie
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_sessies % 99999)
        self.assert404(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_kalender_sessies % 99999)
        self.assert404(resp)

        # maak een wedstrijd aan en wissel die naar een andere vereniging
        self._maak_externe_locatie(self.nhbver1)
        resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        self.assertEqual(1, KalenderWedstrijd.objects.count())
        wedstrijd = KalenderWedstrijd.objects.all()[0]
        wedstrijd.organiserende_vereniging = self.nhbver2
        wedstrijd.save()

        # verkeerde vereniging
        url = self.url_kalender_sessies % wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

    def test_wijzig_sessie(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # maak een wedstrijd en sessie aan
        self._maak_externe_locatie(self.nhbver1)
        resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        self.assertEqual(1, KalenderWedstrijd.objects.count())
        wedstrijd = KalenderWedstrijd.objects.all()[0]
        wedstrijd.datum_einde = wedstrijd.datum_begin + datetime.timedelta(days=2)
        wedstrijd.save()
        url = self.url_kalender_sessies % wedstrijd.pk
        resp = self.client.post(url, {'nieuwe_sessie': 'graag'})
        self.assert_is_redirect(resp, url)
        self.assertEqual(1, KalenderWedstrijdSessie.objects.count())
        sessie = KalenderWedstrijdSessie.objects.all()[0]

        # haal de wijzig pagina op
        url = self.url_kalender_wijzig_sessie % (wedstrijd.pk, sessie.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/wijzig-sessie.dtl', 'plein/site_layout.dtl'))

        # lege post
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_kalender_sessies % wedstrijd.pk)

        # zet de datum op de 3 mogelijkheden
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum': 'datum_2'})
        self.assert_is_redirect(resp, self.url_kalender_sessies % wedstrijd.pk)
        sessie = KalenderWedstrijdSessie.objects.get(pk=sessie.pk)
        self.assertEqual(sessie.datum, wedstrijd.datum_einde)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum': 'datum_0'})
        self.assert_is_redirect(resp, self.url_kalender_sessies % wedstrijd.pk)
        sessie = KalenderWedstrijdSessie.objects.get(pk=sessie.pk)
        self.assertEqual(sessie.datum, wedstrijd.datum_begin)

        # wijzig een aantal parameters
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum': 'datum_0',
                                          'tijd_begin': '12:34',
                                          'duur': 'duur_60',
                                          'max_sporters': '42'})
        self.assert_is_redirect(resp, self.url_kalender_sessies % wedstrijd.pk)
        sessie = KalenderWedstrijdSessie.objects.get(pk=sessie.pk)
        self.assertEqual(sessie.datum, wedstrijd.datum_begin)
        self.assertEqual(sessie.tijd_begin.hour, 12)
        self.assertEqual(sessie.tijd_begin.minute, 34)
        self.assertEqual(str(sessie.tijd_einde), '13:34:00')
        self.assertEqual(sessie.max_sporters, 42)

        # test de tijdstippen voor een nachtverschieting
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'tijd_begin': '23:30',
                                          'duur': 'duur_90'})
        self.assert_is_redirect(resp, self.url_kalender_sessies % wedstrijd.pk)
        sessie = KalenderWedstrijdSessie.objects.get(pk=sessie.pk)
        self.assertEqual(str(sessie.tijd_begin), '23:30:00')
        self.assertEqual(str(sessie.tijd_einde), '01:00:00')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'tijd_begin': '22:00',
                                          'duur': 'duur_120'})
        self.assert_is_redirect(resp, self.url_kalender_sessies % wedstrijd.pk)
        sessie = KalenderWedstrijdSessie.objects.get(pk=sessie.pk)
        self.assertEqual(str(sessie.tijd_begin), '22:00:00')
        self.assertEqual(str(sessie.tijd_einde), '00:00:00')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/wijzig-sessie.dtl', 'plein/site_layout.dtl'))

        # annuleer de wedstrijd
        old_status = wedstrijd.status
        wedstrijd.status = WEDSTRIJD_STATUS_GEANNULEERD
        wedstrijd.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/wijzig-sessie.dtl', 'plein/site_layout.dtl'))

        # verwijder de sessie
        self.assertEqual(1, KalenderWedstrijdSessie.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verwijder_sessie': 'graag'})
        self.assert404(resp)
        self.assertEqual(1, KalenderWedstrijdSessie.objects.count())

        # herstel de wedstrijd
        wedstrijd.status = old_status
        wedstrijd.save()

        # verwijder de sessie
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verwijder_sessie': 'graag'})
        self.assert_is_redirect(resp, self.url_kalender_sessies % wedstrijd.pk)
        self.assertEqual(0, KalenderWedstrijdSessie.objects.count())

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

    def test_wijzig_sessie_bad(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # maak een wedstrijd en sessie aan
        self._maak_externe_locatie(self.nhbver1)
        resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        self.assertEqual(1, KalenderWedstrijd.objects.count())
        wedstrijd = KalenderWedstrijd.objects.all()[0]
        url = self.url_kalender_sessies % wedstrijd.pk
        resp = self.client.post(url, {'nieuwe_sessie': 'graag'})
        self.assert_is_redirect(resp, url)
        self.assertEqual(1, KalenderWedstrijdSessie.objects.count())
        sessie = KalenderWedstrijdSessie.objects.all()[0]

        # niet bestaande wedstrijd
        url = self.url_kalender_wijzig_sessie % (999999, 0)
        resp = self.client.get(url)
        self.assert404(resp)
        resp = self.client.post(url)
        self.assert404(resp)

        # niet bestaande sessie
        url = self.url_kalender_wijzig_sessie % (wedstrijd.pk, 999999)
        resp = self.client.get(url)
        self.assert404(resp)
        resp = self.client.post(url)
        self.assert404(resp)

        url = self.url_kalender_wijzig_sessie % (wedstrijd.pk, sessie.pk)

        # slechte datum en tijd
        oude_datum = sessie.datum
        resp = self.client.post(url, {'datum': 'datum_999'})
        sessie = KalenderWedstrijdSessie.objects.get(pk=sessie.pk)
        self.assertEqual(oude_datum, sessie.datum)

        # slechte tijd
        resp = self.client.post(url, {'tijd_begin': 'hoi'})
        self.assert404(resp)
        resp = self.client.post(url, {'tijd_begin': '24:60'})
        self.assert404(resp)

        # goede tijd, slechte duur
        resp = self.client.post(url, {'tijd_begin': '10:30',
                                      'duur': 'hoi'})
        self.assert_is_redirect_not_plein(resp)
        resp = self.client.post(url, {'tijd_begin': '10:30',
                                      'duur': 'duur_99999'})
        self.assert_is_redirect_not_plein(resp)

        # slecht aantal sporters
        resp = self.client.post(url, {'max_sporters': 'hoi'})
        self.assert404(resp)
        resp = self.client.post(url, {'max_sporters': '-1'})
        self.assert404(resp)
        resp = self.client.post(url, {'max_sporters': 0.141})
        self.assert404(resp)
        resp = self.client.post(url, {'max_sporters': '0'})
        self.assert404(resp)
        resp = self.client.post(url, {'max_sporters': '1000'})
        self.assert404(resp)

        # niet van deze vereniging
        wedstrijd.organiserende_vereniging = self.nhbver2
        wedstrijd.save()
        url = self.url_kalender_wijzig_sessie % (wedstrijd.pk, sessie.pk)
        resp = self.client.get(url)
        self.assert403(resp)
        resp = self.client.post(url)
        self.assert403(resp)

        # maak nog een wedstrijd en sessie aan
        resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assertEqual(2, KalenderWedstrijd.objects.count())
        wedstrijd2 = KalenderWedstrijd.objects.exclude(pk=wedstrijd.pk)[0]
        url = self.url_kalender_sessies % wedstrijd2.pk
        resp = self.client.post(url, {'nieuwe_sessie': 'graag'})
        self.assert_is_redirect(resp, url)
        self.assertEqual(2, KalenderWedstrijdSessie.objects.count())
        sessie2 = KalenderWedstrijdSessie.objects.exclude(pk=sessie.pk)[0]

        # mix de twee: sessie hoort niet bij wedstrijd
        url = self.url_kalender_wijzig_sessie % (wedstrijd2.pk, sessie.pk)
        resp = self.client.get(url)
        self.assert404(resp)
        resp = self.client.post(url)
        self.assert404(resp)

    def test_wijzig_wedstrijd_datum(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # maak een wedstrijd en sessie aan
        self._maak_externe_locatie(self.nhbver1)
        resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        self.assertEqual(1, KalenderWedstrijd.objects.count())
        wedstrijd = KalenderWedstrijd.objects.all()[0]
        url = self.url_kalender_sessies % wedstrijd.pk
        resp = self.client.post(url, {'nieuwe_sessie': 'graag'})
        self.assert_is_redirect(resp, url)
        self.assertEqual(1, KalenderWedstrijdSessie.objects.count())
        sessie = KalenderWedstrijdSessie.objects.all()[0]

        # wijzig de wedstrijd datum en controleer dat de sessie mee gaat
        self.assertEqual(sessie.datum, wedstrijd.datum_begin)
        url = self.url_kalender_wijzig_wedstrijd % wedstrijd.pk
        datum = wedstrijd.datum_begin + datetime.timedelta(days=3)
        resp = self.client.post(url, {'datum_begin': str(datum)})
        self.assert_is_redirect_not_plein(resp)

        wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
        sessie = KalenderWedstrijdSessie.objects.get(pk=sessie.pk)
        self.assertEqual(wedstrijd.datum_begin, datum)
        self.assertEqual(sessie.datum, datum)


# end of file
