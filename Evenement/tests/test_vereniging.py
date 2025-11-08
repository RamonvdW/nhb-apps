# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Evenement.definities import EVENEMENT_STATUS_GEACCEPTEERD
from Evenement.models import Evenement
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Locatie.models import EvenementLocatie
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestEvenementVereniging(E2EHelpers, TestCase):

    """ tests voor de Evenement applicatie, module Vereniging """

    test_after = ('Evenement.tests.test_details',)

    url_lijst_vereniging = '/kalender/evenement/vereniging/lijst/'
    volgende_bestel_nr = 1234567

    def setUp(self):
        """ initialisatie van de test case """

        self.account_100000 = self.e2e_create_account('100000', 'normaal@test.not', 'Tester',
                                                      accepteer_vhpg=True)

        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(regio_nr=112),
                    bank_iban='IBAN123456789',
                    bank_bic='BIC2BIC',
                    kvk_nummer='KvK1234',
                    website='www.bb.not',
                    contact_email='info@bb.not',
                    telefoonnummer='12345678')
        ver.save()

        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()
        self.functie_hwl.accounts.add(self.account_100000)

        sporter = Sporter(
                        lid_nr=100000,
                        voornaam='Ad',
                        achternaam='de Admin',
                        geboorte_datum='1966-06-06',
                        sinds_datum='2020-02-02',
                        account=self.account_100000,
                        bij_vereniging=ver,
                        adres_code='1234XX')
        sporter.save()
        self.sporter_100000 = sporter

        locatie = EvenementLocatie(
                    naam='Arnhemhal',
                    vereniging=ver,
                    adres='Papendallaan 9\n6816VD Arnhem',
                    plaats='Arnhem')
        locatie.save()

        now_date = timezone.now().date()
        soon_date = now_date + datetime.timedelta(days=10)       # geeft "nog x dagen"

        evenement = Evenement(
                        titel='Test evenement',
                        status=EVENEMENT_STATUS_GEACCEPTEERD,
                        organiserende_vereniging=ver,
                        datum=soon_date,
                        aanvang='09:30',
                        inschrijven_tot=1,
                        locatie=locatie,
                        contact_naam='Dhr. Organisator',
                        contact_email='info@test.not',
                        contact_website='www.test.not',
                        contact_telefoon='023-1234567',
                        beschrijving='Test beschrijving',
                        prijs_euro_normaal="15",
                        prijs_euro_onder18="15")
        evenement.save()
        self.evenement = evenement

    def test_anon(self):
        resp = self.client.get(self.url_lijst_vereniging)
        self.assert_is_redirect_login(resp)

        # inlog, maar geen rol
        self.e2e_login_and_pass_otp(self.account_100000)
        resp = self.client.get(self.url_lijst_vereniging)
        self.assert403(resp, "Geen toegang")

    def test_hwl(self):
        self.e2e_login_and_pass_otp(self.account_100000)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_vereniging)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('evenement/overzicht-vereniging.dtl', 'design/site_layout.dtl'))

        # verwijder alle evenementen
        Evenement.objects.all().delete()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_vereniging)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('evenement/overzicht-vereniging.dtl', 'design/site_layout.dtl'))

    def test_sec(self):
        functie_sec = maak_functie("SEC test", "SEC")
        functie_sec.vereniging = self.functie_hwl.vereniging
        functie_sec.save()
        functie_sec.accounts.add(self.account_100000)

        self.e2e_login_and_pass_otp(self.account_100000)
        self.e2e_wissel_naar_functie(functie_sec)

        self.evenement.datum -= datetime.timedelta(days=100)
        self.evenement.workshop_opties = '1.1 test A\n1.2 test B\n2.1 test C\n'
        self.evenement.save(update_fields=['datum', 'workshop_opties'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_vereniging)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('evenement/overzicht-vereniging.dtl', 'design/site_layout.dtl'))


# end of file
