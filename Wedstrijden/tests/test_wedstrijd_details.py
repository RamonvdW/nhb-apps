# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.definities import ORGANISATIE_WA
from BasisTypen.models import BoogType
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from Sporter.operations import get_sporter_voorkeuren
from Vereniging.models import Vereniging
from Wedstrijden.models import Wedstrijd, WedstrijdSessie
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestWedstrijdenWedstrijdDetails(E2EHelpers, TestCase):

    """ tests voor de Wedstrijden applicatie, module Wedstrijd details """

    url_sporter_voorkeuren = '/sporter/voorkeuren/%s/'                    # sporter_pk
    url_wedstrijden_maak_nieuw = '/wedstrijden/vereniging/kies-type/'
    url_wedstrijden_wijzig_wedstrijd = '/wedstrijden/%s/wijzig/'          # wedstrijd_pk

    url_wedstrijden_wedstrijd_details = '/wedstrijden/%s/details/'        # wedstrijd_pk

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

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

        # wordt HWL, stel sporter voorkeuren in en maak een wedstrijd aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        self.lid_nr = 123456
        self.account = self.e2e_create_account(str(self.lid_nr), 'test@test.not', 'Voornaam')

        self.boog_r = boog_r = BoogType.objects.get(afkorting='R')

        sporter = Sporter(
                    lid_nr=self.lid_nr,
                    geslacht='M',
                    voornaam='Ad',
                    achternaam='de Admin',
                    geboorte_datum='1966-06-06',
                    sinds_datum='2020-02-02',
                    adres_code='1234AB56',
                    account=self.account,
                    bij_vereniging=self.ver1)
        sporter.save()
        self.sporter = sporter
        self.sporter_voorkeuren = get_sporter_voorkeuren(sporter, mag_database_wijzigen=True)

        # maak alle SporterBoog aan
        resp = self.client.post(self.url_sporter_voorkeuren, {'sporter_pk' : sporter.pk,
                                                              'schiet_R': 'on'})
        self.assert_is_redirect_not_plein(resp)

        sporterboog = SporterBoog.objects.get(sporter=sporter, boogtype=boog_r)
        self.sporterboog = sporterboog

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
        get_sporter_voorkeuren(sporter2)

        SporterBoog(
                sporter=sporter2,
                boogtype=boog_r,
                voor_wedstrijd=True).save()

        # voeg een locatie toe
        locatie = WedstrijdLocatie(
                        baan_type='E',      # externe locatie
                        naam='Test locatie')
        locatie.save()
        locatie.verenigingen.add(self.ver1)

        # wordt HWL en maak een wedstrijd aan
        self.e2e_wissel_naar_functie(self.functie_hwl)

        resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'khsn'})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(1, Wedstrijd.objects.count())
        self.wedstrijd = Wedstrijd.objects.first()
        url = self.url_wedstrijden_wijzig_wedstrijd % self.wedstrijd.pk
        self.assert_is_redirect(resp, url)

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
        self.wkls_r = wkls_r

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
        self.wkls_c = wkls_c

    def test_wedstrijd_info(self):
        resp = self.client.get(self.url_wedstrijden_wedstrijd_details % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # wedstrijd info met WA status
        self.wedstrijd.organisatie = ORGANISATIE_WA
        self.wedstrijd.save(update_fields=['organisatie'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_wedstrijd_details % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/wedstrijd-details.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # wedstrijd in de toekomst zetten zodat er op ingeschreven kan worden
        self.wedstrijd.datum_begin += datetime.timedelta(days=10)
        self.wedstrijd.datum_einde = self.wedstrijd.datum_begin
        self.wedstrijd.save(update_fields=['datum_begin', 'datum_einde'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_wedstrijd_details % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/wedstrijd-details.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.client.logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_wedstrijd_details % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/wedstrijd-details.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_uitslag(self):
        self.wedstrijd.url_uitslag_1 = 'http://uitslag.test.not/part_a.pdf'
        self.wedstrijd.url_uitslag_2 = 'http://uitslag.test.not/part_b.pdf'
        self.wedstrijd.url_uitslag_3 = 'http://uitslag.test.not/part_c.pdf'
        self.wedstrijd.url_uitslag_4 = 'http://uitslag.test.not/part_d.pdf'
        self.wedstrijd.eis_kwalificatie_scores = True       # extra coverage
        self.wedstrijd.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_wedstrijd_details % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/wedstrijd-details.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        urls = self.extract_all_urls(resp, skip_menu=True, skip_external=False)
        self.assertTrue('http://uitslag.test.not/part_a.pdf' in urls)
        self.assertTrue('http://uitslag.test.not/part_b.pdf' in urls)
        self.assertTrue('http://uitslag.test.not/part_c.pdf' in urls)
        self.assertTrue('http://uitslag.test.not/part_d.pdf' in urls)

    def test_flyer(self):
        self.wedstrijd.url_flyer = 'http://test.not/flyer.pdf'
        self.wedstrijd.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_wedstrijd_details % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/wedstrijd-details.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        urls = self.extract_all_urls(resp, skip_menu=True, skip_external=False)
        self.assertTrue('http://test.not/flyer.pdf' in urls)

    def test_extern_beheerd(self):
        self.wedstrijd.extern_beheerd = True
        self.wedstrijd.contact_website = 'https://extern.test.not/inschrijven/'
        self.wedstrijd.datum_einde = self.wedstrijd.datum_begin + datetime.timedelta(days=1)    # extra coverage
        self.wedstrijd.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_wedstrijd_details % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/wedstrijd-details.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

# end of file
