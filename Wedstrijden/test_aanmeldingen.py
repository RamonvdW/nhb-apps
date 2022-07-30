# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter, SporterBoog, get_sporter_voorkeuren
from Wedstrijden.models import WedstrijdLocatie
from .models import (Wedstrijd, WedstrijdSessie, WedstrijdInschrijving, WedstrijdKortingscode,
                     INSCHRIJVING_STATUS_AFGEMELD, WEDSTRIJD_KORTING_VERENIGING)
from TestHelpers.e2ehelpers import E2EHelpers


class TestWedstrijdenInschrijven(E2EHelpers, TestCase):

    """ tests voor de Wedstrijden applicatie, module Aanmeldingen """

    test_after = ('Wedstrijden.test_wedstrijd',)

    url_aanmeldingen_wedstrijd = '/wedstrijden/%s/aanmeldingen/'       # wedstrijd_pk
    url_aanmeldingen_sporter = '/wedstrijden/sporter/%s/'              # sporter_lid_nr
    url_aanmeldingen_afmelden = '/wedstrijden/afmelden/%s/'            # inschrijving_pk

    url_kalender_wedstrijd_info = '/wedstrijden/%s/info/'                          # wedstrijd_pk
    url_kalender_maak_nieuw = '/wedstrijden/vereniging/kies-type/'
    url_kalender_vereniging = '/wedstrijden/vereniging/'
    url_inschrijven_groepje = '/wedstrijden/inschrijven/%s/groep/'                 # wedstrijd_pk
    url_inschrijven_toevoegen_mandje = '/wedstrijden/inschrijven/toevoegen-mandje/'
    url_sporter_voorkeuren = '/sporter/voorkeuren/%s/'                          # sporter_pk

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

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

        # wordt HWL, stel sporter voorkeuren in en maak een wedstrijd aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        self.lid_nr = 123456
        self.account = self.e2e_create_account(str(self.lid_nr), 'test@nhb.not', 'Voornaam')

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
                    bij_vereniging=self.nhbver1)
        sporter1.save()
        self.sporter1 = sporter1
        self.sporter_voorkeuren = get_sporter_voorkeuren(sporter1)
        self.client.get(self.url_sporter_voorkeuren % sporter1.pk)   # maakt alle SporterBoog records aan

        sporterboog = SporterBoog.objects.get(sporter=sporter1, boogtype=self.boog_r)
        sporterboog.voor_wedstrijd = True
        sporterboog.save(update_fields=['voor_wedstrijd'])
        self.sporterboog1 = sporterboog

        sporter2 = Sporter(
                    lid_nr=self.lid_nr + 1,
                    geslacht='V',
                    voornaam='Fa',
                    achternaam='Millie',
                    geboorte_datum='1966-06-04',
                    sinds_datum='2020-02-02',
                    adres_code='1234AB56',
                    bij_vereniging=self.nhbver1)
        sporter2.save()
        self.sporter2 = sporter2
        get_sporter_voorkeuren(sporter2)
        self.client.get(self.url_sporter_voorkeuren % sporter2.pk)   # maakt alle SporterBoog records aan

        sporterboog = SporterBoog.objects.get(sporter=sporter2, boogtype=self.boog_c)
        sporterboog.voor_wedstrijd = True
        sporterboog.save(update_fields=['voor_wedstrijd'])
        self.sporterboog2 = sporterboog

        # voeg een locatie toe
        locatie = WedstrijdLocatie(
                        baan_type='E',      # externe locatie
                        naam='Test locatie')
        locatie.save()
        locatie.verenigingen.add(self.nhbver1)

        # wordt HWL en maak een wedstrijd aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        resp = self.client.post(self.url_kalender_maak_nieuw, {'keuze': 'nhb'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        self.assertEqual(1, Wedstrijd.objects.count())
        self.wedstrijd = Wedstrijd.objects.all()[0]

        # maak een R sessie aan
        sessie = WedstrijdSessie(
                        datum=self.wedstrijd.datum_begin,
                        tijd_begin='10:00',
                        tijd_einde='15:00',
                        max_sporters=50)
        sessie.save()
        self.wedstrijd.sessies.add(sessie)
        wkls = self.wedstrijd.wedstrijdklassen.filter(boogtype__afkorting='R')
        sessie.wedstrijdklassen.set(wkls)
        self.sessie_r = sessie

        # maak een C sessie aan
        sessie = WedstrijdSessie(
                        datum=self.wedstrijd.datum_begin,
                        tijd_begin='10:00',
                        tijd_einde='15:00',
                        max_sporters=50)
        sessie.save()
        self.wedstrijd.sessies.add(sessie)
        wkls = self.wedstrijd.wedstrijdklassen.filter(boogtype__afkorting='C')
        sessie.wedstrijdklassen.set(wkls)
        self.sessie_c = sessie

        # schrijf de twee sporters in
        self.e2e_login_and_pass_otp(self.account)
        # self.e2e_wisselnaarrol_sporter()
        url = self.url_inschrijven_groepje % self.wedstrijd.pk

        resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'snel': 1,
                                                                        'wedstrijd': self.wedstrijd.pk,
                                                                        'sporterboog': self.sporterboog1.pk,
                                                                        'sessie': self.sessie_r.pk,
                                                                        'boog': self.boog_r.pk})
        self.assert_is_redirect(resp, self.url_kalender_wedstrijd_info % self.wedstrijd.pk)
        self.assertEqual(1, WedstrijdInschrijving.objects.count())
        self.inschrijving1 = WedstrijdInschrijving.objects.all()[0]

        resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'snel': 1,
                                                                        'wedstrijd': self.wedstrijd.pk,
                                                                        'sporterboog': self.sporterboog2.pk,
                                                                        'sessie': self.sessie_r.pk,
                                                                        'boog': self.boog_c.pk})
        self.assert_is_redirect(resp, self.url_kalender_wedstrijd_info % self.wedstrijd.pk)
        self.assertEqual(2, WedstrijdInschrijving.objects.count())
        self.inschrijving2 = WedstrijdInschrijving.objects.exclude(pk=self.inschrijving1.pk)[0]

        korting = WedstrijdKortingscode(
                        code='TESTING1234',
                        geldig_tot_en_met='2099-12-31',
                        uitgegeven_door=self.nhbver1,
                        percentage=42,
                        soort=WEDSTRIJD_KORTING_VERENIGING,
                        voor_vereniging=self.nhbver1)
        korting.save()

        self.inschrijving2.status = INSCHRIJVING_STATUS_AFGEMELD
        self.inschrijving2.gebruikte_code = korting
        self.inschrijving2.save(update_fields=['status', 'gebruikte_code'])

    def test_anon(self):
        self.client.logout()

        resp = self.client.get(self.url_aanmeldingen_wedstrijd % self.wedstrijd.pk)
        self.assert403(resp)

        resp = self.client.get(self.url_aanmeldingen_sporter % self.sporter1.lid_nr)
        self.assert403(resp)

        resp = self.client.get(self.url_aanmeldingen_afmelden % self.inschrijving1.pk)
        self.assert403(resp)

    def test_aanmeldingen(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

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

    def test_details_sporter(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        url = self.url_aanmeldingen_sporter % self.sporter1.lid_nr

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/aanmeldingen-sporter.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(url)

        # als BB
        self.e2e_wisselnaarrol_bb()

        url = self.url_aanmeldingen_sporter % self.sporter2.lid_nr      # is afgemeld
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/aanmeldingen-sporter.dtl', 'plein/site_layout.dtl'))

        # bad
        resp = self.client.get(self.url_aanmeldingen_sporter % 'Y<42')
        self.assert404(resp, 'Geen valide parameter')

        resp = self.client.get(self.url_aanmeldingen_sporter % 999999)
        self.assert404(resp, 'Sporter niet gevonden')

    def test_afmelden(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        url = self.url_aanmeldingen_afmelden % self.inschrijving1.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_aanmeldingen_sporter % self.sporter1.lid_nr)

        # maak een tweede vereniging
        ver2 = NhbVereniging(
                        ver_nr=1001,
                        naam="Kleine Club",
                        regio=NhbRegio.objects.get(regio_nr=112))
        ver2.save()
        self.wedstrijd.organiserende_vereniging = ver2
        self.wedstrijd.save()

        url = self.url_aanmeldingen_afmelden % self.inschrijving1.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert404(resp, 'Verkeerde vereniging')

        # nogmaals, als BB
        self.e2e_wisselnaarrol_bb()

        url = self.url_aanmeldingen_afmelden % self.inschrijving2.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_aanmeldingen_sporter % self.sporter2.lid_nr)

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

        # bad
        resp = self.client.post(self.url_aanmeldingen_afmelden % 999999)
        self.assert404(resp, 'Inschrijving niet gevonden')

        resp = self.client.post(self.url_aanmeldingen_afmelden % 'X=1')
        self.assert404(resp, 'Inschrijving niet gevonden')

# end of file
