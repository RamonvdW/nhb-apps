# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter
from Wedstrijden.models import WedstrijdLocatie
from .models import KalenderWedstrijd, KalenderWedstrijdSessie, WEDSTRIJD_STATUS_GEANNULEERD
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestKalenderWedstrijd(E2EHelpers, TestCase):

    """ tests voor de Kalender applicatie """

    url_kalender_manager = '/kalender/manager/'
    url_kalender_vereniging = '/kalender/vereniging/'
    url_kalender_wijzig_wedstrijd = '/kalender/%s/wijzig/'  # wedstrijd_pk
    url_kalender_zet_status = '/kalender/%s/zet-status/'  # wedstrijd_pk
    url_kalender_sessies = '/kalender/%s/sessies/'  # wedstrijd_pk

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
                                          'scheidsrechters': 'Scheids1\nScheids2',
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
        self.assertEqual(wedstrijd.scheidsrechters, 'Scheids1\nScheids2')
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
                                          'aantal_banen': '41',
                                          'discipline': 'disc_3D',
                                          'wa_status': 'wa_B',
                                          'scheidsrechters': 'Scheids4',
                                          'begrenzing': 'begrenzing_V',         # mag wel
                                          'extern': 'nee'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.titel, 'Test Titel 3')
        self.assertEqual(wedstrijd.datum_begin, oude_datum_begin)
        self.assertEqual(wedstrijd.datum_einde, oude_datum_einde)
        self.assertEqual(wedstrijd.contact_naam, 'Test Naam 3')
        self.assertEqual(wedstrijd.contact_email, 'Test Email 3')
        self.assertEqual(wedstrijd.contact_website, 'http://test3.website.nl')
        self.assertEqual(wedstrijd.contact_telefoon, 'Test Telefoon 3')
        self.assertEqual(wedstrijd.aantal_banen, 42)
        self.assertEqual(wedstrijd.discipline, 'OD')
        self.assertEqual(wedstrijd.scheidsrechters, 'Scheids1\nScheids2')
        self.assertEqual(wedstrijd.begrenzing, 'V')
        self.assertTrue(wedstrijd.extern_beheerd)

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
                                          'scheidsrechters': 'Scheids3',
                                          'begrenzing': 'begrenzing_Y',
                                          'extern': 'nee'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.titel, 'Test Titel 2')
        self.assertEqual(wedstrijd.datum_begin, oude_datum_begin)
        self.assertEqual(wedstrijd.datum_einde, oude_datum_einde)
        self.assertEqual(wedstrijd.contact_naam, 'Test Naam 3')
        self.assertEqual(wedstrijd.contact_email, 'Test Email 3')
        self.assertEqual(wedstrijd.contact_website, 'http://test3.website.nl')
        self.assertEqual(wedstrijd.contact_telefoon, 'Test Telefoon 3')
        self.assertEqual(wedstrijd.aantal_banen, 42)
        self.assertEqual(wedstrijd.discipline, 'OD')
        self.assertEqual(wedstrijd.scheidsrechters, 'Scheids1\nScheids2')
        self.assertEqual(wedstrijd.begrenzing, 'V')
        self.assertTrue(wedstrijd.extern_beheerd)

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

        wedstrijd.status = 'W'      # wacht op goedkeuring
        wedstrijd.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        wedstrijd.status = 'A'      # geaccepteerd
        wedstrijd.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'titel': 'Aangepast door BB'})
        self.assert_is_redirect(resp, self.url_kalender_manager)

        wedstrijd.status = 'X'      # geannuleerd
        wedstrijd.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # echt verwijderen van de wedstrijd
        wedstrijd.status = 'O'      # ontwerp
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

    def test_vastpinnen(self):
        # controleer dat sessies en boogtypen niet aangepast kunnen worden als ze in gebruik zijn
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # maak een wedstrijd met twee sessies aan
        self._maak_externe_locatie(self.nhbver1)
        resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        self.assertEqual(1, KalenderWedstrijd.objects.count())
        wedstrijd = KalenderWedstrijd.objects.all()[0]
        self.assertEqual(wedstrijd.boogtypen.count(), 6)
        self.assertEqual(wedstrijd.wedstrijdklassen.count(), 49)

        url = self.url_kalender_sessies % wedstrijd.pk
        resp = self.client.post(url, {'nieuwe_sessie': 'graag'})
        self.assert_is_redirect(resp, url)
        resp = self.client.post(url, {'nieuwe_sessie': 'graag'})
        self.assert_is_redirect(resp, url)
        self.assertEqual(2, KalenderWedstrijdSessie.objects.count())
        sessie = KalenderWedstrijdSessie.objects.all()[0]
        sessie2 = KalenderWedstrijdSessie.objects.all()[1]

        wkl = wedstrijd.wedstrijdklassen.get(beschrijving='Recurve 50+ vrouwen (master)')
        sessie2.wedstrijdklassen.add(wkl)

        wkl = wedstrijd.wedstrijdklassen.get(beschrijving='Recurve 50+ mannen (master)')
        wkl_pks = list(wedstrijd.wedstrijdklassen.values_list('pk', flat=True))
        sessie.wedstrijdklassen.add(wkl)
        sessie2.wedstrijdklassen.add(wkl)

        # zet een paar boogtypen uit
        url = self.url_kalender_wijzig_wedstrijd % wedstrijd.pk
        post_data = dict()
        post_data['boog_R'] = 'on'
        post_data['boog_C'] = 'on'
        for pk in wkl_pks:
            post_data['klasse_%s' % pk] = 'on'
        # for
        with self.assert_max_queries(20):
            resp = self.client.post(url, post_data)
        self.assert_is_redirect_not_plein(resp)

        self.assertEqual(wedstrijd.boogtypen.count(), 2)                # alleen R en C
        self.assertEqual(wedstrijd.wedstrijdklassen.count(), 17)        # alleen R en C klassen

        # kies een wedstrijdklasse in een sessie
        sessie.wedstrijdklassen.add(wkl)

        # probeer nu de recurve boog uit te zetten
        del post_data['boog_R']
        with self.assert_max_queries(20):
            resp = self.client.post(url, post_data)
        self.assert_is_redirect_not_plein(resp)

        self.assertEqual(wedstrijd.boogtypen.count(), 2)                # alleen R en C

        # probeer nu alle wedstrijdklassen uit te zetten
        with self.assert_max_queries(20):
            resp = self.client.post(url, {})
        self.assert_is_redirect_not_plein(resp)

        self.assertEqual(wedstrijd.boogtypen.count(), 1)                # alleen R
        self.assertEqual(wedstrijd.wedstrijdklassen.count(), 2)         # alleen de in de sessies gebruikte klassen

        # doe een GET, voor de coverage
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

# end of file
