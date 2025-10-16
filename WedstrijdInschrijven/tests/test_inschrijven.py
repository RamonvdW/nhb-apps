# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.definities import GESLACHT_ANDERS, GESLACHT_ALLE
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from Sporter.operations import get_sporter_voorkeuren
from Vereniging.models import Vereniging
from Wedstrijden.definities import (WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD, WEDSTRIJD_BEGRENZING_VERENIGING,
                                    WEDSTRIJD_BEGRENZING_REGIO, WEDSTRIJD_BEGRENZING_RAYON)
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving
from TestHelpers.e2ehelpers import E2EHelpers


class TestWedstrijdInschrijven(E2EHelpers, TestCase):

    """ tests voor de Wedstrijden applicatie, module Inschrijven """

    test_after = ('Wedstrijden.tests.test_wedstrijd_details',)

    url_wedstrijden_sessies = '/wedstrijden/%s/sessies/'                               # wedstrijd_pk
    url_wedstrijden_wijzig_wedstrijd = '/wedstrijden/%s/wijzig/'                       # wedstrijd_pk
    url_wedstrijden_wijzig_sessie = '/wedstrijden/%s/sessies/%s/wijzig/'               # wedstrijd_pk, sessie_pk
    url_wedstrijden_wedstrijd_details = '/wedstrijden/%s/details/'                     # wedstrijd_pk
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
        self.boog_tr = BoogType.objects.get(afkorting='TR')

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
        resp = self.client.post(self.url_sporter_voorkeuren, {'sporter_pk': sporter.pk,
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
        get_sporter_voorkeuren(sporter2, mag_database_wijzigen=True)

        self.sporterboog2 = SporterBoog(
                                sporter=sporter2,
                                boogtype=boog_r,
                                voor_wedstrijd=True)
        self.sporterboog2.save()

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
        wkls_r = self.wedstrijd.wedstrijdklassen.filter(boogtype__afkorting__in=('R', 'TR'))
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

    def test_sporter(self):
        self.e2e_login_and_pass_otp(self.account)
        # self.e2e_wisselnaarrol_sporter()

        # nog niet ingeschreven pagina
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_sporter % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-sporter.dtl', 'design/site_layout.dtl'))

        # met boogtype
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_sporter_boog % (self.wedstrijd.pk, 'R'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-sporter.dtl', 'design/site_layout.dtl'))

        # schrijf in
        self.assertEqual(0, WedstrijdInschrijving.objects.count())
        resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'snel': 1,
                                                                        'wedstrijd': self.wedstrijd.pk,
                                                                        'sporterboog': self.sporterboog.pk,
                                                                        'sessie': self.sessie_r.pk,
                                                                        'klasse': self.wkls_r[0].pk})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-toegevoegd-aan-mandje.dtl',
                                         'design/site_layout.dtl'))
        self.assertEqual(1, WedstrijdInschrijving.objects.count())

        inschrijving = (WedstrijdInschrijving
                        .objects
                        .select_related('wedstrijd',
                                        'sporterboog',
                                        'sporterboog__sporter')
                        .get(sporterboog=self.sporterboog))
        self.assertTrue(str(inschrijving) != '')
        self.assertTrue(inschrijving.korte_beschrijving() != '')
        inschrijving.wedstrijd.titel = 'Dit is een erg lange titel die afgekapt gaat worden door de functie'
        self.assertTrue(inschrijving.korte_beschrijving() != '')

        # wel ingeschreven pagina
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_sporter % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-sporter.dtl', 'design/site_layout.dtl'))

        # zet tweede boog en probeer opnieuw in te schrijven
        sporterboog = SporterBoog.objects.get(boogtype=self.boog_tr, sporter=self.sporter)
        sporterboog.voor_wedstrijd = True
        sporterboog.save()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_sporter_boog % (self.wedstrijd.pk, 'TR'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-sporter.dtl', 'design/site_layout.dtl'))

        # zet all boog voorkeuren uit
        SporterBoog.objects.filter(sporter=self.sporter).update(voor_wedstrijd=False)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_sporter_boog % (self.wedstrijd.pk, 'TR'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-sporter.dtl', 'design/site_layout.dtl'))

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
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-groepje.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        resp = self.client.get(url + '?bondsnummer=bla')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-groepje.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        resp = self.client.get(url + '?bondsnummer=0')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-groepje.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        resp = self.client.get(self.url_inschrijven_groepje % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        resp = self.client.get(url + '?bondsnummer=%s' % self.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-groepje.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # selecteer een sporter
        url = self.url_inschrijven_groepje_lid_boog % (self.wedstrijd.pk, 'X', 'X')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-groepje.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # te laag lid nr
        url = self.url_inschrijven_groepje_lid_boog % (self.wedstrijd.pk, 0, 'X')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-groepje.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # goed lid nr en boogtype
        url = self.url_inschrijven_groepje_lid_boog % (self.wedstrijd.pk, self.sporter.pk, 'R')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-groepje.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # schrijf in
        resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'snel': 1,
                                                                        'wedstrijd': self.wedstrijd.pk,
                                                                        'sporterboog': self.sporterboog.pk,
                                                                        'sessie': self.sessie_r.pk,
                                                                        'klasse': self.wkls_r[0].pk})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-toegevoegd-aan-mandje.dtl',
                                         'design/site_layout.dtl'))

        # al wel ingeschreven
        with self.assert_max_queries(20):
            resp = self.client.get(url + '?bondsnummer=%s' % self.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-groepje.dtl', 'design/site_layout.dtl'))

    def test_familie(self):
        self.e2e_login_and_pass_otp(self.account)
        # self.e2e_wisselnaarrol_sporter()

        # nog niet ingeschreven
        with self.assert_max_queries(21):
            resp = self.client.get(self.url_inschrijven_familie % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-familie.dtl', 'design/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, 'bla', 'x'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-familie.dtl', 'design/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, '0', 'x'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-familie.dtl', 'design/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, '999999', 'R'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-familie.dtl', 'design/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        url = self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, self.lid_nr, 'r')
        with self.assert_max_queries(21):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-familie.dtl', 'design/site_layout.dtl'))

        # schrijf in
        resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'snel': 1,
                                                                        'wedstrijd': self.wedstrijd.pk,
                                                                        'sporterboog': self.sporterboog.pk,
                                                                        'sessie': self.sessie_r.pk,
                                                                        'klasse': self.wkls_r[1].pk,
                                                                        'goto': 'F'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-toegevoegd-aan-mandje.dtl',
                                         'design/site_layout.dtl'))

        # al wel ingeschreven
        with self.assert_max_queries(21):
            resp = self.client.get(self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, self.lid_nr, 'R'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-familie.dtl', 'design/site_layout.dtl'))

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
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-sporter.dtl', 'design/site_layout.dtl'))

        url = self.url_inschrijven_groepje % self.wedstrijd.pk
        resp = self.client.get(url + '?bondsnummer=%s' % self.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-groepje.dtl', 'design/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, self.lid_nr, 'R'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-familie.dtl', 'design/site_layout.dtl'))

        # geslacht anders, voorkeur nog niet ingesteld --> kan niet inschrijven
        self.sporter_voorkeuren.wedstrijd_geslacht_gekozen = False
        self.sporter_voorkeuren.save(update_fields=['wedstrijd_geslacht_gekozen'])

        # nog niet ingeschreven pagina
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_sporter % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-sporter.dtl', 'design/site_layout.dtl'))
        self.assertContains(resp, 'Om in te kunnen schrijven op deze wedstrijd moet je kiezen')

        url = self.url_inschrijven_groepje % self.wedstrijd.pk
        resp = self.client.get(url + '?bondsnummer=%s' % self.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-groepje.dtl', 'design/site_layout.dtl'))

        url = self.url_inschrijven_familie_lid_boog % (self.wedstrijd.pk, self.lid_nr, 'r')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-familie.dtl', 'design/site_layout.dtl'))

        # corner case: na sluitingsdatum
        self.wedstrijd.datum_begin = timezone.now().date()
        self.wedstrijd.save(update_fields=['datum_begin'])
        resp = self.client.get(url)
        self.assert404(resp, 'Inschrijving is gesloten')

        # corner case: extern beheerde website
        self.wedstrijd.extern_beheerd = True
        self.wedstrijd.save(update_fields=['extern_beheerd'])
        resp = self.client.get(url)
        self.assert404(resp, 'Externe inschrijving')

    def test_handmatig_hwl(self):
        # de HWL kan handmatig sporters toevoegen aan zijn wedstrijd

        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        url = self.url_inschrijven_handmatig % self.wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-handmatig.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # zoek een lid
        resp = self.client.get(url + '?bondsnummer=0')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-handmatig.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(url + '?bondsnummer=%s' % self.sporter.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-handmatig.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # poging tot aanmelden
        resp = self.client.post(url, {'sporterboog': 'x', 'sessie': 0})
        self.assert404(resp, 'Slecht verzoek')

        resp = self.client.post(url, {'sporterboog': 0, 'sessie': 'x'})
        self.assert404(resp, 'Slecht verzoek')

        resp = self.client.post(url, {'sporterboog': 999999, 'sessie': 999999, 'klasse': 999999})
        self.assert404(resp, 'Onderdeel van verzoek niet gevonden')

        resp = self.client.post(url, {'sporterboog': 999999,
                                      'sessie': self.sessie_r.pk,
                                      'klasse': self.wkls_r[0].pk})
        self.assert404(resp, 'Onderdeel van verzoek niet gevonden')

        self.assertEqual(0, WedstrijdInschrijving.objects.count())

        # echt aanmelden
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'sporterboog': self.sporterboog.pk,
                                          'sessie': self.sessie_r.pk,
                                          'klasse': self.wkls_r[0].pk,
                                          'snel': 1})
        self.assert_is_redirect(resp, self.url_aanmeldingen % self.wedstrijd.pk)

        self.assertEqual(1, WedstrijdInschrijving.objects.count())

        # al aangemeld
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'sporterboog': self.sporterboog.pk,
                                          'sessie': self.sessie_r.pk,
                                          'klasse': self.wkls_r[0].pk})
        self.assert_is_redirect(resp, self.url_aanmeldingen % self.wedstrijd.pk)

        self.assertEqual(1, WedstrijdInschrijving.objects.count())

        # afmelden
        inschrijving = WedstrijdInschrijving.objects.all().select_related('wedstrijd', 'sessie', 'sporterboog')[0]
        self.assertEqual(inschrijving.wedstrijd.pk, self.wedstrijd.pk)
        self.assertEqual(inschrijving.sessie.pk, self.sessie_r.pk)
        self.assertEqual(inschrijving.sporterboog.pk, self.sporterboog.pk)
        inschrijving.status = WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD
        inschrijving.save(update_fields=['status'])

        # opnieuw aanmelden
        with self.assert_max_queries(27):
            resp = self.client.post(url, {'sporterboog': self.sporterboog.pk,
                                          'sessie': self.sessie_r.pk,
                                          'klasse': self.wkls_r[0].pk,
                                          'snel': 1})
        self.assert_is_redirect(resp, self.url_aanmeldingen % self.wedstrijd.pk)

        self.assertEqual(1, WedstrijdInschrijving.objects.count())

        # doe een get met de sporter ingeschreven
        resp = self.client.get(url + '?bondsnummer=%s' % self.sporter.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-handmatig.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # opnieuw afmelden
        WedstrijdInschrijving.objects.all().delete()

        # url parameters: slecht lid_nr < 100000
        url = self.url_inschrijven_handmatig_lid_boog % (self.wedstrijd.pk, 0, self.boog_r.afkorting)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-handmatig.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # url parameters: select boog type X waardoor sporterboog niet gevonden wordt
        url = self.url_inschrijven_handmatig_lid_boog % (self.wedstrijd.pk, self.sporter.lid_nr, 'X')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-handmatig.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # url parameters: alles goed
        url = self.url_inschrijven_handmatig_lid_boog % (self.wedstrijd.pk, self.sporter.lid_nr, self.boog_r.afkorting)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-handmatig.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # geslacht anders, wel wedstrijdgeslacht gekozen
        self.sporter.geslacht = GESLACHT_ANDERS
        self.sporter.save(update_fields=['geslacht'])
        self.assertTrue(self.sporter_voorkeuren.wedstrijd_geslacht_gekozen)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-handmatig.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertNotContains(
            resp,
            'Om in te kunnen schrijven op deze wedstrijd moet deze sporter eerst instellen om met de mannen of vrouwen mee te doen')

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
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-handmatig.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(
            resp,
            'Om in te kunnen schrijven op deze wedstrijd moet deze sporter eerst instellen om met de mannen of vrouwen mee te doen')

        # niet bestaande wedstrijd
        url = self.url_inschrijven_handmatig % 999999

        resp = self.client.get(url)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        resp = self.client.post(url)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

        # wedstrijd van andere vereniging
        ver2 = Vereniging(
                        ver_nr=2000,
                        naam="Test Club",
                        regio=Regio.objects.get(regio_nr=113))
        ver2.save()
        hwl2 = maak_functie('HWL Ver 2000', 'HWL')
        hwl2.vereniging = ver2
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
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-handmatig.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_begrenzing_vereniging(self):
        self.e2e_login_and_pass_otp(self.account)

        url = self.url_inschrijven_sporter_boog % (self.wedstrijd.pk, 'R')

        self.wedstrijd.begrenzing = WEDSTRIJD_BEGRENZING_VERENIGING
        self.wedstrijd.save(update_fields=['begrenzing'])

        # wel compatible met doelgroep
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-sporter.dtl', 'design/site_layout.dtl'))

        # zet de wedstrijd over op een andere vereniging dan die van de sporter (self.ver1 / regio 112)
        ver2 = Vereniging(
                        ver_nr=1001,
                        naam="Andere Club",
                        regio=Regio.objects.get(regio_nr=101))      # andere regio en rayon
        ver2.save()
        self.wedstrijd.organiserende_vereniging = ver2
        self.wedstrijd.save(update_fields=['organiserende_vereniging'])

        # niet compatibel met doelgroep
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-sporter.dtl', 'design/site_layout.dtl'))

    def test_begrenzing_regio(self):
        self.e2e_login_and_pass_otp(self.account)

        url = self.url_inschrijven_sporter_boog % (self.wedstrijd.pk, 'R')

        self.wedstrijd.begrenzing = WEDSTRIJD_BEGRENZING_REGIO
        self.wedstrijd.save(update_fields=['begrenzing'])

        # zet de wedstrijd over op een andere vereniging dan die van de sporter (self.ver1 / regio 112)
        ver2 = Vereniging(
                    ver_nr=1001,
                    naam="Andere Club",
                    regio=self.ver1.regio)      # zelfde regio
        ver2.save()
        self.wedstrijd.organiserende_vereniging = ver2
        self.wedstrijd.save(update_fields=['organiserende_vereniging'])

        # wel compatible met doelgroep
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-sporter.dtl', 'design/site_layout.dtl'))

        ver2.regio = Regio.objects.get(regio_nr=101)      # andere regio
        ver2.save(update_fields=['regio'])

        # niet compatibel met doelgroep
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-sporter.dtl', 'design/site_layout.dtl'))

    def test_begrenzing_rayon(self):
        self.e2e_login_and_pass_otp(self.account)

        url = self.url_inschrijven_sporter_boog % (self.wedstrijd.pk, 'R')

        self.wedstrijd.begrenzing = WEDSTRIJD_BEGRENZING_RAYON
        self.wedstrijd.save(update_fields=['begrenzing'])

        # zet de wedstrijd over op een andere vereniging dan die van de sporter (self.ver1 / regio 112)
        ver2 = Vereniging(
                    ver_nr=1001,
                    naam="Andere Club",
                    regio=Regio.objects.get(regio_nr=111))  # zelfde rayon als 112
        ver2.save()
        self.wedstrijd.organiserende_vereniging = ver2
        self.wedstrijd.save(update_fields=['organiserende_vereniging'])

        # wel compatible met doelgroep
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-sporter.dtl', 'design/site_layout.dtl'))

        ver2.regio = Regio.objects.get(regio_nr=101)  # andere rayon
        ver2.save(update_fields=['regio'])

        # niet compatibel met doelgroep
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-sporter.dtl', 'design/site_layout.dtl'))

    def test_geen_wedstrijden(self):
        # vereniging mag niet meedoen aan wedstrijden
        self.ver1.geen_wedstrijden = True
        self.ver1.save(update_fields=['geen_wedstrijden'])

        self.e2e_login_and_pass_otp(self.account)

        url = self.url_inschrijven_sporter_boog % (self.wedstrijd.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-sporter.dtl', 'design/site_layout.dtl'))

# end of file
