# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import KalenderWedstrijdklasse
from Functie.operations import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Wedstrijden.models import WedstrijdLocatie, Wedstrijd, WedstrijdSessie, WEDSTRIJD_STATUS_GEANNULEERD
import datetime


class TestWedstrijd(E2EHelpers, TestCase):

    """ tests voor de Wedstrijden applicatie, module wedstrijd wijzigen """

    url_kalender_manager = '/wedstrijden/manager/'
    url_kalender_vereniging = '/wedstrijden/vereniging/'
    url_kalender_maak_nieuw = '/wedstrijden/vereniging/kies-type/'
    url_kalender_wijzig_wedstrijd = '/wedstrijden/%s/wijzig/'  # wedstrijd_pk
    url_kalender_zet_status = '/wedstrijden/%s/zet-status/'    # wedstrijd_pk
    url_kalender_sessies = '/wedstrijden/%s/sessies/'          # wedstrijd_pk

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        Sporter(
                lid_nr=100000,
                voornaam='Ad',
                achternaam='de Admin',
                geboorte_datum='1966-06-06',
                sinds_datum='2020-02-02',
                account=self.account_admin).save()
        self.sporter = Sporter.objects.get(lid_nr=100000)     # geeft bruikbare geboorte_datum

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

        # onder 18 in 2022
        Sporter(
                lid_nr=100001,
                voornaam='Onder',
                achternaam='Achttien',
                geboorte_datum='2012-06-06',
                sinds_datum='2020-02-02').save()
        self.sporter_jong = Sporter.objects.get(lid_nr=100001)     # geeft bruikbare geboorte_datum

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
        resp = self.client.post(self.url_kalender_maak_nieuw, {'keuze': 'nhb'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.all()[0]
        self.assertTrue(str(wedstrijd) != '')

        url = self.url_kalender_wijzig_wedstrijd % wedstrijd.pk

        # haal de wedstrijd op met status 'ontwerp'
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

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
                                          'extern': 'ja',
                                          'sluit': 'sluit_5'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
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
        self.assertEqual(wedstrijd.inschrijven_tot, 5)
        self.assertTrue(wedstrijd.extern_beheerd)

        datum = '%s-1-1' % (wedstrijd.datum_begin.year + 1)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum_begin': datum,
                                          'wedstrijd_duur': 'duur_5',
                                          'wa_status': 'wa_A',
                                          'aantal_banen': '0'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.wa_status, 'B')
        self.assertFalse(wedstrijd.extern_beheerd)

        # akkoord WA status
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wa_status': 'wa_A',
                                          'akkoord_a_status': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
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
                                          'extern': 'nee',
                                          'sluit': 'sluit_9999'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
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
        self.assertEqual(wedstrijd.inschrijven_tot, 5)
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
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.titel, 'Test Titel 2')
        self.assertEqual(wedstrijd.datum_begin, oude_datum_begin)
        self.assertEqual(wedstrijd.datum_einde, oude_datum_einde)
        self.assertEqual(wedstrijd.contact_naam, 'Test Naam 2')
        self.assertEqual(wedstrijd.contact_email, 'Test Email 2')
        self.assertEqual(wedstrijd.contact_website, 'Test Website 2')
        self.assertEqual(wedstrijd.contact_telefoon, 'Test Telefoon 2')
        self.assertEqual(wedstrijd.aantal_banen, 42)
        self.assertEqual(wedstrijd.discipline, 'OD')
        self.assertEqual(wedstrijd.scheidsrechters, 'Scheids1\nScheids2')
        self.assertEqual(wedstrijd.begrenzing, 'V')
        self.assertTrue(wedstrijd.extern_beheerd)

        # niet bestaande wedstrijd
        resp = self.client.get(self.url_kalender_wijzig_wedstrijd % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')
        resp = self.client.post(self.url_kalender_wijzig_wedstrijd % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # nu als BB
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

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
        self.assertEqual(1, Wedstrijd.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verwijder_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_manager)
        self.assertEqual(0, Wedstrijd.objects.count())

        wedstrijd.datum_begin = datetime.date(2022, 1, 1)
        wedstrijd.prijs_euro_onder18 = 42.0
        wedstrijd.prijs_euro_normaal = 99.0

        prijs = wedstrijd.bepaal_prijs_voor_sporter(self.sporter)
        self.assertEqual(prijs, 99.0)

        prijs = wedstrijd.bepaal_prijs_voor_sporter(self.sporter_jong)
        self.assertEqual(prijs, 42.0)

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

    def test_wijzig_bad(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # wissel naar HWL en maak een wedstrijd aan
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self._maak_externe_locatie(self.nhbver1)
        resp = self.client.post(self.url_kalender_maak_nieuw, {'keuze': 'nhb'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.all()[0]
        url = self.url_kalender_wijzig_wedstrijd % wedstrijd.pk

        # wijzig velden via de 'post' interface
        with self.assert_max_queries(20):
            resp = self.client.post(url, {})        # geen parameters
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        # geen valide datum (parsing exception)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum_begin': 'not-a-date'})
        self.assert404(resp, 'Geen valide datum')

        # te ver in het verleden
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum_begin': '2000-01-02'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wedstrijd_duur': 'duur_'})
        self.assert404(resp, 'Fout in wedstrijd duur')

        # illegaal aantal banen
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_banen': 'x'})
        self.assert404(resp, 'Fout in aantal banen')

        resp = self.client.post(url, {'sluit': 'sluit_bla'})
        self.assert404(resp, 'Fout in sluiting wedstrijd')

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
            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)      # nog steeds aanwezig?
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
        resp = self.client.post(self.url_kalender_maak_nieuw, {'keuze': 'nhb'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.all()[0]
        url = self.url_kalender_zet_status % wedstrijd.pk

        with self.assert_max_queries(20):
            resp = self.client.post(url, {})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        # doorzetten naar 'Wacht op goedkeuring'
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verder': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
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
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.status, 'O')

        # vanuit ontwerp blijf je in Ontwerp
        with self.assert_max_queries(20):
            resp = self.client.post(url, {})
        self.assert_is_redirect(resp, self.url_kalender_manager)

        # van Ontwerp weer naar Wacht-op-goedkeuring
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verder': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_manager)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.status, 'W')

        # van Wacht-op-goedkeuring door naar Geaccepteerd
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verder': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_manager)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.status, 'A')

        # van Geaccepteerd kan je niet verder of terug
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verder': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_manager)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.status, 'A')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'terug': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_manager)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.status, 'A')

        # Annuleer
        for status in "OWAX":
            wedstrijd.status = status
            wedstrijd.save()
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'annuleer': 'ja'})
            self.assert_is_redirect(resp, self.url_kalender_manager)
            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
            self.assertEqual(wedstrijd.status, 'X')
        # for

        # slechte wedstrijd_pk
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_kalender_zet_status % 999999, {})
        self.assert404(resp, 'Wedstrijd niet gevonden')

    def test_wijzig_wedstrijd_datum(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # maak een wedstrijd en sessie aan
        self._maak_externe_locatie(self.nhbver1)
        resp = self.client.post(self.url_kalender_maak_nieuw, {'keuze': 'nhb'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.all()[0]
        url = self.url_kalender_sessies % wedstrijd.pk
        resp = self.client.post(url, {'nieuwe_sessie': 'graag'})
        self.assert_is_redirect(resp, url)
        self.assertEqual(1, WedstrijdSessie.objects.count())
        sessie = WedstrijdSessie.objects.all()[0]
        self.assertTrue(str(sessie) != '')

        # wijzig de wedstrijd datum en controleer dat de sessie mee gaat
        self.assertEqual(sessie.datum, wedstrijd.datum_begin)
        url = self.url_kalender_wijzig_wedstrijd % wedstrijd.pk
        datum = wedstrijd.datum_begin + datetime.timedelta(days=3)
        resp = self.client.post(url, {'datum_begin': str(datum)})
        self.assert_is_redirect_not_plein(resp)

        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        sessie = WedstrijdSessie.objects.get(pk=sessie.pk)
        self.assertEqual(wedstrijd.datum_begin, datum)
        self.assertEqual(sessie.datum, datum)

    def test_vastpinnen(self):
        # controleer dat sessies en boogtypen niet aangepast kunnen worden als ze in gebruik zijn
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # maak een wedstrijd met twee sessies aan
        self._maak_externe_locatie(self.nhbver1)
        resp = self.client.post(self.url_kalender_maak_nieuw, {'keuze': 'nhb'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.all()[0]
        self.assertEqual(wedstrijd.boogtypen.count(), 5)
        self.assertEqual(wedstrijd.wedstrijdklassen.count(), 70)

        # wedstrijd wordt aangemaakt met alle bogen en wedstrijdklassen aangevinkt
        wkl_pks = list(wedstrijd.wedstrijdklassen.values_list('pk', flat=True))

        # zet een paar boogtypen uit
        url = self.url_kalender_wijzig_wedstrijd % wedstrijd.pk
        post_data = dict()
        post_data['boog_R'] = 'on'
        post_data['boog_C'] = 'on'
        # wedstrijdklassen waarvoor geen boog aangevinkt is, die verdwijnen
        for pk in wkl_pks:
            post_data['klasse_%s' % pk] = 'on'
        # for
        with self.assert_max_queries(20):
            resp = self.client.post(url, post_data)
        self.assert_is_redirect_not_plein(resp)

        self.assertEqual(wedstrijd.boogtypen.count(), 2)                # alleen R en C
        # wedstrijdklassen waarvoor geen boog aangevinkt is, die verdwijnen
        self.assertEqual(wedstrijd.wedstrijdklassen.count(), 28)        # alleen R en C klassen

        # sessie wordt aangemaakt met alle wedstrijdklassen van de wedstrijd
        url = self.url_kalender_sessies % wedstrijd.pk
        resp = self.client.post(url, {'nieuwe_sessie': 'graag'})
        self.assert_is_redirect(resp, url)
        resp = self.client.post(url, {'nieuwe_sessie': 'graag'})
        self.assert_is_redirect(resp, url)
        self.assertEqual(2, WedstrijdSessie.objects.count())
        sessie = WedstrijdSessie.objects.all()[0]
        sessie2 = WedstrijdSessie.objects.all()[1]

        wkl = wedstrijd.wedstrijdklassen.get(volgorde=111)  # Recurve 50+ Heren
        sessie.wedstrijdklassen.set([wkl])        # alle uit, behalve deze
        sessie2.wedstrijdklassen.set([wkl])       # alle uit, behalve deze

        wkl = wedstrijd.wedstrijdklassen.get(volgorde=112)  # Recurve 50+ Dames
        sessie2.wedstrijdklassen.add(wkl)         # nu 2 klassen

        # probeer nu de recurve boog uit te zetten
        url = self.url_kalender_wijzig_wedstrijd % wedstrijd.pk
        del post_data['boog_R']
        with self.assert_max_queries(20):
            resp = self.client.post(url, post_data)
        self.assert_is_redirect_not_plein(resp)

        self.assertEqual(wedstrijd.boogtypen.count(), 2)                # alleen R en C

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # probeer nu alle wedstrijdklassen uit te zetten
        with self.assert_max_queries(20):
            resp = self.client.post(url, {})
        self.assert_is_redirect_not_plein(resp)

        self.assertEqual(wedstrijd.boogtypen.count(), 1)                # alleen R
        self.assertEqual(wedstrijd.wedstrijdklassen.count(), 2)         # alleen de in de sessies gebruikte klassen

        # corner-case: uniseks + gender-specifieke klasse actief
        wkl = KalenderWedstrijdklasse.objects.get(volgorde=110)
        wedstrijd.wedstrijdklassen.add(wkl)
        sessie2.wedstrijdklassen.add(wkl)         # nu 3 klassen

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_wijzig_ifaa(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # wissel naar HWL en maak een wedstrijd aan
        self._maak_externe_locatie(self.nhbver1)  # locatie is noodzakelijk
        self.e2e_wissel_naar_functie(self.functie_hwl)
        resp = self.client.post(self.url_kalender_maak_nieuw, {'keuze': 'ifaa'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.all()[0]
        self.assertTrue(str(wedstrijd) != '')

        url = self.url_kalender_wijzig_wedstrijd % wedstrijd.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

    def test_wijzig_wa(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # wissel naar HWL en maak een wedstrijd aan
        self._maak_externe_locatie(self.nhbver1)  # locatie is noodzakelijk
        self.e2e_wissel_naar_functie(self.functie_hwl)
        resp = self.client.post(self.url_kalender_maak_nieuw, {'keuze': 'wa'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.all()[0]
        self.assertTrue(str(wedstrijd) != '')

        url = self.url_kalender_wijzig_wedstrijd % wedstrijd.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # zet wat parameters, inclusief de prijzen
        datum = '%s-1-1' % (wedstrijd.datum_begin.year + 1)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum_begin': datum,
                                          'wedstrijd_duur': 'duur_5',
                                          'aantal_banen': '0',
                                          'prijs_normaal': '10,23',
                                          'prijs_onder18': '5.56789'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(str(wedstrijd.prijs_euro_onder18), '5.57')
        self.assertEqual(str(wedstrijd.prijs_euro_normaal), '10.23')

        resp = self.client.post(url, {'prijs_normaal': 'crap'})
        self.assert404(resp, 'Geen toegestane prijs')

        resp = self.client.post(url, {'prijs_onder18': 'crap'})
        self.assert404(resp, 'Geen toegestane prijs')

        resp = self.client.post(url, {'prijs_normaal': '-50'})
        self.assert404(resp, 'Geen toegestane prijs')

        resp = self.client.post(url, {'prijs_onder18': '1000'})
        self.assert404(resp, 'Geen toegestane prijs')

# end of file