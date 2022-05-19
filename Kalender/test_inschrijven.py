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
from .models import KalenderWedstrijd, KalenderWedstrijdSessie, KalenderInschrijving
from TestHelpers.e2ehelpers import E2EHelpers


class TestKalenderInschrijven(E2EHelpers, TestCase):

    """ tests voor de Kalender applicatie, module Inschrijven """

    test_after = ('Kalender.test_wedstrijd',)

    url_kalender_sessies = '/kalender/%s/sessies/'                              # wedstrijd_pk
    url_kalender_wijzig_sessie = '/kalender/%s/sessies/%s/wijzig/'              # wedstrijd_pk, sessie_pk
    url_kalender_wedstrijd_info = '/kalender/%s/info/'                          # wedstrijd_pk

    url_kalender_maak_nieuw = '/kalender/vereniging/kies-type/'
    url_kalender_vereniging = '/kalender/vereniging/'
    url_inschrijven_sporter = '/kalender/inschrijven/%s/sporter/'                   # wedstrijd_pk
    url_inschrijven_sporter_boog = '/kalender/inschrijven/%s/sporter/%s/'           # wedstrijd_pk, boog_afk
    url_inschrijven_groepje = '/kalender/inschrijven/%s/groep/'                     # wedstrijd_pk
    url_inschrijven_groepje_lid_boog = '/kalender/inschrijven/%s/groep/%s/%s/'      # wedstrijd_pk, lid_nr, boog_afk
    url_inschrijven_familie = '/kalender/inschrijven/%s/familie/'                   # wedstrijd_pk
    url_inschrijven_familie_lid_boog = '/kalender/inschrijven/%s/familie/%s/%s/'    # wedstrijd_pk, lid_nr, boog_afk
    url_inschrijven_familie = '/kalender/inschrijven/%s/familie/'                   # wedstrijd_pk
    url_inschrijven_toevoegen = '/kalender/inschrijven/toevoegen/'

    url_sporter_voorkeuren = '/sporter/voorkeuren/%s/'                              # sporter_pk

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
                    bij_vereniging=self.nhbver1)
        sporter.save()
        self.sporter = sporter
        self.sporter_voorkeuren = get_sporter_voorkeuren(sporter)
        self.client.get(self.url_sporter_voorkeuren % sporter.pk)   # maakt alle SporterBoog records aan

        sporterboog = SporterBoog.objects.get(sporter=sporter, boogtype=boog_r)
        sporterboog.voor_wedstrijd = True
        sporterboog.save(update_fields=['voor_wedstrijd'])
        self.sporterboog = sporterboog

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
        locatie.verenigingen.add(self.nhbver1)

        # wordt HWL en maak een wedstrijd aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        resp = self.client.post(self.url_kalender_maak_nieuw, {'keuze': 'nhb'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        self.assertEqual(1, KalenderWedstrijd.objects.count())
        self.wedstrijd = KalenderWedstrijd.objects.all()[0]

        # maak een R sessie aan
        sessie = KalenderWedstrijdSessie(
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
        sessie = KalenderWedstrijdSessie(
                        datum=self.wedstrijd.datum_begin,
                        tijd_begin='10:00',
                        tijd_einde='15:00',
                        max_sporters=50)
        sessie.save()
        self.wedstrijd.sessies.add(sessie)
        wkls = self.wedstrijd.wedstrijdklassen.filter(boogtype__afkorting='C')
        sessie.wedstrijdklassen.set(wkls)
        self.sessie_c = sessie

    def test_anon(self):
        self.client.logout()

        resp = self.client.get(self.url_inschrijven_sporter % self.wedstrijd.pk)
        self.assert403(resp)

        resp = self.client.get(self.url_inschrijven_groepje % self.wedstrijd.pk)
        self.assert403(resp)

        resp = self.client.get(self.url_inschrijven_familie % self.wedstrijd.pk)
        self.assert403(resp)

        resp = self.client.post(self.url_inschrijven_toevoegen)
        self.assert403(resp)

    def test_sporter(self):
        self.e2e_login_and_pass_otp(self.account)
        # self.e2e_wisselnaarrol_sporter()

        # nog niet ingeschreven pagina
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_sporter % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/inschrijven-sporter.dtl', 'plein/site_layout.dtl'))

        # schrijf in
        self.assertEqual(0, KalenderInschrijving.objects.count())
        resp = self.client.post(self.url_inschrijven_toevoegen, {'snel': 1,
                                                                 'wedstrijd': self.wedstrijd.pk,
                                                                 'sporterboog': self.sporterboog.pk,
                                                                 'sessie': self.sessie_r.pk})
        self.assert_is_redirect(resp, self.url_kalender_wedstrijd_info % self.wedstrijd.pk)
        self.assertEqual(1, KalenderInschrijving.objects.count())

        inschrijving = (KalenderInschrijving
                        .objects
                        .select_related('wedstrijd',
                                        'sporterboog',
                                        'sporterboog__sporter')
                        .all())[0]
        self.assertTrue(str(inschrijving) != '')
        self.assertTrue(inschrijving.korte_beschrijving() != '')
        inschrijving.wedstrijd.titel = 'Dit is een erg lange titel die afgekapt gaat worden door de functie'
        self.assertTrue(inschrijving.korte_beschrijving() != '')

        # wel ingeschreven pagina
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_sporter % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/inschrijven-sporter.dtl', 'plein/site_layout.dtl'))

        # bad stuff
        resp = self.client.get(self.url_inschrijven_sporter % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        resp = self.client.post(self.url_inschrijven_toevoegen, {'wedstrijd': 'hoi'})
        self.assert404(resp, 'Slecht verzoek')

        resp = self.client.post(self.url_inschrijven_toevoegen, {'wedstrijd': 999999,
                                                                 'sporterboog': 999999,
                                                                 'sessie': 999999})
        self.assert404(resp, 'Onderdeel van verzoek niet gevonden')

        # login als een gebruiker met een username != lid_nr
        self.account.username = 'hoi'
        self.account.save()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_sporter % self.wedstrijd.pk)
        self.assert404(resp, 'Bondsnummer ontbreekt')

    def test_groepje(self):
        self.e2e_login_and_pass_otp(self.account)
        # self.e2e_wisselnaarrol_sporter()

        url = self.url_inschrijven_groepje % self.wedstrijd.pk

        # nog niet in geschreven
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(url + '?bondsnummer=bla')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(url + '?bondsnummer=0')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_groepje % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        resp = self.client.get(url + '?bondsnummer=%s' % self.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))

        # schrijf in
        resp = self.client.post(self.url_inschrijven_toevoegen, {'snel': 1,
                                                                 'wedstrijd': self.wedstrijd.pk,
                                                                 'sporterboog': self.sporterboog.pk,
                                                                 'sessie': self.sessie_r.pk})
        self.assert_is_redirect(resp, self.url_kalender_wedstrijd_info % self.wedstrijd.pk)

        # al wel ingeschreven
        with self.assert_max_queries(20):
            resp = self.client.get(url + '?bondsnummer=%s' % self.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))

    def test_familie(self):
        self.e2e_login_and_pass_otp(self.account)
        # self.e2e_wisselnaarrol_sporter()

        # nog niet ingeschreven
        with self.assert_max_queries(21):
            resp = self.client.get(self.url_inschrijven_familie % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, 'bla', 'x'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, '0', 'x'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, '999999', 'R'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        url = self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, self.lid_nr, 'r')
        with self.assert_max_queries(21):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

        # schrijf in
        resp = self.client.post(self.url_inschrijven_toevoegen, {'snel': 1,
                                                                 'wedstrijd': self.wedstrijd.pk,
                                                                 'sporterboog': self.sporterboog.pk,
                                                                 'sessie': self.sessie_r.pk,
                                                                 'goto': 'F'})
        self.assert_is_redirect(resp, url)

        # al wel ingeschreven
        with self.assert_max_queries(21):
            resp = self.client.get(self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, self.lid_nr, 'R'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

    def test_sporter_anders(self):
        self.e2e_login_and_pass_otp(self.account)
        # self.e2e_wisselnaarrol_sporter()

        # geslacht anders, voorkeur ingesteld (door Setup) --> kan wel inschrijven
        self.sporter.geslacht = 'X'
        self.sporter.save(update_fields=['geslacht'])

        # nog niet ingeschreven pagina
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_sporter % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/inschrijven-sporter.dtl', 'plein/site_layout.dtl'))

        url = self.url_inschrijven_groepje % self.wedstrijd.pk
        resp = self.client.get(url + '?bondsnummer=%s' % self.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, self.lid_nr, 'R'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

        # geslacht anders, voorkeur nog niet ingesteld --> kan niet inschrijven
        self.sporter_voorkeuren.wedstrijd_geslacht_gekozen = False
        self.sporter_voorkeuren.save(update_fields=['wedstrijd_geslacht_gekozen'])

        # nog niet ingeschreven pagina
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_sporter % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/inschrijven-sporter.dtl', 'plein/site_layout.dtl'))

        url = self.url_inschrijven_groepje % self.wedstrijd.pk
        resp = self.client.get(url + '?bondsnummer=%s' % self.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, self.lid_nr, 'r'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

# end of file
