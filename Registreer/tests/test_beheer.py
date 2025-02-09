# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestelling.models import Bestelling, BestellingProduct
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Mailer.models import MailQueue
from Registreer.definities import (REGISTRATIE_FASE_COMPLEET, REGISTRATIE_FASE_AFGEWEZEN, REGISTRATIE_FASE_BEGIN,
                                   REGISTRATIE_FASE_EMAIL)
from Registreer.models import GastRegistratie
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
from Webwinkel.models import WebwinkelProduct, WebwinkelKeuze
from Wedstrijden.definities import WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF
from Wedstrijden.models import WedstrijdInschrijving, Wedstrijd, WedstrijdSessie
import datetime


class TestRegistreerBeheer(E2EHelpers, TestCase):

    """ tests voor de Vereniging applicatie, module gast-accounts """

    test_after = ('BasisTypen', 'ImportCRM', 'Functie', 'Sporter', 'Competitie')

    url_gast_accounts = '/account/registreer/beheer-gast-accounts/'
    url_gast_details = '/account/registreer/beheer-gast-accounts/%s/details/'   # lid_nr
    url_opheffen = '/account/registreer/beheer-gast-accounts/opheffen/'
    url_overzetten = '/account/registreer/beheer-gast-accounts/overzetten/%s/%s/'  # van_lid_nr, naar_lid_nr

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        regio_111 = Regio.objects.get(regio_nr=111)

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=regio_111)
        ver.save()
        self.ver1 = ver

        # maak het lid aan dat SEC wordt
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Secretaris",
                    email="rdesecretaris@gmail.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver)
        sporter.save()
        self.sporter_100001 = sporter

        self.account_sec = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)

        # maak een vereniging aan voor de gasten
        self.ver_extern = Vereniging.objects.get(ver_nr=settings.EXTERN_VER_NR)

        self.functie_sec_extern = maak_functie("SEC extern", "SEC")
        self.functie_sec_extern.vereniging = self.ver_extern
        self.functie_sec_extern.save()
        self.functie_sec_extern.accounts.add(self.account_sec)

        # maak een gast-account aan
        gast = GastRegistratie(
                    lid_nr=800001,
                    fase=REGISTRATIE_FASE_COMPLEET,
                    email="een@gasten.not",
                    email_is_bevestigd=True,
                    voornaam="Een",
                    achternaam="van de Gasten",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    geslacht="V",
                    eigen_sportbond_naam="Eigen bond",
                    eigen_lid_nummer="EB-1234",
                    club="Eigen club",
                    club_plaats="Eigen plaats",
                    land="Eigen land",
                    telefoon="+998877665544",
                    wa_id="",
                    logboek="")
        gast.save()
        self.gast_800001 = gast

        self.account_800001 = self.e2e_create_account(gast.lid_nr, gast.email, gast.voornaam)

        sporter = Sporter(
                    lid_nr=gast.lid_nr,
                    is_gast=True,
                    geslacht=gast.geslacht,
                    voornaam=gast.voornaam,
                    achternaam=gast.achternaam,
                    email=gast.email,
                    geboorte_datum=gast.geboorte_datum,
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=self.ver_extern,
                    account=self.account_800001)
        sporter.save()
        self.sporter_800001 = sporter

        gast.sporter = sporter
        gast.account = self.account_800001
        gast.save(update_fields=['sporter', 'account'])

        self.boog_r = BoogType.objects.get(afkorting='R')
        self.sporterboog_800001 = SporterBoog(sporter=sporter, boogtype=self.boog_r)
        self.sporterboog_800001.save()

        # gast-registratie die nog niet af is
        gast = GastRegistratie(
                    lid_nr=0,
                    fase=REGISTRATIE_FASE_EMAIL,
                    email="een@gasten.not",
                    email_is_bevestigd=False,
                    voornaam="Een",
                    achternaam="van de Gasten",
                    logboek="")
        gast.save()

    def test_anon(self):
        self.client.logout()

        resp = self.client.get(self.url_gast_accounts)
        self.assert403(resp)

        resp = self.client.get(self.url_gast_details % 99999)
        self.assert403(resp)

        resp = self.client.post(self.url_opheffen)
        self.assert403(resp)

        resp = self.client.post(self.url_overzetten % (999999, 999999))
        self.assert403(resp)

    def test_overzicht(self):
        # wordt SEC van de vereniging voor gast-accounts
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec_extern)
        self.e2e_check_rol('SEC')

        # haal de gast-accounts ledenlijst op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_accounts)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/beheer-gast-accounts.dtl', 'plein/site_layout.dtl'))

        # zet een last_login
        self.account_800001.last_login = timezone.now()
        self.account_800001.save(update_fields=['last_login'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_accounts)

        # ontkoppel het account
        self.sporter_800001.account = None
        self.sporter_800001.save(update_fields=['account'])
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/beheer-gast-accounts.dtl', 'plein/site_layout.dtl'))

        self.gast_800001.account = None
        self.gast_800001.fase = REGISTRATIE_FASE_AFGEWEZEN
        self.gast_800001.save(update_fields=['account', 'fase'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_accounts)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/beheer-gast-accounts.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_gast_accounts)

    def test_details(self):
        # wordt SEC van de vereniging voor gast-accounts
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec_extern)
        self.e2e_check_rol('SEC')

        # maak een bestelling aan
        Bestelling(bestel_nr=1, account=self.account_800001).save()

        # maak een inschrijving op een wedstrijd aan
        locatie = WedstrijdLocatie(
                        naam='locatie',
                        adres='',
                        notities='')
        locatie.save()

        datum = "2000-01-01"

        wedstrijd = Wedstrijd(
                        titel='test',
                        datum_begin=datum,
                        datum_einde=datum,
                        organiserende_vereniging=self.ver1,
                        locatie=locatie)
        wedstrijd.save()

        sessie = WedstrijdSessie(datum=datum, tijd_begin="10:00", tijd_einde="11:00")
        sessie.save()

        klasse = KalenderWedstrijdklasse.objects.first()

        inschrijving = WedstrijdInschrijving(
                            wanneer=timezone.now(),
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            sporterboog=self.sporterboog_800001,
                            wedstrijdklasse=klasse,
                            koper=self.account_800001)
        inschrijving.save()

        # haal de details van een gast-account op
        # deze heeft een bestelling, is inschrijven voor een wedstrijd en is de koper
        # gast-account kan dus niet opgeheven worden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_details % self.gast_800001.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/beheer-gast-account-details.dtl', 'plein/site_layout.dtl'))
        # self.e2e_open_in_browser(resp)
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [])

        # lever twee mogelijke matches
        wa_id = "12345"
        sporter_200001 = Sporter(
                            lid_nr=200001,
                            geslacht='M',
                            voornaam="Andere voornaam",
                            achternaam="Andere achternaam",
                            email="andere@test.not",
                            geboorte_datum=self.gast_800001.geboorte_datum,
                            wa_id=wa_id,
                            sinds_datum=datetime.date(year=2010, month=11, day=12),
                            bij_vereniging=self.ver1)
        sporter_200001.save()

        self.gast_800001.eigen_lid_nummer = "200001"
        self.gast_800001.club = self.ver1.naam
        self.gast_800001.club_plaats = self.ver1.plaats
        self.gast_800001.account = None     # geen account, dan tonen we hoeveel dagen geleden registratie is gestart
        self.gast_800001.save(update_fields=['eigen_lid_nummer', 'club', 'club_plaats', 'account'])

        sporter_200002 = Sporter(
                            lid_nr=200002,
                            geslacht=self.gast_800001.geslacht,
                            voornaam=self.gast_800001.voornaam,
                            achternaam=self.gast_800001.achternaam,
                            email=self.gast_800001.email,
                            geboorte_datum=datetime.date(year=2000, month=1, day=1),
                            sinds_datum=datetime.date(year=2010, month=11, day=12),
                            account=self.account_800001,        # voor de coverage
                            bij_vereniging=None)
        sporter_200002.save()

        # haal de details van een gast-account op --> zonder overzetten/opheffen knoppen
        # sporter 200001 is de beste kandidaat, maar heeft geen account
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_details % self.gast_800001.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/beheer-gast-account-details.dtl', 'plein/site_layout.dtl'))
        # self.e2e_open_in_browser(resp)
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [])

        # zet het account over
        sporter_200002.account = None
        sporter_200002.save(update_fields=['account'])
        sporter_200001.account = self.account_800001
        sporter_200001.save(update_fields=['account'])

        # haal de details van een gast-account op --> met overzetten knop
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_details % self.gast_800001.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/beheer-gast-account-details.dtl', 'plein/site_layout.dtl'))
        # self.e2e_open_in_browser(resp)
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls: %s' % repr(urls))
        url = self.url_overzetten % (800001, 200001)
        self.assertIn(url, urls)

        # haal de details van een gast-account op --> met opheffen knop
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_details % self.gast_800001.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/beheer-gast-account-details.dtl', 'plein/site_layout.dtl'))
        # self.e2e_open_in_browser(resp)

        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls: %s' % repr(urls))
        url = self.url_overzetten % (800001, 200001)
        self.assertIn(url, urls)

        # pas de wedstrijdinschrijving aan
        inschrijving.status = WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF
        inschrijving.save(update_fields=['status'])

        self.gast_800001.wa_id = wa_id
        self.gast_800001.save(update_fields=['wa_id'])

        # haal de details van het gast-account op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_details % self.gast_800001.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/beheer-gast-account-details.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls: %s' % repr(urls))
        url = self.url_overzetten % (800001, 200001)
        self.assertIn(url, urls)

        # verwijder de inschrijving, dan komt de opheffen knop
        inschrijving.delete()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_details % self.gast_800001.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/beheer-gast-account-details.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls: %s' % repr(urls))
        self.assertIn(self.url_opheffen, urls)

        # corner-case: afgewezen
        self.gast_800001.fase = REGISTRATIE_FASE_AFGEWEZEN
        self.gast_800001.save(update_fields=['fase'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_details % self.gast_800001.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/beheer-gast-account-details.dtl', 'plein/site_layout.dtl'))

        # niet bestaand nummer
        resp = self.client.get(self.url_gast_details % 999999)
        self.assert404(resp, 'Slechte parameter')

        self.e2e_assert_other_http_commands_not_supported(self.url_gast_details % self.gast_800001.lid_nr)

    def test_opheffen(self):
        # wordt SEC van de vereniging voor gast-accounts
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec_extern)
        self.e2e_check_rol('SEC')

        resp = self.client.post(self.url_opheffen)
        self.assert404(resp, 'Niet gevonden')

        resp = self.client.post(self.url_opheffen, {'lid_nr': 999999})
        self.assert404(resp, 'Niet gevonden')

        self.assertEqual(0, MailQueue.objects.count())

        resp = self.client.post(self.url_opheffen, {'lid_nr': self.gast_800001.lid_nr})
        self.assert_is_redirect(resp, self.url_gast_accounts)

        self.assertEqual(1, MailQueue.objects.count())
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_registreer/gast-afgewezen.dtl')
        self.assert_consistent_email_html_text(mail)

        # nog een keer (al afgewezen)
        resp = self.client.post(self.url_opheffen, {'lid_nr': self.gast_800001.lid_nr})
        self.assert_is_redirect(resp, self.url_gast_accounts)

    def test_incompleet_opheffen(self):
        # maak de registratie half af
        # wel een account, geen sporter

        self.gast_800001.sporter = None
        self.gast_800001.save(update_fields=['sporter'])

        self.sporterboog_800001.delete()
        self.sporter_800001.delete()

        # wordt SEC van de vereniging voor gast-accounts
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec_extern)
        self.e2e_check_rol('SEC')

        self.assertEqual(0, MailQueue.objects.count())

        resp = self.client.post(self.url_opheffen, {'lid_nr': self.gast_800001.lid_nr})
        self.assert_is_redirect(resp, self.url_gast_accounts)

        self.assertEqual(1, MailQueue.objects.count())
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_registreer/gast-afgewezen.dtl')
        self.assert_consistent_email_html_text(mail)

        gast = GastRegistratie.objects.get(lid_nr=self.gast_800001.lid_nr)
        self.assertEqual(gast.fase, REGISTRATIE_FASE_AFGEWEZEN)

        # maak nog een gast-account aan
        gast2 = GastRegistratie(
                    lid_nr=800002,
                    fase=REGISTRATIE_FASE_BEGIN,
                    email="twee@gasten.not",
                    email_is_bevestigd=True,
                    voornaam="Twee",
                    achternaam="van de Gasten",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    geslacht="M",
                    eigen_sportbond_naam="Eigen bond",
                    eigen_lid_nummer="EB-1235",
                    club="Eigen club",
                    club_plaats="Eigen plaats",
                    land="Eigen land",
                    telefoon="+998877665545",
                    wa_id="",
                    logboek="")
        gast2.save()

        resp = self.client.post(self.url_opheffen, {'lid_nr': gast2.lid_nr})
        self.assert_is_redirect(resp, self.url_gast_accounts)

        gast2 = GastRegistratie.objects.get(lid_nr=gast2.lid_nr)
        self.assertEqual(gast2.fase, REGISTRATIE_FASE_AFGEWEZEN)

    def test_bestelling_overzetten(self):
        # maak een nieuwe sporter aan voor de overdracht
        sporter = Sporter(
                    lid_nr=100002,
                    geslacht="M",
                    voornaam="Lid",
                    achternaam="Geworden",
                    email="lidgeworden@gmail.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=self.ver1)
        sporter.save()

        van_lid_nr = self.gast_800001.lid_nr
        naar_lid_nr = sporter.lid_nr
        url = self.url_overzetten % (van_lid_nr, naar_lid_nr)

        # wordt SEC van de vereniging voor gast-accounts
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec_extern)
        self.e2e_check_rol('SEC')

        # niet bestaand gastaccount
        resp = self.client.post(self.url_overzetten % (999999, 999999))
        self.assert404(resp, 'Gast-account niet gevonden')

        # niet bestaande sporter
        resp = self.client.post(self.url_overzetten % (van_lid_nr, 999999))
        self.assert404(resp, 'Sporter niet gevonden')

        # sporter heeft geen account
        resp = self.client.post(url)
        self.assert404(resp, 'Sporter heeft nog geen account')

        account = self.e2e_create_account(str(sporter.lid_nr), sporter.email, sporter.voornaam)
        sporter.account = account
        sporter.save(update_fields=['account'])

        # maak een bestelling aan
        bestelling = Bestelling(bestel_nr=1, account=self.account_800001)
        bestelling.save()

        # maak een inschrijving op een wedstrijd aan
        locatie = WedstrijdLocatie(
                        naam='locatie',
                        adres='',
                        notities='')
        locatie.save()

        datum = "2000-01-01"
        wedstrijd = Wedstrijd(
                        titel='test',
                        datum_begin=datum,
                        datum_einde=datum,
                        organiserende_vereniging=self.ver1,
                        locatie=locatie)
        wedstrijd.save()
        sessie = WedstrijdSessie(datum=datum, tijd_begin="10:00", tijd_einde="11:00")
        sessie.save()

        klasse = KalenderWedstrijdklasse.objects.first()
        inschrijving = WedstrijdInschrijving(
                            wanneer=timezone.now(),
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            sporterboog=self.sporterboog_800001,
                            wedstrijdklasse=klasse,
                            koper=self.account_800001)
        inschrijving.save()

        webwinkel_product = WebwinkelProduct()
        webwinkel_product.save()
        keuze = WebwinkelKeuze(
                    wanneer=timezone.now(),
                    koper=self.account_800001,
                    product=webwinkel_product)
        keuze.save()

        prod = BestellingProduct(
                    wedstrijd_inschrijving=inschrijving,
                    webwinkel_keuze=keuze)
        prod.save()
        bestelling.producten.add(prod)

        resp = self.client.post(url)
        self.assert404(resp, 'SporterBoog ontbreekt voor boog R')

        SporterBoog(sporter=sporter, boogtype=self.boog_r).save()

        resp = self.client.post(url)
        url_redir = self.url_gast_details % van_lid_nr
        self.assert_is_redirect(resp, url_redir)

        # nog een keer, andere paden door de code
        bestelling.refresh_from_db()
        bestelling.account = self.account_800001
        bestelling.save(update_fields=['account'])
        resp = self.client.post(url)
        url_redir = self.url_gast_details % van_lid_nr
        self.assert_is_redirect(resp, url_redir)

        # derde keer door de code
        prod.webwinkel_keuze = None
        prod.wedstrijd_inschrijving = None
        prod.save()
        bestelling.account = self.account_800001
        bestelling.save(update_fields=['account'])
        resp = self.client.post(url)
        url_redir = self.url_gast_details % van_lid_nr
        self.assert_is_redirect(resp, url_redir)

        self.e2e_assert_other_http_commands_not_supported(url, get=True, post=False)

# end of file
