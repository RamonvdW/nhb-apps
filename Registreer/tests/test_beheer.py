# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestel.models import Bestelling
from Functie.operations import maak_functie
from Mailer.models import MailQueue
from NhbStructuur.models import Regio
from Registreer.definities import REGISTRATIE_FASE_COMPLEET, REGISTRATIE_FASE_AFGEWEZEN
from Registreer.models import GastRegistratie
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
from Wedstrijden.definities import INSCHRIJVING_STATUS_DEFINITIEF
from Wedstrijden.models import WedstrijdInschrijving, Wedstrijd, WedstrijdSessie, WedstrijdLocatie
import datetime


class TestRegistreerBeheer(E2EHelpers, TestCase):

    """ tests voor de Vereniging applicatie, module gast-accounts """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie', 'Sporter', 'Competitie')

    url_gast_accounts = '/account/registreer/beheer-gast-accounts/'
    url_gast_details = '/account/registreer/beheer-gast-accounts/%s/details/'   # lid_nr
    url_opheffen = '/account/registreer/beheer-gast-accounts/opheffen/'

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

        boog_r = BoogType.objects.get(afkorting='R')
        self.sporterboog_800001 = SporterBoog(sporter=sporter, boogtype=boog_r)
        self.sporterboog_800001.save()

    def test_anon(self):
        self.client.logout()

        resp = self.client.get(self.url_gast_accounts)
        self.assert403(resp)

        resp = self.client.get(self.url_gast_details % 99999)
        self.assert403(resp)

        resp = self.client.post(self.url_opheffen)
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
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_details % self.gast_800001.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/beheer-gast-account-details.dtl', 'plein/site_layout.dtl'))

        # lever twee mogelijke matches
        wa_id = "12345"
        Sporter(
            lid_nr=200001,
            geslacht='M',
            voornaam="Andere voornaam",
            achternaam="Andere achternaam",
            email="andere@test.not",
            geboorte_datum=self.gast_800001.geboorte_datum,
            wa_id=wa_id,
            sinds_datum=datetime.date(year=2010, month=11, day=12),
            bij_vereniging=self.ver1).save()

        self.gast_800001.eigen_lid_nummer = "200001"
        self.gast_800001.club = self.ver1.naam
        self.gast_800001.club_plaats = self.ver1.plaats
        self.gast_800001.account = None     # geen account, dan tonen we hoeveel dagen geleden registratie is gestart
        self.gast_800001.save(update_fields=['eigen_lid_nummer', 'club', 'club_plaats', 'account'])

        Sporter(
            lid_nr=200002,
            geslacht=self.gast_800001.geslacht,
            voornaam=self.gast_800001.voornaam,
            achternaam=self.gast_800001.achternaam,
            email=self.gast_800001.email,
            geboorte_datum=datetime.date(year=2000, month=1, day=1),
            sinds_datum=datetime.date(year=2010, month=11, day=12),
            account=self.account_800001,        # voor de coverage
            bij_vereniging=None).save()

        # haal de details van een gast-account op --> met opheffen knop
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_details % self.gast_800001.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/beheer-gast-account-details.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True)
        #print('urls: %s' % repr(urls))
        self.assertIn(self.url_opheffen, urls)

        # pas de wedstrijdinschrijving aan
        inschrijving.status = INSCHRIJVING_STATUS_DEFINITIEF
        inschrijving.save(update_fields=['status'])

        self.gast_800001.wa_id = wa_id
        self.gast_800001.save(update_fields=['wa_id'])

        # haal de details van een gast-account op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_details % self.gast_800001.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/beheer-gast-account-details.dtl', 'plein/site_layout.dtl'))

        # corner-case: afgewezen
        self.gast_800001.fase = REGISTRATIE_FASE_AFGEWEZEN
        self.gast_800001.save(update_fields=['fase'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_details % self.gast_800001.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/beheer-gast-account-details.dtl', 'plein/site_layout.dtl'))

        # niet bestaand nummer
        with self.assert_max_queries(20):
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
        self.assert_email_html_ok(mail)
        self.assert_consistent_email_html_text(mail)

        # nog een keer (al afgewezen)
        resp = self.client.post(self.url_opheffen, {'lid_nr': self.gast_800001.lid_nr})
        self.assert_is_redirect(resp, self.url_gast_accounts)


# end of file
