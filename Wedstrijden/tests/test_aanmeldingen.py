# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import BoogType
from Bestel.models import BestelProduct
from Functie.operations import maak_functie
from NhbStructuur.models import NhbRegio
from Sporter.models import Sporter, SporterBoog
from Sporter.operations import get_sporter_voorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import INSCHRIJVING_STATUS_AFGEMELD, WEDSTRIJD_KORTING_VERENIGING
from Wedstrijden.models import WedstrijdLocatie, Wedstrijd, WedstrijdSessie, WedstrijdInschrijving, WedstrijdKorting
from datetime import timedelta


class TestWedstrijdenInschrijven(E2EHelpers, TestCase):

    """ tests voor de Wedstrijden applicatie, module Aanmeldingen """

    test_after = ('Wedstrijden.tests.test_wedstrijd',)

    url_aanmeldingen_wedstrijd = '/wedstrijden/%s/aanmeldingen/'                    # wedstrijd_pk
    url_details_aanmelding = '/wedstrijden/details-aanmelding/%s/'                  # inschrijving_pk
    url_aanmeldingen_afmelden = '/wedstrijden/afmelden/%s/'                         # inschrijving_pk
    url_aanmeldingen_download_tsv = '/wedstrijden/%s/aanmeldingen/download/tsv/'    # wedstrijd_pk
    url_aanmeldingen_download_csv = '/wedstrijden/%s/aanmeldingen/download/csv/'    # wedstrijd_pk

    url_wedstrijd_details = '/wedstrijden/%s/details/'                     # wedstrijd_pk
    url_wedstrijden_maak_nieuw = '/wedstrijden/vereniging/kies-type/'
    url_wedstrijden_vereniging = '/wedstrijden/vereniging/'
    url_inschrijven_groepje = '/wedstrijden/inschrijven/%s/groep/'                  # wedstrijd_pk
    url_inschrijven_toevoegen_mandje = '/wedstrijden/inschrijven/toevoegen-mandje/'
    url_sporter_voorkeuren = '/sporter/voorkeuren/%s/'                              # sporter_pk

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        # maak een test vereniging
        self.ver1 = Vereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=NhbRegio.objects.get(regio_nr=112))
        self.ver1.save()

        self.functie_hwl = maak_functie('HWL Ver 1000', 'HWL')
        self.functie_hwl.vereniging = self.ver1
        self.functie_hwl.accounts.add(self.account_admin)
        self.functie_hwl.save()

        # wordt HWL, stel sporter voorkeuren in en maak een wedstrijd aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        self.lid_nr = 123456
        self.account = self.e2e_create_account(str(self.lid_nr), 'test@test.not', 'Voornaam')

        self.boog_r = BoogType.objects.get(afkorting='R')
        self.boog_c = BoogType.objects.get(afkorting='C')

        sporter1 = Sporter(
                    lid_nr=self.lid_nr,
                    geslacht='M',
                    voornaam='Ad',
                    achternaam='de Admin',
                    geboorte_datum='1966-06-06',
                    sinds_datum='2020-02-02',
                    adres_code='1234AB56',
                    account=self.account,
                    bij_vereniging=self.ver1)
        sporter1.save()
        self.sporter1 = sporter1
        self.sporter_voorkeuren = get_sporter_voorkeuren(sporter1)
        self.client.get(self.url_sporter_voorkeuren % sporter1.pk)   # maakt alle SporterBoog records aan

        sporterboog = SporterBoog.objects.get(sporter=sporter1, boogtype=self.boog_r)
        sporterboog.voor_wedstrijd = True
        sporterboog.save(update_fields=['voor_wedstrijd'])
        self.sporterboog1r = sporterboog

        sporterboog = SporterBoog.objects.get(sporter=sporter1, boogtype=self.boog_c)
        sporterboog.voor_wedstrijd = True
        sporterboog.save(update_fields=['voor_wedstrijd'])
        self.sporterboog1c = sporterboog

        sporter2 = Sporter(
                    lid_nr=self.lid_nr + 1,
                    geslacht='V',
                    voornaam='Fa',
                    achternaam='Millie',
                    geboorte_datum='1966-06-04',
                    sinds_datum='2020-02-02',
                    adres_code='1234AB56',
                    bij_vereniging=self.ver1)
        sporter2.save()
        self.sporter2 = sporter2
        get_sporter_voorkeuren(sporter2)
        self.client.get(self.url_sporter_voorkeuren % sporter2.pk)   # maakt alle SporterBoog records aan

        sporterboog = SporterBoog.objects.get(sporter=sporter2, boogtype=self.boog_c)
        sporterboog.voor_wedstrijd = True
        sporterboog.save(update_fields=['voor_wedstrijd'])
        self.sporterboog2c = sporterboog

        # voeg een locatie toe
        locatie = WedstrijdLocatie(
                        baan_type='E',      # externe locatie
                        naam='Test locatie')
        locatie.save()
        locatie.verenigingen.add(self.ver1)

        # wordt HWL en maak een wedstrijd aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'khsn'})
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)

        self.assertEqual(1, Wedstrijd.objects.count())
        self.wedstrijd = Wedstrijd.objects.first()

        # maak een R sessie aan
        sessie = WedstrijdSessie(
                        datum=self.wedstrijd.datum_begin,
                        tijd_begin='10:00',
                        tijd_einde='15:00',
                        max_sporters=50)
        sessie.save()
        self.wedstrijd.sessies.add(sessie)
        wkls_r = self.wedstrijd.wedstrijdklassen.filter(boogtype__afkorting='R')
        sessie.wedstrijdklassen.set(wkls_r)
        self.sessie_r = sessie

        # maak een C sessie aan
        sessie = WedstrijdSessie(
                        datum=self.wedstrijd.datum_begin,
                        tijd_begin='10:00',
                        tijd_einde='15:00',
                        max_sporters=50)
        sessie.save()
        self.wedstrijd.sessies.add(sessie)
        wkls_c = self.wedstrijd.wedstrijdklassen.filter(boogtype__afkorting='C')
        sessie.wedstrijdklassen.set(wkls_c)
        self.sessie_c = sessie

        # schrijf de twee sporters in
        self.e2e_login_and_pass_otp(self.account)
        # self.e2e_wisselnaarrol_sporter()
        url = self.url_inschrijven_groepje % self.wedstrijd.pk

        # zorg dat de wedstrijd als 'gesloten' gezien wordt
        begin = self.wedstrijd.datum_begin
        self.wedstrijd.datum_begin = timezone.now().date()
        self.wedstrijd.save(update_fields=['datum_begin'])
        resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'snel': 1,
                                                                        'wedstrijd': self.wedstrijd.pk,
                                                                        'sporterboog': self.sporterboog1r.pk,
                                                                        'sessie': self.sessie_r.pk,
                                                                        'klasse': wkls_r[0].pk,
                                                                        'boog': self.boog_r.pk})
        self.assert404(resp, 'Inschrijving is gesloten')

        self.wedstrijd.datum_begin += timedelta(days=self.wedstrijd.inschrijven_tot - 1)
        self.wedstrijd.save(update_fields=['datum_begin'])
        resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'snel': 1,
                                                                        'wedstrijd': self.wedstrijd.pk,
                                                                        'sporterboog': self.sporterboog1r.pk,
                                                                        'sessie': self.sessie_r.pk,
                                                                        'klasse': wkls_r[0].pk,
                                                                        'boog': self.boog_r.pk})
        self.assert404(resp, 'Inschrijving is gesloten')

        self.wedstrijd.datum_begin = begin
        self.wedstrijd.save(update_fields=['datum_begin'])

        resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'snel': 1,
                                                                        'wedstrijd': self.wedstrijd.pk,
                                                                        'sporterboog': self.sporterboog1r.pk,
                                                                        'sessie': self.sessie_r.pk,
                                                                        'klasse': wkls_r[0].pk,
                                                                        'boog': self.boog_r.pk})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/inschrijven-toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(1, WedstrijdInschrijving.objects.count())
        self.inschrijving1r = WedstrijdInschrijving.objects.first()

        resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'snel': 1,
                                                                        'wedstrijd': self.wedstrijd.pk,
                                                                        'sporterboog': self.sporterboog1c.pk,
                                                                        'sessie': self.sessie_c.pk,
                                                                        'klasse': wkls_c[0].pk,
                                                                        'boog': self.boog_c.pk})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/inschrijven-toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(2, WedstrijdInschrijving.objects.count())
        self.inschrijving1c = WedstrijdInschrijving.objects.exclude(pk=self.inschrijving1r.pk)[0]

        resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'snel': 1,
                                                                        'wedstrijd': self.wedstrijd.pk,
                                                                        'sporterboog': self.sporterboog2c.pk,
                                                                        'sessie': self.sessie_c.pk,
                                                                        'klasse': wkls_c[1].pk,
                                                                        'boog': self.boog_c.pk})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/inschrijven-toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(3, WedstrijdInschrijving.objects.count())
        self.inschrijving2 = WedstrijdInschrijving.objects.exclude(pk__in=(self.inschrijving1r.pk,
                                                                           self.inschrijving1c.pk))[0]

        korting = WedstrijdKorting(
                        geldig_tot_en_met='2099-12-31',
                        soort=WEDSTRIJD_KORTING_VERENIGING,
                        uitgegeven_door=self.ver1,
                        percentage=42)
        korting.save()

        self.inschrijving1r.korting = korting
        self.inschrijving1r.save(update_fields=['korting'])

        self.inschrijving2.status = INSCHRIJVING_STATUS_AFGEMELD
        self.inschrijving2.korting = korting
        self.inschrijving2.save(update_fields=['status', 'korting'])

    def test_anon(self):
        self.client.logout()

        resp = self.client.get(self.url_aanmeldingen_wedstrijd % self.wedstrijd.pk)
        self.assert403(resp)

        resp = self.client.get(self.url_details_aanmelding % self.inschrijving1r.pk)
        self.assert403(resp)

        resp = self.client.get(self.url_aanmeldingen_afmelden % self.inschrijving1r.pk)
        self.assert403(resp)

        resp = self.client.get(self.url_aanmeldingen_download_tsv % self.wedstrijd.pk)
        self.assert403(resp)

        resp = self.client.get(self.url_aanmeldingen_download_csv % self.wedstrijd.pk)
        self.assert403(resp)

    def test_aanmeldingen(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        url = self.url_aanmeldingen_wedstrijd % self.wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/aanmeldingen.dtl', 'plein/site_layout.dtl'))

        # als BB (andere kruimels, verder niets)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(url)

        self.e2e_assert_other_http_commands_not_supported(url)

        # bad
        resp = self.client.get(self.url_aanmeldingen_wedstrijd % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        resp = self.client.get(self.url_aanmeldingen_wedstrijd % 'X=1')
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # wordt SEC
        functie_sec = maak_functie('SEC Ver 1000', 'SEC')
        functie_sec.vereniging = self.ver1
        functie_sec.save()
        functie_sec.accounts.add(self.account_admin)

        # opnieuw inloggen om de SEC functie te kunnen zien
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(functie_sec)
        self.e2e_check_rol('SEC')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/aanmeldingen.dtl', 'plein/site_layout.dtl'))

    def test_details_sporter(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        url = self.url_details_aanmelding % self.inschrijving1r.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/aanmelding-details.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(url)

        # als BB
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/aanmelding-details.dtl', 'plein/site_layout.dtl'))

        # # maak de sporter niet ingeschreven
        # self.inschrijving2.delete()
        #
        # url = self.url_details_aanmelding % self.inschrijving2.pk      # is afgemeld
        # print('url=%s' % repr(url))
        # with self.assert_max_queries(20):
        #     resp = self.client.get(url)
        # self.assertEqual(resp.status_code, 200)     # 200 = OK
        # self.assert_html_ok(resp)
        # self.assert_template_used(resp, ('wedstrijden/aanmelding-details.dtl', 'plein/site_layout.dtl'))

        # bad
        resp = self.client.get(self.url_details_aanmelding % 'Y<42')
        self.assert404(resp, 'Geen valide parameter')

        resp = self.client.get(self.url_details_aanmelding % 999999)
        self.assert404(resp, 'Aanmelding niet gevonden')

        # maak 1 inschrijving afgemeld
        self.inschrijving1c.status = INSCHRIJVING_STATUS_AFGEMELD
        self.inschrijving1c.save(update_fields=['status'])

        # verkeerde vereniging
        ver2 = Vereniging(
                        ver_nr=2000,
                        naam="Andere Club",
                        regio=NhbRegio.objects.get(regio_nr=116))
        ver2.save()
        self.wedstrijd.organiserende_vereniging = ver2
        self.wedstrijd.save(update_fields=['organiserende_vereniging'])

        self.e2e_wissel_naar_functie(self.functie_hwl)

        url = self.url_details_aanmelding % self.inschrijving1c.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde vereniging')

    def test_afmelden(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        url = self.url_aanmeldingen_afmelden % self.inschrijving1r.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_details_aanmelding % self.inschrijving1r.pk)

        # maak een tweede vereniging
        ver2 = Vereniging(
                        ver_nr=1001,
                        naam="Kleine Club",
                        regio=NhbRegio.objects.get(regio_nr=112))
        ver2.save()
        self.wedstrijd.organiserende_vereniging = ver2
        self.wedstrijd.save()

        url = self.url_aanmeldingen_afmelden % self.inschrijving1r.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert404(resp, 'Verkeerde vereniging')

        # nogmaals, als BB
        self.e2e_wisselnaarrol_bb()

        url = self.url_aanmeldingen_afmelden % self.inschrijving2.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_details_aanmelding % self.inschrijving2.pk)  # is afgemeld

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

        # bad
        resp = self.client.post(self.url_aanmeldingen_afmelden % 999999)
        self.assert404(resp, 'Inschrijving niet gevonden')

        resp = self.client.post(self.url_aanmeldingen_afmelden % 'X=1')
        self.assert404(resp, 'Inschrijving niet gevonden')

    def test_afmelden_bestelproduct(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        BestelProduct(wedstrijd_inschrijving=self.inschrijving1r).save()

        url = self.url_aanmeldingen_afmelden % self.inschrijving1r.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_details_aanmelding % self.inschrijving1r.pk)

    def test_download(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # echte download
        url = self.url_aanmeldingen_download_tsv % self.wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert200_is_bestand_tsv(resp)

        url = self.url_aanmeldingen_download_csv % self.wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert200_is_bestand_csv(resp)

        # als verkeerde HWL
        ver2 = Vereniging(
                            ver_nr=2000,
                            naam="Extra Club",
                            regio=NhbRegio.objects.get(regio_nr=116))
        ver2.save()

        self.wedstrijd.organiserende_vereniging = ver2
        self.wedstrijd.save(update_fields=['organiserende_vereniging'])

        resp = self.client.get(self.url_aanmeldingen_download_tsv % self.wedstrijd.pk)
        self.assert404(resp, 'Wedstrijd is niet bij jullie vereniging')

        resp = self.client.get(self.url_aanmeldingen_download_csv % self.wedstrijd.pk)
        self.assert404(resp, 'Wedstrijd is niet bij jullie vereniging')

        # nu als BB
        self.e2e_wisselnaarrol_bb()

        # koppel een sporter los van een vereniging
        self.sporter1.bij_vereniging = None
        self.sporter1.save(update_fields=['bij_vereniging'])

        # sporter zonder gekozen geslacht
        self.sporter_voorkeuren.wedstrijd_geslacht_gekozen = False
        self.sporter_voorkeuren.save(update_fields=['wedstrijd_geslacht_gekozen'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanmeldingen_download_tsv % self.wedstrijd.pk)
        self.assert200_is_bestand_tsv(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanmeldingen_download_csv % self.wedstrijd.pk)
        self.assert200_is_bestand_csv(resp)

        # wedstrijd niet gevonden
        resp = self.client.get(self.url_aanmeldingen_download_tsv % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        resp = self.client.get(self.url_aanmeldingen_download_csv % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

# end of file
