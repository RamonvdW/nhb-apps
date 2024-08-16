# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from BasisTypen.models import KalenderWedstrijdklasse
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEANNULEERD, AANTAL_SCHEIDS_GEEN_KEUZE
from Wedstrijden.models import Wedstrijd, WedstrijdSessie
import datetime


class TestWedstrijdenWijzigWedstrijd(E2EHelpers, TestCase):

    """ tests voor de Wedstrijden applicatie, module wedstrijd wijzigen """

    url_wedstrijden_manager = '/wedstrijden/manager/'
    url_wedstrijden_manager_wacht = url_wedstrijden_manager + 'wacht/'
    url_wedstrijden_manager_ontwerp = url_wedstrijden_manager + 'ontwerp/'
    url_wedstrijden_manager_geaccepteerd = url_wedstrijden_manager + 'geaccepteerd/'
    url_wedstrijden_vereniging = '/wedstrijden/vereniging/lijst/'
    url_wedstrijden_maak_nieuw = '/wedstrijden/vereniging/kies-type/'
    url_wedstrijden_wijzig_wedstrijd = '/wedstrijden/%s/wijzig/'  # wedstrijd_pk
    url_wedstrijden_zet_status = '/wedstrijden/%s/zet-status/'    # wedstrijd_pk
    url_wedstrijden_sessies = '/wedstrijden/%s/sessies/'          # wedstrijd_pk

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
        self._maak_externe_locatie(self.ver1)            # locatie is noodzakelijk
        self.e2e_wissel_naar_functie(self.functie_hwl)
        resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'khsn'})
        self.assert_is_redirect_not_plein(resp)

        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.first()
        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk
        self.assert_is_redirect(resp, url)
        self.assertTrue(str(wedstrijd) != '')

        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk

        # haal de wedstrijd op met status 'ontwerp'
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # buiten locatie zonder binnen locatie
        locatie_buiten = self._maak_accommodatie_buiten(self.ver1)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # buiten locatie met binnen locatie
        self._maak_accommodatie_binnen(self.ver1)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

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
                                          'sluit': 'sluit_5',
                                          'kwalificatie_scores': 'X'})
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)

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
        self.assertTrue(wedstrijd.eis_kwalificatie_scores)

        datum = '%s-1-1' % (wedstrijd.datum_begin.year + 1)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum_begin': datum,
                                          'wedstrijd_duur': 'duur_5',
                                          'wa_status': 'wa_A',
                                          'aantal_banen': '0'})
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.wa_status, 'B')
        self.assertFalse(wedstrijd.extern_beheerd)

        # akkoord WA status
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wa_status': 'wa_A',
                                          'akkoord_a_status': 'ja'})
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.wa_status, 'A')

        # akkoord verkoopvoorwaarden
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'akkoord_verkoop': 'ja'})
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertTrue(wedstrijd.verkoopvoorwaarden_status_acceptatie)

        # een GET met akkoord verkoopvoorwaarden geeft de knop om goedkeuring aan te vragen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # zet de wedstrijd hard door 'Wacht op goedkeuring' en haal de pagina opnieuw op
        wedstrijd.status = 'W'
        wedstrijd.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

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
                                          'sluit': 'sluit_9999',
                                          'aantal_scheids': '2'})
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)
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
        self.assertEqual(wedstrijd.aantal_scheids, AANTAL_SCHEIDS_GEEN_KEUZE)     # mag niet

        # zet de wedstrijd door 'Geaccepteerd' en haal de pagina opnieuw op
        wedstrijd.aantal_scheids = 0
        wedstrijd.status = 'A'
        wedstrijd.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # variaties op aantal scheids
        wedstrijd.aantal_scheids = 1
        wedstrijd.save(update_fields=['aantal_scheids'])
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # variaties op aantal scheids
        wedstrijd.aantal_scheids = 5
        wedstrijd.save(update_fields=['aantal_scheids'])
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # zet de wedstrijd door 'Geannuleerd' en haal de pagina opnieuw op
        wedstrijd.aantal_scheids = AANTAL_SCHEIDS_GEEN_KEUZE
        wedstrijd.status = WEDSTRIJD_STATUS_GEANNULEERD
        wedstrijd.save(update_fields=['aantal_scheids', 'status'])
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

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
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)
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
        resp = self.client.get(self.url_wedstrijden_wijzig_wedstrijd % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')
        resp = self.client.post(self.url_wedstrijden_wijzig_wedstrijd % 999999)
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

        # stel het aantal scheidsrechters in
        self.assertEqual(wedstrijd.aantal_scheids, AANTAL_SCHEIDS_GEEN_KEUZE)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': '1'})
        self.assert_is_redirect(resp, self.url_wedstrijden_manager_wacht)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.aantal_scheids, 1)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': '50'})
        self.assert_is_redirect(resp, self.url_wedstrijden_manager_wacht)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.aantal_scheids, 1)

        wedstrijd.status = 'A'      # geaccepteerd
        wedstrijd.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'titel': 'Aangepast door BB'})
        self.assert_is_redirect(resp, self.url_wedstrijden_manager_geaccepteerd)

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
        self.assert_is_redirect(resp, self.url_wedstrijden_manager_ontwerp)
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
        self._maak_externe_locatie(self.ver1)
        resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'khsn'})
        self.assert_is_redirect_not_plein(resp)

        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.first()
        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk
        self.assert_is_redirect(resp, url)

        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk

        # wijzig velden via de 'post' interface
        with self.assert_max_queries(20):
            resp = self.client.post(url, {})        # geen parameters
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)

        # geen valide datum (parsing exception)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum_begin': 'not-a-date'})
        self.assert404(resp, 'Geen valide datum')

        # te ver in het verleden
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum_begin': '2000-01-02'})
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)

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
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)

        # verwijderen in verkeerde fase
        for status in "WAX":
            wedstrijd.status = status
            wedstrijd.save()
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'verwijder_wedstrijd': 'ja'})
            self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)
            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)      # nog steeds aanwezig?
        # for

        # verkeerder vereniging
        wedstrijd.organiserende_vereniging = self.ver2
        wedstrijd.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {})
        self.assert403(resp)

    def test_wijzig_wedstrijd_datum(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # maak een wedstrijd en sessie aan
        self._maak_externe_locatie(self.ver1)
        resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'khsn'})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.first()
        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk
        self.assert_is_redirect(resp, url)

        url = self.url_wedstrijden_sessies % wedstrijd.pk
        resp = self.client.post(url, {'nieuwe_sessie': 'graag'})
        self.assert_is_redirect(resp, url)
        self.assertEqual(1, WedstrijdSessie.objects.count())
        sessie = WedstrijdSessie.objects.first()
        self.assertTrue(str(sessie) != '')

        # wijzig de wedstrijd datum en controleer dat de sessie mee gaat
        self.assertEqual(sessie.datum, wedstrijd.datum_begin)
        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk
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
        self._maak_externe_locatie(self.ver1)
        resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'khsn'})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.first()
        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk
        self.assert_is_redirect(resp, url)
        self.assertEqual(wedstrijd.boogtypen.count(), 5)
        self.assertEqual(wedstrijd.wedstrijdklassen.count(), 70)

        # wedstrijd wordt aangemaakt met alle bogen en wedstrijdklassen aangevinkt
        wkl_pks = list(wedstrijd.wedstrijdklassen.values_list('pk', flat=True))

        # zet een paar boogtypen uit
        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk
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
        url = self.url_wedstrijden_sessies % wedstrijd.pk
        resp = self.client.post(url, {'nieuwe_sessie': 'graag'})
        self.assert_is_redirect(resp, url)
        resp = self.client.post(url, {'nieuwe_sessie': 'graag'})
        self.assert_is_redirect(resp, url)
        self.assertEqual(2, WedstrijdSessie.objects.count())
        sessie = WedstrijdSessie.objects.first()
        sessie2 = WedstrijdSessie.objects.all()[1]

        wkl = wedstrijd.wedstrijdklassen.get(volgorde=111)  # Recurve 50+ Heren
        sessie.wedstrijdklassen.set([wkl])        # alle uit, behalve deze
        sessie2.wedstrijdklassen.set([wkl])       # alle uit, behalve deze

        wkl = wedstrijd.wedstrijdklassen.get(volgorde=112)  # Recurve 50+ Dames
        sessie2.wedstrijdklassen.add(wkl)         # nu 2 klassen

        # probeer nu de recurve boog uit te zetten
        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk
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

        # corner-case: gemengd + gender-specifieke klasse actief
        wkl = KalenderWedstrijdklasse.objects.get(volgorde=110)
        wedstrijd.wedstrijdklassen.add(wkl)
        sessie2.wedstrijdklassen.add(wkl)         # nu 3 klassen

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_wijzig_ifaa(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # wissel naar HWL en maak een wedstrijd aan
        self._maak_externe_locatie(self.ver1)  # locatie is noodzakelijk
        self.e2e_wissel_naar_functie(self.functie_hwl)
        resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'ifaa'})
        self.assert_is_redirect_not_plein(resp)

        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.first()
        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk
        self.assert_is_redirect(resp, url)
        self.assertTrue(str(wedstrijd) != '')

        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

    def test_wijzig_wa(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # wissel naar HWL en maak een wedstrijd aan
        self._maak_externe_locatie(self.ver1)  # locatie is noodzakelijk
        self.e2e_wissel_naar_functie(self.functie_hwl)
        resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'wa'})
        self.assert_is_redirect_not_plein(resp)

        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.first()
        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk
        self.assert_is_redirect(resp, url)
        self.assertTrue(str(wedstrijd) != '')

        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk

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
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)
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

    def test_uitvoerend(self):
        # maak het bondsbureau aan als vereniging
        ver_bb = Vereniging(
                            ver_nr=1234,
                            naam="Bondsbureau",
                            regio=Regio.objects.get(regio_nr=100))
        ver_bb.save()

        # elke vereniging heeft minimaal 1 locatie nodig om een wedstrijd aan te mogen maken
        self._maak_externe_locatie(ver_bb)

        functie_hwl = maak_functie('HWL Ver 1234', 'HWL')
        functie_hwl.vereniging = ver_bb
        functie_hwl.accounts.add(self.account_admin)
        functie_hwl.save()

        # login en wordt HWL van het bondsbureau
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(functie_hwl)

        # test de keuze van een uitvoerende vereniging
        with override_settings(WEDSTRIJDEN_KIES_UITVOERENDE_VERENIGING=(ver_bb.ver_nr,)):
            resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'khsn'})
            self.assert_is_redirect_not_plein(resp)

            self.assertEqual(1, Wedstrijd.objects.count())
            wedstrijd = Wedstrijd.objects.first()
            url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk
            self.assert_is_redirect(resp, url)
            self.assertIsNone(wedstrijd.uitvoerende_vereniging)
            url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk

            # probeer te delegeren, maar die vereniging heeft nog geen locatie
            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)  # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('wedstrijden/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

            with self.assert_max_queries(20):
                resp = self.client.post(url, {'uitvoerend': 'ver_%s' % self.ver1.ver_nr})
            self.assert_is_redirect_not_plein(resp)

            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
            self.assertIsNone(wedstrijd.uitvoerende_vereniging)

            # geef de vereniging waaraan we willen delegeren ook 1 locatie
            loc = self._maak_accommodatie_binnen(self.ver1)

            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)  # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('wedstrijden/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

            with self.assert_max_queries(20):
                resp = self.client.post(url, {'uitvoerend': 'ver_%s' % self.ver1.ver_nr,
                                              'locatie': 'loc_%s' % loc.pk})
            self.assert_is_redirect_not_plein(resp)

            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
            self.assertEqual(wedstrijd.uitvoerende_vereniging, self.ver1)

            # haal de wijzig pagina op, nu met de optie om van een andere vereniging te kiezen
            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)  # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('wedstrijden/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

            # zet de uitvoerende vereniging op de eigen vereniging om deze te "resetten"
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'uitvoerend': 'ver_%s' % ver_bb.ver_nr})
            self.assert_is_redirect_not_plein(resp)

            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
            self.assertIsNone(wedstrijd.uitvoerende_vereniging)

            # corner case
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'uitvoerend': ''})
            self.assert_is_redirect_not_plein(resp)

    def test_ter_info(self):
        # alleen de BB en MWZ mogen de ter-info vlag zetten

        self.e2e_login_and_pass_otp(self.account_admin)

        # wissel naar HWL en maak een wedstrijd aan
        self._maak_externe_locatie(self.ver1)  # locatie is noodzakelijk
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'wa'})
        self.assert_is_redirect_not_plein(resp)

        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.first()
        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk
        self.assert_is_redirect(resp, url)
        self.assertFalse(wedstrijd.is_ter_info)

        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk

        # probeer de 'ter info' vlag te zetten
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'ter_info': 1})
            self.assert_is_redirect_not_plein(resp)

        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertFalse(wedstrijd.is_ter_info)

        # probeer het nog een keer, als BB
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # probeer de 'ter info' vlag te zetten
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'ter_info': 1})
            self.assert_is_redirect_not_plein(resp)

        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertTrue(wedstrijd.is_ter_info)

        # probeer de 'ter info' vlag te resetten
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'ter_info': ''})
            self.assert_is_redirect_not_plein(resp)

        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertFalse(wedstrijd.is_ter_info)

        # haal als HWL het overzicht op met een 'ter info' wedstrijd
        wedstrijd.is_ter_info = True
        wedstrijd.save(update_fields=['is_ter_info'])

        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))


# end of file
