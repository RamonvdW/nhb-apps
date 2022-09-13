# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType, KalenderWedstrijdklasse, GESLACHT_ANDERS, GESLACHT_ALLE
from Functie.operations import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter, SporterBoog, get_sporter_voorkeuren
from Wedstrijden.models import (WedstrijdLocatie, INSCHRIJVING_STATUS_AFGEMELD, ORGANISATIE_WA,
                                Wedstrijd, WedstrijdSessie, WedstrijdInschrijving)
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestWedstrijdenInschrijven(E2EHelpers, TestCase):

    """ tests voor de Wedstrijden applicatie, module Inschrijven """

    test_after = ('Wedstrijden.test_wedstrijd',)

    url_wedstrijden_sessies = '/wedstrijden/%s/sessies/'                               # wedstrijd_pk
    url_wedstrijden_wijzig_sessie = '/wedstrijden/%s/sessies/%s/wijzig/'               # wedstrijd_pk, sessie_pk
    url_wedstrijden_wedstrijd_info = '/wedstrijden/%s/info/'                           # wedstrijd_pk
    url_aanmeldingen = '/wedstrijden/%s/aanmeldingen/'                                 # wedstrijd_pk

    url_wedstrijden_maak_nieuw = '/wedstrijden/vereniging/kies-type/'
    url_wedstrijden_vereniging = '/wedstrijden/vereniging/'
    url_inschrijven_sporter = '/wedstrijden/inschrijven/%s/sporter/'                   # wedstrijd_pk
    url_inschrijven_sporter_boog = '/wedstrijden/inschrijven/%s/sporter/%s/'           # wedstrijd_pk, boog_afk
    url_inschrijven_groepje = '/wedstrijden/inschrijven/%s/groep/'                     # wedstrijd_pk
    url_inschrijven_groepje_lid_boog = '/wedstrijden/inschrijven/%s/groep/%s/%s/'      # wedstrijd_pk, lid_nr, boog_afk
    url_inschrijven_familie = '/wedstrijden/inschrijven/%s/familie/'                   # wedstrijd_pk
    url_inschrijven_familie_lid_boog = '/wedstrijden/inschrijven/%s/familie/%s/%s/'    # wedstrijd_pk, lid_nr, boog_afk
    url_inschrijven_handmatig = '/wedstrijden/inschrijven/%s/handmatig/'                 # wedstrijd_pk
    url_inschrijven_handmatig_lid_boog = '/wedstrijden/inschrijven/%s/handmatig/%s/%s/'  # wedstrijd_pk, lid_nr, boog_afk

    url_inschrijven_toevoegen_mandje = '/wedstrijden/inschrijven/toevoegen-mandje/'

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
        self.e2e_login_and_pass_otp(self.account_admin)     # TODO: niet nodig?
        self.e2e_wissel_naar_functie(self.functie_hwl)

        resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'nhb'})
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)
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

    def test_anon(self):
        self.client.logout()

        resp = self.client.get(self.url_inschrijven_sporter % self.wedstrijd.pk)
        self.assert403(resp)

        resp = self.client.get(self.url_inschrijven_groepje % self.wedstrijd.pk)
        self.assert403(resp)

        resp = self.client.get(self.url_inschrijven_familie % self.wedstrijd.pk)
        self.assert403(resp)

        resp = self.client.post(self.url_inschrijven_toevoegen_mandje)
        self.assert403(resp)

    def test_wedstrijd_info(self):
        resp = self.client.get(self.url_wedstrijden_wedstrijd_info % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # wedstrijd info met WA status
        self.wedstrijd.organisatie = ORGANISATIE_WA
        self.wedstrijd.save(update_fields=['organisatie'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_wedstrijd_info % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/wedstrijd-details.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # wedstrijd in de toekomst zetten zodat er op ingeschreven kan worden
        self.wedstrijd.datum_begin += datetime.timedelta(days=10)
        self.wedstrijd.datum_einde = self.wedstrijd.datum_begin
        self.wedstrijd.save(update_fields=['datum_begin', 'datum_einde'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_wedstrijd_info % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/wedstrijd-details.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.client.logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_wedstrijd_info % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/wedstrijd-details.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_sporter(self):
        self.e2e_login_and_pass_otp(self.account)
        # self.e2e_wisselnaarrol_sporter()

        # nog niet ingeschreven pagina
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_sporter % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/inschrijven-sporter.dtl', 'plein/site_layout.dtl'))

        # met boogtype
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_sporter_boog % (self.wedstrijd.pk, 'R'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/inschrijven-sporter.dtl', 'plein/site_layout.dtl'))

        # schrijf in
        self.assertEqual(0, WedstrijdInschrijving.objects.count())
        resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'snel': 1,
                                                                        'wedstrijd': self.wedstrijd.pk,
                                                                        'sporterboog': self.sporterboog.pk,
                                                                        'sessie': self.sessie_r.pk,
                                                                        'klasse': self.wkls_r[0].pk})
        self.assert_is_redirect(resp, self.url_wedstrijden_wedstrijd_info % self.wedstrijd.pk)
        self.assertEqual(1, WedstrijdInschrijving.objects.count())

        inschrijving = (WedstrijdInschrijving
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
        self.assert_template_used(resp, ('wedstrijden/inschrijven-sporter.dtl', 'plein/site_layout.dtl'))

        # bad stuff
        resp = self.client.get(self.url_inschrijven_sporter % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'wedstrijd': 'hoi'})
        self.assert404(resp, 'Slecht verzoek')

        resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'wedstrijd': 999999,
                                                                        'sporterboog': 999999,
                                                                        'sessie': 999999,
                                                                        'klasse': 999999})
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
        self.assert_template_used(resp, ('wedstrijden/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        resp = self.client.get(url + '?bondsnummer=bla')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        resp = self.client.get(url + '?bondsnummer=0')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        resp = self.client.get(self.url_inschrijven_groepje % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        resp = self.client.get(url + '?bondsnummer=%s' % self.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # selecteer een sporter
        url = self.url_inschrijven_groepje_lid_boog % (self.wedstrijd.pk, 'X', 'X')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # te laag lid nr
        url = self.url_inschrijven_groepje_lid_boog % (self.wedstrijd.pk, 0, 'X')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # goed lid nr en boogtype
        url = self.url_inschrijven_groepje_lid_boog % (self.wedstrijd.pk, self.sporter.pk, 'R')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # schrijf in
        resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'snel': 1,
                                                                        'wedstrijd': self.wedstrijd.pk,
                                                                        'sporterboog': self.sporterboog.pk,
                                                                        'sessie': self.sessie_r.pk,
                                                                        'klasse': self.wkls_r[0].pk})
        self.assert_is_redirect(resp, self.url_wedstrijden_wedstrijd_info % self.wedstrijd.pk)

        # al wel ingeschreven
        with self.assert_max_queries(20):
            resp = self.client.get(url + '?bondsnummer=%s' % self.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))

    def test_familie(self):
        self.e2e_login_and_pass_otp(self.account)
        # self.e2e_wisselnaarrol_sporter()

        # nog niet ingeschreven
        with self.assert_max_queries(21):
            resp = self.client.get(self.url_inschrijven_familie % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, 'bla', 'x'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, '0', 'x'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, '999999', 'R'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        url = self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, self.lid_nr, 'r')
        with self.assert_max_queries(21):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

        # schrijf in
        resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'snel': 1,
                                                                        'wedstrijd': self.wedstrijd.pk,
                                                                        'sporterboog': self.sporterboog.pk,
                                                                        'sessie': self.sessie_r.pk,
                                                                        'klasse': self.wkls_r[1].pk,
                                                                        'goto': 'F'})
        self.assert_is_redirect(resp, url)

        # al wel ingeschreven
        with self.assert_max_queries(21):
            resp = self.client.get(self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, self.lid_nr, 'R'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

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
        self.assert_template_used(resp, ('wedstrijden/inschrijven-sporter.dtl', 'plein/site_layout.dtl'))

        url = self.url_inschrijven_groepje % self.wedstrijd.pk
        resp = self.client.get(url + '?bondsnummer=%s' % self.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, self.lid_nr, 'R'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

        # geslacht anders, voorkeur nog niet ingesteld --> kan niet inschrijven
        self.sporter_voorkeuren.wedstrijd_geslacht_gekozen = False
        self.sporter_voorkeuren.save(update_fields=['wedstrijd_geslacht_gekozen'])

        # nog niet ingeschreven pagina
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_sporter % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/inschrijven-sporter.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Om in te kunnen schrijven op deze wedstrijd moet je kiezen')

        url = self.url_inschrijven_groepje % self.wedstrijd.pk
        resp = self.client.get(url + '?bondsnummer=%s' % self.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, self.lid_nr, 'r'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

    def test_handmatig_hwl(self):
        # de HWL kan handmatig sporters toevoegen aan zijn wedstrijd

        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        url = self.url_inschrijven_handmatig % self.wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-handmatig.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # zoek een lid
        resp = self.client.get(url + '?bondsnummer=0')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-handmatig.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(url + '?bondsnummer=%s' % self.sporter.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-handmatig.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # poging tot aanmelden
        resp = self.client.post(url, {'sporterboog': 'x', 'sessie': 0})
        self.assert404(resp, 'Slecht verzoek')

        resp = self.client.post(url, {'sporterboog': 0, 'sessie': 'x'})
        self.assert404(resp, 'Slecht verzoek')

        resp = self.client.post(url, {'sporterboog': 999999, 'sessie': 999999, 'klasse': 999999})
        self.assert404(resp, 'Onderdeel van verzoek niet gevonden')

        resp = self.client.post(url, {'sporterboog': 999999, 'sessie': self.sessie_r.pk, 'klasse': self.wkls_r[0].pk})
        self.assert404(resp, 'Onderdeel van verzoek niet gevonden')

        self.assertEqual(0, WedstrijdInschrijving.objects.count())

        # echt aanmelden
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'sporterboog': self.sporterboog.pk, 'sessie': self.sessie_r.pk, 'klasse': self.wkls_r[0].pk,
                                          'snel': 1})
        self.assert_is_redirect(resp, self.url_aanmeldingen % self.wedstrijd.pk)

        self.assertEqual(1, WedstrijdInschrijving.objects.count())

        # al aangemeld
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'sporterboog': self.sporterboog.pk, 'sessie': self.sessie_r.pk, 'klasse': self.wkls_r[0].pk})
        self.assert_is_redirect(resp, self.url_aanmeldingen % self.wedstrijd.pk)

        self.assertEqual(1, WedstrijdInschrijving.objects.count())

        # afmelden
        inschrijving = WedstrijdInschrijving.objects.all().select_related('wedstrijd', 'sessie', 'sporterboog')[0]
        self.assertEqual(inschrijving.wedstrijd.pk, self.wedstrijd.pk)
        self.assertEqual(inschrijving.sessie.pk, self.sessie_r.pk)
        self.assertEqual(inschrijving.sporterboog.pk, self.sporterboog.pk)
        inschrijving.status = INSCHRIJVING_STATUS_AFGEMELD
        inschrijving.save(update_fields=['status'])

        # opnieuw aanmelden
        with self.assert_max_queries(24):
            resp = self.client.post(url, {'sporterboog': self.sporterboog.pk, 'sessie': self.sessie_r.pk, 'klasse': self.wkls_r[0].pk,
                                          'snel': 1})
        self.assert_is_redirect(resp, self.url_aanmeldingen % self.wedstrijd.pk)

        self.assertEqual(1, WedstrijdInschrijving.objects.count())

        # doe een get met de sporter ingeschreven
        resp = self.client.get(url + '?bondsnummer=%s' % self.sporter.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-handmatig.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # opnieuw afmelden
        WedstrijdInschrijving.objects.all().delete()

        # url parameters: slecht lid_nr < 100000
        url = self.url_inschrijven_handmatig_lid_boog % (self.wedstrijd.pk, 0, self.boog_r.afkorting)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-handmatig.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # url parameters: select boog type X waardoor sporterboog niet gevonden wordt
        url = self.url_inschrijven_handmatig_lid_boog % (self.wedstrijd.pk, self.sporter.lid_nr, 'X')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-handmatig.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # url parameters: alles goed
        url = self.url_inschrijven_handmatig_lid_boog % (self.wedstrijd.pk, self.sporter.lid_nr, self.boog_r.afkorting)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-handmatig.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # geslacht anders, wel wedstrijdgeslacht gekozen
        self.sporter.geslacht = GESLACHT_ANDERS
        self.sporter.save(update_fields=['geslacht'])
        self.assertTrue(self.sporter_voorkeuren.wedstrijd_geslacht_gekozen)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-handmatig.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertNotContains(resp, 'Om in te kunnen schrijven op deze wedstrijd moet deze sporter eerst instellen om met de mannen of vrouwen mee te doen')

        # geen geslacht gekozen
        self.sporter_voorkeuren.wedstrijd_geslacht_gekozen = False
        self.sporter_voorkeuren.save(update_fields=['wedstrijd_geslacht_gekozen'])

        # geef deze sporter meerdere bogen
        boog_c = BoogType.objects.get(afkorting='C')
        sporterboog2 = SporterBoog.objects.get(sporter=self.sporter, boogtype=boog_c)
        sporterboog2.voor_wedstrijd = True
        sporterboog2.save(update_fields=['voor_wedstrijd'])

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-handmatig.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Om in te kunnen schrijven op deze wedstrijd moet deze sporter eerst instellen om met de mannen of vrouwen mee te doen')

        # niet bestaande wedstrijd
        url = self.url_inschrijven_handmatig % 999999

        resp = self.client.get(url)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        resp = self.client.post(url)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

        # wedstrijd van andere vereniging
        ver2 = NhbVereniging(
                        ver_nr=2000,
                        naam="Test Club",
                        regio=NhbRegio.objects.get(regio_nr=113))
        ver2.save()
        hwl2 = maak_functie('HWL Ver 2000', 'HWL')
        hwl2.nhb_ver = ver2
        hwl2.save()
        hwl2.accounts.add(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)     # doet eval rollen
        self.e2e_wissel_naar_functie(hwl2)

        url = self.url_inschrijven_handmatig % self.wedstrijd.pk
        resp = self.client.get(url)
        self.assert403(resp, 'Wedstrijd van andere vereniging')

        resp = self.client.post(url)
        self.assert403(resp, 'Wedstrijd van andere vereniging')

    def test_handmatig_hwl_anders(self):
        # handmatig inschrijven van een sporter met geslacht 'anders' op een wedstrijd met gender-neutrale klassen

        # verbouw de wedstrijd
        wkls = KalenderWedstrijdklasse.objects.filter(leeftijdsklasse__wedstrijd_geslacht=GESLACHT_ALLE)
        self.wedstrijd.wedstrijdklassen.set(wkls)

        # verbouw de sessies
        wkls = self.wedstrijd.wedstrijdklassen.filter(boogtype__afkorting='R')
        self.sessie_r.wedstrijdklassen.set(wkls)

        wkls = self.wedstrijd.wedstrijdklassen.filter(boogtype__afkorting='C')
        self.sessie_c.wedstrijdklassen.set(wkls)

        # geslacht anders, geen keuze voor wedstrijden gemaakt
        self.sporter.geslacht = GESLACHT_ANDERS
        self.sporter.save(update_fields=['geslacht'])
        self.sporter_voorkeuren.wedstrijd_geslacht_gekozen = False
        self.sporter_voorkeuren.save(update_fields=['wedstrijd_geslacht_gekozen'])

        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        url = self.url_inschrijven_handmatig % self.wedstrijd.pk

        # zoek een lid
        with self.assert_max_queries(20):
            resp = self.client.get(url + '?bondsnummer=%s' % self.sporter.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijden/inschrijven-handmatig.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)


# end of file
