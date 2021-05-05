# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
from Wedstrijden.models import WedstrijdLocatie
from .models import KalenderWedstrijd


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
        self.url_kalender_maand = '/kalender/pagina-%s-%s/'          # jaar, maand
        self.url_kalender_manager = '/kalender/manager/'
        self.url_kalender_vereniging = '/kalender/vereniging/'
        self.url_kalender_wijzig = '/kalender/%s/wijzig/'           # wedstrijd_pk
        self.url_kalender_zet_status = '/kalender/%s/zet-status/'   # wedstrijd_pk

    def _maak_externe_locatie(self):
        # voeg een locatie toe
        locatie = WedstrijdLocatie(
                        baan_type='E',      # externe locatie
                        naam='Test locatie')
        locatie.save()
        locatie.verenigingen.add(self.nhbver1)

        return locatie

    def test_anon(self):
        self.client.logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender)
        self.assert_is_redirect_not_plein(resp)

        resp = self.client.get(self.url_kalender_manager)
        self.assert403(resp)

        resp = self.client.get(self.url_kalender_vereniging)
        self.assert403(resp)

        resp = self.client.get(self.url_kalender_wijzig % 0)
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
        self._maak_externe_locatie()
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
        locatie = self._maak_externe_locatie()
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
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self._maak_externe_locatie()
        resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        self.assertEqual(1, KalenderWedstrijd.objects.count())
        wedstrijd = KalenderWedstrijd.objects.all()[0]
        url = self.url_kalender_wijzig % wedstrijd.pk

        # haal de wedstrijd op met status 'ontwerp'
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # wijzig velden via de 'post' interface
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'titel': 'Test Titel',
                                          'wedstrijd_duur': 'duur_1',
                                          'contact_naam': 'Test Naam',
                                          'contact_email': 'Test Email',
                                          'contact_website': 'Test Website',
                                          'contact_telefoon': 'Test Telefoon',
                                          'aantal_banen': '42',
                                          'discipline': 'disc_OD',
                                          'wa_status': 'wa_B',
                                          'scheidsrechters': 'Scheid1\nScheid2'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.titel, 'Test Titel')
        self.assertEqual(wedstrijd.datum_begin, wedstrijd.datum_einde)
        self.assertEqual(wedstrijd.contact_naam, 'Test Naam')
        self.assertEqual(wedstrijd.contact_email, 'Test Email')
        self.assertEqual(wedstrijd.contact_website, 'Test Website')
        self.assertEqual(wedstrijd.contact_telefoon, 'Test Telefoon')
        self.assertEqual(wedstrijd.aantal_banen, 42)
        self.assertEqual(wedstrijd.discipline, 'OD')
        self.assertEqual(wedstrijd.scheidsrechters, 'Scheid1\nScheid2')

        datum = '%s-1-1' % (wedstrijd.datum_begin.year + 1)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum_begin': datum,
                                          'wedstrijd_duur': 'duur_5',
                                          'wa_status': 'wa_A',
                                          'aantal_banen': '0'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.wa_status, 'B')

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
                                          'contact_website': 'Test Website 3',
                                          'contact_telefoon': 'Test Telefoon 3',
                                          'aantal_banen': '41',                 # mag wel
                                          'discipline': 'disc_3D',
                                          'wa_status': 'wa_B',
                                          'scheidsrechters': 'Scheid4'})        # mag wel
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.titel, 'Test Titel 3')
        self.assertEqual(wedstrijd.datum_begin, oude_datum_begin)
        self.assertEqual(wedstrijd.datum_einde, oude_datum_einde)
        self.assertEqual(wedstrijd.contact_naam, 'Test Naam 3')
        self.assertEqual(wedstrijd.contact_email, 'Test Email 3')
        self.assertEqual(wedstrijd.contact_website, 'Test Website 3')
        self.assertEqual(wedstrijd.contact_telefoon, 'Test Telefoon 3')
        self.assertEqual(wedstrijd.aantal_banen, 41)
        self.assertEqual(wedstrijd.discipline, 'OD')
        self.assertEqual(wedstrijd.scheidsrechters, 'Scheid4')

        # zet de wedstrijd door 'Geaccepteerd' en haal de pagina opnieuw op
        wedstrijd.status = 'A'
        wedstrijd.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # zet de wedstrijd door 'Geannuleerd' en haal de pagina opnieuw op
        wedstrijd.status = 'X'
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
                                          'scheidsrechters': 'Scheid3'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.titel, 'Test Titel 2')
        self.assertEqual(wedstrijd.datum_begin, oude_datum_begin)
        self.assertEqual(wedstrijd.datum_einde, oude_datum_einde)
        self.assertEqual(wedstrijd.contact_naam, 'Test Naam 3')
        self.assertEqual(wedstrijd.contact_email, 'Test Email 3')
        self.assertEqual(wedstrijd.contact_website, 'Test Website 3')
        self.assertEqual(wedstrijd.contact_telefoon, 'Test Telefoon 3')
        self.assertEqual(wedstrijd.aantal_banen, 41)
        self.assertEqual(wedstrijd.discipline, 'OD')
        self.assertEqual(wedstrijd.scheidsrechters, 'Scheid4')

        # niet bestaande wedstrijd
        resp = self.client.get(self.url_kalender_wijzig % 999999)
        self.assert404(resp)
        resp = self.client.post(self.url_kalender_wijzig % 999999)
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
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verwijder_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_manager)

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

    def test_wijzig_bad(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # wissel naar HWL en maak een wedstrijd aan
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self._maak_externe_locatie()
        resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        self.assertEqual(1, KalenderWedstrijd.objects.count())
        wedstrijd = KalenderWedstrijd.objects.all()[0]
        url = self.url_kalender_wijzig % wedstrijd.pk

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

        # illegaal aantal banen
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_banen': 'x'})
        self.assert404(resp)

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
        self._maak_externe_locatie()
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

# end of file
